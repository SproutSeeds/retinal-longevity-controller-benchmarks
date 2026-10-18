"""Adversarial tests use synthetic data; none are added to observed results."""
import copy
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix

import extension as e
from neural_analysis import RawData

PAIRS = [{'lane': 'one', 'treated': 'T1', 'control': 'C1'},
         {'lane': 'two', 'treated': 'T2', 'control': 'C2'}]
TYPES = ['Oligodendrocyte', 'Microglia']


def fixture(cells_per_type=20, genes=600):
    rows = [{'animal_id': animal, 'celltype': ct}
            for animal in ('T1', 'C1', 'T2', 'C2') for ct in TYPES for _ in range(cells_per_type)]
    metadata = pd.DataFrame(rows, index=[f'cell_{i:04}' for i in range(len(rows))])
    return RawData(csc_matrix(np.full((genes, len(rows)), 2, dtype=np.int64)),
                   [f'g{i}' for i in range(genes)], metadata, 'synthetic')


class AlgebraTests(unittest.TestCase):
    def test_closed_form_and_reference_sign_reversal(self):
        r = e.decompositions([.8, .2], [.2, .8], [2., 0.], [0., 2.])
        self.assertAlmostEqual(r['control_reference']['composition'], -1.2)
        self.assertAlmostEqual(r['treated_reference']['composition'], 1.2)
        self.assertAlmostEqual(r['symmetric']['composition'], 0)
        for record in r.values():
            self.assertAlmostEqual(record['total'], 0)
            self.assertAlmostEqual(record['composition'] + record['within_type'], 0)

    def test_identical_fractions_leave_only_within_component(self):
        for r in e.decompositions([.3, .7], [.3, .7], [4, 2], [2, 1]).values():
            self.assertEqual(r['composition'], 0)
            self.assertAlmostEqual(r['within_type'], 1.3)

    def test_identical_type_means_leave_only_composition(self):
        for r in e.decompositions([.3, .7], [.8, .2], [4, 2], [4, 2]).values():
            self.assertEqual(r['within_type'], 0)
            self.assertAlmostEqual(r['composition'], -1)

    def test_single_type(self):
        for r in e.decompositions([1], [1], [2], [3]).values():
            self.assertEqual(r['total'], -1)
            self.assertEqual(r['composition'], 0)

    def test_random_algebra_and_symmetric_average(self):
        rng = np.random.default_rng(932)
        for _ in range(100):
            p, q = rng.dirichlet(np.ones(4)), rng.dirichlet(np.ones(4))
            x, y = rng.normal(size=4), rng.normal(size=4)
            r = e.decompositions(p, q, x, y)
            for field in e.FIELDS + ('composition_by_type', 'within_by_type'):
                np.testing.assert_allclose(r['symmetric'][field],
                                           .5 * (np.asarray(r['control_reference'][field]) + np.asarray(r['treated_reference'][field])), rtol=0, atol=e.TOL)

    def test_invalid_vectors(self):
        invalid = [([], [], [], []), ([.5], [1], [2], [3]),
                   ([-1, 2], [0, 1], [0, 1], [0, 1]),
                   ([1], [1], [np.nan], [1]), ([1], [1], [np.inf], [1]),
                   ([[1]], [1], [1], [1]), ([1], [1], [1, 2], [1])]
        for args in invalid:
            with self.subTest(args=args), self.assertRaises(ValueError):
                e.decompositions(*args)

    def test_unequal_lane_counts_do_not_weight_the_average(self):
        lanes = [{'conventions': e.decompositions([1], [1], [v], [0])} for v in (2, 8)]
        self.assertEqual(e.lane_average(lanes)['symmetric']['total'], 5)

    def test_no_percentage_attribution(self):
        result = e.decompositions([.8, .2], [.2, .8], [2, 0], [0, 2])
        self.assertNotIn('percent', str(result))
        self.assertTrue(result['control_reference']['opposed_components'])


class PanelTests(unittest.TestCase):
    def setUp(self):
        self.raw = fixture(cells_per_type=2, genes=3)
        self.values = np.arange(48, dtype=float).reshape(3, 16) / 7
        self.values[2] = 0

    def test_every_gene_and_zero_retained_with_fixed_denominator(self):
        r = e.summarize(self.values, self.raw.genes, self.raw.metadata, TYPES, PAIRS, per_gene=True)
        self.assertEqual(len(r['gene_contributions']), 3)
        self.assertEqual([g['gene'] for g in r['gene_contributions']], self.raw.genes)
        self.assertEqual(r['gene_contributions'][2]['equal_lane_mean']['symmetric']['total'], 0)
        self.assertEqual(r['gene_contributions'][2]['panel_weight'], 1 / 3)
        for convention in e.CONVENTIONS:
            for field in e.FIELDS:
                self.assertAlmostEqual(sum(g['equal_lane_mean'][convention][field] for g in r['gene_contributions']), r['equal_lane_mean'][convention][field])

    def test_direct_cell_average_and_gene_type_means(self):
        r = e.summarize(self.values, self.raw.genes, self.raw.metadata, TYPES, PAIRS, per_gene=True)
        scores = self.values.mean(axis=0)
        for lane in r['lane_contrasts']:
            difference = scores[(self.raw.metadata.animal_id == lane['treated']).to_numpy()].mean() - scores[(self.raw.metadata.animal_id == lane['control']).to_numpy()].mean()
            self.assertAlmostEqual(lane['conventions']['symmetric']['total'], difference)

    def test_cell_order_invariance(self):
        a = e.summarize(self.values, self.raw.genes, self.raw.metadata, TYPES, PAIRS)
        order = np.arange(len(self.raw.metadata))[::-1]
        b = e.summarize(self.values[:, order], self.raw.genes, self.raw.metadata.iloc[order], TYPES, PAIRS)
        for convention in e.CONVENTIONS:
            for field in e.FIELDS:
                self.assertAlmostEqual(a['equal_lane_mean'][convention][field], b['equal_lane_mean'][convention][field])

    def test_absent_type_does_not_become_zero(self):
        selected = ~((self.raw.metadata.animal_id == 'T1') & (self.raw.metadata.celltype == TYPES[0])).to_numpy()
        with self.assertRaisesRegex(ValueError, 'Absent types'):
            e.summarize(self.values, self.raw.genes, self.raw.metadata, TYPES, PAIRS, selected=selected)

    def test_duplicate_genes_or_animals_and_bad_mask_rejected(self):
        for genes, pairs, selected in [(['g0'] * 3, PAIRS, None),
                                       (self.raw.genes, [PAIRS[0], PAIRS[0]], None),
                                       (self.raw.genes, PAIRS, np.ones(16, dtype=int))]:
            with self.assertRaises(ValueError):
                e.summarize(self.values, genes, self.raw.metadata, TYPES, pairs, selected=selected)


class DepthTests(unittest.TestCase):
    def test_threshold_and_denominators(self):
        raw = fixture()
        support, selected = e.depth_support(raw, TYPES, PAIRS)
        self.assertEqual(support['status'], 'available')
        self.assertEqual(int(selected.sum()), 160)
        for row in support['rows']:
            self.assertEqual(row['retained_cells'], 20)
            self.assertEqual(row['unthinned_retained_detected_genes'], 600)
            self.assertEqual(row['retained_fraction_all_recovered'], .5)

    def test_one_sparse_stratum_invalidates_whole_fixed_support(self):
        raw = fixture()
        x = raw.counts.toarray()
        x[:, 0] = 1
        raw.counts = csc_matrix(x)
        support, _ = e.depth_support(raw, TYPES, PAIRS)
        self.assertEqual(support['status'], 'unavailable')
        self.assertEqual(support['fixed_common_types'], TYPES)
        self.assertEqual(support['failures'][0]['failures'], ['cells_below_20'])
        panels = {'p': {'present_mouse_genes': ['g0']}}
        parent = {'support': [{'cell_floor': 20, 'common_named_types': TYPES}]}
        r = e.depth_diagnostic(raw, {'cohort2_primary': {'pairs': PAIRS}}, panels, parent)
        self.assertIsNone(r['marginal_inputs'])
        self.assertEqual(len(r['thinned']), 3)
        self.assertTrue(all(row['status'] == 'unavailable' for row in r['thinned']))

    def test_gene_floor_measured_before_sampling(self):
        raw = fixture()
        x = raw.counts.toarray()
        x[499:, :20] = 0
        x[0, :20] += 10
        raw.counts = csc_matrix(x)
        support, _ = e.depth_support(raw, TYPES, PAIRS)
        self.assertEqual(support['rows'][0]['retained_cells'], 20)
        self.assertEqual(support['rows'][0]['support_failures'], ['detected_genes_below_500'])

    def test_all_recovered_denominator_includes_out_of_support(self):
        raw = fixture()
        raw.metadata.loc[raw.metadata.index[20:25], 'celltype'] = 'unresolved'
        support, _ = e.depth_support(raw, TYPES, PAIRS, min_cells=15)
        self.assertEqual(support['denominators']['T1']['all_recovered_cells'], 40)
        self.assertEqual(support['denominators']['T1']['retained_fraction_all_recovered'], 35 / 40)

    def test_empty_depth_summary(self):
        self.assertIsNone(e.depth_summary([]))

    def test_sorted_sampling_replay_and_bounds(self):
        ids = ['z', 'a', 'm']
        counts = np.array([[100, 0, 1100], [50, 950, 200], [0, 700, 300]])
        a = e.thin_marginals(ids, counts, 181026)
        b = e.thin_marginals(ids[::-1], counts[::-1], 181026)
        self.assertEqual(a[0], ['a', 'm', 'z'])
        np.testing.assert_array_equal(a[2], b[2])
        self.assertTrue((a[2] <= a[1]).all())
        self.assertTrue((a[2].sum(axis=1) == 1000).all())
        self.assertEqual(a[2][2, 1], 0)
        np.testing.assert_array_equal(a[2][1], a[1][1])

    def test_remainder_preserves_total_population(self):
        ids, counts, draws = e.thin_marginals(['a'], np.array([[500, 500, 19000]]), 181026)
        self.assertEqual(int(draws.sum()), 1000)
        self.assertGreater(int(draws[0, -1]), 850)
        self.assertLess(int(draws[0, :2].sum()), 150)

    def test_distinct_seeds_with_stochastic_population(self):
        counts = np.array([[300, 500, 1200]] * 10)
        a = e.thin_marginals([str(i) for i in range(10)], counts, 181026)[2]
        b = e.thin_marginals([str(i) for i in range(10)], counts, 181027)[2]
        self.assertFalse(np.array_equal(a, b))

    def test_invalid_sampling_rejected(self):
        for ids, counts in [(['a', 'a'], np.array([[500, 500], [500, 500]])),
                            (['a'], np.array([[100., 900.]])), (['a'], np.array([[-1, 1001]])),
                            (['a'], np.array([[100, 899]])), (['a'], np.array([[10, 10**9]])),
                            (['a'], np.array([[1000]]))]:
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                e.thin_marginals(ids, counts, 181026)


class GateTests(unittest.TestCase):
    def build_gate(self, root):
        here = root / 'decomposition'
        here.mkdir()
        (root / 'analysis').mkdir()
        for path in (here / 'posthoc-contract.json', here / 'contract.json', here / 'decompose.py',
                     root / 'analysis/neural_analysis.py'):
            path.write_text('fixture')
        parent = {'contract_sha256': e.sha(here / 'contract.json'), 'code_sha256': e.sha(here / 'decompose.py'),
                  'analysis_loader_sha256': e.sha(root / 'analysis/neural_analysis.py')}
        e.save_json(here / 'results.json', parent)
        receipt = {'expression_execution_authorized': True, 'commit': 'abc',
                   'contract_sha256': e.sha(here / 'posthoc-contract.json'), 'parent_result_sha256': e.sha(here / 'results.json')}
        e.save_json(here / 'EXTENSION_FREEZE.json', receipt)
        return here, receipt

    def test_strict_checks_five_commit_bindings_and_replay_checks_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            here, _ = self.build_gate(Path(directory))
            frozen = {'decomposition_contract_sha256': e.sha(here / 'contract.json')}
            with mock.patch.object(e, 'require_freeze', return_value=frozen), mock.patch.object(e, 'verify_committed_file') as verify:
                e.require_extension_freeze(False, here)
                self.assertEqual(verify.call_count, 5)
                verify.reset_mock()
                e.require_extension_freeze(True, here)
                verify.assert_not_called()
                (here / 'posthoc-contract.json').write_text('changed')
                with self.assertRaisesRegex(ValueError, 'Pinned extension input'):
                    e.require_extension_freeze(True, here)

    def test_unauthorized_or_changed_parent_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            here, receipt = self.build_gate(Path(directory))
            receipt['expression_execution_authorized'] = 'true'
            e.save_json(here / 'EXTENSION_FREEZE.json', receipt)
            with self.assertRaisesRegex(ValueError, 'not authorized'):
                e.require_extension_freeze(True, here)
            receipt['expression_execution_authorized'] = True
            e.save_json(here / 'EXTENSION_FREEZE.json', receipt)
            parent = json.loads((here / 'results.json').read_text())
            parent['code_sha256'] = 'wrong'
            e.save_json(here / 'results.json', parent)
            with self.assertRaisesRegex(ValueError, 'Pinned extension input'):
                e.require_extension_freeze(True, here)

    def test_scratch_guard_internal_and_space(self):
        with self.assertRaisesRegex(ValueError, 'internal /tmp'):
            e.scratch_guard(Path('/opt/rejected-extension-scratch'))
        with mock.patch.object(e.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=7)):
            with self.assertRaisesRegex(ValueError, 'free space'):
                e.scratch_guard(minimum_free=8)
        with mock.patch.object(e.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=8)):
            self.assertTrue(e.scratch_guard(minimum_free=8).is_relative_to(Path('/tmp').resolve()))


if __name__ == '__main__':
    unittest.main()
