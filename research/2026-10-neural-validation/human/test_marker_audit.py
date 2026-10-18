#!/usr/bin/env python3
"""Behavioral and source-regression checks for the post hoc marker audit."""
import gzip
import json
from pathlib import Path
import tempfile
import unittest

import marker_audit as audit


class MarkerAuditTests(unittest.TestCase):
    def test_contributions_and_omissions_separate_sign_from_magnitude(self):
        values = {"dominant": [0, 0, 20, 20], "weak": [0, 0, 1, 1], "zero": [0, 0, 0, 0]}
        result = audit.decompose(values, [2, 3], [0, 1])
        dominant = next(row for row in result["gene_details"] if row["gene"] == "dominant")
        self.assertEqual(result["mean_difference"], 7)
        self.assertAlmostEqual(sum(row["additive_contribution"] for row in result["gene_details"]), 7)
        self.assertEqual(dominant["omission_effect"], .5)
        self.assertTrue(dominant["omission_preserves_full_mean_sign"])
        self.assertLess(dominant["omission_retained_magnitude"], .1)

    def test_zero_feature_remains_in_panel_denominator(self):
        result = audit.decompose({"a": [0, 2], "b": [0, 0]}, [1], [0])
        self.assertEqual(result["panel_size"], 2)
        self.assertEqual(result["mean_difference"], 1)
        zero = next(row for row in result["gene_details"] if row["gene"] == "b")
        self.assertEqual(zero["omission_effect"], 2)
        self.assertEqual(zero["additive_contribution"], 0)

    def test_signed_and_absolute_shares_differ_for_opposing_effects(self):
        result = audit.decompose({"up": [0, 4], "down": [3, 0]}, [1], [0])
        up = next(row for row in result["gene_details"] if row["gene"] == "up")
        self.assertEqual(up["signed_share"], 4)
        self.assertAlmostEqual(up["absolute_share"], 4 / 7)

    def test_all_zero_effect_has_no_share_or_retained_magnitude(self):
        result = audit.decompose({"a": [0, 0], "b": [0, 0]}, [1], [0])
        for detail in result["gene_details"]:
            self.assertIsNone(detail["signed_share"])
            self.assertIsNone(detail["absolute_share"])
            self.assertIsNone(detail["omission_retained_magnitude"])

    def test_sample_permutation_does_not_make_rep_labels_pairs(self):
        result = audit.decompose({"a": [0, 2, 3, 9], "b": [2, 1, 2, 8]}, [2, 3], [0, 1])
        swapped = audit.decompose({"a": [2, 0, 9, 3], "b": [1, 2, 8, 2]}, [2, 3], [0, 1])
        self.assertEqual(result["mean_difference"], swapped["mean_difference"])
        self.assertEqual(sorted(result["four_library_differences"]), sorted(swapped["four_library_differences"]))

    def test_rank_zero_ties_and_scalar_invariance(self):
        expected = [0, 0, .8, .8]
        self.assertEqual(audit.zero_anchored_ranks([0, 0, 2, 2]), expected)
        self.assertEqual(audit.zero_anchored_ranks([0, 0, 20, 20]), expected)
        self.assertEqual(audit.zero_anchored_ranks([0, 0]), [0, 0])
        self.assertEqual(audit.zero_anchored_ranks([1, 2, 3]), [1 / 3, 2 / 3, 1])

    def test_rank_is_still_composition_dependent(self):
        before = audit.zero_anchored_ranks([0, 1, 2])
        after = audit.zero_anchored_ranks([4, 1, 2])
        self.assertNotEqual(before[1], after[1])

    def test_all_transforms_preserve_zero_expression(self):
        values, _ = audit.transforms({"a": [1, 2], "b": [3, 4], "zero": [0, 0]}, [1])
        for method in values.values():
            self.assertEqual(method["zero"], [0, 0])

    def test_library_scaling_invariant(self):
        source = {"a": [1, 2], "b": [3, 4], "c": [5, 6], "z": [0, 0]}
        scaled = {g: [v[0] * 7, v[1] * 2] for g, v in source.items()}
        one, _ = audit.transforms(source, [1])
        two, _ = audit.transforms(scaled, [1])
        for method, values in one.items():
            for gene, vector in values.items():
                for v1, v2 in zip(vector, two[method][gene]):
                    self.assertAlmostEqual(v1, v2, places=12)

    def test_trimmed_denominator_responds_to_single_abundant_composition(self):
        source = {"dominant": [100, 1000], "a": [1, 1], "b": [2, 2], "c": [3, 3]}
        values, details = audit.transforms(source, [1])
        self.assertNotEqual(values["log2_cpm"]["a"][0], values["log2_cpm"]["a"][1])
        self.assertEqual(values["log2_top1_excluded_cpm_equivalent"]["a"][0], values["log2_top1_excluded_cpm_equivalent"]["a"][1])
        self.assertEqual(details["top_abundance_exclusions"]["log2_top1_excluded_cpm_equivalent"]["excluded_features"], ["dominant"])
        self.assertGreater(values["log2_top1_excluded_cpm_equivalent"]["dominant"][1], 0)

    def test_invalid_counts_rejected(self):
        for body in ["gene,a,a\ng,1,2\n", "gene,a,b\ng,-1,2\n", "gene,a,b\ng,NaN,2\n", "gene,a,b\ng.1,1,2\ng.2,1,3\n", "gene,a,b\ng,0,2\n"]:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "counts.csv.gz"
                with gzip.open(path, "wt") as stream:
                    stream.write(body)
                with self.assertRaises(ValueError):
                    audit.read_counts(path)

    def test_source_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.txt"
            path.write_text("original")
            expected = audit.sha(path)
            path.write_text("changed")
            with self.assertRaises(ValueError):
                audit.check_hash(path, expected)

    def test_duplicate_or_inconsistent_sample_metadata_rejected(self):
        records = []
        for construct in ["OSK", "O4YRSK"]:
            for day in [0, 4]:
                for rep in [1, 2]:
                    condition = "no dox" if day == 0 else "dox"
                    records.append("\n".join([
                        f"^SAMPLE = GSM{len(records) + 1}",
                        f"!Sample_title = {construct}, {condition}, 4 days, rep{rep}",
                        "!Sample_organism_ch1 = Homo sapiens",
                        "!Sample_characteristics_ch1 = cell line: GM00731",
                        f"!Sample_characteristics_ch1 = treatment: {construct}, {condition}, 4 days",
                        f"!Sample_description = Column name in raw_counts_matrix.csv: {construct}_{day}D_{rep}",
                    ]))
        source = "\n".join(records)
        columns = [f"{construct}_D{day}_{i}" for construct in ["OSK", "O4YRSK"] for day in [0, 4] for i in [1, 2]]
        self.assertEqual(len(audit.validate_samples(source, columns)), 8)
        with self.assertRaises(ValueError):
            audit.validate_samples(source, columns[:-1] + columns[:1])
        with self.assertRaises(ValueError):
            audit.validate_samples(source.replace("cell line: GM00731", "cell line: other", 1), columns)

    def test_real_data_rejects_four_markers_all_zero_claim(self):
        result = json.loads((audit.HERE / "marker-audit.json").read_text())
        availability = {row["gene"]: row for row in result["availability"]}
        self.assertEqual(availability["NANOG"]["detected_libraries"], 2)
        self.assertEqual(availability["NANOG"]["raw_count_sum"], 2)
        self.assertEqual(availability["SALL4"]["detected_libraries"], 8)
        self.assertEqual(availability["SALL4"]["raw_count_sum"], 74)
        self.assertEqual(availability["PRDM14"]["raw_count_sum"], 0)
        self.assertEqual(availability["ZFP42"]["raw_count_sum"], 0)
        self.assertLessEqual(result["original_replay_max_absolute_error"], 1e-10)

    def test_real_cd24_omission_exposes_joint_pair_sign_failure(self):
        result = json.loads((audit.HERE / "marker-audit.json").read_text())
        rows = [row for row in result["contrasts"] if row["panel"] == "reprogramming_without_OSK_overlap"
                and row["method"] in {"log2_cpm", "log2_median_ratio_cpm_equivalent"}]
        self.assertEqual(len(rows), 4)
        for row in rows:
            detail = next(d for d in row["gene_details"] if d["gene"] == "CD24")
            self.assertTrue(detail["omission_preserves_full_mean_sign"])
            self.assertGreater(detail["signed_share"], .79)
            self.assertLess(detail["omission_retained_magnitude"], .24)
            self.assertLess(min(detail["omission_four_library_differences"]), 0)
            self.assertGreater(max(detail["omission_four_library_differences"]), 0)

    def test_prior_immutable_hashes_match_contract(self):
        contract = json.loads((audit.HERE / "posthoc-contract.json").read_text())
        for name, expected in contract["prior_sha256"].items():
            self.assertEqual(audit.sha(audit.PRIOR / name), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
