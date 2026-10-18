#!/usr/bin/env python3
"""Synthetic-only tests: this module never reads observed H5 matrices."""
import json
from pathlib import Path
import tempfile
import unittest

import h5py
import numpy as np
from scipy.sparse import csc_matrix

import percell_audit as audit


def sample(gsm, donor, day, counts, totals=None, detected=None):
    counts = np.asarray(counts, dtype=np.int64)
    n = len(counts)
    totals = np.asarray(totals if totals is not None else [100] * n, dtype=np.int64)
    detected = np.asarray(detected if detected is not None else [600] * n, dtype=np.int64)
    markers = ["I", "E1", "E2", "P"]
    return audit.Sample(gsm, donor, day, np.array([f"cell{i}" for i in range(n)]), markers,
                        counts, totals, detected, np.zeros(n, dtype=np.int64),
                        {g: f"id_{g}" for g in markers}, n, "synthetic")


class PerCellAuditTests(unittest.TestCase):
    def test_freeze_blocks_missing_authority_or_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            contract, scout, freeze = [folder / name for name in ["contract.json", "scout.json", "freeze.json"]]
            contract.write_text("{}")
            scout.write_text("[]")
            with self.assertRaises(ValueError):
                audit.require_freeze(contract, scout, freeze)
            receipt = {"expression_execution_authorized": True, "commit": "a" * 40,
                       "contract_sha256": audit.sha(contract), "scout_sha256": audit.sha(scout)}
            freeze.write_text(json.dumps(receipt))
            self.assertEqual(audit.require_freeze(contract, scout, freeze), receipt)
            receipt["expression_execution_authorized"] = False
            freeze.write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):
                audit.require_freeze(contract, scout, freeze)
            receipt["expression_execution_authorized"] = True
            freeze.write_text(json.dumps(receipt))
            contract.write_text('{"altered":true}')
            with self.assertRaises(ValueError):
                audit.require_freeze(contract, scout, freeze)

    def test_hand_checked_joint_table_and_empty_denominator(self):
        tables = audit.joint_tables([False, False, True, True], [0, 2, 1, 3], [False, True, False, True])
        binary = [row for row in tables if row["table"] == "binary_2x2"]
        self.assertEqual([row["count"] for row in binary], [1, 1, 1, 1])
        self.assertEqual([row["fraction"] for row in binary], [.25] * 4)
        for family in {row["table"] for row in tables}:
            self.assertEqual(sum(row["count"] for row in tables if row["table"] == family), 4)
        empty = audit.joint_tables([], [], [])
        self.assertTrue(all(row["count"] == 0 and row["fraction"] is None for row in empty))

    def test_endogenous_count_uses_multiple_genes_and_threshold(self):
        values = np.array([[10, 0, 0], [1, 1, 0], [2, 2, 2]])
        self.assertEqual(audit.coexpression_counts(values, [0, 1, 2]).tolist(), [1, 2, 3])
        self.assertEqual(audit.coexpression_counts(values, [0, 1, 2], 2).tolist(), [1, 0, 3])
        with self.assertRaises(ValueError):
            audit.coexpression_counts(values, [0], 0)

    def test_quantile_ties_report_realized_fraction(self):
        one = sample("a0", "a", 0, [[0, 0, 0, 0]] * 4)
        thresholds = audit.donor_cutoffs([one], {"a0": np.zeros(4)}, {"a0": np.ones(4, dtype=bool)}, .1)
        self.assertEqual(thresholds["a"]["nominal_quantile"], .1)
        self.assertEqual(thresholds["a"]["D0_identity_low_fraction"], 1)
        self.assertEqual(thresholds["a"]["tie_count_at_threshold"], 4)

    def test_baselines_are_separate_for_each_donor(self):
        samples = [sample("a0", "a", 0, [[0, 0, 0, 0]] * 2), sample("b0", "b", 0, [[0, 0, 0, 0]] * 2)]
        thresholds = audit.donor_cutoffs(samples, {"a0": np.array([0, 1]), "b0": np.array([10, 20])},
                                        {s.gsm: np.ones(2, dtype=bool) for s in samples}, .1)
        self.assertAlmostEqual(thresholds["a"]["threshold"], .1)
        self.assertAlmostEqual(thresholds["b"]["threshold"], 11)
        with self.assertRaises(ValueError):
            audit.donor_cutoffs(samples, {"a0": np.array([0, 1]), "b0": np.array([10, 20])},
                                {"a0": np.ones(2, dtype=bool), "b0": np.zeros(2, dtype=bool)}, .1)

    def test_dropout_and_qc_variants_keep_their_denominators(self):
        samples = [sample("a0", "a", 0, [[1, 0, 0, 0], [2, 1, 1, 1]], detected=[100, 700]),
                   sample("a3", "a", 3, [[0, 1, 1, 0], [1, 2, 2, 0]], detected=[200, 800])]
        depth = audit.depth_cutoffs(samples)
        primary, _ = audit.analyze_variant(samples, {"id": "primary", "q": .1, "umi": 1}, ["E1", "E2"], ["I"], ["P"], depth)
        filtered, _ = audit.analyze_variant(samples, {"id": "qc", "q": .1, "umi": 1, "min_genes_exclusive": 500}, ["E1", "E2"], ["I"], ["P"], depth)
        self.assertEqual([row["n_retained"] for row in primary], [2, 2])
        self.assertEqual([row["n_retained"] for row in filtered], [1, 1])
        self.assertEqual(filtered[0]["baseline"]["D0_denominator"], 1)
        self.assertEqual(primary[0]["baseline"]["D0_denominator"], 2)

    def test_depth_bins_partition_even_with_tied_cutpoints(self):
        samples = [sample("a0", "a", 0, [[1, 1, 1, 0]] * 3, totals=[100, 100, 100]),
                   sample("a3", "a", 3, [[1, 1, 1, 0]] * 4, totals=[50, 100, 200, 500])]
        depth = audit.depth_cutoffs(samples)
        rows = []
        for i in range(4):
            current, _ = audit.analyze_variant(samples, {"id": f"depth{i}", "q": .1, "umi": 1, "depth_bin": i}, ["E1", "E2"], ["I"], ["P"], depth)
            rows.extend(current)
        for s in samples:
            self.assertEqual(sum(row["n_retained"] for row in rows if row["gsm"] == s.gsm), len(s.totals))
        self.assertTrue(any(row["n_retained"] == 0 for row in rows))
        self.assertTrue(all(row["baseline"]["D0_denominator"] == 3 for row in rows))

    def test_hypergeometric_conserves_total_bounds_and_replays(self):
        counts = np.array([[10, 20, 30], [2, 2, 2], [0, 0, 0]])
        totals = np.array([100, 10, 50])
        one, remainder = audit.thin_markers(counts, totals, 10, np.random.Generator(np.random.PCG64(42)))
        two, other_remainder = audit.thin_markers(counts, totals, 10, np.random.Generator(np.random.PCG64(42)))
        np.testing.assert_array_equal(one, two)
        np.testing.assert_array_equal(remainder, other_remainder)
        np.testing.assert_array_equal(one.sum(axis=1) + remainder, np.array([10, 10, 10]))
        np.testing.assert_array_equal(one[1], counts[1])
        self.assertTrue(np.all(one <= counts))
        np.testing.assert_array_equal(one[2], [0, 0, 0])

    def test_hypergeometric_rejects_double_counting_and_small_libraries(self):
        with self.assertRaises(ValueError):
            audit.thin_markers(np.array([[5, 6]]), np.array([10]), 5, np.random.default_rng(1))
        with self.assertRaises(ValueError):
            audit.thin_markers(np.array([[1, 1]]), np.array([10]), 20, np.random.default_rng(1))

    def test_thinning_recomputes_donor_baseline_and_retention(self):
        samples = [sample("a0", "a", 0, [[1, 1, 1, 0], [20, 20, 20, 0]], totals=[500, 2000]),
                   sample("a3", "a", 3, [[10, 10, 10, 0], [10, 10, 10, 0]], totals=[1000, 2000])]
        spec = {"id": "thin", "q": .1, "umi": 1, "thin": 1000, "seed": 181026}
        rows, _ = audit.analyze_variant(samples, spec, ["E1", "E2"], ["I"], ["P"], audit.depth_cutoffs(samples))
        self.assertEqual([row["n_retained"] for row in rows], [1, 2])
        self.assertEqual(rows[0]["baseline"]["D0_denominator"], 1)
        self.assertEqual(rows[0]["realized_D0_identity_low_fraction_in_this_variant"], 1)

    def test_gene_expression_only_h5_and_stable_cell_order(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.h5"
            dense = np.array([[4, 0, 0], [1, 2, 0], [1, 0, 0], [0, 1, 0], [2, 1, 0], [100, 100, 100]])
            matrix = csc_matrix(dense)
            with h5py.File(path, "w") as h5:
                node = h5.create_group("matrix")
                for name, values in [("data", matrix.data), ("indices", matrix.indices), ("indptr", matrix.indptr), ("shape", matrix.shape)]:
                    node.create_dataset(name, data=values)
                node.create_dataset("barcodes", data=np.array([b"b2", b"b1", b"empty"]))
                feature = node.create_group("features")
                feature.create_dataset("name", data=np.array([b"I", b"E1", b"E2", b"P", b"MT-X", b"tag"]))
                feature.create_dataset("id", data=np.array([f"id{i}".encode() for i in range(6)]))
                feature.create_dataset("feature_type", data=np.array([b"Gene Expression"] * 5 + [b"Antibody Capture"]))
            info = {"sha256": audit.sha(path), "gsm": "synthetic", "donor": "a", "day": 0}
            loaded = audit.load_h5(path, info, ["I", "E1", "E2", "P"])
            self.assertEqual(loaded.barcodes.tolist(), ["b1", "b2"])
            self.assertEqual(loaded.totals.tolist(), [4, 8])
            self.assertEqual(loaded.mito.tolist(), [1, 2])
            self.assertEqual(loaded.deposited_barcodes, 3)
            with self.assertRaises(ValueError):
                audit.load_h5(path, info, ["missing"])
            with h5py.File(path, "a") as h5:
                h5["matrix/features/name"][2] = b"E1"
            info["sha256"] = audit.sha(path)
            with self.assertRaises(ValueError):
                audit.load_h5(path, info, ["E1"])

    def test_omission_changes_only_named_panel_and_keeps_all_variants(self):
        specs = audit.variant_specs(["a", "b", "c", "d", "e"], ["i", "j", "k", "l", "m"])
        self.assertEqual(len(specs), 22)
        self.assertEqual(len({row["id"] for row in specs}), 22)
        samples = [sample("a0", "a", 0, [[2, 1, 1, 0], [2, 0, 1, 0]])]
        spec = {"id": "omit", "q": .1, "umi": 1, "omit_core": "E1"}
        rows, _ = audit.analyze_variant(samples, spec, ["E1", "E2"], ["I"], ["P"], audit.depth_cutoffs(samples))
        self.assertEqual(rows[0]["endogenous_panel"], ["E2"])
        self.assertEqual(rows[0]["identity_panel"], ["I"])
        self.assertEqual(rows[0]["coexpression_at_least_two_count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
