#!/usr/bin/env python3
"""Independent source extraction, schema agreement and real-CLI rejection tests."""
import argparse
from collections import Counter
import copy
import csv
from decimal import Decimal
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPO = ROOT.parents[1]
ENGINE = ROOT / 'scripts/controller_rpe_uncertainty_evaluator_v2.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def table(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def select(rows, selector):
    return [r for r in rows if all(r[k] == v for k, v in selector.items())]


def sign(value):
    return 1 if value > 0 else -1 if value < 0 else 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    checks = []
    comparisons = 0
    maximum = 0.0

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def numeric(actual, expected, name):
        nonlocal comparisons, maximum
        expected = float(expected)
        actual = float(actual)
        assert math.isfinite(expected) and math.isfinite(actual), name
        error = abs(actual - expected) / max(1.0, abs(expected))
        maximum = max(maximum, error)
        comparisons += 1
        assert error < 2e-10, (name, actual, expected)

    proc = subprocess.run([sys.executable, str(HERE / 'run.py'), '--verify'], capture_output=True, text=True)
    check('all nine CLI packets and deterministic result reproduction', proc.returncode == 0)
    if proc.returncode:
        raise RuntimeError(proc.stdout + proc.stderr)
    catalog = load(HERE / 'ADMISSION_CATALOG.json')
    schema = load(HERE / 'SCHEMA.json')
    cases = load(HERE / 'CASES.json')
    frozen = load(HERE / 'FREEZE.json')
    baseline = load(HERE / 'BASELINE.json')
    for relative, digest in frozen['inputs'].items():
        check('frozen ' + relative, sha(HERE / relative) == digest)
    unchanged = {p: digest for p, digest in baseline['protected_files'].items() if p not in baseline['allowed_later_changes']}
    for relative, digest in unchanged.items():
        check('protected ' + relative, sha(REPO / relative) == digest)
    execution = load(HERE / 'EXECUTION.json')
    check('freeze precedes implementation execution', not frozen['implementation_existed'] and frozen['frozen_at_utc'] < execution['started_at_utc'])
    for reference in catalog['base_catalogs']:
        check('base catalog ' + reference['id'], sha(REPO / reference['source']['path']) == reference['source']['sha256'])
    bases = {r['id']: load(REPO / r['source']['path']) for r in catalog['base_catalogs']}
    descriptor = {r['evidence_id']: r for r in catalog['evidence']}
    source = catalog['bundles'][0]['sources']
    data = {k: table(REPO / r['path']) for k, r in source.items() if k != 'contract'}
    contract = load(REPO / source['contract']['path'])
    canonical = {}
    for record in load(HERE / 'EVALUATIONS.json')['evaluations']:
        if record['packet_id'] not in {'UNLINKED_RNA_FUNCTION', 'SOFTWARE_CONTROL'}:
            for observation in record['evaluation']['observations']:
                canonical[observation['evidence_id']] = observation
    for eid, observation in canonical.items():
        entry = descriptor[eid]
        binding = next(r for r in bases[entry['base_catalog_id']]['evidence'] if r['evidence_id'] == eid)
        uncertainty = observation['uncertainty']
        if entry['kind'] == 'paired_function':
            rows = select(table(REPO / binding['path']), binding['selector'])
            expected_values = [Decimal(r[binding['value_b']]) - Decimal(r[binding['value_a']]) for r in rows]
            vector = uncertainty['unit_vector']
            check(eid + ' all assay-qualified local units', [r['unit_id'] for r in vector] == [eid + ':local_experiment:' + r['local_experiment'] for r in rows])
            for row, original, difference in zip(vector, rows, expected_values):
                numeric(row['control'], Decimal(original[binding['value_a']]), eid)
                numeric(row['treated'], Decimal(original[binding['value_b']]), eid)
                numeric(row['difference'], difference, eid)
            numeric(uncertainty['estimate'], sum(expected_values) / len(expected_values), eid)
            check(eid + ' unavailable precision and function retained', uncertainty['resolution'] == 'descriptive_function_only'
                  and uncertainty['interval']['status'] == 'unavailable' and uncertainty['interval']['low'] is None
                  and uncertainty['interval']['high'] is None and uncertainty['interval']['level'] is None)
            continue
        selector = binding['selector']
        common = {k: selector[k] for k in ['study', 'panel', 'contrast']}
        contrast = next(c for c in contract['contrasts'] if c['study'] == selector['study'] and c['id'] == selector['contrast'])
        effect_rows = select(data['effects'], common)
        directions = []
        interval_directions = []
        omission_stability = True
        primary_pattern = None
        for method in contract['normalization']:
            effects = [r for r in effect_rows if r['method'] == method]
            check(eid + ' ' + method + ' single source effect', len(effects) == 1)
            effect = effects[0]
            current = next(r for r in uncertainty['normalization']['methods'] if r['method'] == method)
            nominal = current['interval']
            low, high = Decimal(effect['ci95_low']), Decimal(effect['ci95_high'])
            interval_directions.append(0 if low <= 0 <= high else 1 if low > 0 else -1)
            directions.append(sign(Decimal(effect['estimate'])))
            numeric(current['estimate'], Decimal(effect['estimate']), eid + ' alternate estimate')
            numeric(nominal['low'], low, eid + ' low')
            numeric(nominal['high'], high, eid + ' high')
            check(eid + ' ' + method + ' source nominal interval', nominal['status'] == 'available' and nominal['level'] == .95)
            score_rows = [r for r in data['scores'] if r['study'] == selector['study'] and r['panel'] == selector['panel']
                          and r['method'] == method and r['condition'] in {contrast['treated'], contrast['control']} and r['status'] == 'primary']
            scores = {r['column']: r for r in score_rows}
            metadata = {r['column']: r for r in data['samples'] if r['study'] == selector['study'] and r['condition'] in {contrast['treated'], contrast['control']}}
            if contrast['paired']:
                pairs = select(data['pairs'], dict(common, method=method))
                values = [Decimal(r['treated']) - Decimal(r['control']) for r in pairs]
                estimate = sum(values) / len(values)
                pattern = 'mixed' if len({sign(v) for v in values}) > 1 else 'consistent'
                if method == selector['method']:
                    by_donor = {r['donor']: r for r in pairs}
                    observed = {r['unit_id']: r for r in uncertainty['unit_vector']}
                    check(eid + ' donor vector complete', set(by_donor) == set(observed))
                    for donor, row in by_donor.items():
                        actual = observed[donor]
                        numeric(actual['difference'], Decimal(row['treated']) - Decimal(row['control']), eid + ' donor')
                        numeric(actual['treated'], Decimal(row['treated']), eid + ' treated')
                        numeric(actual['control'], Decimal(row['control']), eid + ' control')
                        expected_a = next(m['accession'] for m in metadata.values() if m['donor_pair'] == donor and m['condition'] == contrast['treated'])
                        expected_b = next(m['accession'] for m in metadata.values() if m['donor_pair'] == donor and m['condition'] == contrast['control'])
                        check(eid + ' donor accession pairing ' + donor, actual['treated_unit_id'] == expected_a and actual['control_unit_id'] == expected_b)
                expected_units = {r['donor'] for r in pairs}
            else:
                a = [Decimal(r['score']) for r in score_rows if r['condition'] == contrast['treated']]
                b = [Decimal(r['score']) for r in score_rows if r['condition'] == contrast['control']]
                estimate = sum(a) / len(a) - sum(b) / len(b)
                pattern = 'unpaired'
                if method == selector['method']:
                    check(eid + ' unpaired vector keeps six actual samples', len(uncertainty['unit_vector']) == len(a) + len(b) == 6)
                    for row in uncertainty['unit_vector']:
                        original = scores[row['column']]
                        numeric(row['value'], Decimal(original['score']), eid + ' unpaired score')
                        check(eid + ' raw score unit ' + row['column'], row['unit_id'] == metadata[row['column']]['accession']
                              and row['arm'] == ('treated' if original['condition'] == contrast['treated'] else 'control'))
                expected_units = set(scores)
            numeric(effect['estimate'], estimate, eid + ' independently reconstructed contrast')
            if method == selector['method']:
                primary_pattern = pattern
                numeric(uncertainty['estimate'], estimate, eid + ' selected estimate')
            kind = 'donor_pair_omission' if contrast['paired'] else 'sample_omission'
            expected_keys = {(kind, unit) for unit in expected_units} | {('panel_gene_omission', gene) for gene in contract['panels'][selector['panel']]['genes']}
            omissions = select(data['sensitivities'], dict(common, method=method))
            out = next(r for r in uncertainty['omissions']['methods'] if r['method'] == method)
            actual = {(r['kind'], r['omitted']): r for r in out['values']}
            check(eid + ' ' + method + ' every planned omission', set(actual) == expected_keys and out['observed_count'] == out['expected_count'] == len(expected_keys))
            for row in omissions:
                value = Decimal(row['estimate'])
                numeric(actual[row['kind'], row['omitted']]['estimate'], value, eid + ' omission')
                preserved = sign(value) == sign(estimate)
                check(eid + ' ' + method + ' omission sign ' + row['omitted'], actual[row['kind'], row['omitted']]['direction_preserved'] == preserved)
                omission_stability &= preserved and row['status'] == 'available'
        stable_normalizations = len(set(directions)) == 1 and (0 in interval_directions or len(set(interval_directions)) == 1 and set(interval_directions) == set(directions))
        if primary_pattern == 'mixed':
            expected = 'heterogeneous_units'
        elif 0 in interval_directions:
            expected = 'uncertain_direction'
        elif not stable_normalizations or not omission_stability:
            expected = 'sensitivity_fragile'
        elif entry['dependence'] != 'named_donor_pairing':
            expected = 'conditional_on_unverified_dependence'
        else:
            expected = 'source_bounded_direction'
        check(eid + ' independent uncertainty resolution', uncertainty['resolution'] == expected)
        check(eid + ' complete sensitivity and donor descriptors', uncertainty['unit_pattern'] == primary_pattern
              and uncertainty['omissions']['direction_and_precision_preserved'] == omission_stability
              and uncertainty['normalization']['direction_agreement'] == stable_normalizations)
        check(eid + ' no equivalence or function join', uncertainty['equivalence'] == 'not_tested' and uncertainty['rna_function_join']['status'] == 'not_admitted')

    # Production code is imported only after independent source/numerical checks.
    spec = importlib.util.spec_from_file_location('uncertainty_v2_under_test', ENGINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for example in cases['truth_table']:
        check('resolution truth table ' + example['id'], module.resolve(example['intervals'], example['units'], example['sensitivity'], example['dependence']) == example['expected'])
    for low, high, expected in [(-1, 0, 'contains_zero'), (0, 1, 'contains_zero'), (-1, 1, 'contains_zero'), (1, 2, 'increased'), (-2, -1, 'decreased')]:
        check('zero-inclusive interval boundary ' + str((low, high)), module.interval_direction(low, high) == expected)
    for name in ['packet_schema', 'catalog_schema']:
        Draft202012Validator.check_schema(schema[name])
    schema_examples = [(load(HERE / 'packets' / (c['packet_id'] + '.json')), 'packet_schema') for c in cases['valid_packets']]
    schema_examples.append((catalog, 'catalog_schema'))
    packet_template = load(HERE / 'packets/GSE126633_CPM.json')
    for key, value in [('schema', 'wrong'), ('packet_id', True), ('requested_scope', 'clinical'), ('evidence_kind', 'inferred'), ('evidence_ids', []), ('evidence_ids', ['a', 'a'])]:
        item = copy.deepcopy(packet_template); item[key] = value
        schema_examples.append((item, 'packet_schema'))
    for extra in ['interval', 'join', 'confidence', 'restoration_verdict']:
        item = copy.deepcopy(packet_template); item[extra] = True
        schema_examples.append((item, 'packet_schema'))
    for item, name in schema_examples:
        standard = Draft202012Validator(schema[name]).is_valid(item)
        try:
            module.validate_shape(item, schema[name]); custom = True
        except ValueError:
            custom = False
        check('declared schema agreement ' + str(len(checks)), custom == standard)

    rejections = []
    tmp_root = ROOT / 'tmp'
    tmp_root.mkdir(exist_ok=True)
    ignored = subprocess.run(['git', 'check-ignore', str(tmp_root / 'rpe-v2-probe')], cwd=REPO, capture_output=True)
    check('software fixtures confined to ignored controller tmp', ignored.returncode == 0)
    for cid in cases['rejection_cases']:
        with tempfile.TemporaryDirectory(prefix='rpe-v2-', dir=tmp_root) as directory:
            work = Path(directory)
            packet = copy.deepcopy(packet_template)
            altered = copy.deepcopy(catalog)
            target = 'GSE126633_CPM_rpe_identity'
            expected_reason = None
            raw = None
            extra_args = []

            def role_file(role, edit, drop=None):
                reference = altered['bundles'][0]['sources'][role]
                rows = table(REPO / reference['path'])
                fields = list(rows[0])
                edit(rows)
                if drop:
                    fields.remove(drop)
                    for row in rows: row.pop(drop)
                path = work / (role + '.tsv')
                with path.open('w', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=fields, delimiter='\t', lineterminator='\n')
                    writer.writeheader(); writer.writerows(rows)
                reference.update(path=str(path.relative_to(REPO)), sha256=sha(path))

            def relevant(row, method='CPM'):
                return row.get('study') == 'GSE126633' and row.get('panel') == 'rpe_identity' and row.get('contrast') == 'TNT_minus_control' and row.get('method') == method

            def edit_effect(field, value):
                role_file('effects', lambda rows: next(r for r in rows if relevant(r)).update({field: value}))

            if cid.startswith('packet_'):
                changes = {'packet_schema': ('schema', 'wrong'), 'packet_duplicate_evidence': ('evidence_ids', ['x', 'x']),
                    'packet_unknown_evidence': ('evidence_ids', ['unadmitted']), 'packet_interval_override': ('interval', [0, 0]),
                    'packet_join_override': ('join', True), 'packet_confidence_override': ('confidence', 1),
                    'packet_scope': ('requested_scope', 'clinical'), 'packet_kind': ('evidence_kind', 'inferred'),
                    'packet_boolean_id': ('packet_id', True), 'packet_whitespace_id': ('packet_id', '   '),
                    'packet_promotion_override': ('restoration_verdict', 'established')}
                if cid == 'packet_missing_field':
                    packet.pop('evidence_kind'); expected_reason = 'schema_required'
                else:
                    key, value = changes[cid]; packet[key] = value
                    expected_reason = 'unadmitted_evidence' if cid == 'packet_unknown_evidence' else 'schema_'
            elif cid in {'duplicate_json_key', 'json_nan', 'json_infinity'}:
                raw = '{"packet_id":"a","packet_id":"b"}' if cid == 'duplicate_json_key' else '{"packet_id":' + ('NaN' if cid == 'json_nan' else 'Infinity') + '}'
                expected_reason = 'duplicate_json_key' if cid == 'duplicate_json_key' else 'nonfinite_json_number'
            elif cid == 'catalog_unknown_field':
                altered['confidence'] = 1; expected_reason = 'schema_unknown_field'
            elif cid == 'catalog_cross_assay_link':
                altered['reviewed_cross_assay_links'] = [{'evidence_ids': ['a', 'b']}]; expected_reason = 'schema_max_items'
            elif cid == 'catalog_schema':
                altered['schema'] = 'wrong'; expected_reason = 'schema_const'
            elif cid in {'catalog_duplicate_evidence', 'catalog_duplicate_base', 'catalog_duplicate_bundle'}:
                key = {'catalog_duplicate_evidence': 'evidence', 'catalog_duplicate_base': 'base_catalogs', 'catalog_duplicate_bundle': 'bundles'}[cid]
                altered[key].append(copy.deepcopy(altered[key][0])); expected_reason = 'duplicate_'
            elif cid == 'base_engine_hash':
                altered['base_engine_sha256'] = '0' * 64; expected_reason = 'base_engine_hash_mismatch'
            elif cid in {'source_hash', 'source_escape', 'source_missing'}:
                reference = altered['bundles'][0]['sources']['effects']
                if cid == 'source_hash': reference['sha256'] = '0' * 64; expected_reason = 'source_hash_mismatch'
                else: reference['path'] = '../../outside-root.tsv' if cid == 'source_escape' else 'programs/partial-reprogramming-controller/tmp/nonexistent-v2-source.tsv'; expected_reason = 'source_outside_root_or_missing'
            elif cid == 'duplicate_tsv_header':
                reference = altered['bundles'][0]['sources']['effects']; original = (REPO / reference['path']).read_text()
                first, rest = original.split('\n', 1); names = first.split('\t'); names[-1] = names[0]
                path = work / 'duplicate-header.tsv'; path.write_text('\t'.join(names) + '\n' + rest)
                reference.update(path=str(path.relative_to(REPO)), sha256=sha(path)); expected_reason = 'duplicate_or_empty_tsv_header'
            elif cid == 'missing_tsv_field':
                role_file('effects', lambda rows: None, drop='ci95_low'); expected_reason = 'missing_tsv_field'
            elif cid in {'effect_cardinality', 'normalization_duplicate'}:
                role_file('effects', lambda rows: rows.append(copy.deepcopy(next(r for r in rows if relevant(r))))); expected_reason = 'duplicate_normalization_effect'
            elif cid in {'interval_reversed', 'interval_zero_width', 'interval_excludes_estimate', 'interval_nonfinite'}:
                def edit(rows):
                    r = next(r for r in rows if relevant(r))
                    if cid == 'interval_reversed': r['ci95_low'], r['ci95_high'] = r['ci95_high'], r['ci95_low']
                    if cid == 'interval_zero_width': r['ci95_low'] = r['ci95_high'] = r['estimate']
                    if cid == 'interval_excludes_estimate': r['ci95_low'] = '1'; r['ci95_high'] = '2'
                    if cid == 'interval_nonfinite': r['ci95_high'] = 'NaN'
                role_file('effects', edit); expected_reason = 'nonfinite_measurement' if cid == 'interval_nonfinite' else 'invalid_interval_bounds'
            elif cid in {'estimate_units_disagree', 'standard_error_disagrees', 'degrees_freedom_disagree', 'unit_count_disagrees'}:
                field, value, expected_reason = {'estimate_units_disagree': ('estimate', '100', 'effect_estimate_unit_vector_mismatch'),
                    'standard_error_disagrees': ('se', '100', 'effect_standard_error_mismatch'), 'degrees_freedom_disagree': ('df', '100', 'effect_degrees_freedom_mismatch'),
                    'unit_count_disagrees': ('n_treated', '99', 'effect_unit_count_mismatch')}[cid]
                edit_effect(field, value)
            elif cid in {'pair_missing', 'pair_duplicate'}:
                def edit(rows):
                    row = next(r for r in rows if relevant(r))
                    if cid == 'pair_missing': rows.remove(row)
                    else: rows.append(copy.deepcopy(row))
                role_file('pairs', edit); expected_reason = 'paired_donor_roster_mismatch' if cid == 'pair_missing' else 'duplicate_or_missing_donor_pair'
            elif cid in {'unit_id_missing', 'unit_id_duplicate', 'metadata_unit_unknown'}:
                def edit(rows):
                    local = [r for r in rows if r['study'] == 'GSE126633' and r['donor_pair']]
                    if cid == 'unit_id_missing': local[0]['accession'] = ''
                    if cid == 'unit_id_duplicate': local[0]['accession'] = local[1]['accession']
                    if cid == 'metadata_unit_unknown': local[0]['column'] = 'unknown_column'
                role_file('samples', edit); expected_reason = 'score_metadata_unit_mismatch' if cid == 'metadata_unit_unknown' else 'duplicate_or_missing_unit_identifier'
            elif cid == 'unpaired_pairing_claim':
                packet = load(HERE / 'packets/GSE132828_CPM.json')
                next(r for r in altered['evidence'] if r['evidence_id'] == 'GSE132828_CPM_rpe_identity')['dependence'] = 'named_donor_pairing'
                expected_reason = 'unsupported_source_dependence_claim'
            elif cid in {'omission_missing', 'omission_duplicate', 'omission_unplanned', 'sensitivity_nonfinite', 'sensitivity_status'}:
                def edit(rows):
                    row = next(r for r in rows if relevant(r))
                    if cid == 'omission_missing': rows.remove(row)
                    if cid == 'omission_duplicate': rows.append(copy.deepcopy(row))
                    if cid == 'omission_unplanned': row['omitted'] = 'unplanned_gene'
                    if cid == 'sensitivity_nonfinite': row['estimate'] = 'Infinity'
                    if cid == 'sensitivity_status': row['status'] = 'invented_confidence'
                role_file('sensitivities', edit)
                expected_reason = 'nonfinite_measurement' if cid == 'sensitivity_nonfinite' else 'unrecognized_sensitivity_status' if cid == 'sensitivity_status' else 'incomplete_duplicate_or_unplanned_omission'
            elif cid == 'normalization_missing':
                role_file('effects', lambda rows: rows.__setitem__(slice(None), [r for r in rows if not relevant(r, 'median_ratio')]))
                expected_reason = 'incomplete_or_unknown_normalization_effect'
            elif cid in {'function_invented_precision', 'RNA_precision_override'}:
                if cid == 'function_invented_precision':
                    packet = load(HERE / 'packets/FUNCTION_RESCUE.json'); target = 'POS_RESCUE_FIELD'
                    next(r for r in altered['evidence'] if r['evidence_id'] == target)['interval_policy'] = 'source_nominal_95'
                    expected_reason = 'function_precision_or_pairing_not_admitted'
                else:
                    next(r for r in altered['evidence'] if r['evidence_id'] == target)['interval_policy'] = 'not_estimated'
                    expected_reason = 'invalid_rna_uncertainty_policy'
            elif cid in {'base_catalog_unsupported_join', 'base_duplicate_evidence', 'function_unit_unknown'}:
                reference = altered['base_catalogs'][1 if cid == 'function_unit_unknown' else 0]['source']
                base = load(REPO / reference['path'])
                if cid == 'base_catalog_unsupported_join': base['reviewed_cross_assay_links'] = [{'evidence_ids': ['unused']}]; expected_reason = 'unsupported_base_catalog_or_join'
                if cid == 'base_duplicate_evidence': base['evidence'].append(copy.deepcopy(base['evidence'][0])); expected_reason = 'duplicate_base_evidence'
                if cid == 'function_unit_unknown':
                    packet = load(HERE / 'packets/FUNCTION_RESCUE.json')
                    binding = next(r for r in base['evidence'] if r['evidence_id'] == 'POS_RESCUE_FIELD')
                    rows = table(REPO / binding['path']); next(r for r in rows if r['sheet'] == 'Figure 5')['local_experiment'] = '99'
                    path = work / 'function.tsv'
                    with path.open('w', newline='') as stream:
                        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
                    binding.update(path=str(path.relative_to(REPO)), sha256=sha(path)); expected_reason = 'unknown_function_unit_identifier'
                path = work / 'base.json'; dump(path, base); reference.update(path=str(path.relative_to(REPO)), sha256=sha(path))
            elif cid == 'empty_panel':
                reference = altered['bundles'][0]['sources']['contract']; original = load(REPO / reference['path'])
                original['panels']['rpe_identity']['genes'] = []; path = work / 'empty-panel-contract.json'; dump(path, original)
                reference.update(path=str(path.relative_to(REPO)), sha256=sha(path)); expected_reason = 'invalid_fixed_panel'
            elif cid == 'output_alias_input':
                extra_args = ['--output', str(work / 'packet.json')]; expected_reason = 'output_aliases_evidence_or_input'
            else:
                raise AssertionError('Frozen rejection case lacks implementation: ' + cid)
            packet_path = work / 'packet.json'; catalog_path = work / 'catalog.json'
            if raw is None: dump(packet_path, packet)
            else: packet_path.write_text(raw)
            dump(catalog_path, altered)
            before = packet_path.read_bytes()
            p = subprocess.run([sys.executable, str(ENGINE), '--packet', str(packet_path), '--catalog', str(catalog_path), *extra_args], capture_output=True, text=True)
            ok = p.returncode == 2 and 'RPE v2 evidence rejected:' in p.stderr and expected_reason in p.stderr and 'Traceback' not in p.stderr and not p.stdout
            check('real CLI rejects ' + cid, ok)
            check('rejection preserves input ' + cid, packet_path.read_bytes() == before)
            rejections.append({'case_id': cid, 'status': 'PASS', 'exit_code': p.returncode, 'reason': p.stderr.strip()})
    # An overflowing JSON exponent is another spelling of nonfinite input.
    try:
        module.strict_json('{"x":1e999}')
        overflow_rejected = False
    except ValueError:
        overflow_rejected = True
    check('overflowing JSON exponent is rejected', overflow_rejected)
    for relative, digest in unchanged.items():
        assert sha(REPO / relative) == digest, relative
    result = {'status': 'PASS', 'claim_level': 'Verified', 'scope': 'Same-agent independent source extraction, numerical consumption, schema agreement and deterministic software verification only.',
        'check_count': len(checks), 'checks': checks, 'numerical_values_compared': comparisons,
        'maximum_scaled_error': maximum, 'tolerance': 2e-10, 'rejection_case_count': len(rejections), 'rejections': rejections,
        'protected_prior_files': len(unchanged), 'schema_agreement_examples': len(schema_examples),
        'engine_sha256': sha(ENGINE), 'verifier_sha256': sha(Path(__file__)), 'frontier_model_evaluation': False}
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
    if args.verify:
        assert (HERE / 'VERIFICATION.json').read_text() == rendered, 'Verification receipt differs'
    else:
        (HERE / 'VERIFICATION.json').write_text(rendered)
    print(f'PASS v2 verification: {len(checks)} checks; {comparisons} source-derived values; {len(rejections)} real CLI rejections; max scaled error {maximum:.3g}')


if __name__ == '__main__':
    main()
