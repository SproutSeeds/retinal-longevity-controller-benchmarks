#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Synthetic adversaries only: these tests do not read biological expression."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix

from neural_analysis import (RawData, Pseudobulk, aggregate, attach_admission, composition,
                             evaluate_contrast, load_raw_rds, mean_difference, normalizations,
                             panel_coverage, require_freeze, stability_descriptor,
                             summarize_method, support_failures, validate_sparse_counts, save_json, sha)
from prepare_orthology import mapping_from_rows
from cohort1_analysis import attach_cohort1_admission, cross_cohort_comparison, direction_details


THRESHOLDS = {'minimum_panel_coverage_source_human': .8,
              'minimum_panel_coverage_orthology_eligible': .8,
              'minimum_panel_genes_present': 3,
              'median_ratio_min_all_positive_genes': 100}
PAIRS = [{'lane': 'Lane1', 'treated': 'T1', 'control': 'C1'},
         {'lane': 'Lane2', 'treated': 'T2', 'control': 'C2'}]
PANEL = {'indices': [0, 1, 2], 'present_mouse_genes': ['G0', 'G1', 'G2'], 'failures': []}


def raw_fixture():
    counts = csc_matrix(np.array([[1, 3, 2, 4], [2, 4, 3, 5], [3, 5, 4, 6]], dtype=np.int64))
    columns = ['c1', 'c2', 'c3', 'c4']
    meta = pd.DataFrame({'hash.ID': ['h1', 'h1', 'h2', 'h2'],
                         'orig.ident': ['Lane1'] * 4, 'age': ['old'] * 4,
                         'genotype': ['OSKM'] * 4,
                         'Treatment': ['2Dox0', '2Dox0', 'untr', 'untr'],
                         'Celltype': ['A', '27', 'A', 'A'],
                         'LMO_classification.global': ['Singlet'] * 4,
                         'nCount_RNA': np.asarray(counts.sum(axis=0)).ravel()}, index=columns)
    admission = {'animals': [
        {'hash_id': 'h1', 'animal_label': 'T1', 'lane': 'Lane1', 'age_group': 'old',
         'genotype': 'OSKM', 'treatment': '2Dox0', 'cells': 2, 'celltype_counts': {'A': 1, '27': 1}},
        {'hash_id': 'h2', 'animal_label': 'C1', 'lane': 'Lane1', 'age_group': 'old',
         'genotype': 'OSKM', 'treatment': 'untr', 'cells': 2, 'celltype_counts': {'A': 2}}]}
    return counts, ['G0', 'G1', 'G2'], columns, meta, admission


def bulk_fixture():
    animals = ['T1', 'T2', 'C1', 'C2', 'C3']
    x = np.tile(np.arange(1, 601, dtype=np.int64)[:, None] % 10 + 10, (1, 5))
    x[:3, :2] *= 3
    qc, metadata = [], {}
    for a in animals:
        metadata[a] = {'lane': {'T1': 'Lane1', 'C1': 'Lane1', 'T2': 'Lane2', 'C2': 'Lane2', 'C3': 'Lane3'}[a],
                       'treatment': '2Dox0' if a.startswith('T') else 'untr',
                       'age_group': 'old', 'genotype': 'OSKM'}
        qc.append({'animal_id': a, 'celltype': 'A', 'cells': 20, 'detected_genes': 600,
                   'raw_library_total': int(x[:, animals.index(a)].sum()), **metadata[a]})
    return Pseudobulk(x, [f'G{i}' for i in range(600)], [(a, 'A') for a in animals], qc, metadata)


def evaluation(pb=None, cells=20, controls=None):
    return evaluate_contrast(pb or bulk_fixture(), 'A', PANEL, ['T1', 'T2'], controls or ['C1', 'C2'],
                             PAIRS, THRESHOLDS, cells, 500, 'lane_balanced_primary', 'primary_support')


class RawValidationTests(unittest.TestCase):
    def test_valid_sparse_fixture(self):
        counts, genes, columns, meta, _ = raw_fixture()
        self.assertTrue(validate_sparse_counts(counts, genes, columns, meta))

    def test_swapped_cell_metadata_fails(self):
        counts, genes, columns, meta, _ = raw_fixture()
        with self.assertRaisesRegex(ValueError, 'ordered'):
            validate_sparse_counts(counts, genes, columns, meta.iloc[::-1])

    def test_same_order_wrong_library_totals_fail(self):
        counts, genes, columns, meta, _ = raw_fixture()
        meta.loc['c1', 'nCount_RNA'] += 1
        with self.assertRaisesRegex(ValueError, 'totals'):
            validate_sparse_counts(counts, genes, columns, meta)

    def test_negative_fractional_and_nonfinite_counts_fail(self):
        for bad in [-1, .5, float('nan'), float('inf')]:
            counts, genes, columns, meta, _ = raw_fixture()
            counts = counts.astype(float)
            counts.data[0] = bad
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, 'Invalid raw counts'):
                validate_sparse_counts(counts, genes, columns, meta)

    def test_duplicate_genes_fail(self):
        counts, genes, columns, meta, _ = raw_fixture()
        genes[1] = genes[0]
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate_sparse_counts(counts, genes, columns, meta)

    def test_duplicate_sparse_coordinates_fail(self):
        counts, genes, columns, meta, _ = raw_fixture()
        counts = csc_matrix((np.array([1, 1, 1]), np.array([0, 0, 1]), np.array([0, 3, 3, 3, 3])), shape=(3, 4))
        with self.assertRaisesRegex(ValueError, 'Duplicate or unsorted'):
            validate_sparse_counts(counts, genes, columns, meta)

    def test_zero_cell_library_fails(self):
        counts, genes, columns, meta, _ = raw_fixture()
        values = counts.toarray()
        values[:, 0] = 0
        with self.assertRaisesRegex(ValueError, 'Empty'):
            validate_sparse_counts(csc_matrix(values), genes, columns, meta)

    def test_hash_mismatch_fails_before_r_parser(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'invalid.rds'
            path.write_text('This is deliberately not an R object.')
            with self.assertRaisesRegex(ValueError, 'source hash'):
                load_raw_rds(path, '0' * 64)


class IdentityTests(unittest.TestCase):
    def test_unknown_animal_fails(self):
        _, _, _, meta, admission = raw_fixture()
        meta.loc['c1', 'hash.ID'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            attach_admission(meta, admission)

    def test_duplicate_animal_labels_fail(self):
        _, _, _, meta, admission = raw_fixture()
        admission['animals'][1]['animal_label'] = 'T1'
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            attach_admission(meta, admission)

    def test_conflicting_treatment_fails(self):
        _, _, _, meta, admission = raw_fixture()
        meta.loc['c1', 'Treatment'] = 'untr'
        with self.assertRaisesRegex(ValueError, 'conflict'):
            attach_admission(meta, admission)

    def test_nonsinglet_fails(self):
        _, _, _, meta, admission = raw_fixture()
        meta.loc['c1', 'LMO_classification.global'] = 'Doublet'
        with self.assertRaisesRegex(ValueError, 'Non-singlet'):
            attach_admission(meta, admission)

    def test_changed_celltype_assignment_fails(self):
        _, _, _, meta, admission = raw_fixture()
        meta.loc['c1', 'Celltype'] = '27'
        with self.assertRaisesRegex(ValueError, 'Cell-type assignment'):
            attach_admission(meta, admission)


class AggregationTests(unittest.TestCase):
    def fixture_bulk(self):
        counts, genes, _, meta, admission = raw_fixture()
        raw = RawData(counts, genes, attach_admission(meta, admission), 'synthetic')
        return aggregate(raw, ['A', '27', 'empty'])

    def test_zero_and_unknown_types_remain_in_grid(self):
        pb = self.fixture_bulk()
        self.assertEqual(len(pb.qc), 6)
        self.assertEqual(pb.counts[:, pb.keys.index(('C1', '27'))].sum(), 0)
        self.assertEqual(sum(q['cells'] for q in pb.qc), 4)

    def test_pseudobulk_sums_by_animal_not_condition(self):
        pb = self.fixture_bulk()
        np.testing.assert_array_equal(pb.counts[:, pb.keys.index(('C1', 'A'))], [6, 8, 10])
        np.testing.assert_array_equal(pb.counts[:, pb.keys.index(('T1', 'A'))], [1, 2, 3])

    def test_unknown_cells_retained_in_all_composition_denominator(self):
        pb = self.fixture_bulk()
        output = composition(pb, ['A', 'empty'], [PAIRS[0]], ['T1'], ['C1'])
        t = next(r for r in output['rows'] if r['animal_id'] == 'T1' and r['celltype'] == 'A')
        self.assertEqual(t['fraction_all_recovered'], .5)
        self.assertEqual(t['fraction_named_recovered'], 1)
        self.assertEqual(t['unresolved_cells'], 1)

    def test_sparse_required_animal_invalidates_entire_primary(self):
        pb = bulk_fixture()
        pb.qc[0]['cells'] = 19
        result = evaluation(pb)
        self.assertEqual(result['status'], 'unavailable')
        self.assertEqual(result['support_failures'], {'T1': ['cells_below_20']})
        self.assertEqual(result['methods'], {})

    def test_sensitivity_does_not_modify_primary_failure(self):
        pb = bulk_fixture()
        pb.qc[0]['cells'] = 15
        self.assertEqual(evaluation(pb, cells=20)['status'], 'unavailable')
        self.assertEqual(evaluation(pb, cells=10)['status'], 'available')

    def test_detected_gene_failure_is_independent_of_cell_count(self):
        q = {'cells': 10000, 'detected_genes': 499, 'raw_library_total': 1000000}
        self.assertEqual(support_failures(q, 20, 500), ['detected_genes_below_500'])


class NormalizationAndPanelTests(unittest.TestCase):
    def test_independent_depth_scaling_leaves_both_normalizations_unchanged(self):
        pb = bulk_fixture()
        base, _ = normalizations(pb.counts, 100)
        scaled, _ = normalizations(pb.counts * np.array([2, 3, 7, 11, 5]), 100)
        for key in base:
            np.testing.assert_allclose(base[key], scaled[key], rtol=1e-13, atol=1e-13)

    def test_no_positive_genes_preserves_cpm_and_declares_median_ratio_failure(self):
        values, audit = normalizations(np.eye(3), 1)
        self.assertEqual(set(values), {'log2_cpm'})
        self.assertEqual(audit['median_ratio_status'], 'insufficient_all_positive_genes')
        self.assertIsNone(audit['median_ratio_size_factors'])

    def test_zero_panel_genes_are_averaged_not_dropped(self):
        values = np.array([[0, 0], [0, 0], [9, 3]], dtype=float)
        row = summarize_method(values, PANEL, ['T', 'C'], ['T'], ['C'], [])
        self.assertEqual(row['animal_scores'], {'T': 3, 'C': 1})
        self.assertEqual(row['mean_difference'], 2)

    def test_source_coverage_does_not_shrink_after_orthology_exclusion(self):
        orthology = {'panels': {'panel': [f'H{i}' for i in range(8)]}, 'transgene_mouse_symbols': [],
                     'mapping': {f'H{i}': {'status': 'mapped' if i < 7 else 'excluded',
                                          'mouse_symbol': f'M{i}' if i < 7 else None} for i in range(8)}}
        result = panel_coverage(orthology, [f'M{i}' for i in range(6)], THRESHOLDS)['panel']
        self.assertEqual(result['source_coverage'], .75)
        self.assertGreater(result['eligible_coverage'], .8)
        self.assertIn('insufficient_original_source_panel_coverage', result['failures'])

    def test_ambiguous_hgnc_assertions_fail(self):
        row = {'human_symbol': 'H', 'support': 'HGNC', 'mouse_ensembl_gene': 'ENSMUSG1', 'mgi_id': 'MGI:1', 'mouse_symbol': 'M'}
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            mapping_from_rows([row, dict(row, mouse_symbol='M2')], ['H'])

    def test_non_hgnc_candidate_cannot_substitute_for_missing_ortholog(self):
        row = {'human_symbol': 'CXCL8', 'support': 'Treefam,OrthoDB', 'mouse_symbol': 'Cxcl15'}
        result = mapping_from_rows([row], ['CXCL8'])['CXCL8']
        self.assertEqual(result['status'], 'no_HGNC_supported_mouse_ortholog')
        self.assertIsNone(result['mouse_symbol'])

    def test_fixed_transgene_exclusion_and_named_symbol_exceptions(self):
        frozen = json.loads((Path(__file__).parent / 'orthology.json').read_text())
        endogenous = frozen['panels']['reprogramming_without_OSKM_overlap']
        self.assertNotIn('POU5F1', endogenous)
        self.assertNotIn('SOX2', endogenous)
        self.assertEqual(len(endogenous), 7)
        self.assertEqual(frozen['mapping']['CD24']['mouse_symbol'], 'Cd24a')
        self.assertEqual(frozen['mapping']['TP53']['mouse_symbol'], 'Trp53')


class ContrastTests(unittest.TestCase):
    def test_equal_weighted_animal_mean_matches_equal_weighted_lane_difference(self):
        result = evaluation()
        for row in result['methods'].values():
            expected = np.mean([p['difference'] for p in row['within_lane_differences']])
            self.assertAlmostEqual(row['mean_difference'], expected)
        self.assertEqual(result['independent_animal_counts'], {'treated': 2, 'control': 2})

    def test_every_animal_and_lane_omission_retained(self):
        result = evaluation()
        self.assertEqual(len(result['single_animal_omissions']), 4)
        self.assertEqual(len(result['single_lane_omissions']), 2)
        omitted_t = next(r for r in result['single_animal_omissions'] if r['omitted_animal'] == 'T1')
        self.assertEqual(len(omitted_t['remaining_treated']), 1)
        for row in result['single_lane_omissions']:
            self.assertEqual(len(row['remaining_treated']), 1)
            self.assertEqual(len(row['remaining_controls']), 1)

    def test_cell_count_expansion_cannot_increase_animal_sample_size(self):
        pb = bulk_fixture()
        initial = evaluation(pb)
        for q in pb.qc:
            q['cells'] *= 100
        expanded = evaluation(pb)
        self.assertEqual(initial['methods'], expanded['methods'])
        self.assertEqual(expanded['independent_animal_counts'], {'treated': 2, 'control': 2})

    def test_animal_cannot_appear_in_both_groups(self):
        with self.assertRaisesRegex(ValueError, 'both contrast groups'):
            evaluation(controls=['T1', 'C1'])

    def test_opposite_lane_direction_cannot_pass_stability(self):
        primary = evaluation()
        secondary = evaluation(controls=['C1', 'C2', 'C3'])
        for row in primary['methods'].values():
            row['within_lane_differences'][0]['difference'] = -1
        result = stability_descriptor(primary, secondary, .25)
        self.assertEqual(result['status'], 'unstable_or_incomplete')
        self.assertTrue(any('lane_direction' in s for s in result['failures']))

    def test_normalization_sign_reversal_cannot_pass_stability(self):
        primary = evaluation()
        primary['methods']['log2_median_ratio_cpm_equivalent']['mean_difference'] = -1
        result = stability_descriptor(primary, evaluation(), .25)
        self.assertTrue(any('normalization_direction' in s for s in result['failures']))

    def test_gene_omission_reversal_cannot_pass_stability(self):
        primary = evaluation()
        primary['methods']['log2_cpm']['single_gene_omission_differences']['G0'] = -1
        result = stability_descriptor(primary, evaluation(), .25)
        self.assertTrue(any('gene_omission_direction' in s for s in result['failures']))

    def test_missing_secondary_is_incomplete_not_pass(self):
        primary = evaluation()
        secondary = copy.deepcopy(primary)
        secondary['status'] = 'unavailable'
        result = stability_descriptor(primary, secondary, .25)
        self.assertIn('all_controls_sensitivity_unavailable', result['failures'])

    def test_unapproved_receipt_blocks_before_git_or_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            path.write_text('{"expression_execution_authorized": false}')
            with self.assertRaisesRegex(ValueError, 'not authorized'):
                require_freeze(path, path, path)


class Cohort1AndReplayTests(unittest.TestCase):
    def fixture_metadata(self):
        _, _, _, meta, admission = raw_fixture()
        meta = meta.rename(columns={'LMO_classification.global': 'LMO2_classification.global'})
        meta['orig.ident'] = 'SeuratProject'
        for row in admission['animals']:
            row.update(orig_ident='SeuratProject', sex='male', lane='single_library', geo_library='GSMsynthetic')
        return meta, admission

    def test_cohort1_adapter_keeps_original_fields_and_explicit_source_derived_labels(self):
        meta, admission = self.fixture_metadata()
        result = attach_cohort1_admission(meta, admission)
        self.assertEqual(set(result['orig.ident']), {'SeuratProject'})
        self.assertEqual(set(result['lane']), {'single_library'})
        self.assertEqual(set(result['animal_id']), {'T1', 'C1'})

    def test_cohort1_changed_treatment_is_rejected(self):
        meta, admission = self.fixture_metadata()
        meta.loc['c1', 'Treatment'] = 'untr'
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            attach_cohort1_admission(meta, admission)

    def test_cohort1_changed_cell_annotation_is_rejected(self):
        meta, admission = self.fixture_metadata()
        meta.loc['c1', 'Celltype'] = 'unseen'
        with self.assertRaisesRegex(ValueError, 'annotations changed'):
            attach_cohort1_admission(meta, admission)

    def test_cohort1_single_library_does_not_invent_lane_pairs(self):
        result = evaluate_contrast(bulk_fixture(), 'A', PANEL, ['T1', 'T2'], ['C1', 'C2'], [],
                                   THRESHOLDS, 20, 500, 'cohort1_single_library_comparator', 'primary_support')
        self.assertEqual(result['single_lane_omissions'], [])
        self.assertTrue(all(row['within_lane_differences'] == [] for row in result['methods'].values()))
        self.assertTrue(all(len(row['all_treated_control_differences']) == 4 for row in result['methods'].values()))

    def test_cross_cohort_mean_agreement_is_separate_from_pair_consistency(self):
        one = evaluation()
        two = evaluation()
        for row in one['methods'].values():
            row['all_treated_control_differences'][0]['difference'] = -10
        a = {'contrasts': [{'panel_name': 'panel', 'comparison': one, 'direction_details': direction_details(one)}]}
        b = {'contrasts': [{'panel_name': 'panel', 'primary': two}]}
        row = cross_cohort_comparison(a, b, .25)['comparisons'][0]
        self.assertTrue(row['same_direction_and_floor_both_normalizations'])
        self.assertFalse(row['cohort1_direction_details']['log2_cpm']['all_pairwise_differences_share_mean_sign'])

    def test_cross_cohort_unavailable_stratum_is_retained(self):
        one = evaluation()
        one['status'] = 'unavailable'
        one['support_failures'] = {'T1': ['cells_below_20']}
        one['methods'] = {}
        a = {'contrasts': [{'panel_name': 'panel', 'comparison': one, 'direction_details': {}}]}
        b = {'contrasts': [{'panel_name': 'panel', 'primary': evaluation()}]}
        row = cross_cohort_comparison(a, b, .25)['comparisons'][0]
        self.assertEqual(row['status'], 'unavailable')
        self.assertEqual(row['cohort1_support_failures'], {'T1': ['cells_below_20']})
        self.assertEqual(row['methods'], {})

    def test_hash_only_replay_accepts_exact_archived_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract, orthology, receipt = root / 'contract', root / 'orthology', root / 'receipt'
            contract.write_text('frozen synthetic contract')
            orthology.write_text('frozen synthetic orthology')
            record = {'expression_execution_authorized': True, 'contract_sha256': sha(contract),
                      'orthology_sha256': sha(orthology), 'commit': 'historical-unavailable-in-test'}
            save_json(receipt, record)
            self.assertEqual(require_freeze(receipt, contract, orthology, True), record)

    def test_hash_only_replay_rejects_modified_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract, orthology, receipt = root / 'contract', root / 'orthology', root / 'receipt'
            contract.write_text('frozen synthetic contract')
            orthology.write_text('frozen synthetic orthology')
            save_json(receipt, {'expression_execution_authorized': True, 'contract_sha256': sha(contract),
                               'orthology_sha256': sha(orthology), 'commit': 'synthetic'})
            contract.write_text('changed after freeze')
            with self.assertRaisesRegex(ValueError, 'has changed'):
                require_freeze(receipt, contract, orthology, True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
