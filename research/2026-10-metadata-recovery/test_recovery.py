#!/usr/bin/env python3
"""Scientific intake failures: never manufacture identity or valid coefficients."""
import unittest
from recover_metadata import extract_parameters, require_exact_mapping


class RecoveryTests(unittest.TestCase):
    def row(self, library='L1', barcode='C1', treatment='control'):
        return dict(library_id=library, cell_barcode=barcode, perturbation=treatment, donor_or_pool_id='pool-A')

    def test_same_barcode_in_different_libraries_is_not_a_collision(self):
        result = require_exact_mapping([('L1', 'C1'), ('L2', 'C1')], [self.row(), self.row('L2')])
        self.assertEqual(result['keys'], 2)
        self.assertFalse(result['biological_independence_verified'])

    def test_age_rows_cannot_be_used_as_identity_mapping(self):
        with self.assertRaises(ValueError):
            require_exact_mapping([('L1', 'C1')], [{'age': 55}])

    def test_conflicting_assignments_rejected(self):
        with self.assertRaises(ValueError):
            require_exact_mapping([('L1', 'C1')], [self.row(), self.row(treatment='target')])

    def test_partial_coverage_rejected(self):
        with self.assertRaises(ValueError):
            require_exact_mapping([('L1', 'C1'), ('L1', 'C2')], [self.row()])

    def test_unknown_key_rejected(self):
        with self.assertRaises(ValueError):
            require_exact_mapping([('L1', 'C1')], [self.row(barcode='C2')])

    def coefficients(self):
        return [['Ensembl ID', 'Gene symbol', 'Coefficient'],
                ['Intercept', '-', '1', '1'], ['LibType.Total', '-', '0', '0'],
                ['LibType.mRNA', '-', '0', '0'], ['ENSG00000000001', 'X', '.5', '.1']]

    def test_duplicate_model_terms_rejected(self):
        rows = self.coefficients()
        with self.assertRaises(ValueError):
            extract_parameters(rows + [rows[-1]])

    def test_nonfinite_coefficient_rejected(self):
        rows = self.coefficients()
        rows[-1][2] = 'NaN'
        with self.assertRaises(ValueError):
            extract_parameters(rows)

    def test_missing_intercept_rejected(self):
        rows = self.coefficients()
        with self.assertRaises(ValueError):
            extract_parameters([rows[0]] + rows[2:])


if __name__ == '__main__':
    unittest.main()
