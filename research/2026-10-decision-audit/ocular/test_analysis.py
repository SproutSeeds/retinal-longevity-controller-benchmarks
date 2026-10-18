#!/usr/bin/env python3
"""Synthetic tests of sample weighting, sparse modalities, QC and partitions."""
import itertools
import json
from pathlib import Path
import tempfile
import unittest

import h5py
import numpy as np

import analyze as a


class AnalysisTests(unittest.TestCase):
    def test_exact_enumeration_uses_animals(self):
        values = [10, 11, 12, 13, 0, 1, 2]
        labels = [True] * 4 + [False] * 3
        d, n, denominator, rows = a.exact_permutation(values, labels)
        self.assertEqual(d, 10.5)
        self.assertEqual(denominator, 35)
        self.assertEqual(len(set(x["treated_indices"] for x in rows)), 35)
        self.assertGreaterEqual(n, 1)
        self.assertGreaterEqual(a.holm([n / denominator] * 4)[0], 4 / 35)

    def test_permutation_all_ties_and_translation(self):
        labels = [True] * 4 + [False] * 3
        result = a.exact_permutation([3] * 7, labels)
        self.assertEqual(result[:3], (0.0, 35, 35))
        one = a.exact_permutation([1, 2, 8, 4, 3, 7, 6], labels)
        two = a.exact_permutation([101, 102, 108, 104, 103, 107, 106], labels)
        self.assertAlmostEqual(one[0], two[0])
        self.assertEqual(one[1:3], two[1:3])

    def test_holm_keeps_family(self):
        self.assertEqual(a.holm([.2, .01, .03, 1]), [.4, .04, .09, 1])

    def test_rank_zero_ties(self):
        np.testing.assert_allclose(a.average_ranks([0, 0, 5, 9]), [1/6, 1/6, 2/3, 1])
        np.testing.assert_allclose(a.average_ranks([0, 0, 0]), [.5, .5, .5])

    def test_marker_ambiguity_and_detection_threshold(self):
        # Two marker bins, 2 markers per bin, four synthetic cells.
        values = np.array([[1, 2, 1, 0], [1, 2, 1, 0], [0, 2, 0, 0], [0, 2, 0, 0]])
        np.testing.assert_array_equal(a.marker_partition(values, [[0, 1], [2, 3]], 1), [0, 2, 0, 3])
        np.testing.assert_array_equal(a.marker_partition(values, [[0, 1], [2, 3]], 2), [3, 2, 3, 3])

    def test_sparse_modalities_qc_and_pseudobulk(self):
        contract = a.read_json(a.HERE / "contract.json")
        panels = a.read_json(a.HERE / "panels.json")
        genes = {}
        for p in panels["panels"].values():
            for g in p["genes"]:
                if g["mouse_ensembl_gene"]:
                    genes[g["mouse_ensembl_gene"]] = g["mouse_symbol"]
        markers = sorted({m for p in contract["composition"]["marker_bins"].values() for m in p})
        for marker in markers:
            if marker not in genes.values():
                genes["marker_" + marker] = marker
        genes["mito_gene"] = "mt-Fake"
        while len(genes) < 500:
            genes["fake_" + str(len(genes))] = "Fake" + str(len(genes))
        ids, names = list(genes), list(genes.values())
        dense = np.full((501, 5), 2, dtype=np.int64)
        dense[500] = 1000000  # ATAC must never contribute to RNA counts or QC.
        dense[names.index("mt-Fake")] = 0
        for marker in markers:
            dense[names.index(marker)] = 0
        for marker in contract["composition"]["marker_bins"]["excitatory_marker_bin"]:
            dense[names.index(marker), 0] = 2
        for marker in contract["composition"]["marker_bins"]["microglial_marker_bin"]:
            dense[names.index(marker), 4] = 1
        dense[names.index("mt-Fake"), 1] = 50  # Mito fraction failure.
        dense[:500, 2] = 0
        dense[:100, 2] = 1  # Low RNA and low feature failures.
        dense[:500, 3] = 100  # High RNA failure.
        data, rows, pointers = [], [], [0]
        for c in range(5):
            nonzero = np.flatnonzero(dense[:, c])
            rows.extend(nonzero.tolist())
            data.extend(dense[nonzero, c].tolist())
            pointers.append(len(data))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "example.h5"
            with h5py.File(path, "w") as h:
                m = h.create_group("matrix")
                m["data"], m["indices"], m["indptr"] = data, rows, pointers
                m["shape"] = [501, 5]
                m["barcodes"] = np.asarray([f"cell{i}".encode() for i in range(5)])
                f = m.create_group("features")
                f["id"] = np.asarray([x.encode() for x in ids + ["chr1:1-100"]])
                f["name"] = np.asarray([x.encode() for x in names + ["peak"]])
                f["feature_type"] = np.asarray([b"Gene Expression"] * 500 + [b"Peaks"])
            record = a.extract(path, {"gsm": "synthetic", "animal_id": "one", "group": "APP_GFP"}, contract, panels)
        self.assertEqual(record["qc"]["n_deposited"], 5)
        self.assertEqual(record["qc"]["n_rna_qc"], 2)
        self.assertFalse(record["qc"]["primary_qc_eligible"])
        np.testing.assert_array_equal(record["counts"]["qc"], dense[:500, [0, 4]].sum(axis=1))
        np.testing.assert_array_equal(record["counts"]["all"], dense[:500].sum(axis=1))
        self.assertEqual(int(record["bin_n"][1].sum()), 2)
        self.assertEqual(int(record["bin_n"][2].sum()), 2)
        bin_names = list(contract["composition"]["marker_bins"])
        self.assertEqual(record["bin_n"][1][bin_names.index("excitatory_marker_bin")], 1)
        self.assertEqual(record["bin_n"][1][bin_names.index("microglial_marker_bin")], 1)
        self.assertEqual(record["bin_n"][2][-1], 1)


if __name__ == "__main__":
    unittest.main()
