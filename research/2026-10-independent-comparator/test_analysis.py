#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1", "rdata==1.1.0"]
# ///
"""Adversarial identity, normalization and false-alarm checks on toy fixtures."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import analyze as a
import fetch_inputs as f
import inspect_neural as n


def samples():
    out = []
    for construct in ['OSK', 'O4YRSK']:
        for day, condition in [('0', 'no dox'), ('4', 'dox')]:
            for rep in ['1', '2']:
                out.append({'accession': 'GSM' + str(len(out)), 'title': [f'{construct}, {condition}, 4 days, rep{rep}'],
                            'description': [f'Column name in raw_counts_matrix.csv: {construct}_{day}D_{rep}'],
                            'organism_ch1': ['Homo sapiens'],
                            'characteristics_ch1': ['cell line: GM00731', f'treatment: {construct}, {condition}, 4 days', 'batch: 1']})
    return out


COLS = [f'{c}_D{d}_{r}' for c in ['OSK', 'O4YRSK'] for d in ['0', '4'] for r in ['1', '2']]


class HumanIdentity(unittest.TestCase):
    def test_shuffled_order_preserves_join(self):
        self.assertEqual(a.human_join(samples(), COLS), a.human_join(samples()[::-1], COLS[3:] + COLS[:3]))

    def test_ambiguous_missing_and_unknown_keys_fail(self):
        for mutation in ['duplicate', 'missing', 'unsupported']:
            with self.subTest(mutation=mutation):
                rows = samples()
                if mutation == 'duplicate': rows[1]['description'] = rows[0]['description']
                if mutation == 'missing': rows[0]['description'] = []
                if mutation == 'unsupported': rows[0]['description'] = ['Column name in raw_counts_matrix.csv: OSK_99D_1']
                with self.assertRaises(ValueError): a.human_join(rows, COLS)

    def test_title_treatment_donor_species_corruption_fails(self):
        for field, value in [('title', ['OSK, dox, 4 days, rep1']),
                             ('organism_ch1', ['Mus musculus']),
                             ('characteristics_ch1', ['cell line: other', 'treatment: OSK, no dox, 4 days']),
                             ('characteristics_ch1', ['cell line: GM00731', 'treatment: OSK, dox, 4 days'])]:
            with self.subTest(field=field, value=value):
                rows = samples(); rows[0][field] = value
                with self.assertRaises(ValueError): a.human_join(rows, COLS)

    def test_duplicate_and_extra_count_columns_fail(self):
        for cols in [COLS[:-1] + [COLS[0]], COLS + ['extra']]:
            with self.assertRaises(ValueError): a.human_join(samples(), cols)

    def test_invalid_counts_fail(self):
        for value in [-1, np.nan, np.inf]:
            x = pd.DataFrame([[1., 3.], [2., 4.]])
            x.iloc[0, 0] = value
            with self.assertRaises(ValueError): a.validate_counts(x)
        for x in [pd.DataFrame([[1, 0], [2, 0]]), pd.DataFrame([[1, 3], [2, 4]], index=['dup', 'dup'])]:
            with self.assertRaises(ValueError): a.validate_counts(x)

    def test_CPM_invariant_to_library_depth(self):
        x = pd.DataFrame([[1., 2.], [4., 8.], [8., 16.]])
        primary = a.normalizations(x)[0]['log2_cpm']
        np.testing.assert_allclose(primary[0], primary[1], rtol=0, atol=1e-12)

    def test_panel_mean_and_four_pairs_hand_calculated(self):
        x = pd.DataFrame({'c1': [1., 3.], 'c2': [3., 5.], 't1': [5., 7.], 't2': [7., 9.]}, index=['a', 'b'])
        result = a.compare_panel(x, ['t1', 't2'], ['c1', 'c2'])
        self.assertEqual(result['mean_difference'], 4)
        self.assertEqual(result['four_library_differences'], [4, 2, 6, 4])
        self.assertEqual(set(result['single_gene_omission_differences'].values()), {4})

    def test_ambiguous_HGNC_mapping_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'hgnc.tsv'
            p.write_text('symbol\tstatus\thgnc_id\tensembl_gene_id\nA\tApproved\tHGNC:1\tENSG1\nA\tApproved\tHGNC:2\tENSG2\n')
            with self.assertRaises(ValueError): a.approved_gene_map(p, ['A'])


class NeuralIdentity(unittest.TestCase):
    def test_metadata_count_order_and_animal_conflicts_fail(self):
        animal_id = 'A-L0002-06102018-lane1-2Dox0-TGTGATGG'
        frame = pd.DataFrame({'hash.ID': [animal_id, animal_id], 'orig.ident': ['Lane1', 'Lane1'],
                              'age_genotype': ['old_OSKM', 'old_OSKM'], 'age': ['old', 'old'],
                              'genotype': ['OSKM', 'OSKM'], 'Treatment': ['2Dox0', '2Dox0'],
                              'Celltype': ['Microglia', 'Microglia'], 'LMO_classification.global': ['Singlet', 'Singlet']}, index=['c1', 'c2'])
        args = ({animal_id: 'old_OSKM'}, {animal_id: '2Dox0'})
        self.assertTrue(n.validate_metadata(frame, ['c1', 'c2'], *args))
        with self.assertRaises(ValueError): n.validate_metadata(frame, ['c2', 'c1'], *args)
        frame.loc['c1', 'Treatment'] = 'untr'
        with self.assertRaises(ValueError): n.validate_metadata(frame, ['c1', 'c2'], *args)

    def test_author_map_ambiguity_fails(self):
        text = 'age_genotype <- plyr::mapvalues(x = svz_sing$hash.ID, from = c("A","A"), to = c("old_OSKM","young_OSKM"))'
        with self.assertRaises(ValueError): n.code_mapping(text, 'age_genotype')


class SyntheticBoundaries(unittest.TestCase):
    def test_zero_prevalence_perfect_specificity_zero_flags(self):
        self.assertEqual(a.confirmation([a.no_flag_probability(400, 0, .05, .8, 0)] * 3),
                         {'any_donor_flagged': 0., 'two_or_more_donors_flagged': 0.})

    def test_all_null_independent_error_matches_closed_form(self):
        q = a.no_flag_probability(200, 0, .05, .8, .001)
        result = a.confirmation([q] * 6)
        self.assertAlmostEqual(result['any_donor_flagged'], 1 - .999**1200, places=12)
        self.assertAlmostEqual(result['two_or_more_donors_flagged'], 1 - q**6 - 6 * (1-q) * q**5, places=12)

    def test_confirmation_requires_distinct_donors(self):
        for q in [[0], [0, 1], [1, 1, 1]]:
            self.assertEqual(a.confirmation(q)['two_or_more_donors_flagged'], 0)
        self.assertEqual(a.confirmation([0, 0])['two_or_more_donors_flagged'], 1)

    def test_probability_ordering_and_extremes(self):
        for allocation in [[400]*3, [1000,100,100]]:
            result = a.confirmation([a.no_flag_probability(k, .01, .05, .8, 0) for k in allocation])
            self.assertLessEqual(result['two_or_more_donors_flagged'], result['any_donor_flagged'])
        self.assertEqual(a.no_flag_probability(10, 1, .05, 1, 0), 0)
        self.assertEqual(a.no_flag_probability(10, .01, .05, 0, 0), 1)


class FrozenSource(unittest.TestCase):
    def test_wrong_hash_does_not_overwrite_existing_cache(self):
        class Response:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b'changed source'
        with tempfile.TemporaryDirectory() as tmp, patch.object(f, 'urlopen', return_value=Response()), patch.object(f.shutil, 'disk_usage') as disk:
            disk.return_value.free = 20_000_000_000
            target = Path(tmp) / 'source.txt'; target.write_bytes(b'original')
            result = f.fetch_one({'id': 'source.txt', 'url': 'https://example.invalid/source', 'expected_sha256': '0'*64}, Path(tmp))
            self.assertEqual(result['status'], 'access_failure')
            self.assertEqual(target.read_bytes(), b'original')


if __name__ == '__main__':
    unittest.main(verbosity=2)
