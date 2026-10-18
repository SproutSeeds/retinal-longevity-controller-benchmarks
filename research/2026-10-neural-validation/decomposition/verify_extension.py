#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Verify saved extension algebra and synthetic tests without loading raw RDS.

--reproduce additionally reruns the observed calculation from cached raw RNA in
both strict-commit and archived-hash modes, writing a separate byte-replay receipt.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

import extension as e

HERE = Path(__file__).resolve().parent


class Checks:
    def __init__(self):
        self.count = 0

    def require(self, condition, message):
        self.count += 1
        if not condition:
            raise AssertionError(message)

    def close(self, actual, expected, message):
        self.require(np.shape(actual) == np.shape(expected) and
                     np.isfinite(np.asarray(actual, dtype=float)).all() and
                     np.allclose(actual, expected, rtol=0, atol=e.TOL), message)


def check_components(record, p_t, p_c, mu_t, mu_c, check):
    p_t, p_c, mu_t, mu_c = [np.asarray(x, dtype=float) for x in (p_t, p_c, mu_t, mu_c)]
    check.require(len({x.shape for x in (p_t, p_c, mu_t, mu_c)}) == 1 and p_t.ndim == 1, 'Common support dimensions')
    for fractions in (p_t, p_c):
        check.require((fractions >= 0).all(), 'Nonnegative conditional fractions')
        check.close(fractions.sum(), 1, 'Conditional fractions sum to one')
    total = p_t @ mu_t - p_c @ mu_c
    expected = {
        'control_reference': ((p_t - p_c) * mu_c, p_t * (mu_t - mu_c)),
        'treated_reference': ((p_t - p_c) * mu_t, p_c * (mu_t - mu_c)),
        'symmetric': (.5 * (p_t - p_c) * (mu_t + mu_c), .5 * (p_t + p_c) * (mu_t - mu_c))}
    check.require(set(record) == set(e.CONVENTIONS), 'Every convention retained')
    for convention, (composition, within) in expected.items():
        saved = record[convention]
        for field, value in [('total', total), ('composition', composition.sum()), ('within_type', within.sum()),
                             ('composition_by_type', composition), ('within_by_type', within)]:
            check.close(saved[field], value, 'Independent convention formula: ' + field)
        check.close(saved['total'], saved['composition'] + saved['within_type'], 'Convention identity')
        check.require(saved['identity_error'] <= e.TOL, 'Recorded identity error')
        check.require(saved['opposed_components'] == (saved['composition'] * saved['within_type'] < 0), 'Opposing component label')
        for field in e.FIELDS:
            expected_sign = 'positive' if saved[field] > 0 else 'negative' if saved[field] < 0 else 'zero'
            check.require(saved['signs'][field] == expected_sign, 'Component sign label')
    for field in e.FIELDS + ('composition_by_type', 'within_by_type'):
        check.close(record['symmetric'][field], .5 * (np.asarray(record['control_reference'][field]) + np.asarray(record['treated_reference'][field])), 'Symmetric reference average')


def check_average(row, check):
    for convention in e.CONVENTIONS:
        saved = row['equal_lane_mean'][convention]
        for field in e.FIELDS + ('composition_by_type', 'within_by_type'):
            expected = np.mean([lane['conventions'][convention][field] for lane in row['lane_contrasts']], axis=0)
            check.close(saved[field], expected, 'Equal lane weighting')
        check.close(saved['total'], saved['composition'] + saved['within_type'], 'Equal-lane identity')
        check.require(saved['opposed_components'] == (saved['composition'] * saved['within_type'] < 0), 'Equal-lane opposition')


def check_panel(row, pairs, check):
    check.require(row['status'] == 'available', 'Available panel')
    check.require(row['panel_size'] == len(row['panel_genes']) == len(set(row['panel_genes'])), 'Fixed distinct gene denominator')
    check.require(len(row['lane_contrasts']) == len(pairs), 'Every lane retained')
    for lane, pair in zip(row['lane_contrasts'], pairs, strict=True):
        check.require(all(lane[k] == pair[k] for k in pair), 'Paired animal identity')
        check_components(lane['conventions'], lane['fractions_treated'], lane['fractions_control'], lane['means_treated'], lane['means_control'], check)
        for role in ('treated', 'control'):
            animal = pair[role]
            counts = np.asarray(row['counts_by_animal_type'][animal])
            check.require(len(counts) == len(row['common_types']) and (counts > 0).all(), 'Fixed positive type support')
            check.close(lane['fractions_' + role], counts / counts.sum(), 'Observed conditional fraction')
            check.close(np.asarray(lane['fractions_' + role]) @ lane['means_' + role], row['animal_direct_cell_average'][animal], 'Direct average from type means')
        check.close(lane['direct_cell_average_difference'], row['animal_direct_cell_average'][pair['treated']] - row['animal_direct_cell_average'][pair['control']], 'Direct paired difference')
        check.close(lane['conventions']['symmetric']['total'], lane['direct_cell_average_difference'], 'Same direct total')
    check_average(row, check)


def check_genes(row, check):
    genes = row['gene_contributions']
    check.require([g['gene'] for g in genes] == row['panel_genes'], 'Every fixed gene, including zero contributions')
    for gene in genes:
        check.close(gene['panel_weight'], 1 / row['panel_size'], 'Fixed per-gene contribution weight')
        for gl, lane in zip(gene['lane_contrasts'], row['lane_contrasts'], strict=True):
            check.require(all(gl[k] == lane[k] for k in ('lane', 'treated', 'control')), 'Gene lane identity')
            check_components(gl['conventions'], lane['fractions_treated'], lane['fractions_control'],
                             np.asarray(gl['means_treated_unweighted']) / row['panel_size'],
                             np.asarray(gl['means_control_unweighted']) / row['panel_size'], check)
        check_average(gene, check)
    for k, lane in enumerate(row['lane_contrasts']):
        for role in ('treated', 'control'):
            check.close(np.mean([g['lane_contrasts'][k]['means_' + role + '_unweighted'] for g in genes], axis=0), lane['means_' + role], 'Gene means reproduce panel type means')
        for convention in e.CONVENTIONS:
            for field in e.FIELDS + ('composition_by_type', 'within_by_type'):
                check.close(np.sum([g['lane_contrasts'][k]['conventions'][convention][field] for g in genes], axis=0), lane['conventions'][convention][field], 'Per-gene sum reproduces panel component')
    for convention in e.CONVENTIONS:
        for field in e.FIELDS:
            check.close(sum(g['equal_lane_mean'][convention][field] for g in genes), row['equal_lane_mean'][convention][field], 'Equal-lane gene sum')


def check_depth(depth, parent, panels, pairs, check):
    support = depth['support']
    original = next(row for row in parent['support'] if row['cell_floor'] == 20)
    common = original['common_named_types']
    animals = [a for pair in pairs for a in (pair['treated'], pair['control'])]
    check.require(common == support['fixed_common_types'] == ['Oligodendrocyte', 'Microglia'], 'Fixed two-type depth support')
    check.require((depth['scale'], depth['depth'], depth['seeds']) == (10000, 1000, list(e.SEEDS)), 'Fixed scale, depth and three seeds')
    check.require((support['minimum_cells'], support['minimum_detected_genes']) == (20, 500), 'Original support thresholds')
    check.require(support['support_measured_before_thinning'] is True, 'Unthinned support test')
    check.require([(row['animal_id'], row['celltype']) for row in support['rows']] == [(a, ct) for a in animals for ct in common], 'Every depth support stratum')
    expected_failures = []
    for row in support['rows']:
        animal, ct = row['animal_id'], row['celltype']
        denominator = support['denominators'][animal]
        old = original['denominators'][animal]
        check.require(row['original_cells'] == old['counts_by_retained_type'][ct], 'Original per-type cell count')
        check.require(row['original_cells'] == row['retained_cells'] + row['excluded_cells'], 'Depth selection count conservation')
        check.require(denominator['all_recovered_cells'] == old['all_recovered_cells'], 'All-recovered denominator preserved')
        check.close(row['retained_fraction_all_recovered'], row['retained_cells'] / old['all_recovered_cells'], 'Retained type fraction all recovered')
        expected = []
        if row['retained_cells'] < 20:
            expected.append('cells_below_20')
        if row['unthinned_retained_detected_genes'] < 500:
            expected.append('detected_genes_below_500')
        if row['unthinned_retained_library_total'] <= 0:
            expected.append('empty_pseudobulk')
        check.require(row['support_failures'] == expected, 'Every fixed support failure recorded')
        if expected:
            expected_failures.append({'animal_id': animal, 'celltype': ct, 'failures': expected})
        if row['retained_cells']:
            check.require(row['retained_depth']['cells'] == row['retained_cells'] and row['retained_depth']['minimum'] >= 1000, 'Retained depth threshold')
            check.require(row['retained_depth']['total_umis'] == row['unthinned_retained_library_total'], 'Retained library total')
    for animal in animals:
        denominator = support['denominators'][animal]
        rows = [row for row in support['rows'] if row['animal_id'] == animal]
        check.require(denominator['retained_cells'] == sum(row['retained_cells'] for row in rows), 'Retained animal cell count')
        check.require(denominator['original_common_support_cells'] == sum(row['original_cells'] for row in rows), 'Original animal support count')
        check.require(denominator['depth_excluded_common_support_cells'] == sum(row['excluded_cells'] for row in rows), 'Depth exclusions')
        check.require(denominator['all_excluded_cells'] == denominator['all_recovered_cells'] - denominator['retained_cells'], 'All exclusions')
        check.close(denominator['retained_fraction_all_recovered'], denominator['retained_cells'] / denominator['all_recovered_cells'], 'Retained animal fraction')
    check.require(support['failures'] == expected_failures, 'Fixed support failure list')
    check.require(support['status'] == ('unavailable' if expected_failures else 'available'), 'Whole-diagnostic support gate')
    check.require([row['seed'] for row in depth['thinned']] == list(e.SEEDS), 'Every seed retained')
    check.require([row['panel'] for row in depth['unthinned_subset']] == list(panels), 'All unthinned subset panels')
    if expected_failures:
        check.require(depth['marginal_inputs'] is None, 'No draws after fixed support failure')
        check.require(all(row['status'] == 'unavailable' for row in depth['unthinned_subset']), 'Unthinned subset not promoted after support failure')
        check.require(all(row['status'] == 'unavailable' for row in depth['thinned']), 'All seeds unavailable after support failure')
        return
    inputs = depth['marginal_inputs']
    union = sorted({gene for panel in panels.values() for gene in panel})
    check.require(inputs['category_genes'] == union and inputs['last_category'] == 'REMAINDER_ALL_OTHER_RNA', 'Exact union and one remainder')
    check.require(inputs['numpy_version'] == '2.5.4' and inputs['rng'] == 'PCG64' and inputs['sampling_method'] == 'multivariate_hypergeometric:marginals', 'Frozen RNG and method')
    ids = inputs['cell_ids']
    check.require(ids == sorted(set(ids)), 'Sorted unique input cell IDs')
    counts = np.asarray(inputs['counts_by_cell'])
    library = np.asarray(inputs['raw_library_totals'])
    check.require(counts.shape == (len(ids), len(union) + 1) and np.issubdtype(counts.dtype, np.integer) and (counts >= 0).all(), 'Integer nonnegative marginal input matrix')
    check.require(np.array_equal(counts.sum(axis=1), library) and (library >= 1000).all(), 'All RNA counts preserved by remainder')
    metadata = pd.DataFrame({'animal_id': inputs['animal_ids'], 'celltype': inputs['celltypes']}, index=ids)
    check.require(set(metadata.animal_id) == set(animals) and set(metadata.celltype) == set(common), 'Exact retained animal/type identities')
    for row in support['rows']:
        selected = ((metadata.animal_id == row['animal_id']) & (metadata.celltype == row['celltype'])).to_numpy()
        check.require(int(selected.sum()) == row['retained_cells'], 'Retained marginal cells agree with support')
        check.require(e.depth_summary(library[selected]) == row['retained_depth'], 'Retained depths agree with input counts')

    def check_scores(panel_rows, log_values):
        check.require([row['panel'] for row in panel_rows] == list(panels), 'All fixed panels in depth run')
        for row in panel_rows:
            check.require(row['common_types'] == common and row['panel_genes'] == panels[row['panel']], 'Identical depth panel and common support')
            check_panel(row, pairs, check)
            indices = [union.index(gene) for gene in panels[row['panel']]]
            scores = log_values[:, indices].mean(axis=1)
            for lane in row['lane_contrasts']:
                for role in ('treated', 'control'):
                    animal = lane[role]
                    means = [float(scores[((metadata.animal_id == animal) & (metadata.celltype == ct)).to_numpy()].mean()) for ct in common]
                    check.close(lane['means_' + role], means, 'Recomputed depth type means')
                    direct = float(scores[(metadata.animal_id == animal).to_numpy()].mean())
                    check.close(row['animal_direct_cell_average'][animal], direct, 'Recomputed direct depth average')

    check_scores(depth['unthinned_subset'], np.log2(1 + 10000 * counts[:, :-1] / library[:, None]))
    for sample in depth['thinned']:
        check.require(sample['status'] == 'available', 'Available seed')
        draws = np.asarray(sample['draws_by_cell'])
        check.require(draws.shape == counts.shape and np.issubdtype(draws.dtype, np.integer), 'Integer draw matrix')
        check.require((draws >= 0).all() and (draws <= counts).all(), 'Every draw within input bounds')
        check.require((draws.sum(axis=1) == 1000).all(), 'Exactly 1000 UMIs per cell')
        check.require(sample['draw_sha256_little_endian_int64'] == hashlib.sha256(draws.astype('<i8').tobytes()).hexdigest(), 'Draw byte digest')
        rng = np.random.Generator(np.random.PCG64(sample['seed']))
        replay = np.asarray([rng.multivariate_hypergeometric(row, 1000, method='marginals') for row in counts])
        check.require(np.array_equal(draws, replay), 'Exact seed replay from saved marginal inputs')
        check_scores(sample['panels'], np.log2(1 + 10000 * draws[:, :-1] / 1000))


def verify_saved(replay_frozen_hashes=False):
    freeze, parent = e.require_extension_freeze(replay_frozen_hashes)
    result = json.loads((HERE / 'extension-results.json').read_text())
    contract = json.loads((HERE.parent / 'analysis/contract.json').read_text())
    check = Checks()
    check.require(result['freeze'] == freeze, 'Exact extension freeze receipt')
    for field, path in [('extension_code_sha256', HERE / 'extension.py'), ('extension_contract_sha256', HERE / 'posthoc-contract.json'),
                        ('parent_result_sha256', HERE / 'results.json'), ('parent_code_sha256', HERE / 'decompose.py'),
                        ('analysis_loader_sha256', HERE.parent / 'analysis/neural_analysis.py'),
                        ('orthology_sha256', HERE.parent / 'analysis/orthology.json')]:
        check.require(result[field] == e.sha(path), 'Current artifact binding: ' + field)
    check.require(result['source_sha256'] == parent['source_sha256'], 'Parent raw RNA source hash')
    check.require(result['prior_outcomes_known'] is True and result['synthetic_data_in_observed_results'] is False, 'Post hoc observed evidence class')
    check.require(result['parent_support'] == parent['support'], 'All original support failures preserved')
    key = lambda row: tuple(row[k] for k in ('cell_floor', 'panel', 'scale'))
    check.require(len(result['original_rows']) == 16 and [key(row) for row in result['original_rows']] == [key(row) for row in parent['results']], 'Every original row retained in order')
    pairs = contract['cohort2_primary']['pairs']
    panels = {}
    for row, original in zip(result['original_rows'], parent['results'], strict=True):
        check.require(row['status'] == original['status'], 'Original availability retained')
        if row['status'] != 'available':
            check.require(row['parent_failure'] == original, 'Complete original failure retained')
            continue
        panels[row['panel']] = original['panel_genes']
        check.require(row['panel_genes'] == original['panel_genes'] and row['common_types'] == original['common_types'], 'Exact original genes and common types')
        check_panel(row, pairs, check)
        check_genes(row, check)
        for lane, old in zip(row['lane_contrasts'], original['lane_contrasts'], strict=True):
            for field in e.FIELDS + ('composition_by_type', 'within_by_type'):
                check.close(lane['conventions']['symmetric'][field], old[field], 'Original symmetric component unchanged')
            for field in ('fractions_treated', 'fractions_control', 'means_treated', 'means_control'):
                check.close(lane[field], old[field], 'Original conditional summary unchanged')
    check_depth(result['depth_diagnostic'], parent, panels, pairs, check)
    return check.count, result


def reproduce(cache, receipt_path):
    scratch = e.scratch_guard()
    scratch.mkdir(parents=True, exist_ok=True)
    original = HERE / 'extension-results.json'
    expected = original.read_bytes()
    rows = []
    with tempfile.TemporaryDirectory(prefix='extension-replay-', dir=scratch) as directory:
        for mode in ('strict_original_commit_proof', 'archived_hashes_historical_git_proof_not_rerun'):
            output = Path(directory) / (mode + '.json')
            command = [sys.executable, str(HERE / 'extension.py'), '--cache', str(cache), '--output', str(output)]
            if mode.startswith('archived'):
                command.append('--replay-frozen-hashes')
            completed = subprocess.run(command, text=True, capture_output=True, check=True)
            identical = output.read_bytes() == expected
            rows.append({'mode': mode, 'byte_identical': identical, 'sha256': e.sha(output),
                         'bytes': output.stat().st_size, 'runner_stdout': completed.stdout.strip()})
            if not identical:
                raise AssertionError('Observed replay differs: ' + mode)
    receipt = {'status': 'PASS', 'claim_level': 'Verified', 'scope': 'Observed raw-source replay, separately from saved-output verification',
               'source_sha256': json.loads(original.read_text())['source_sha256'],
               'extension_code_sha256': e.sha(HERE / 'extension.py'), 'verifier_code_sha256': e.sha(Path(__file__)),
               'result_sha256': e.sha(original), 'runs': rows,
               'determinism': 'Pinned Python/dependencies; lexically sorted unique cell IDs; PCG64 seeds 181026,181027,181028; exact 1000-UMI marginal draws.'}
    e.save_json(receipt_path, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay-frozen-hashes', action='store_true', help='Archived hash verification; historical git proof is not rerun.')
    parser.add_argument('--output', type=Path, default=HERE / 'EXTENSION_VERIFICATION.json')
    parser.add_argument('--reproduce', action='store_true', help='Additionally replay observed output from cached RDS in both modes.')
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--reproduction-output', type=Path, default=HERE / 'EXTENSION_REPRODUCTION.json')
    args = parser.parse_args()
    if args.reproduce and args.cache is None:
        parser.error('--reproduce requires --cache')
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern='test_extension.py')
    tests = unittest.TextTestRunner(verbosity=1).run(suite)
    if not tests.wasSuccessful():
        raise SystemExit('FAIL: synthetic tests')
    count, result = verify_saved(args.replay_frozen_hashes)
    receipt = {'status': 'PASS', 'claim_level': 'Verified', 'checks_passed': count, 'synthetic_tests_passed': tests.testsRun,
               'verification_scope': 'Saved-output hashes, algebra, support and exact draw replay plus synthetic adversarial tests; raw RDS is not opened.',
               'git_proof': 'historical proof not rerun; archived hashes checked' if args.replay_frozen_hashes else 'strict original commit proof rerun',
               'source_sha256': result['source_sha256'], 'extension_code_sha256': e.sha(HERE / 'extension.py'),
               'verifier_code_sha256': e.sha(Path(__file__)), 'tests_sha256': e.sha(HERE / 'test_extension.py'),
               'contract_sha256': e.sha(HERE / 'posthoc-contract.json'), 'result_sha256': e.sha(HERE / 'extension-results.json'),
               'parent_result_sha256': e.sha(HERE / 'results.json'),
               'original_rows': len(result['original_rows']), 'depth_support': result['depth_diagnostic']['support']['status']}
    e.save_json(args.output, receipt)
    print(f'PASS: {count} saved-output checks; {tests.testsRun} synthetic tests; no raw RDS read')
    if args.reproduce:
        reproduce(args.cache, args.reproduction_output)
        print('PASS: observed result byte-identical in strict and archived-hash modes')


if __name__ == '__main__':
    main()
