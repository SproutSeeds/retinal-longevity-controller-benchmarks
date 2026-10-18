#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Synthetic arithmetic tests, never evidence of a biological effect."""
import unittest
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix
from decompose import symmetric, run
from neural_analysis import RawData


class DecompositionTests(unittest.TestCase):
    def test_empty_support_preserves_every_scale_and_panel_failure(self):
        root = Path(__file__).resolve().parent.parent
        contract = json.loads((root / 'analysis/contract.json').read_text())
        orthology = json.loads((root / 'analysis/orthology.json').read_text())
        animals = ['L0002', 'L0003', 'L0004', 'L0011']
        metadata = pd.DataFrame({'animal_id': animals, 'celltype': ['Microglia'] * 4,
            'lane': ['Lane1', 'Lane1', 'Lane2', 'Lane2'],
            'treatment': ['2Dox0', 'untr', '2Dox0', 'untr'],
            'age_group': ['old'] * 4, 'genotype': ['OSKM'] * 4})
        raw = RawData(csc_matrix(np.ones((1, 4), dtype=np.int64)), ['Unmapped'], metadata, 'synthetic')
        result = run(raw, contract, orthology)
        self.assertEqual(len(result['results']), 16)
        self.assertEqual({row['scale'] for row in result['results']}, {10000, 1000000})
        self.assertTrue(all(row['status'] == 'unavailable' and row['reason'] == 'empty_common_support'
                            for row in result['results']))

    def test_pure_composition(self):
        r = symmetric([.8, .2], [.2, .8], [0, 10], [0, 10])
        self.assertAlmostEqual(r['total'], -6)
        self.assertAlmostEqual(r['composition'], -6)
        self.assertEqual(r['within_type'], 0)

    def test_pure_within_type(self):
        r = symmetric([.5, .5], [.5, .5], [4, 8], [2, 4])
        self.assertEqual(r['total'], 3)
        self.assertEqual(r['composition'], 0)
        self.assertEqual(r['within_type'], 3)

    def test_cancelling_components_have_zero_total(self):
        r = symmetric([.75, .25], [.25, .75], [2, 4], [1, 3])
        self.assertEqual(r['total'], 0)
        self.assertEqual(r['composition'], -1)
        self.assertEqual(r['within_type'], 1)
        self.assertTrue(r['opposed_components'])

    def test_swapping_animals_reverses_all_components(self):
        a = symmetric([.4, .6], [.1, .9], [2, 6], [4, 7])
        b = symmetric([.1, .9], [.4, .6], [4, 7], [2, 6])
        for k in ['total', 'composition', 'within_type']:
            self.assertAlmostEqual(a[k], -b[k])

    def test_type_order_invariance(self):
        x = [[.4, .6], [.1, .9], [2, 6], [4, 7]]
        a, b = symmetric(*x), symmetric(*(v[::-1] for v in x))
        for k in ['total', 'composition', 'within_type']:
            self.assertAlmostEqual(a[k], b[k])

    def test_unmatched_support_fails(self):
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            symmetric([1], [.5, .5], [2], [3])

    def test_invalid_fractions_fail(self):
        for p in [[.4, .4], [-.1, 1.1]]:
            with self.assertRaisesRegex(ValueError, 'sum to one'):
                symmetric(p, [.5, .5], [2, 3], [3, 4])

    def test_missing_and_nonfinite_fail(self):
        for x in [[], [float('nan')], [float('inf')]]:
            with self.assertRaisesRegex(ValueError, 'Finite nonempty'):
                symmetric(x, [1], [2], [3])

    def test_seeded_identity(self):
        rng = np.random.default_rng(181026)
        for n in [1, 2, 5, 10]:
            for _ in range(25):
                p, q = rng.dirichlet(np.ones(n), size=2)
                a, b = rng.normal(0, 10, size=(2, n))
                r = symmetric(p, q, a, b)
                self.assertAlmostEqual(r['total'], r['composition'] + r['within_type'])


if __name__ == '__main__':
    unittest.main()
