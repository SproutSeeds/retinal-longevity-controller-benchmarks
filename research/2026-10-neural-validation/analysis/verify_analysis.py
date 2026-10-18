#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Audit published result arithmetic and run synthetic scientific adversaries."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

import numpy as np

from neural_analysis import save_json, sha

HERE = Path(__file__).resolve().parent


def check_results(data):
    checks = []

    def check(name, value):
        checks.append({'name': name, 'status': 'PASS' if bool(value) else 'FAIL'})

    check('exact_3857_cells_and_7_animals', data['cell_count'] == 3857 and data['independent_animals'] == 7)
    check('full_7_by_14_animal_celltype_grid', len(data['animal_celltype_qc']) == 98)
    check('full_10_by_4_by_2_predeclared_contrast_grid', len(data['contrasts']) == 80)
    check('all_280_named_animal_panel_profiles_retained', len(data['animal_panel_profiles']) == 280)
    check('qc_total_recovers_all_cells', sum(q['cells'] for q in data['animal_celltype_qc']) == 3857)
    check('numeric_clusters_preserved', sum(q['cells'] for q in data['animal_celltype_qc'] if q['celltype'].isdigit()) == 70)
    check('readouts_remain_insufficient', set(data['readouts'].values()) == {'insufficient_signal'})
    check('cohort2_current_analysis_code_bound', data['analysis_code_sha256'] == sha(HERE / 'neural_analysis.py'))
    for animal in sorted({q['animal_id'] for q in data['composition']['rows']}):
        rows = [r for r in data['composition']['rows'] if r['animal_id'] == animal]
        check('all_composition_sums_to_one:' + animal, abs(sum(r['fraction_all_recovered'] for r in rows) - 1) < 1e-12)
        check('named_composition_sums_to_one:' + animal,
              abs(sum(r['fraction_named_recovered'] for r in rows if r['fraction_named_recovered'] is not None) - 1) < 1e-12)
    for row in data['contrasts']:
        label = ':'.join([row['primary']['support_tier'], row['primary']['celltype'], row['panel_name']])
        for role in ['primary', 'secondary']:
            result = row[role]
            if result['status'] == 'unavailable':
                check('unavailable_keeps_reason_and_no_effect:' + role + ':' + label,
                      bool(result['support_failures'] or result['panel_failures']) and result['methods'] == {})
                continue
            check('available_has_no_failures:' + role + ':' + label,
                  not result['support_failures'] and not result['panel_failures'])
            check('exact_animal_count:' + role + ':' + label,
                  result['independent_animal_counts'] == {'treated': 2, 'control': 2 if role == 'primary' else 3})
            check('all_animals_omitted_once:' + role + ':' + label,
                  {x['omitted_animal'] for x in result['single_animal_omissions']} == set(result['animals']))
            for method, stats in result['methods'].items():
                expected = np.mean([stats['animal_scores'][a] for a in result['treated_animals']]) - np.mean(
                    [stats['animal_scores'][a] for a in result['control_animals']])
                check('effect_equals_animal_means:' + role + ':' + label + ':' + method,
                      abs(expected - stats['mean_difference']) < 1e-12)
                check('score_equals_fixed_gene_average:' + role + ':' + label + ':' + method,
                      all(abs(np.mean(list(values.values())) - stats['animal_scores'][animal]) < 1e-12
                          for animal, values in stats['animal_gene_values'].items()))
                if role == 'primary':
                    check('primary_equals_lane_average:' + label + ':' + method,
                          abs(np.mean([p['difference'] for p in stats['within_lane_differences']]) - expected) < 1e-12)
                check('all_genes_omitted_once:' + role + ':' + label + ':' + method,
                      set(stats['single_gene_omission_differences']) == set(result['panel']['present_mouse_genes']))
                for omitted, effect in stats['single_gene_omission_differences'].items():
                    scores = {a: np.mean([value for gene, value in values.items() if gene != omitted])
                              for a, values in stats['animal_gene_values'].items()}
                    expected_omission = np.mean([scores[a] for a in result['treated_animals']]) - np.mean(
                        [scores[a] for a in result['control_animals']])
                    check('omission_arithmetic:' + role + ':' + label + ':' + method + ':' + omitted,
                          abs(expected_omission - effect) < 1e-12)
            factors = result['normalization']['median_ratio_size_factors']
            if factors is not None:
                check('geometric_centered_factors:' + role + ':' + label,
                      all(f > 0 for f in factors) and abs(np.mean(np.log(factors))) < 1e-12)
    check('all_pass', all(c['status'] == 'PASS' for c in checks))
    return checks


def check_cohort1_and_cross(cohort1, cohort2, cross):
    checks = []

    def check(name, value):
        checks.append({'name': name, 'status': 'PASS' if bool(value) else 'FAIL'})

    check('cohort1_exact_1194_cells_four_animals_one_library',
          cohort1['cell_count'] == 1194 and cohort1['independent_animals'] == 4 and cohort1['independent_libraries'] == 1)
    check('cohort1_full_56_animal_type_and_80_contrast_rows',
          len(cohort1['animal_celltype_qc']) == 56 and len(cohort1['contrasts']) == 80)
    check('cohort1_all_160_named_animal_panel_profiles', len(cohort1['animal_panel_profiles']) == 160)
    check('cohort1_all_cells_preserved', sum(q['cells'] for q in cohort1['animal_celltype_qc']) == 1194)
    check('cohort1_current_analysis_code_bound', cohort1['analysis_code_sha256'] == sha(HERE / 'cohort1_analysis.py'))
    check('cohort1_current_shared_code_bound', cohort1['shared_analysis_code_sha256'] == sha(HERE / 'neural_analysis.py'))
    check('cross_cohort_input_bytes_bound', cross['cohort1_result_sha256'] == sha(HERE / 'cohort1-results.json')
          and cross['cohort2_result_sha256'] == sha(HERE / 'cohort2-results.json'))
    check('cross_cohort_full_80_rows', len(cross['comparisons']) == 80)
    ids1 = {r['animal_id'] for r in cohort1['animal_celltype_qc']}
    ids2 = {r['animal_id'] for r in cohort2['animal_celltype_qc']}
    check('cohort_animal_identifiers_disjoint', not (ids1 & ids2))
    for cohort_name, data in [('cohort1', cohort1), ('cohort2', cohort2)]:
        qc = {(q['animal_id'], q['celltype']): q for q in data['animal_celltype_qc']}
        for row in data['animal_panel_profiles']:
            label = ':'.join([cohort_name, row['animal_id'], row['celltype'], row['panel_name']])
            total = qc[(row['animal_id'], row['celltype'])]['raw_library_total']
            if total == 0:
                check('empty_profile_unscored:' + label,
                      row['log2_cpm_score'] is None and row['log2_cpm_gene_values'] is None)
            else:
                expected = {g: float(np.log2(1 + 1e6 * value / total)) for g, value in row['raw_counts'].items()}
                check('per_animal_logcpm_matches_raw_panel_counts:' + label,
                      all(abs(value - row['log2_cpm_gene_values'][g]) < 1e-12 for g, value in expected.items()))
        check('readouts_insufficient:' + cohort_name, set(data['readouts'].values()) == {'insufficient_signal'})
    for animal in sorted(ids1):
        rows = [r for r in cohort1['composition']['rows'] if r['animal_id'] == animal]
        check('cohort1_composition_exact_denominator:' + animal,
              abs(sum(r['fraction_all_recovered'] for r in rows) - 1) < 1e-12 and
              abs(sum(r['fraction_named_recovered'] for r in rows if r['fraction_named_recovered'] is not None) - 1) < 1e-12)
    for row in cohort1['contrasts']:
        result = row['comparison']
        label = ':'.join([result['support_tier'], result['celltype'], row['panel_name']])
        if result['status'] == 'unavailable':
            check('cohort1_failed_stratum_retained:' + label,
                  bool(result['support_failures'] or result['panel_failures']) and not result['methods'])
            continue
        check('cohort1_no_invented_lane_omissions:' + label, result['single_lane_omissions'] == [])
        check('cohort1_two_treated_two_controls:' + label,
              result['independent_animal_counts'] == {'treated': 2, 'control': 2})
        check('cohort1_all_four_animal_omissions:' + label,
              {r['omitted_animal'] for r in result['single_animal_omissions']} == set(result['animals']))
        for method, stats in result['methods'].items():
            key = label + ':' + method
            expected = np.mean([stats['animal_scores'][a] for a in result['treated_animals']]) - np.mean(
                [stats['animal_scores'][a] for a in result['control_animals']])
            check('cohort1_animal_mean_arithmetic:' + key, abs(expected - stats['mean_difference']) < 1e-12)
            check('cohort1_four_descriptive_pairs_no_lane_pairs:' + key,
                  len(stats['all_treated_control_differences']) == 4 and stats['within_lane_differences'] == []
                  and stats['pairwise_differences_are_independent_replicates'] is False)
            check('cohort1_pairwise_arithmetic:' + key,
                  all(abs(stats['animal_scores'][p['treated']] - stats['animal_scores'][p['control']] - p['difference']) < 1e-12
                      for p in stats['all_treated_control_differences']))
            for omitted, value in stats['single_gene_omission_differences'].items():
                scores = {a: np.mean([v for g, v in gene_values.items() if g != omitted])
                          for a, gene_values in stats['animal_gene_values'].items()}
                omission = np.mean([scores[a] for a in result['treated_animals']]) - np.mean(
                    [scores[a] for a in result['control_animals']])
                check('cohort1_gene_omission_arithmetic:' + key + ':' + omitted, abs(value - omission) < 1e-12)
    for row in cross['comparisons']:
        label = ':'.join([row['support_tier'], row['celltype'], row['panel_name']])
        if row['status'] == 'unavailable':
            check('cross_unavailable_does_not_impute:' + label, row['methods'] == {})
            continue
        for method, values in row['methods'].items():
            if values['status'] != 'available':
                continue
            a, b = values['cohort1_mean_difference'], values['cohort2_mean_difference']
            check('cross_direction_and_floor_arithmetic:' + label + ':' + method,
                  values['same_nonzero_direction'] == bool(a != 0 and b != 0 and np.sign(a) == np.sign(b))
                  and values['both_pass_fixed_floor'] == bool(abs(a) >= cross['descriptive_floor'] and abs(b) >= cross['descriptive_floor']))
    return checks


def main():
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern='test_neural_analysis.py')
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    tests = {'claim_level': 'Verified' if result.wasSuccessful() else 'Heuristic',
             'evidence_class': 'synthetic_software_adversaries_only',
             'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
             'status': 'PASS' if result.wasSuccessful() else 'FAIL',
             'test_code_sha256': sha(HERE / 'test_neural_analysis.py'),
             'analysis_code_sha256': sha(HERE / 'neural_analysis.py')}
    save_json(HERE / 'TESTS.json', tests)
    data = json.loads((HERE / 'cohort2-results.json').read_text())
    checks = check_results(data)
    cohort1 = json.loads((HERE / 'cohort1-results.json').read_text())
    cross = json.loads((HERE / 'cross-cohort-results.json').read_text())
    checks.extend(check_cohort1_and_cross(cohort1, data, cross))
    verification = {'claim_level': 'Verified' if all(c['status'] == 'PASS' for c in checks) else 'Heuristic',
                    'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) and result.wasSuccessful() else 'FAIL',
                    'checks': checks, 'check_count': len(checks), 'synthetic_tests': tests,
                    'result_sha256': sha(HERE / 'cohort2-results.json'),
                    'cohort1_result_sha256': sha(HERE / 'cohort1-results.json'),
                    'cross_cohort_result_sha256': sha(HERE / 'cross-cohort-results.json'),
                    'verification_code_sha256': sha(Path(__file__)),
                    'scope': 'Arithmetic, provenance and synthetic failure resistance; does not establish biological benefit or replicate independence.'}
    save_json(HERE / 'VERIFICATION.json', verification)
    print(verification['status'], len(checks), 'result checks;', result.testsRun, 'synthetic tests')
    if verification['status'] != 'PASS':
        sys.exit(1)


if __name__ == '__main__':
    main()
