#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Frozen post hoc algebra and depth diagnostics for recovered-cell summaries."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'analysis'))
from neural_analysis import (aggregate, load_cohort2, panel_coverage, require_freeze,
                             save_json, sha, support_failures, verify_committed_file)

CONVENTIONS = ('control_reference', 'treated_reference', 'symmetric')
FIELDS = ('total', 'composition', 'within_type')
SEEDS = (181026, 181027, 181028)
DEPTH = 1000
SCALE = 10000
TOL = 1e-10


def assert_close(actual, expected, message):
    if not np.allclose(actual, expected, rtol=0, atol=TOL):
        raise ValueError(message)


def sign(value):
    return 'positive' if value > 0 else 'negative' if value < 0 else 'zero'


def component_record(total, composition, within):
    composition, within = np.asarray(composition), np.asarray(within)
    comp, inner = float(composition.sum()), float(within.sum())
    error = abs(total - comp - inner)
    if error > TOL:
        raise ValueError('Decomposition identity failed')
    return {'total': float(total), 'composition': comp, 'within_type': inner,
            'composition_by_type': composition.tolist(), 'within_by_type': within.tolist(),
            'identity_error': error, 'opposed_components': comp * inner < 0,
            'signs': {'total': sign(total), 'composition': sign(comp), 'within_type': sign(inner)}}


def decompositions(p_t, p_c, mu_t, mu_c):
    arrays = [np.asarray(x, dtype=float) for x in (p_t, p_c, mu_t, mu_c)]
    if any(x.ndim != 1 or not x.size or not np.isfinite(x).all() for x in arrays):
        raise ValueError('Finite nonempty vectors are required')
    if len({x.shape for x in arrays}) != 1:
        raise ValueError('Identical common support is required')
    p_t, p_c, mu_t, mu_c = arrays
    if any((p < 0).any() or abs(p.sum() - 1) > 1e-12 for p in (p_t, p_c)):
        raise ValueError('Fractions must be nonnegative and sum to one')
    total = float(p_t @ mu_t - p_c @ mu_c)
    control = ((p_t - p_c) * mu_c, p_t * (mu_t - mu_c))
    treated = ((p_t - p_c) * mu_t, p_c * (mu_t - mu_c))
    symmetric = tuple(.5 * (a + b) for a, b in zip(control, treated))
    return {name: component_record(total, *values)
            for name, values in zip(CONVENTIONS, (control, treated, symmetric))}


def lane_average(lanes):
    if not lanes:
        raise ValueError('At least one lane is required')
    return {convention: component_record(
        float(np.mean([lane['conventions'][convention]['total'] for lane in lanes])),
        np.mean([lane['conventions'][convention]['composition_by_type'] for lane in lanes], axis=0),
        np.mean([lane['conventions'][convention]['within_by_type'] for lane in lanes], axis=0))
        for convention in CONVENTIONS}


def summarize(values, genes, metadata, common_types, pairs, selected=None, per_gene=False):
    """Decompose a fixed equal-gene panel; rows are genes, columns ordered cells."""
    values = np.asarray(values, dtype=float)
    if (values.ndim != 2 or values.shape != (len(genes), len(metadata))
            or not genes or len(set(genes)) != len(genes) or not np.isfinite(values).all()):
        raise ValueError('Invalid gene/cell score matrix')
    if not common_types or len(set(common_types)) != len(common_types):
        raise ValueError('Unique nonempty support is required')
    if selected is None:
        selected = np.ones(len(metadata), dtype=bool)
    selected = np.asarray(selected)
    if selected.shape != (len(metadata),) or selected.dtype != bool:
        raise ValueError('An ordered boolean selection mask is required')
    animals = [a for pair in pairs for a in (pair['treated'], pair['control'])]
    if len(set(animals)) != len(animals):
        raise ValueError('Every paired animal must be distinct')
    means, fractions, direct, counts, gene_means = {}, {}, {}, {}, {}
    scores = values.mean(axis=0)
    retained_type = metadata['celltype'].isin(common_types).to_numpy()
    for animal in animals:
        animal_mask = (metadata['animal_id'] == animal).to_numpy()
        masks = [selected & animal_mask & (metadata['celltype'] == ct).to_numpy() for ct in common_types]
        counts[animal] = [int(mask.sum()) for mask in masks]
        if min(counts[animal]) <= 0:
            raise ValueError('Absent types cannot be imputed or removed')
        fractions[animal] = np.asarray(counts[animal]) / sum(counts[animal])
        gene_means[animal] = np.column_stack([values[:, mask].mean(axis=1) for mask in masks])
        means[animal] = np.asarray([scores[mask].mean() for mask in masks])
        direct[animal] = float(scores[selected & animal_mask & retained_type].mean())
        assert_close(fractions[animal] @ means[animal], direct[animal], 'Direct cell average mismatch')
    lanes = []
    for pair in pairs:
        t, c = pair['treated'], pair['control']
        conventions = decompositions(fractions[t], fractions[c], means[t], means[c])
        direct_delta = direct[t] - direct[c]
        assert_close(conventions['symmetric']['total'], direct_delta, 'Direct difference mismatch')
        lanes.append({**pair, 'conventions': conventions,
                      'fractions_treated': fractions[t].tolist(), 'fractions_control': fractions[c].tolist(),
                      'means_treated': means[t].tolist(), 'means_control': means[c].tolist(),
                      'direct_cell_average_difference': direct_delta})
    result = {'status': 'available', 'common_types': common_types, 'panel_genes': list(genes),
              'panel_size': len(genes), 'counts_by_animal_type': counts,
              'animal_direct_cell_average': direct, 'lane_contrasts': lanes,
              'equal_lane_mean': lane_average(lanes)}
    if per_gene:
        gene_rows = []
        for g, name in enumerate(genes):
            gene_lanes = []
            for pair in pairs:
                t, c = pair['treated'], pair['control']
                mt, mc = gene_means[t][g], gene_means[c][g]
                gene_lanes.append({**pair, 'means_treated_unweighted': mt.tolist(),
                                   'means_control_unweighted': mc.tolist(),
                                   'conventions': decompositions(fractions[t], fractions[c],
                                                               mt / len(genes), mc / len(genes))})
            gene_rows.append({'gene': name, 'panel_weight': 1 / len(genes),
                              'lane_contrasts': gene_lanes, 'equal_lane_mean': lane_average(gene_lanes)})
        result['gene_contributions'] = gene_rows
        for k, lane in enumerate(lanes):
            for convention in CONVENTIONS:
                for field in FIELDS:
                    assert_close(sum(g['lane_contrasts'][k]['conventions'][convention][field] for g in gene_rows),
                                 lane['conventions'][convention][field], 'Gene contribution sum mismatch')
    return result


def depth_summary(values):
    values = np.asarray(values)
    if not len(values):
        return None
    return {'cells': len(values), 'minimum': int(values.min()), 'maximum': int(values.max()),
            'mean': float(values.mean()), 'median': float(np.median(values)),
            'q25': float(np.quantile(values, .25)), 'q75': float(np.quantile(values, .75)),
            'total_umis': int(values.sum())}


def depth_support(raw, common_types, pairs, depth=DEPTH, min_cells=20, min_genes=500):
    library = np.asarray(raw.counts.sum(axis=0)).ravel()
    if (library <= 0).any():
        raise ValueError('All recovered cells require positive raw libraries')
    animals = [a for pair in pairs for a in (pair['treated'], pair['control'])]
    metadata = raw.metadata
    selected = metadata['animal_id'].isin(animals).to_numpy() & metadata['celltype'].isin(common_types).to_numpy() & (library >= depth)
    rows, denominators, failures = [], {}, []
    for animal in animals:
        animal_mask = (metadata['animal_id'] == animal).to_numpy()
        all_cells = int(animal_mask.sum())
        original_total = int((animal_mask & metadata['celltype'].isin(common_types).to_numpy()).sum())
        retained_total = int((animal_mask & selected).sum())
        denominators[animal] = {'all_recovered_cells': all_cells, 'original_common_support_cells': original_total,
                               'retained_cells': retained_total, 'depth_excluded_common_support_cells': original_total - retained_total,
                               'all_excluded_cells': all_cells - retained_total,
                               'retained_fraction_all_recovered': retained_total / all_cells}
        for celltype in common_types:
            original = animal_mask & (metadata['celltype'] == celltype).to_numpy()
            retained = original & selected
            pb = np.asarray(raw.counts[:, retained].sum(axis=1)).ravel()
            qc = {'cells': int(retained.sum()), 'detected_genes': int((pb > 0).sum()), 'raw_library_total': int(pb.sum())}
            reasons = support_failures(qc, min_cells, min_genes)
            if reasons:
                failures.append({'animal_id': animal, 'celltype': celltype, 'failures': reasons})
            rows.append({'animal_id': animal, 'celltype': celltype, 'original_cells': int(original.sum()),
                         'retained_cells': qc['cells'], 'excluded_cells': int(original.sum() - retained.sum()),
                         'retained_fraction_all_recovered': qc['cells'] / all_cells,
                         'original_depth': depth_summary(library[original]), 'retained_depth': depth_summary(library[retained]),
                         'unthinned_retained_detected_genes': qc['detected_genes'],
                         'unthinned_retained_library_total': qc['raw_library_total'], 'support_failures': reasons})
    return {'status': 'unavailable' if failures else 'available', 'fixed_common_types': common_types,
            'minimum_umis': depth, 'minimum_cells': min_cells, 'minimum_detected_genes': min_genes,
            'support_measured_before_thinning': True, 'rows': rows, 'denominators': denominators,
            'failures': failures}, selected


def thin_marginals(cell_ids, category_counts, seed, depth=DEPTH):
    """Sorted-cell PCG64 exact multivariate hypergeometric draws, including remainder."""
    ids = list(cell_ids)
    counts = np.asarray(category_counts)
    if len(ids) != len(set(ids)) or any(not isinstance(x, str) or not x for x in ids):
        raise ValueError('Unique nonempty cell IDs are required')
    if (counts.ndim != 2 or counts.shape[0] != len(ids) or counts.shape[1] < 2
            or not np.issubdtype(counts.dtype, np.integer) or (counts < 0).any()):
        raise ValueError('Nonnegative integer cell/category counts are required')
    total = counts.sum(axis=1)
    if depth <= 0 or (total < depth).any() or (total >= 1_000_000_000).any():
        raise ValueError('Invalid sampling depth or population exceeds marginal-method bound')
    order = np.argsort(np.asarray(ids), kind='stable')
    ordered = counts[order]
    generator = np.random.Generator(np.random.PCG64(seed))
    draws = np.asarray([generator.multivariate_hypergeometric(row, depth, method='marginals') for row in ordered], dtype=np.int64)
    if (draws < 0).any() or (draws > ordered).any() or (draws.sum(axis=1) != depth).any():
        raise ValueError('Sampling conservation or input bounds failed')
    return [ids[i] for i in order], ordered, draws


def require_extension_freeze(replay_frozen_hashes=False, here=HERE):
    root = here.parent
    receipt = json.loads((here / 'EXTENSION_FREEZE.json').read_text())
    parent = json.loads((here / 'results.json').read_text())
    if receipt.get('expression_execution_authorized') is not True:
        raise ValueError('Extension execution is not authorized')
    bindings = [(here / 'posthoc-contract.json', receipt['contract_sha256']),
                (here / 'results.json', receipt['parent_result_sha256']),
                (here / 'contract.json', parent['contract_sha256']),
                (here / 'decompose.py', parent['code_sha256']),
                (root / 'analysis/neural_analysis.py', parent['analysis_loader_sha256'])]
    for path, expected in bindings:
        if sha(path) != expected:
            raise ValueError('Pinned extension input changed: ' + path.name)
    freeze = require_freeze(root / 'FREEZE.json', root / 'analysis/contract.json', root / 'analysis/orthology.json', replay_frozen_hashes)
    if sha(here / 'contract.json') != freeze['decomposition_contract_sha256']:
        raise ValueError('Parent prospective contract mismatch')
    if not replay_frozen_hashes:
        for path, _ in bindings:
            verify_committed_file(path, receipt['commit'])
    return receipt, parent


def scratch_guard(path=Path('/tmp/cx004-neural-validation-2026-10-18'), minimum_free=8 * 1024 ** 3):
    path = Path(path).resolve()
    internal = Path('/tmp').resolve()
    if not path.is_relative_to(internal):
        raise ValueError('Large scratch must remain under internal /tmp')
    ancestor = path
    while not ancestor.exists():
        ancestor = ancestor.parent
    if shutil.disk_usage(ancestor).free < minimum_free:
        raise ValueError('Insufficient internal scratch free space')
    return path


def original_rows(raw, contract, orthology, parent):
    panels = panel_coverage(orthology, raw.genes, contract['thresholds'])
    pairs = contract['cohort2_primary']['pairs']
    pb = aggregate(raw, contract['cell_types']['named'] + contract['cell_types']['unresolved'])
    qc = {(row['animal_id'], row['celltype']): row for row in pb.qc}
    animals = [a for pair in pairs for a in (pair['treated'], pair['control'])]
    library = np.asarray(raw.counts.sum(axis=0)).ravel()
    rows = []
    for original in parent['results']:
        key = {k: original[k] for k in ('cell_floor', 'panel', 'scale')}
        common = [ct for ct in contract['cell_types']['named']
                  if all(not support_failures(qc[(a, ct)], original['cell_floor'], 500) for a in animals)]
        panel = panels[original['panel']]
        if original['status'] != 'available':
            rows.append({**key, 'status': 'unavailable', 'parent_failure': original})
            continue
        if common != original['common_types'] or panel['present_mouse_genes'] != original['panel_genes'] or panel['failures']:
            raise ValueError('Exact original support or panel genes changed')
        values = np.log2(1 + original['scale'] * raw.counts[panel['indices'], :].toarray() / library)
        row = {**key, **summarize(values, original['panel_genes'], raw.metadata, common, pairs, per_gene=True)}
        for lane, old in zip(row['lane_contrasts'], original['lane_contrasts'], strict=True):
            if any(lane[k] != old[k] for k in ('lane', 'treated', 'control')):
                raise ValueError('Original lane identity changed')
            for field in FIELDS + ('composition_by_type', 'within_by_type'):
                assert_close(lane['conventions']['symmetric'][field], old[field], 'Original symmetric component changed')
            for field in ('fractions_treated', 'fractions_control', 'means_treated', 'means_control'):
                assert_close(lane[field], old[field], 'Original fractions or type means changed')
        rows.append(row)
    return rows, panels


def depth_diagnostic(raw, contract, panels, parent):
    pairs = contract['cohort2_primary']['pairs']
    support_row = next(row for row in parent['support'] if row['cell_floor'] == 20)
    common = support_row['common_named_types']
    if common != ['Oligodendrocyte', 'Microglia']:
        raise ValueError('The frozen two-type primary support changed')
    support, selected = depth_support(raw, common, pairs)
    result = {'support': support, 'scale': SCALE, 'depth': DEPTH, 'seeds': list(SEEDS),
              'interpretation': 'Post hoc measurement-depth and cell-selection diagnostic on fixed named-type support; no added animals or biological ground truth.'}
    if support['failures']:
        result['unthinned_subset'] = [{'panel': panel, 'status': 'unavailable', 'reason': 'fixed_support_failure'} for panel in panels]
        result['thinned'] = [{'seed': seed, 'status': 'unavailable', 'reason': 'fixed_support_failure',
                             'panels': [{'panel': panel, 'status': 'unavailable'} for panel in panels]} for seed in SEEDS]
        result['marginal_inputs'] = None
        return result
    metadata = raw.metadata.loc[selected].sort_index()
    positions = raw.metadata.index.get_indexer(metadata.index)
    cell_ids = metadata.index.tolist()
    union_genes = sorted({gene for panel in panels.values() for gene in panel['present_mouse_genes']})
    indices = [raw.genes.index(gene) for gene in union_genes]
    counts = raw.counts[indices, :][:, positions].toarray().astype(np.int64)
    library = np.asarray(raw.counts[:, positions].sum(axis=0)).ravel().astype(np.int64)
    remainder = library - counts.sum(axis=0)
    if (remainder < 0).any():
        raise ValueError('Panel union exceeds raw RNA library')
    categories = np.column_stack([counts.T, remainder])
    result['marginal_inputs'] = {'category_genes': union_genes, 'last_category': 'REMAINDER_ALL_OTHER_RNA',
                                 'cell_ids': cell_ids, 'animal_ids': metadata['animal_id'].tolist(),
                                 'celltypes': metadata['celltype'].tolist(), 'counts_by_cell': categories.tolist(),
                                 'raw_library_totals': library.tolist(), 'rng': 'PCG64',
                                 'sampling_method': 'multivariate_hypergeometric:marginals', 'numpy_version': np.__version__}
    union_log = np.log2(1 + SCALE * counts / library)
    result['unthinned_subset'] = []
    for name, panel in panels.items():
        idx = [union_genes.index(gene) for gene in panel['present_mouse_genes']]
        result['unthinned_subset'].append({'panel': name, **summarize(union_log[idx], panel['present_mouse_genes'], metadata, common, pairs)})
    result['thinned'] = []
    for seed in SEEDS:
        ids, ordered, draws = thin_marginals(cell_ids, categories, seed)
        if ids != cell_ids or not np.array_equal(ordered, categories):
            raise ValueError('Cell ordering changed during sampling')
        log_values = np.log2(1 + SCALE * draws[:, :-1].T / DEPTH)
        panel_rows = []
        for name, panel in panels.items():
            idx = [union_genes.index(gene) for gene in panel['present_mouse_genes']]
            panel_rows.append({'panel': name, **summarize(log_values[idx], panel['present_mouse_genes'], metadata, common, pairs)})
        result['thinned'].append({'seed': seed, 'status': 'available', 'draws_by_cell': draws.tolist(),
                                  'draw_sha256_little_endian_int64': hashlib.sha256(draws.astype('<i8').tobytes()).hexdigest(),
                                  'every_cell_total': DEPTH, 'bounds_pass': True, 'panels': panel_rows})
    return result


def run(raw, contract, orthology, parent, freeze):
    if np.__version__ != '2.5.4':
        raise ValueError('Frozen NumPy 2.5.4 is required for seeded replay')
    if raw.source_sha256 != parent['source_sha256']:
        raise ValueError('Source differs from original decomposition')
    rows, panels = original_rows(raw, contract, orthology, parent)
    if len(rows) != 16 or len({(r['cell_floor'], r['panel'], r['scale']) for r in rows}) != 16:
        raise ValueError('Exactly all 16 original rows are required')
    return {'claim_level': 'Verified', 'evidence_class': 'posthoc_recovered_cell_descriptive_sensitivity',
            'prior_outcomes_known': True, 'freeze': freeze, 'source_sha256': raw.source_sha256,
            'extension_code_sha256': sha(Path(__file__)), 'extension_contract_sha256': sha(HERE / 'posthoc-contract.json'),
            'parent_result_sha256': sha(HERE / 'results.json'), 'parent_code_sha256': sha(HERE / 'decompose.py'),
            'analysis_loader_sha256': sha(HERE.parent / 'analysis/neural_analysis.py'),
            'orthology_sha256': sha(HERE.parent / 'analysis/orthology.json'),
            'parent_support': parent['support'], 'original_rows': rows,
            'depth_diagnostic': depth_diagnostic(raw, contract, panels, parent),
            'interpretation': 'All conventions partition the same conditional recovered-cell average; components are algebraic and have no causal attribution.',
            'limits': ['Named types may contain subtype/state and capture differences.',
                       'Treatment-associated selection into common support can change the conditional estimand.',
                       'Depth conditioning and thinning do not remove capture or cell-selection bias.',
                       'OSKM induction plus doxycycline is compared with untreated animals; no dox-only controls separate drug and construct effects.',
                       'All CX004 readouts remain insufficient_signal.'],
            'synthetic_data_in_observed_results': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=HERE / 'extension-results.json')
    parser.add_argument('--replay-frozen-hashes', action='store_true', help='Check archived input hashes; historical git proof is not rerun.')
    args = parser.parse_args()
    scratch_guard()
    freeze, parent = require_extension_freeze(args.replay_frozen_hashes)
    root = HERE.parent
    contract = json.loads((root / 'analysis/contract.json').read_text())
    orthology = json.loads((root / 'analysis/orthology.json').read_text())
    result = run(load_cohort2(args.cache), contract, orthology, parent, freeze)
    save_json(args.output, result)
    mode = 'archived-hash replay; historical git proof not rerun' if args.replay_frozen_hashes else 'strict original commit proof'
    print(f"PASS: 16 original rows; fixed-depth support {result['depth_diagnostic']['support']['status']}; {mode}")


if __name__ == '__main__':
    main()
