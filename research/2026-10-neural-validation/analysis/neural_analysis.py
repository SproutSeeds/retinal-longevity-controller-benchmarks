#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Frozen animal-level summaries. R is parsed as data and never executed.

Raw reader adapted from this project's preceding inspect_neural.py admission.
The main entry point requires a committed contract receipt before outcomes.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
import rdata
from scipy.sparse import csc_matrix

HERE = Path(__file__).resolve().parent
COMMON_LIMITS = [
    'The observed contrast bundles doxycycline exposure with OSKM induction. BL6 doxycycline-only controls are absent from these processed objects, so drug and construct effects cannot be separated.',
    'CPM and median-ratio agreement checks sensitivity to these size-factor choices; it does not establish absolute RNA changes or eliminate compositional effects.',
    'Animal-level destructive snapshots and small animal counts support descriptive marker-score comparisons; they do not establish rejuvenation, function, recovery, retinal efficacy or safety.',
]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while data := stream.read(1024 * 1024):
            digest.update(data)
    return digest.hexdigest()


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def deref(node):
    while node.info.type.name == 'REF':
        node = node.referenced_object
    return node


def attrs(obj):
    result = {}
    node = deref(obj).attributes
    while node is not None and deref(node).info.type.name != 'NILVALUE':
        node = deref(node)
        key = deref(deref(node.tag).value).value.decode()
        if key in result:
            raise ValueError('Duplicate R attribute')
        result[key] = node.value[0]
        node = node.value[1]
    return result


@dataclass
class RawData:
    counts: csc_matrix
    genes: list[str]
    metadata: pd.DataFrame
    source_sha256: str


def validate_sparse_counts(counts, genes, columns, metadata):
    if not isinstance(counts, csc_matrix):
        raise ValueError('Raw counts must be a CSC matrix')
    counts.check_format(full_check=True)
    if not counts.has_canonical_format:
        raise ValueError('Duplicate or unsorted sparse coordinates')
    if counts.shape != (len(genes), len(columns)):
        raise ValueError('Count dimensions do not match identifiers')
    if len(genes) != len(set(genes)) or len(columns) != len(set(columns)):
        raise ValueError('Duplicate gene or cell identifiers')
    if any(not isinstance(x, str) or not x for x in list(genes) + list(columns)):
        raise ValueError('Missing or non-string count identifier')
    if metadata.index.has_duplicates or list(metadata.index) != list(columns):
        raise ValueError('Cell metadata is not an exact ordered count-column join')
    values = counts.data
    if (not np.isfinite(values).all() or (values < 0).any()
            or (values % 1 != 0).any() or (values > np.iinfo(np.int64).max).any()):
        raise ValueError('Invalid raw counts')
    totals = np.asarray(counts.sum(axis=0)).ravel()
    if (totals <= 0).any():
        raise ValueError('Empty cell library')
    if 'nCount_RNA' not in metadata or not np.array_equal(totals, metadata['nCount_RNA'].to_numpy()):
        raise ValueError('Raw RNA library totals disagree with metadata')
    return True


def attach_admission(metadata, admission):
    required = ['hash.ID', 'orig.ident', 'age', 'genotype', 'Treatment', 'Celltype', 'LMO_classification.global']
    if any(field not in metadata for field in required) or metadata[required].isna().any().any():
        raise ValueError('Missing required cell metadata')
    if set(metadata['LMO_classification.global']) != {'Singlet'}:
        raise ValueError('Non-singlet cell cannot enter the admitted dataset')
    animals = admission['animals']
    mapping = {row['hash_id']: row for row in animals}
    if len(mapping) != len(animals) or len({r['animal_label'] for r in animals}) != len(animals):
        raise ValueError('Ambiguous animal admission')
    if set(metadata['hash.ID']) != set(mapping):
        raise ValueError('Unknown or missing animal identity')
    for sample, group in metadata.groupby('hash.ID', observed=True, sort=True):
        row = mapping[sample]
        expected = {'orig.ident': row['lane'], 'age': row['age_group'],
                    'genotype': row['genotype'], 'Treatment': row['treatment']}
        for field, value in expected.items():
            if set(group[field]) != {value}:
                raise ValueError('Animal metadata conflict: ' + field)
        if len(group) != row['cells']:
            raise ValueError('Animal cell count differs from admission')
        if 'celltype_counts' in row:
            observed = {str(k): int(v) for k, v in group['Celltype'].value_counts().items() if v > 0}
            if observed != row['celltype_counts']:
                raise ValueError('Cell-type assignment differs from admission')
    result = metadata.copy()
    for output, field in [('animal_id', 'animal_label'), ('lane', 'lane'),
                          ('treatment', 'treatment'), ('age_group', 'age_group')]:
        result[output] = [mapping[s][field] for s in result['hash.ID']]
    result['celltype'] = result['Celltype'].astype(str)
    return result


def load_raw_rds(path: Path, expected_sha256: str, admission=None) -> RawData:
    """Return raw genes×cells CSC, ordered gene names and exact metadata.

    This parser only materializes R data slots. The source analysis script is
    neither sourced nor interpreted. A hash mismatch fails before parsing.
    """
    path = Path(path)
    actual_hash = sha(path)
    if actual_hash != expected_sha256:
        raise ValueError('RDS source hash differs from admitted input')
    parsed = rdata.parser.parse_file(path)
    root = attrs(parsed.object)
    metadata = rdata.conversion.convert(root['meta.data'])
    assays = deref(root['assays'])
    names = list(rdata.conversion.convert(attrs(assays)['names']))
    if names.count('RNA') != 1:
        raise ValueError('Exactly one raw RNA assay is required')
    slots = attrs(attrs(assays.value[names.index('RNA')])['counts'])
    dimensions = tuple(int(x) for x in rdata.conversion.convert(slots['Dim']))
    genes, columns = rdata.conversion.convert(slots['Dimnames'])
    genes, columns = list(genes), list(columns)
    values, indices, offsets = [np.asarray(rdata.conversion.convert(slots[k])) for k in ['x', 'i', 'p']]
    if (len(dimensions) != 2 or len(offsets) != dimensions[1] + 1 or offsets[0] != 0
            or offsets[-1] != len(values) or len(indices) != len(values)
            or (np.diff(offsets) < 0).any() or (indices < 0).any() or (indices >= dimensions[0]).any()):
        raise ValueError('Invalid raw sparse count slots')
    counts = csc_matrix((values, indices, offsets), shape=dimensions)
    validate_sparse_counts(counts, genes, columns, metadata)
    if admission is not None:
        metadata = attach_admission(metadata, admission)
    return RawData(counts.astype(np.int64), genes, metadata, actual_hash)


def load_cohort2(cache_dir: Path) -> RawData:
    if sha(HERE / 'source-admission.json') != '242b49dc6face56e46d55c840c12319a91dc78365d27b385b8eabea4b230d3e3':
        raise ValueError('Cohort2 admission snapshot changed')
    admission = json.loads((HERE / 'source-admission.json').read_text())
    return load_raw_rds(Path(cache_dir) / 'svz_iOSKM_cohort2_toshare.rds',
                        admission['source_sha256'], admission)


@dataclass
class Pseudobulk:
    counts: np.ndarray
    genes: list[str]
    keys: list[tuple[str, str]]
    qc: list[dict]
    animals: dict[str, dict]


def aggregate(raw: RawData, celltypes) -> Pseudobulk:
    meta = raw.metadata
    for field in ['animal_id', 'celltype', 'lane', 'treatment', 'age_group']:
        if field not in meta or meta[field].isna().any():
            raise ValueError('Unadmitted metadata: ' + field)
    if set(meta['celltype']) - set(celltypes):
        raise ValueError('Unfrozen cell-type label')
    animals = {}
    for animal, group in meta.groupby('animal_id', sort=True):
        details = {}
        for field in ['lane', 'treatment', 'age_group', 'genotype']:
            values = set(group[field])
            if len(values) != 1:
                raise ValueError('Animal spans incompatible metadata: ' + field)
            details[field] = next(iter(values))
        animals[str(animal)] = details
    keys = list(itertools.product(sorted(animals), celltypes))
    columns, qc = [], []
    for animal, celltype in keys:
        selector = (meta['animal_id'].to_numpy() == animal) & (meta['celltype'].to_numpy() == celltype)
        counts = np.asarray(raw.counts[:, selector].sum(axis=1)).ravel().astype(np.int64)
        columns.append(counts)
        qc.append({'animal_id': animal, 'celltype': celltype, 'cells': int(selector.sum()),
                   'raw_library_total': int(counts.sum()), 'detected_genes': int((counts > 0).sum()),
                   **animals[animal]})
    return Pseudobulk(np.stack(columns, axis=1), raw.genes, keys, qc, animals)


def support_failures(qc, minimum_cells, minimum_genes):
    failures = []
    if qc['cells'] < minimum_cells:
        failures.append(f"cells_below_{minimum_cells}")
    if qc['detected_genes'] < minimum_genes:
        failures.append(f"detected_genes_below_{minimum_genes}")
    if qc['raw_library_total'] <= 0:
        failures.append('empty_pseudobulk')
    return failures


def normalizations(x, minimum_positive_genes):
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or not np.isfinite(x).all() or (x < 0).any() or (x.sum(axis=0) <= 0).any():
        raise ValueError('Invalid pseudobulk normalization input')
    totals = x.sum(axis=0)
    result = {'log2_cpm': np.log2(1 + 1e6 * x / totals)}
    positive = x[(x > 0).all(axis=1)]
    audit = {'raw_library_totals': totals.tolist(), 'all_positive_genes': len(positive),
             'median_ratio_status': 'available', 'median_ratio_size_factors': None,
             'median_ratio_effective_depths': None}
    if len(positive) < minimum_positive_genes:
        audit['median_ratio_status'] = 'insufficient_all_positive_genes'
        return result, audit
    geometric_means = np.exp(np.log(positive).mean(axis=1))
    factors = np.median(positive / geometric_means[:, None], axis=0)
    factors /= np.exp(np.log(factors).mean())
    effective_depths = factors * np.exp(np.log(totals).mean())
    result['log2_median_ratio_cpm_equivalent'] = np.log2(1 + 1e6 * x / effective_depths)
    audit.update(median_ratio_size_factors=factors.tolist(), median_ratio_effective_depths=effective_depths.tolist())
    return result, audit


def panel_coverage(orthology, genes, thresholds):
    index = {g: i for i, g in enumerate(genes)}
    result = {}
    transgenes = set(orthology['transgene_mouse_symbols'])
    for name, symbols in orthology['panels'].items():
        mapped = [orthology['mapping'][s]['mouse_symbol'] for s in symbols
                  if orthology['mapping'][s]['status'] == 'mapped']
        present = [g for g in mapped if g in index]
        unavailable = [s for s in symbols if orthology['mapping'][s]['status'] != 'mapped']
        failures = []
        if len(present) / len(symbols) < thresholds['minimum_panel_coverage_source_human']:
            failures.append('insufficient_original_source_panel_coverage')
        if not mapped or len(present) / len(mapped) < thresholds['minimum_panel_coverage_orthology_eligible']:
            failures.append('insufficient_orthology_eligible_panel_coverage')
        if len(present) < thresholds['minimum_panel_genes_present']:
            failures.append('too_few_panel_genes')
        result[name] = {'source_human_genes': symbols, 'source_gene_count': len(symbols),
                        'mapped_mouse_genes': mapped, 'mapped_gene_count': len(mapped),
                        'present_mouse_genes': present, 'present_gene_count': len(present),
                        'missing_mapped_mouse_genes': [g for g in mapped if g not in index],
                        'orthology_ineligible_human_genes': unavailable,
                        'source_coverage': len(present) / len(symbols),
                        'eligible_coverage': len(present) / len(mapped) if mapped else 0,
                        'transgene_overlap': sorted(set(present) & transgenes),
                        'failures': failures, 'indices': [index[g] for g in present]}
    return result


def mean_difference(scores, animals, treated, controls):
    lookup = dict(zip(animals, scores))
    if not treated or not controls:
        raise ValueError('Both animal groups are required')
    return float(np.mean([lookup[x] for x in treated]) - np.mean([lookup[x] for x in controls]))


def summarize_method(values, panel, animals, treated, controls, pairs):
    indices = panel['indices']
    panel_values = values[indices, :]
    scores = panel_values.mean(axis=0)
    by_animal = dict(zip(animals, map(float, scores)))
    effect = mean_difference(scores, animals, treated, controls)
    within_lane = [{'lane': p['lane'], 'treated': p['treated'], 'control': p['control'],
                    'difference': by_animal[p['treated']] - by_animal[p['control']]}
                   for p in pairs if p['treated'] in animals and p['control'] in animals]
    omissions = {}
    for i, gene in enumerate(panel['present_mouse_genes']):
        omission_scores = np.delete(panel_values, i, axis=0).mean(axis=0)
        omissions[gene] = mean_difference(omission_scores, animals, treated, controls)
    return {'mean_difference': effect, 'animal_scores': by_animal,
            'animal_gene_values': {a: dict(zip(panel['present_mouse_genes'], map(float, panel_values[:, j])))
                                   for j, a in enumerate(animals)},
            'within_lane_differences': within_lane,
            'all_treated_control_differences': [
                {'treated': t, 'control': c, 'difference': by_animal[t] - by_animal[c]}
                for t, c in itertools.product(treated, controls)],
            'single_gene_omission_differences': omissions,
            'pairwise_differences_are_independent_replicates': False}


def evaluate_contrast(pb, celltype, panel, treated, controls, pairs, thresholds,
                      minimum_cells, minimum_genes, role, support_tier):
    animals = list(treated) + list(controls)
    if len(set(animals)) != len(animals):
        raise ValueError('An animal cannot occur in both contrast groups')
    qc_lookup = {(q['animal_id'], q['celltype']): q for q in pb.qc}
    failures = {a: support_failures(qc_lookup[(a, celltype)], minimum_cells, minimum_genes)
                for a in animals}
    failures = {a: f for a, f in failures.items() if f}
    result = {'celltype': celltype, 'role': role, 'support_tier': support_tier,
              'animals': animals, 'treated_animals': list(treated), 'control_animals': list(controls),
              'independent_animal_counts': {'treated': len(treated), 'control': len(controls)},
              'support_failures': failures, 'panel_failures': panel['failures'],
              'status': 'unavailable' if failures or panel['failures'] else 'available',
              'panel': {k: v for k, v in panel.items() if k != 'indices'},
              'methods': {}, 'single_animal_omissions': [], 'single_lane_omissions': []}
    if result['status'] == 'unavailable':
        return result
    columns = [pb.keys.index((a, celltype)) for a in animals]
    x = pb.counts[:, columns]
    transforms, audit = normalizations(x, thresholds['median_ratio_min_all_positive_genes'])
    result['normalization'] = audit
    result['animal_gene_raw_counts'] = {
        a: dict(zip(panel['present_mouse_genes'], map(int, x[panel['indices'], j])))
        for j, a in enumerate(animals)}
    result['panel_genes_nonzero_by_animal'] = {
        a: [g for g, value in result['animal_gene_raw_counts'][a].items() if value > 0] for a in animals}
    for method, values in transforms.items():
        result['methods'][method] = summarize_method(values, panel, animals, treated, controls, pairs)
    for omitted in animals:
        retained = [a for a in animals if a != omitted]
        t = [a for a in treated if a != omitted]
        c = [a for a in controls if a != omitted]
        if not t or not c:
            raise ValueError('Frozen full contrast unexpectedly has fewer than two animals per group')
        values_by_method, omission_audit = normalizations(x[:, [animals.index(a) for a in retained]],
                                                         thresholds['median_ratio_min_all_positive_genes'])
        result['single_animal_omissions'].append({
            'omitted_animal': omitted, 'remaining_treated': t, 'remaining_controls': c,
            'estimator': 'unpaired_equal_animal_mean_after_omission',
            'authority': 'fragility observation only; original paired-lane estimand is not preserved',
            'normalization': omission_audit,
            'methods': {method: summarize_method(values, panel, retained, t, c, pairs)
                        for method, values in values_by_method.items()}})
    if role == 'lane_balanced_primary':
        for omitted_pair in pairs:
            remaining_pair = [p for p in pairs if p['lane'] != omitted_pair['lane']]
            if len(remaining_pair) != 1:
                raise ValueError('Lane omission must retain exactly one prespecified pair')
            pair = remaining_pair[0]
            retained = [pair['treated'], pair['control']]
            omission_values, omission_audit = normalizations(
                x[:, [animals.index(a) for a in retained]], thresholds['median_ratio_min_all_positive_genes'])
            result['single_lane_omissions'].append({
                'omitted_lane': omitted_pair['lane'], 'remaining_lane': pair['lane'],
                'remaining_treated': [pair['treated']], 'remaining_controls': [pair['control']],
                'authority': 'single pair observation; no independent validation',
                'normalization': omission_audit,
                'methods': {method: summarize_method(values, panel, retained, [pair['treated']],
                                                     [pair['control']], remaining_pair)
                            for method, values in omission_values.items()}})
    return result


def stability_descriptor(primary, secondary, floor):
    required = ['log2_cpm', 'log2_median_ratio_cpm_equivalent']
    failures = []
    if primary['status'] != 'available':
        return {'status': 'unavailable', 'failures': ['primary_support_or_panel_failure']}
    if any(k not in primary['methods'] for k in required):
        return {'status': 'incomplete', 'failures': ['primary_normalization_unavailable']}
    reference = primary['methods'][required[0]]['mean_difference']
    sign = np.sign(reference)
    for method in required:
        row = primary['methods'][method]
        if np.sign(row['mean_difference']) != sign or sign == 0:
            failures.append(method + ':normalization_direction_disagreement_or_zero')
        if abs(row['mean_difference']) < floor:
            failures.append(method + ':below_descriptive_floor')
        if len(row['within_lane_differences']) != 2:
            failures.append(method + ':missing_lane_pair')
        elif any(np.sign(p['difference']) != sign for p in row['within_lane_differences']):
            failures.append(method + ':lane_direction_disagreement_or_zero')
        if any(np.sign(v) != sign for v in row['single_gene_omission_differences'].values()):
            failures.append(method + ':gene_omission_direction_disagreement_or_zero')
    if secondary['status'] != 'available' or any(k not in secondary['methods'] for k in required):
        failures.append('all_controls_sensitivity_unavailable')
    else:
        for method in required:
            if np.sign(secondary['methods'][method]['mean_difference']) != sign:
                failures.append(method + ':all_controls_direction_disagreement_or_zero')
    return {'status': 'stable_descriptive_pattern' if not failures else 'unstable_or_incomplete',
            'failures': failures, 'descriptive_floor': floor,
            'authority': 'heuristic marker-score stability only; no statistical or biological validation'}


def composition(pb, named_types, pairs, treated, controls):
    rows = []
    for animal in sorted(pb.animals):
        animal_qc = [q for q in pb.qc if q['animal_id'] == animal]
        all_count = sum(q['cells'] for q in animal_qc)
        named_count = sum(q['cells'] for q in animal_qc if q['celltype'] in named_types)
        if all_count <= 0 or named_count <= 0:
            raise ValueError('Composition denominator is empty')
        for row in animal_qc:
            rows.append({**row, 'all_recovered_cells': all_count,
                         'named_recovered_cells': named_count,
                         'unresolved_cells': all_count - named_count,
                         'fraction_all_recovered': row['cells'] / all_count,
                         'fraction_named_recovered': row['cells'] / named_count if row['celltype'] in named_types else None})
    lookup = {(r['animal_id'], r['celltype']): r for r in rows}
    contrasts = []
    for celltype in dict.fromkeys(k[1] for k in pb.keys):
        for denominator in ['fraction_all_recovered', 'fraction_named_recovered']:
            if denominator == 'fraction_named_recovered' and celltype not in named_types:
                continue
            values = {a: lookup[(a, celltype)][denominator] for a in pb.animals}
            lane_differences = [{'lane': p['lane'], 'difference': values[p['treated']] - values[p['control']]}
                                for p in pairs]
            contrasts.append({'celltype': celltype, 'denominator': denominator,
                              'within_lane_differences': lane_differences,
                              'primary_lane_mean_difference': float(np.mean([p['difference'] for p in lane_differences])) if lane_differences else None,
                              'all_old_control_mean_difference': float(np.mean([values[a] for a in treated]) - np.mean([values[a] for a in controls]))})
    return {'rows': rows, 'contrasts': contrasts,
            'authority': 'Recovered sequenced singlets; proportions do not estimate tissue abundance.'}


def verify_committed_file(path, commit):
    repo = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=HERE, text=True).strip())
    relative = Path(path).resolve().relative_to(repo)
    frozen = subprocess.check_output(['git', 'show', f"{commit}:{relative.as_posix()}"], cwd=repo)
    if hashlib.sha256(frozen).hexdigest() != sha(path):
        raise ValueError('Freeze commit does not contain the exact current contract input')


def require_freeze(receipt_path, contract_path, orthology_path, replay_frozen_hashes=False):
    receipt = json.loads(Path(receipt_path).read_text())
    if receipt.get('expression_execution_authorized') is not True:
        raise ValueError('Expression execution is not authorized by freeze receipt')
    if receipt['contract_sha256'] != sha(contract_path) or receipt['orthology_sha256'] != sha(orthology_path):
        raise ValueError('Frozen contract or orthology has changed')
    if not replay_frozen_hashes:
        for path in [contract_path, orthology_path]:
            verify_committed_file(path, receipt['commit'])
    return receipt


def qc_and_profiles(pb, contract, panels):
    named = contract['cell_types']['named']
    qc = []
    for row in pb.qc:
        qc.append({**row,
                   'primary_support_failures': support_failures(row, contract['thresholds']['primary_min_cells_per_animal_type'],
                                                               contract['thresholds']['primary_min_detected_genes_per_animal_type']),
                   'lower_support_failures': support_failures(row, contract['thresholds']['sensitivity_min_cells_per_animal_type'],
                                                             contract['thresholds']['sensitivity_min_detected_genes_per_animal_type']),
                   'named_cell_type': row['celltype'] in named})
    animal_profiles = []
    for column, row in enumerate(qc):
        if row['celltype'] not in named:
            continue
        for panel_name, panel in panels.items():
            gene_counts = pb.counts[panel['indices'], column]
            values = np.log2(1 + 1e6 * gene_counts / row['raw_library_total']) if row['raw_library_total'] else None
            animal_profiles.append({
                'animal_id': row['animal_id'], 'celltype': row['celltype'], 'panel_name': panel_name,
                'primary_support_failures': row['primary_support_failures'],
                'lower_support_failures': row['lower_support_failures'],
                'panel_failures': panel['failures'],
                'raw_counts': dict(zip(panel['present_mouse_genes'], map(int, gene_counts))),
                'log2_cpm_gene_values': dict(zip(panel['present_mouse_genes'], map(float, values))) if values is not None else None,
                'log2_cpm_score': float(values.mean()) if values is not None and not panel['failures'] else None,
                'authority': 'Per-animal descriptive profile; sparse or young rows do not enter the eligible old-treatment comparison.'})
    return qc, animal_profiles


def run_cohort2(raw, contract, orthology):
    named = contract['cell_types']['named']
    celltypes = named + contract['cell_types']['unresolved']
    pb = aggregate(raw, celltypes)
    panels = panel_coverage(orthology, raw.genes, contract['thresholds'])
    pairs = contract['cohort2_primary']['pairs']
    treated = [p['treated'] for p in pairs]
    controls = [p['control'] for p in pairs]
    all_controls = controls + ['L0042']
    results = []
    for tier, cells_key, genes_key in [
            ('primary_support', 'primary_min_cells_per_animal_type', 'primary_min_detected_genes_per_animal_type'),
            ('lower_cell_sensitivity', 'sensitivity_min_cells_per_animal_type', 'sensitivity_min_detected_genes_per_animal_type')]:
        for celltype in named:
            for panel_name, panel in panels.items():
                primary = evaluate_contrast(pb, celltype, panel, treated, controls, pairs, contract['thresholds'],
                                            contract['thresholds'][cells_key], contract['thresholds'][genes_key],
                                            'lane_balanced_primary', tier)
                secondary = evaluate_contrast(pb, celltype, panel, treated, all_controls, pairs, contract['thresholds'],
                                              contract['thresholds'][cells_key], contract['thresholds'][genes_key],
                                              'all_old_controls_secondary', tier)
                descriptor = stability_descriptor(primary, secondary, contract['effect_descriptors']['descriptive_floor'])
                results.append({'panel_name': panel_name, 'primary': primary, 'secondary': secondary,
                                'stability_descriptor': descriptor})
    qc, animal_profiles = qc_and_profiles(pb, contract, panels)
    return {'claim_level': 'Verified', 'evidence_class': 'observed_mouse_neural_descriptive_reanalysis',
            'contract_id': contract['id'], 'input_sha256': raw.source_sha256,
            'gene_count': len(raw.genes), 'cell_count': raw.counts.shape[1],
            'independent_animals': len(pb.animals), 'animal_celltype_qc': qc,
            'animal_panel_profiles': animal_profiles,
            'panel_coverage': {name: {k: v for k, v in panel.items() if k != 'indices'} for name, panel in panels.items()},
            'composition': composition(pb, named, pairs, treated, all_controls),
            'contrasts': results,
            'scope_limits': COMMON_LIMITS + [
                'Primary pairing is by sequencing lane; the published animal table also records matched sex within those lane pairs. The date token in the cohort2 sample identifiers is not established as date of birth, and no litter matching is inferred.'
            ],
            'readouts': {f'CX004-R0{i}': 'insufficient_signal' for i in range(1, 5)},
            'inference': 'Descriptive animal-level results. No p-values, calibrated diagnostics, recovery, retinal efficacy or safety inference.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--freeze-receipt', type=Path, required=True)
    parser.add_argument('--orthology', type=Path, default=HERE / 'orthology.json')
    parser.add_argument('--output', type=Path, default=HERE / 'cohort2-results.json')
    parser.add_argument('--replay-frozen-hashes', action='store_true',
                        help='Portable replay: verify archived hashes; historical git proof is not rerun.')
    args = parser.parse_args()
    receipt = require_freeze(args.freeze_receipt, args.contract, args.orthology, args.replay_frozen_hashes)
    contract = json.loads(args.contract.read_text())
    orthology = json.loads(args.orthology.read_text())
    raw = load_cohort2(args.cache)
    result = run_cohort2(raw, contract, orthology)
    result['freeze'] = receipt
    result['analysis_code_sha256'] = sha(Path(__file__))
    save_json(args.output, result)
    pd.DataFrame(result['animal_celltype_qc']).to_csv(args.output.parent / 'animal-celltype-qc.tsv', sep='\t', index=False, na_rep='NA')
    pd.DataFrame(result['composition']['rows']).to_csv(args.output.parent / 'composition.tsv', sep='\t', index=False, na_rep='NA')
    save_json(args.output.parent / 'cohort2-execution-verification.json', {
        'mode': 'archived_hash_replay' if args.replay_frozen_hashes else 'committed_freeze_verified',
        'historical_git_proof_rerun': not args.replay_frozen_hashes,
        'scope': 'Exact frozen hashes checked in both modes. Portable replay does not reestablish historical commit chronology.',
        'result_sha256': sha(args.output), 'contract_sha256': sha(args.contract),
        'orthology_sha256': sha(args.orthology)})
    available = [r for r in result['contrasts'] if r['primary']['status'] == 'available']
    print('Cohort2 complete;', len(result['contrasts']), 'predefined type/panel/tier rows;',
          len(available), 'available primary rows; all unavailable rows retained')


if __name__ == '__main__':
    main()
