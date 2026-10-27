#!/usr/bin/env python3
"""Add typed source uncertainty to the immutable version-1 RPE interpreter.

Only a reviewed catalog supplies measurements, assumptions and source bindings.
Runtime uses the standard library. Nominal source intervals remain descriptive;
source-bounded direction is a heuristic presentation rule, not certification.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
PACK = ROOT / 'benchmarks/rpe-uncertainty-controller-v2-2026-10-26'
V1 = ROOT / 'scripts/controller_rpe_evidence_evaluator.py'
BASE_SHA = '937e44d282df426870761671a0cd21b0b0cb1af26009f7e606042293a62b092b'
TOLERANCE = 2e-10


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate_json_key')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('nonfinite_json_number:' + value)

    result = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)

    def finite_tree(value):
        if isinstance(value, float):
            need(math.isfinite(value), 'nonfinite_json_number')
        if isinstance(value, dict):
            for item in value.values(): finite_tree(item)
        if isinstance(value, list):
            for item in value: finite_tree(item)

    finite_tree(result)
    return result


def validate_shape(value, schema, root=None, location='$'):
    """The closed subset used by the frozen schemas, checked independently."""
    root = schema if root is None else root
    supported = {'$schema', '$defs', '$ref', 'type', 'properties', 'required', 'additionalProperties',
                 'const', 'enum', 'items', 'minItems', 'maxItems', 'uniqueItems', 'minLength', 'pattern'}
    need(not set(schema) - supported, 'unsupported_schema_keyword')
    if '$ref' in schema:
        need(set(schema) == {'$ref'} and schema['$ref'].startswith('#/$defs/'), 'unsupported_schema_reference')
        return validate_shape(value, root['$defs'][schema['$ref'].split('/')[-1]], root, location)
    types = {'object': lambda x: isinstance(x, dict), 'array': lambda x: isinstance(x, list),
             'string': lambda x: isinstance(x, str), 'null': lambda x: x is None}
    if 'type' in schema:
        allowed = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        need(all(t in types for t in allowed), 'unsupported_schema_type')
        need(any(types[t](value) for t in allowed), 'schema_type:' + location)
    if 'const' in schema:
        need(value == schema['const'], 'schema_const:' + location)
    if 'enum' in schema:
        need(value in schema['enum'], 'schema_enum:' + location)
    if isinstance(value, dict):
        properties = schema.get('properties', {})
        need(all(k in value for k in schema.get('required', [])), 'schema_required:' + location)
        if schema.get('additionalProperties') is False:
            need(not set(value) - set(properties), 'schema_unknown_field:' + location)
        for key in value.keys() & properties.keys():
            validate_shape(value[key], properties[key], root, location + '.' + key)
    if isinstance(value, list):
        need(len(value) >= schema.get('minItems', 0), 'schema_min_items:' + location)
        need(len(value) <= schema.get('maxItems', len(value)), 'schema_max_items:' + location)
        if schema.get('uniqueItems'):
            need(len({json.dumps(x, sort_keys=True, allow_nan=False) for x in value}) == len(value), 'schema_duplicate_item:' + location)
        if 'items' in schema:
            for i, item in enumerate(value):
                validate_shape(item, schema['items'], root, location + '[' + str(i) + ']')
    if isinstance(value, str):
        need(len(value) >= schema.get('minLength', 0), 'schema_min_length:' + location)
        if 'pattern' in schema:
            need(re.search(schema['pattern'], value) is not None, 'schema_pattern:' + location)


def number(value):
    need(not isinstance(value, bool), 'boolean_measurement')
    result = float(value)
    need(math.isfinite(result), 'nonfinite_measurement')
    return result


def integer(value):
    need(isinstance(value, str) and re.fullmatch(r'[0-9]+', value) is not None, 'invalid_unit_count')
    return int(value)


def close(actual, expected, reason):
    need(abs(number(actual) - expected) <= TOLERANCE * max(1.0, abs(expected)), reason)


def direction(value):
    return 'increased' if value > 0 else 'decreased' if value < 0 else 'unchanged'


def interval_direction(low, high):
    return 'contains_zero' if low <= 0 <= high else 'increased' if low > 0 else 'decreased'


def resolve(intervals, units, sensitivity, dependence, synthetic=False):
    if synthetic:
        return 'software_control_only'
    if units == 'mixed':
        return 'heterogeneous_units'
    if intervals == 'unavailable':
        return 'precision_unavailable'
    if intervals == 'contains_zero':
        return 'uncertain_direction'
    if not sensitivity:
        return 'sensitivity_fragile'
    if dependence != 'named_donor_pairing':
        return 'conditional_on_unverified_dependence'
    return 'source_bounded_direction'


class Sources:
    def __init__(self, root):
        self.root = root.resolve()
        self.paths = set()
        self.cache = {}

    def path(self, binding):
        relative = binding['path']
        need(isinstance(relative, str) and not Path(relative).is_absolute(), 'source_path_must_be_relative')
        path = (self.root / relative).resolve()
        need(path.is_relative_to(self.root) and path.is_file(), 'source_outside_root_or_missing')
        need(sha(path) == binding['sha256'], 'source_hash_mismatch')
        self.paths.add(path)
        return path

    def json(self, binding):
        path = self.path(binding)
        key = ('json', path)
        if key not in self.cache:
            self.cache[key] = strict_json(path.read_text())
        return self.cache[key]

    def table(self, binding, required):
        path = self.path(binding)
        key = ('table', path)
        if key not in self.cache:
            with path.open(newline='', encoding='utf-8') as stream:
                reader = csv.DictReader(stream, delimiter='\t')
                names = reader.fieldnames or []
                need(names and len(names) == len(set(names)), 'duplicate_or_empty_tsv_header')
                rows = list(reader)
                need(all(None not in r and all(v is not None for v in r.values()) for r in rows), 'malformed_tsv_row')
                self.cache[key] = (set(names), rows)
        names, rows = self.cache[key]
        need(set(required) <= names, 'missing_tsv_field')
        return rows


def unique(rows, field, reason):
    result = {}
    for row in rows:
        key = row[field]
        need(isinstance(key, str) and bool(key.strip()) and key not in result, reason)
        result[key] = row
    return result


def selected(rows, selector):
    return [row for row in rows if all(row.get(k) == v for k, v in selector.items())]


def units_for_method(scores, pairs, metadata, selector, contrast):
    paired = contrast['paired']
    conditions = {contrast['treated'], contrast['control']}
    meta = [r for r in metadata if r['study'] == selector['study'] and r['condition'] in conditions]
    by_column = unique(meta, 'column', 'duplicate_or_missing_metadata_column')
    unique(meta, 'accession', 'duplicate_or_missing_unit_identifier')
    need(all(re.fullmatch(r'GSM[0-9]+', r['accession']) for r in meta), 'invalid_sample_accession')
    need(all(r['primary_normalization'] == 'True' for r in meta), 'nonprimary_unit_in_contrast')
    need(all(r['pairing_admitted'] == str(paired) for r in meta), 'pairing_authority_disagrees')
    local_scores = selected(scores, {k: selector[k] for k in ['study', 'method', 'panel']})
    local_scores = [r for r in local_scores if r['condition'] in conditions and r['status'] == 'primary']
    by_score = unique(local_scores, 'column', 'duplicate_score_unit')
    need(set(by_score) == set(by_column), 'score_metadata_unit_mismatch')
    need(all(r['condition'] == by_column[c]['condition'] for c, r in by_score.items()), 'unit_condition_mismatch')
    treated = [number(r['score']) for r in local_scores if r['condition'] == contrast['treated']]
    control = [number(r['score']) for r in local_scores if r['condition'] == contrast['control']]
    need(len(treated) >= 2 and len(control) >= 2, 'insufficient_unit_replication')
    local_pairs = selected(pairs, selector)
    if not paired:
        need(not local_pairs and all(not r['donor_pair'] for r in meta), 'unpaired_units_cannot_be_paired')
        vector = [{'unit_id': r['accession'], 'column': r['column'],
                   'arm': 'treated' if r['condition'] == contrast['treated'] else 'control',
                   'value': number(by_score[r['column']]['score'])} for r in sorted(meta, key=lambda x: x['column'])]
        return vector, 'unpaired', treated, control, [], set(by_column)
    by_donor = unique(local_pairs, 'donor', 'duplicate_or_missing_donor_pair')
    need(set(by_donor) == {r['donor_pair'] for r in meta} and '' not in by_donor, 'paired_donor_roster_mismatch')
    vector = []
    for donor, row in sorted(by_donor.items()):
        a = [r for r in meta if r['donor_pair'] == donor and r['condition'] == contrast['treated']]
        b = [r for r in meta if r['donor_pair'] == donor and r['condition'] == contrast['control']]
        need(len(a) == len(b) == 1, 'broken_donor_pair')
        av = number(by_score[a[0]['column']]['score'])
        bv = number(by_score[b[0]['column']]['score'])
        close(row['treated'], av, 'pair_score_mismatch')
        close(row['control'], bv, 'pair_score_mismatch')
        close(row['difference'], av - bv, 'pair_difference_mismatch')
        vector.append({'unit_id': donor, 'treated_unit_id': a[0]['accession'], 'control_unit_id': b[0]['accession'],
                       'treated': av, 'control': bv, 'difference': av - bv})
    changes = [r['difference'] for r in vector]
    pattern = 'mixed' if len({direction(v) for v in changes}) > 1 else 'consistent'
    return vector, pattern, treated, control, changes, set(by_donor)


def interval_from_source(row, treated, control, changes, paired):
    need(row['paired'] == str(paired), 'effect_pairing_disagrees')
    need(integer(row['n_treated']) == len(treated) and integer(row['n_control']) == len(control), 'effect_unit_count_mismatch')
    if paired:
        estimate = statistics.mean(changes)
        se = statistics.stdev(changes) / math.sqrt(len(changes))
        df = len(changes) - 1
    else:
        estimate = statistics.mean(treated) - statistics.mean(control)
        a = statistics.variance(treated) / len(treated)
        b = statistics.variance(control) / len(control)
        se = math.sqrt(a + b)
        df = (a + b) ** 2 / (a * a / (len(treated) - 1) + b * b / (len(control) - 1)) if se else len(treated) + len(control) - 2
    close(row['estimate'], estimate, 'effect_estimate_unit_vector_mismatch')
    close(row['se'], se, 'effect_standard_error_mismatch')
    close(row['df'], df, 'effect_degrees_freedom_mismatch')
    method = 'nominal_paired_t' if paired else 'nominal_unpaired_Welch'
    assumptions = ['Three named donor-line pairs; small-sample descriptive interval.'] if paired else [
        'Independence approximation; cross-condition differentiation-round mapping unresolved.']
    if row['status'] == 'unavailable_precision_zero_observed_variance':
        need(se == 0 and not row['ci95_low'] and not row['ci95_high'], 'invented_zero_variance_precision')
        return {'status': 'unavailable', 'reason': row['status'], 'method': method, 'level': None,
                'low': None, 'high': None, 'direction': 'unavailable', 'assumptions': assumptions}, estimate
    need(row['status'] == 'available' and se > 0 and df > 0, 'invalid_available_precision')
    low, high = number(row['ci95_low']), number(row['ci95_high'])
    need(low < high and low <= estimate <= high, 'invalid_interval_bounds')
    close((low + high) / 2, estimate, 'interval_not_centered_on_estimate')
    return {'status': 'available', 'method': method, 'level': .95, 'low': low, 'high': high,
            'direction': interval_direction(low, high), 'assumptions': assumptions,
            'coverage': 'Source nominal descriptive interval; no confirmatory or equivalence claim.'}, estimate


def rna_uncertainty(entry, binding, obs, bundle, sources):
    need(entry['interval_policy'] == 'source_nominal_95' and entry['unit_id_field'] is None, 'invalid_rna_uncertainty_policy')
    contract = sources.json(bundle['contract'])
    methods = contract['normalization']
    need(methods == ['CPM', 'median_ratio'], 'unsupported_or_incomplete_normalizations')
    selector = binding['selector']
    need(set(selector) == {'study', 'method', 'panel', 'contrast'}, 'unsupported_rna_selector')
    need(selector['method'] in methods and binding['study_id'] == selector['study'], 'rna_source_context_mismatch')
    contrasts = [c for c in contract['contrasts'] if c['id'] == selector['contrast'] and c['study'] == selector['study']]
    need(len(contrasts) == 1, 'ambiguous_contrast_contract')
    contrast = contrasts[0]
    need(type(contrast['paired']) is bool and contrast['treated'] != contrast['control'], 'invalid_contrast_design')
    expected_design = 'named_donor_pairing' if contrast['paired'] else 'unresolved_differentiation_round_map'
    need(entry['dependence'] == expected_design, 'unsupported_source_dependence_claim')
    genes = contract['panels'][selector['panel']]['genes']
    need(len(genes) >= 3 and len(set(genes)) == len(genes) and all(isinstance(g, str) and g for g in genes), 'invalid_fixed_panel')
    effects = sources.table(bundle['effects'], ['study', 'method', 'panel', 'contrast', 'paired', 'n_treated', 'n_control', 'estimate', 'se', 'df', 'ci95_low', 'ci95_high', 'status'])
    scores = sources.table(bundle['scores'], ['study', 'method', 'panel', 'column', 'condition', 'score', 'status'])
    pairs = sources.table(bundle['pairs'], ['study', 'method', 'panel', 'contrast', 'donor', 'treated', 'control', 'difference'])
    metadata = sources.table(bundle['samples'], ['study', 'accession', 'column', 'condition', 'donor_pair', 'pairing_admitted', 'primary_normalization'])
    sensitivities = sources.table(bundle['sensitivities'], ['study', 'method', 'panel', 'contrast', 'kind', 'omitted', 'estimate', 'status'])
    common = {k: selector[k] for k in ['study', 'panel', 'contrast']}
    effect_rows = selected(effects, common)
    effect_map = unique(effect_rows, 'method', 'duplicate_normalization_effect')
    need(set(effect_map) == set(methods), 'incomplete_or_unknown_normalization_effect')
    all_sensitivities = selected(sensitivities, common)
    need({r['method'] for r in all_sensitivities} == set(methods), 'incomplete_sensitivity_normalization')
    normalization_results = []
    omission_results = []
    primary = None
    normalization_ok = True
    omissions_ok = True
    for method in methods:
        local_selector = dict(selector, method=method)
        vector, pattern, treated, control, changes, expected_units = units_for_method(scores, pairs, metadata, local_selector, contrast)
        interval, estimate = interval_from_source(effect_map[method], treated, control, changes, contrast['paired'])
        point = direction(estimate)
        normalization_results.append({'method': method, 'estimate': estimate, 'point_direction': point, 'interval': interval})
        unit_kind = 'donor_pair_omission' if contrast['paired'] else 'sample_omission'
        expected = {(unit_kind, unit) for unit in expected_units} | {('panel_gene_omission', gene) for gene in genes}
        rows = [r for r in all_sensitivities if r['method'] == method]
        keys = [(r['kind'], r['omitted']) for r in rows]
        need(len(keys) == len(set(keys)) and set(keys) == expected, 'incomplete_duplicate_or_unplanned_omission')
        values = []
        for row in sorted(rows, key=lambda r: (r['kind'], r['omitted'])):
            need(row['status'] in {'available', 'unavailable_precision_zero_observed_variance'}, 'unrecognized_sensitivity_status')
            value = number(row['estimate'])
            preserved = direction(value) == point
            available = row['status'] == 'available'
            omissions_ok = omissions_ok and preserved and available
            values.append({'kind': row['kind'], 'omitted': row['omitted'], 'estimate': value,
                           'point_direction': direction(value), 'precision_status': row['status'], 'direction_preserved': preserved})
        omission_results.append({'method': method, 'expected_count': len(expected), 'observed_count': len(values), 'values': values})
        if method == selector['method']:
            primary = {'unit_vector': vector, 'unit_pattern': pattern, 'interval': interval, 'estimate': estimate,
                       'n_treated': len(treated), 'n_control': len(control), 'point_direction': point}
            close(obs['mean'], estimate, 'legacy_observation_mean_mismatch')
            expected_values = changes if contrast['paired'] else [estimate]
            need(len(obs['values']) == len(expected_values), 'legacy_unit_vector_length_mismatch')
            for actual, expected_value in zip(obs['values'], expected_values):
                close(actual, expected_value, 'legacy_unit_vector_mismatch')
    point_directions = {r['point_direction'] for r in normalization_results}
    normalization_ok = len(point_directions) == 1
    intervals = [r['interval']['direction'] for r in normalization_results]
    interval_state = 'unavailable' if 'unavailable' in intervals else 'contains_zero' if 'contains_zero' in intervals else 'same_direction'
    if interval_state == 'same_direction':
        normalization_ok = normalization_ok and len(set(intervals)) == 1 and set(intervals) == point_directions
    resolution = resolve(interval_state, primary['unit_pattern'], normalization_ok and omissions_ok, entry['dependence'])
    limits = []
    if primary['unit_pattern'] == 'mixed': limits.append('paired_unit_directions_disagree')
    if interval_state == 'unavailable': limits.append('nominal_precision_unavailable')
    if interval_state == 'contains_zero': limits.append('at_least_one_nominal_interval_contains_zero')
    if not normalization_ok: limits.append('normalization_direction_disagrees')
    if not omissions_ok: limits.append('omission_direction_or_precision_not_stable')
    if entry['dependence'] != 'named_donor_pairing': limits.append('cross_condition_dependence_unresolved')
    return {**primary, 'resolution': resolution, 'normalization': {'methods': normalization_results, 'direction_agreement': normalization_ok},
            'omissions': {'status': 'complete', 'direction_and_precision_preserved': omissions_ok, 'methods': omission_results},
            'source_dependence': entry['dependence'], 'limitations': limits,
            'rna_function_join': {'status': entry['join_status'], 'reason': entry['join_note']},
            'equivalence': 'not_tested', 'source_references': list(bundle.values())}


def function_uncertainty(entry, binding, obs, sources):
    need(entry['bundle_id'] is None and entry['interval_policy'] == 'not_estimated' and entry['dependence'] == 'assay_local_pairing'
         and entry['unit_id_field'] == 'local_experiment', 'function_precision_or_pairing_not_admitted')
    need(binding['calculation'] == 'paired_difference' and binding['modality'] == 'function', 'unsupported_function_binding')
    rows = selected(sources.table(binding, ['local_experiment', binding['value_a'], binding['value_b'], *binding['selector']]), binding['selector'])
    need(len(rows) == binding['expected_rows'], 'function_source_cardinality_mismatch')
    unique(rows, 'local_experiment', 'duplicate_or_missing_function_unit')
    need({r['local_experiment'] for r in rows} == {str(i) for i in range(1, len(rows) + 1)}, 'unknown_function_unit_identifier')
    vector = []
    for row in rows:
        local_id = row['local_experiment']
        need(re.fullmatch(r'[1-9][0-9]*', local_id) is not None, 'invalid_function_unit_identifier')
        a, b = number(row[binding['value_a']]), number(row[binding['value_b']])
        vector.append({'unit_id': binding['evidence_id'] + ':local_experiment:' + local_id,
                       'source_local_experiment': local_id, 'control': a, 'treated': b, 'difference': b - a})
    changes = [r['difference'] for r in vector]
    need(len(changes) == len(obs['values']), 'function_vector_length_mismatch')
    for actual, expected in zip(obs['values'], changes): close(actual, expected, 'function_vector_mismatch')
    close(obs['mean'], statistics.mean(changes), 'function_mean_mismatch')
    return {'estimate': statistics.mean(changes), 'point_direction': direction(statistics.mean(changes)),
            'unit_vector': vector, 'unit_pattern': 'mixed' if len({direction(v) for v in changes}) > 1 else 'consistent',
            'interval': {'status': 'unavailable', 'reason': 'No interval admitted for this source functional summary.', 'level': None, 'low': None, 'high': None, 'direction': 'unavailable'},
            'normalization': {'status': 'not_applicable'}, 'omissions': {'status': 'not_admitted_in_this_uncertainty_extension'},
            'source_dependence': entry['dependence'], 'resolution': 'descriptive_function_only',
            'limitations': ['functional_interval_not_estimated', 'assay_local_labels_do_not_link_assays', 'field_and_per_cell_assays_not_independent_cohorts'],
            'rna_function_join': {'status': entry['join_status'], 'reason': entry['join_note']},
            'equivalence': 'not_tested', 'source_references': [{'path': binding['path'], 'sha256': binding['sha256']}]}


def evaluate_packet(packet, catalog, root=REPO, sources=None):
    sources = Sources(root) if sources is None else sources
    freeze = strict_json((PACK / 'FREEZE.json').read_text())
    need(sha(PACK / 'SCHEMA.json') == freeze['inputs']['SCHEMA.json'], 'frozen_schema_changed')
    schema = strict_json((PACK / 'SCHEMA.json').read_text())
    validate_shape(packet, schema['packet_schema'])
    validate_shape(catalog, schema['catalog_schema'])
    need(catalog['base_engine_sha256'] == BASE_SHA == sha(V1), 'base_engine_hash_mismatch')
    descriptors = unique(catalog['evidence'], 'evidence_id', 'duplicate_catalog_evidence')
    bases = unique(catalog['base_catalogs'], 'id', 'duplicate_base_catalog')
    bundles = unique(catalog['bundles'], 'id', 'duplicate_uncertainty_bundle')
    need(all(eid in descriptors for eid in packet['evidence_ids']), 'unadmitted_evidence')
    base_bindings = {}
    for base_id, reference in bases.items():
        base = sources.json(reference['source'])
        need(base.get('schema') == 'rpe.admission-catalog/1' and base.get('reviewed_cross_assay_links') == [], 'unsupported_base_catalog_or_join')
        base_bindings[base_id] = unique(base['evidence'], 'evidence_id', 'duplicate_base_evidence')
    chosen = []
    for eid in packet['evidence_ids']:
        entry = descriptors[eid]
        need(entry['base_catalog_id'] in base_bindings and eid in base_bindings[entry['base_catalog_id']], 'base_evidence_not_admitted')
        chosen.append(base_bindings[entry['base_catalog_id']][eid])
    spec = importlib.util.spec_from_file_location('immutable_rpe_v1', V1)
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    result = legacy.evaluate_packet({k: v for k, v in packet.items() if k != 'schema'},
             {'schema': 'rpe.admission-catalog/1', 'evidence': chosen, 'reviewed_cross_assay_links': []}, root)
    synthetic = packet['evidence_kind'] == 'synthetic_software_control'
    for observation, binding in zip(result['observations'], chosen):
        entry = descriptors[observation['evidence_id']]
        if entry['kind'] == 'fixed_panel_rna':
            need(binding['modality'] == 'RNA' and entry['bundle_id'] in bundles, 'invalid_rna_bundle')
            uncertainty = rna_uncertainty(entry, binding, observation, bundles[entry['bundle_id']]['sources'], sources)
        else:
            uncertainty = function_uncertainty(entry, binding, observation, sources)
        if synthetic:
            uncertainty['resolution'] = 'software_control_only'
        observation['uncertainty'] = uncertainty
    result['schema'] = 'rpe.uncertainty-evaluation/2'
    result['engine'] = 'deterministic_reviewed_uncertainty_v2'
    result['base_engine_sha256'] = BASE_SHA
    result['uncertainty_schema_sha256'] = sha(PACK / 'SCHEMA.json')
    result['resolution_counts'] = dict(sorted(Counter(o['uncertainty']['resolution'] for o in result['observations']).items()))
    result['axes']['uncertainty'] = 'software_control_only' if synthetic else 'explicit_source_limits_preserved'
    result['uncertainty_policy'] = 'Heuristic source-bounded direction; descriptive nominal intervals, no equivalence inference or restoration promotion.'
    result['reasons'].append('uncertainty_resolution_does_not_supply_missing_function_age_or_safety_authority')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, default=PACK / 'ADMISSION_CATALOG.json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        sources = Sources(REPO)
        packet = strict_json(args.packet.read_text())
        catalog = strict_json(args.catalog.read_text())
        result = evaluate_packet(packet, catalog, sources=sources)
        if args.output:
            protected = sources.paths | {args.packet.resolve(), args.catalog.resolve(), V1.resolve(), (PACK / 'SCHEMA.json').resolve(), (PACK / 'FREEZE.json').resolve(), Path(__file__).resolve()}
            need(args.output.resolve() not in protected, 'output_aliases_evidence_or_input')
        rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
        if args.output:
            args.output.write_text(rendered)
        else:
            print(rendered, end='')
    except (ValueError, KeyError, TypeError, OSError, csv.Error, statistics.StatisticsError) as exc:
        parser.exit(2, 'RPE v2 evidence rejected: ' + str(exc) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
