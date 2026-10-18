#!/usr/bin/env python3
"""Adversarial tests for metadata joins; no expression outcomes are accessed."""
import unittest
from build_recovery import join_cohort1_barcodes


class BarcodeAdmissionTests(unittest.TestCase):
    a = 'ACGTACGTACGTACGT'
    b = 'TGCATGCATGCATGCA'

    def test_uniform_suffix_preserves_full_join(self):
        result = join_cohort1_barcodes([self.a + '-1', self.b + '-1'], [self.a], 'GSM7022367')
        self.assertEqual(result['included_object_barcodes_match_raw'], 1)
        self.assertEqual(result['additional_raw_barcodes_without_recovered_animal_assignment'], 1)

    def test_rejects_other_library(self):
        with self.assertRaisesRegex(ValueError, 'only for'):
            join_cohort1_barcodes([self.a + '-1'], [self.a], 'GSM7022368')

    def test_rejects_mixed_suffix_and_potential_collision(self):
        for raw in ([self.a + '-1', self.b + '-2'], [self.a + '-1', self.a + '-2']):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, 'uniform -1'):
                join_cohort1_barcodes(raw, [self.a], 'GSM7022367')

    def test_rejects_invalid_raw_identifiers(self):
        for raw in (self.a, self.a + '-1-extra', 'lane1_' + self.a + '-1',
                    'N' + self.a[1:] + '-1', self.a[:-1] + '-1', self.a.lower() + '-1'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                join_cohort1_barcodes([raw], [self.a], 'GSM7022367')

    def test_rejects_duplicate_raw(self):
        with self.assertRaisesRegex(ValueError, 'unique'):
            join_cohort1_barcodes([self.a + '-1'] * 2, [self.a], 'GSM7022367')

    def test_rejects_duplicate_object(self):
        with self.assertRaisesRegex(ValueError, 'unique'):
            join_cohort1_barcodes([self.a + '-1'], [self.a] * 2, 'GSM7022367')

    def test_rejects_unmatched_object(self):
        with self.assertRaisesRegex(ValueError, 'no raw barcode match'):
            join_cohort1_barcodes([self.a + '-1'], [self.b], 'GSM7022367')

    def test_rejects_object_lane_prefix_or_suffix(self):
        for obj in (self.a + '-1', 'lane1_' + self.a, self.a[:-1], 'N' + self.a[1:]):
            with self.subTest(obj=obj), self.assertRaisesRegex(ValueError, 'no suffix'):
                join_cohort1_barcodes([self.a + '-1'], [obj], 'GSM7022367')

    def test_rejects_empty_collections(self):
        for raw, obj in (([], [self.a]), ([self.a + '-1'], [])):
            with self.subTest(raw=raw, obj=obj), self.assertRaisesRegex(ValueError, 'nonempty'):
                join_cohort1_barcodes(raw, obj, 'GSM7022367')


if __name__ == '__main__':
    unittest.main()
