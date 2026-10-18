import contextlib
import csv
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import replay

spec = importlib.util.spec_from_file_location("make_synthetic_demo", ROOT / "examples" / "make_synthetic_demo.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "SYNTHETIC_packet"
        self.packet = demo.create_demo(self.folder)

    def manifest(self):
        return replay.read_json(self.packet["manifest"])

    def save_manifest(self, value):
        demo.write_json(self.packet["manifest"], value)

    def run_record(self):
        return replay.read_json(self.packet["run"])

    def save_run(self, value):
        demo.write_json(self.packet["run"], value)

    def compare(self):
        return replay.compare(self.packet["manifest"], self.packet["freeze"], self.packet["freeze_sha256"], self.packet["run"])

    def change_artifact(self, role, change, rehash=True):
        manifest = self.manifest()
        path = self.folder / manifest["artifacts"][role]["path"]
        path.write_text(change(path.read_text()), encoding="utf-8")
        if rehash:
            manifest["artifacts"][role] = demo.artifact(path)
            self.save_manifest(manifest)

    def change_observed(self, change):
        run = self.run_record()
        path = self.folder / run["observed_predictions"]["path"]
        path.write_text(change(path.read_text()), encoding="utf-8")
        run["observed_predictions"] = demo.artifact(path)
        self.save_run(run)

    def assert_invalid_intake(self, pattern):
        with self.assertRaisesRegex(replay.InvalidPacket, pattern):
            replay.freeze(self.packet["manifest"])

    def test_keyed_match_is_order_independent_but_never_reproduction(self):
        result = self.compare()
        self.assertEqual(result["numeric_comparison"], "MATCH")
        self.assertEqual([r["reference_sample_id"] for r in result["rows"]], ["SYNTHETIC_REFERENCE_A", "SYNTHETIC_REFERENCE_B"])
        self.assertFalse(result["reproduction_pass"])
        self.assertFalse(result["biological_pass"])
        self.assertEqual(result["gates"]["reference_ready"], "BLOCKED_ADAPTER_UNRESOLVED")
        self.assertEqual(result["gates"]["reference_pass"], "BLOCKED_NO_VERIFIED_EXECUTION")
        self.assertEqual(result["gates"]["study_calculation"], "NOT_RUN")

    def test_boundary_and_mismatch_are_compared_without_rounding(self):
        self.change_observed(lambda value: value.replace("10.0000005", "10.000001"))
        self.assertEqual(self.compare()["numeric_comparison"], "MATCH")
        self.change_observed(lambda value: value.replace("10.000001", "10.00000100001"))
        self.assertEqual(self.compare()["numeric_comparison"], "MISMATCH")

    def test_swapped_values_cannot_match_by_position_or_average(self):
        self.change_observed(lambda _: "reference_sample_id,prediction\nSYNTHETIC_REFERENCE_A,20\nSYNTHETIC_REFERENCE_B,10\n")
        self.assertEqual(self.compare()["numeric_comparison"], "MISMATCH")

    def test_missing_expected_sample_is_rejected(self):
        self.change_artifact("expected_predictions", lambda value: value.replace("SYNTHETIC_REFERENCE_B,20\n", ""))
        self.assert_invalid_intake("sample keys")

    def test_unexpected_observed_sample_is_rejected(self):
        self.change_observed(lambda value: value + "SYNTHETIC_REFERENCE_C,10\n")
        with self.assertRaisesRegex(replay.InvalidPacket, "sample keys"):
            self.compare()

    def test_missing_observed_sample_is_rejected(self):
        self.change_observed(lambda value: value.replace("SYNTHETIC_REFERENCE_B,20\n", ""))
        with self.assertRaisesRegex(replay.InvalidPacket, "sample keys"):
            self.compare()

    def test_duplicate_observed_sample_is_rejected(self):
        self.change_observed(lambda value: value + "SYNTHETIC_REFERENCE_A,10\n")
        with self.assertRaisesRegex(replay.InvalidPacket, "duplicate"):
            self.compare()

    def test_missing_gene_value_is_rejected_without_imputation(self):
        self.change_artifact("feature_matrix", lambda value: value.replace("SYNTHETIC_LIBRARY_A,SYNTHETIC_GENE_A,2\n", ""))
        self.assert_invalid_intake("missing sample/gene")

    def test_unexpected_gene_is_rejected(self):
        self.change_artifact("feature_matrix", lambda value: value.replace("SYNTHETIC_GENE_A,2", "SYNTHETIC_GENE_C,2"))
        self.assert_invalid_intake("unexpected sample or gene")

    def test_unexpected_matrix_sample_is_rejected(self):
        self.change_artifact("feature_matrix", lambda value: value.replace("SYNTHETIC_LIBRARY_A", "SYNTHETIC_LIBRARY_C"))
        self.assert_invalid_intake("unexpected sample or gene")

    def test_duplicate_gene_sample_pair_is_rejected(self):
        self.change_artifact("feature_matrix", lambda value: value + "SYNTHETIC_LIBRARY_A,SYNTHETIC_GENE_A,2\n")
        self.assert_invalid_intake("duplicate sample/gene")

    def test_ambiguous_sample_mapping_is_rejected(self):
        self.change_artifact("sample_map", lambda value: value.replace("SYNTHETIC_REFERENCE_B", "SYNTHETIC_REFERENCE_A"))
        self.assert_invalid_intake("duplicate reference_sample_id")

    def test_ambiguous_gene_mapping_is_rejected(self):
        self.change_artifact("gene_map", lambda value: value.replace("SYNTHETIC_MODEL_GENE_B", "SYNTHETIC_MODEL_GENE_A"))
        self.assert_invalid_intake("duplicate model_gene_id")

    def test_feature_order_must_be_explicit_and_contiguous(self):
        self.change_artifact("gene_map", lambda value: value.replace(",2\n", ",3\n"))
        self.assert_invalid_intake("contiguous")

    def test_nonfinite_missing_and_overflow_matrix_values_are_rejected(self):
        original = (self.folder / self.manifest()["artifacts"]["feature_matrix"]["path"]).read_text()
        for value in ["NaN", "Infinity", "-inf", "1e99999999", ""]:
            with self.subTest(value=value):
                self.change_artifact("feature_matrix", lambda _, v=value: original.replace("SYNTHETIC_GENE_A,2", "SYNTHETIC_GENE_A," + v))
                self.assert_invalid_intake("nonfinite|exponent|nonempty")

    def test_nonfinite_prediction_is_rejected(self):
        for value in ["NaN", "Infinity", "-inf"]:
            with self.subTest(value=value):
                self.change_observed(lambda _, v=value: "reference_sample_id,prediction\nSYNTHETIC_REFERENCE_A," + v + "\nSYNTHETIC_REFERENCE_B,20\n")
                with self.assertRaisesRegex(replay.InvalidPacket, "nonfinite"):
                    self.compare()

    def test_reference_values_must_be_complete_and_finite(self):
        self.change_artifact("reference_values", lambda value: value.replace("SYNTHETIC_center", "SYNTHETIC_other"))
        self.assert_invalid_intake("reference value keys")
        self.change_artifact("reference_values", lambda value: value.replace("SYNTHETIC_other,0", "SYNTHETIC_center,NaN"))
        self.assert_invalid_intake("nonfinite")

    def test_model_bytes_are_hashed_and_never_deserialized(self):
        self.change_artifact("model", lambda _: "raise RuntimeError('MODEL MUST NEVER EXECUTE')\n")
        result = replay.freeze(self.packet["manifest"])
        self.assertEqual(result["gates"]["reference_ready"], "BLOCKED_ADAPTER_UNRESOLVED")

    def test_artifact_tampering_is_rejected(self):
        self.change_artifact("model", lambda value: value.replace("PLACEHOLDER", "PLAceHOLDER"), rehash=False)
        self.assert_invalid_intake("sha256 mismatch")

    def test_changed_tolerance_and_provenance_invalidate_existing_freeze(self):
        original = self.manifest()
        for group, key, value in [("tolerances", "absolute", "1"), ("provenance", "declared_by", "SYNTHETIC changed declaration")]:
            with self.subTest(group=group):
                manifest = json.loads(json.dumps(original))
                manifest[group][key] = value
                self.save_manifest(manifest)
                with self.assertRaisesRegex(replay.InvalidPacket, "changed after freeze"):
                    self.compare()

    def test_rehashed_changed_input_still_invalidates_freeze(self):
        self.change_artifact("feature_matrix", lambda value: value.replace("SYNTHETIC_GENE_A,2", "SYNTHETIC_GENE_A,2.5"))
        with self.assertRaisesRegex(replay.InvalidPacket, "changed after freeze"):
            self.compare()

    def test_plan_tampering_is_rejected_by_independent_digest(self):
        frozen = replay.read_json(self.packet["freeze"])
        frozen["tolerances"]["absolute"] = "999"
        demo.write_json(self.packet["freeze"], frozen)
        with self.assertRaisesRegex(replay.InvalidPacket, "retained sha256"):
            self.compare()

    def test_run_bindings_and_claimed_execution_cannot_bypass_gate(self):
        original = self.run_record()
        mutations = [("freeze_sha256", "0" * 64), ("manifest_sha256", "0" * 64),
                     ("declared_input_sha256", {}), ("execution_evidence", "verified_execution"),
                     ("prediction_unit", "months"), ("evidence_kind", replay.HISTORICAL)]
        for key, value in mutations:
            with self.subTest(key=key):
                run = dict(original)
                run[key] = value
                self.save_run(run)
                with self.assertRaises(replay.InvalidPacket):
                    self.compare()

    def test_added_pass_flags_are_rejected(self):
        run = self.run_record()
        run["reference_pass"] = True
        self.save_run(run)
        with self.assertRaisesRegex(replay.InvalidPacket, "unexpected fields"):
            self.compare()

    def test_synthetic_relabeling_is_rejected(self):
        manifest = self.manifest()
        manifest["evidence_kind"] = replay.HISTORICAL
        self.save_manifest(manifest)
        self.assert_invalid_intake("synthetic declaration")

    def test_multivalued_identity_is_rejected(self):
        manifest = self.manifest()
        manifest["model_identity"]["model_id"] = ["model-a", "model-b"]
        self.save_manifest(manifest)
        self.assert_invalid_intake("nonempty text")

    def test_duplicate_json_and_csv_fields_are_rejected(self):
        text = self.packet["manifest"].read_text()
        self.packet["manifest"].write_text(text.replace('"study_accession": "GSE304044"', '"study_accession": "GSE304044", "study_accession": "GSE304044"'))
        self.assert_invalid_intake("duplicate key")

    def test_nonfinite_json_is_rejected(self):
        text = self.packet["manifest"].read_text()
        self.packet["manifest"].write_text(text.replace('"absolute": "0.000001"', '"absolute": NaN'))
        self.assert_invalid_intake("nonfinite constant")

    def test_path_traversal_and_symlinks_are_rejected(self):
        manifest = self.manifest()
        artifact = manifest["artifacts"]["model"]
        original_path = artifact["path"]
        artifact["path"] = "../outside"
        self.save_manifest(manifest)
        self.assert_invalid_intake("stay inside")
        artifact["path"] = "SYMLINK_model"
        (self.folder / artifact["path"]).symlink_to(self.folder / original_path)
        self.save_manifest(manifest)
        self.assert_invalid_intake("symlinks")

    def test_author_template_blocks_without_creating_freeze(self):
        output = Path(self.temp.name) / "should-not-exist.json"
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            exit_code = replay.main(["freeze", "--manifest", str(ROOT / "examples" / "author-packet-template.json"), "--out", str(output)])
        self.assertEqual(exit_code, 2)
        self.assertIn("unresolved declaration", error.getvalue())
        self.assertFalse(output.exists())

    def test_existing_receipt_is_preserved(self):
        output = Path(self.temp.name) / "existing.json"
        output.write_text("PRESERVE\n")
        with contextlib.redirect_stderr(io.StringIO()):
            code = replay.main(["freeze", "--manifest", str(self.packet["manifest"]), "--out", str(output)])
        self.assertEqual(code, 2)
        self.assertEqual(output.read_text(), "PRESERVE\n")

    def test_cli_mismatch_writes_downgraded_receipt_and_exits_one(self):
        self.change_observed(lambda value: value.replace("10.0000005", "11"))
        output = Path(self.temp.name) / "mismatch.json"
        with contextlib.redirect_stdout(io.StringIO()):
            code = replay.main(["compare", "--manifest", str(self.packet["manifest"]), "--freeze", str(self.packet["freeze"]),
                                "--freeze-sha256", self.packet["freeze_sha256"], "--run", str(self.packet["run"]), "--out", str(output)])
        self.assertEqual(code, 1)
        result = replay.read_json(output)
        self.assertEqual(result["numeric_comparison"], "MISMATCH")
        self.assertFalse(result["reproduction_pass"])


if __name__ == "__main__":
    unittest.main()
