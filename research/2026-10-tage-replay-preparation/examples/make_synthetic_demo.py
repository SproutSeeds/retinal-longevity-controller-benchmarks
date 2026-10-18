#!/usr/bin/env python3
"""Create unmistakably synthetic comparator inputs. No model is executed."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import replay


def write_json(path, value):
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def artifact(path):
    return {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


def create_demo(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    files = {
        "model": ("SYNTHETIC_model_placeholder.txt", "SYNTHETIC PLACEHOLDER. This is text, not a model. Never executed.\n"),
        "preprocessing": ("SYNTHETIC_preprocessing.txt", "SYNTHETIC identity transform for parser testing only. No historical method is claimed.\n"),
        "environment": ("SYNTHETIC_environment.txt", "SYNTHETIC fixture generated using Python standard library; no inference environment.\n"),
        "provenance": ("SYNTHETIC_provenance.txt", "SYNTHETIC invented sample IDs, genes and numbers. No author statement, animal or biological observation.\n"),
        "gene_map": ("SYNTHETIC_gene_map.csv", "source_gene_id,model_gene_id,model_position\nSYNTHETIC_GENE_B,SYNTHETIC_MODEL_GENE_B,2\nSYNTHETIC_GENE_A,SYNTHETIC_MODEL_GENE_A,1\n"),
        "sample_map": ("SYNTHETIC_sample_map.csv", "source_sample_id,reference_sample_id\nSYNTHETIC_LIBRARY_B,SYNTHETIC_REFERENCE_B\nSYNTHETIC_LIBRARY_A,SYNTHETIC_REFERENCE_A\n"),
        "feature_matrix": ("SYNTHETIC_feature_matrix.csv", "source_sample_id,source_gene_id,value\nSYNTHETIC_LIBRARY_A,SYNTHETIC_GENE_B,3\nSYNTHETIC_LIBRARY_B,SYNTHETIC_GENE_A,4\nSYNTHETIC_LIBRARY_B,SYNTHETIC_GENE_B,5\nSYNTHETIC_LIBRARY_A,SYNTHETIC_GENE_A,2\n"),
        "expected_predictions": ("SYNTHETIC_expected.csv", "reference_sample_id,prediction\nSYNTHETIC_REFERENCE_A,10\nSYNTHETIC_REFERENCE_B,20\n"),
        "reference_values": ("SYNTHETIC_reference_values.csv", "reference_key,value,unit\nSYNTHETIC_center,0,synthetic_units\n"),
    }
    artifacts = {}
    for role, (name, content) in files.items():
        path = directory / name
        path.write_text(content, encoding="utf-8")
        artifacts[role] = artifact(path)
    manifest = {
        "schema": "cx004.tage_received_manifest.v1",
        "evidence_kind": replay.SYNTHETIC,
        "study_accession": "GSE304044",
        "model_identity": {
            "model_id": "SYNTHETIC_MODEL_NEVER_EXECUTED",
            "historical_version": "synthetic-v1",
            "training_target": "synthetic numbers",
            "species": "synthetic; no organism",
            "tissue_scope": "synthetic; no tissue",
            "feature_namespace": "synthetic invented gene IDs",
            "prediction_unit": "synthetic_units",
            "historical_equivalence_declaration": "SYNTHETIC fixture has no historical equivalence",
        },
        "provenance": {
            "declared_by": "SYNTHETIC example generator",
            "source_locator": "examples/make_synthetic_demo.py",
            "received_utc": "2026-10-18T00:00:00Z",
            "historical_basis": "SYNTHETIC software fixture only",
        },
        "preprocessing": {
            "input_scale": "synthetic_units",
            "normalization": "SYNTHETIC identity; no normalization performed",
            "gene_mapping": "SYNTHETIC explicit one-to-one map; model_position gives order",
            "missing_gene_policy": "SYNTHETIC reject incomplete matrix; no imputation",
            "control_centering": "SYNTHETIC center of zero recorded but never applied",
            "reference_cohorts": "SYNTHETIC no cohorts",
            "fixture_stage": "already_preprocessed_model_input",
        },
        "reference_value_keys": ["SYNTHETIC_center"],
        "reference_values_explanation": "SYNTHETIC zero exists only to test finite reference-value parsing",
        "tolerances": {"absolute": "0.000001", "relative": "0", "unit": "synthetic_units", "rationale": "SYNTHETIC comparator test threshold; never a historical tolerance"},
        "artifacts": artifacts,
    }
    manifest_path = directory / "SYNTHETIC_manifest.json"
    write_json(manifest_path, manifest)
    freeze_path = directory / "SYNTHETIC_freeze.json"
    replay.write_json(freeze_path, replay.freeze(manifest_path))
    # Deliberately reversed sample order. Values are hand-authored, not predictions.
    observed_path = directory / "SYNTHETIC_observed.csv"
    observed_path.write_text("reference_sample_id,prediction\nSYNTHETIC_REFERENCE_B,20\nSYNTHETIC_REFERENCE_A,10.0000005\n", encoding="utf-8")
    run = {
        "schema": "cx004.tage_external_output.v1",
        "evidence_kind": replay.SYNTHETIC,
        "freeze_sha256": replay.digest(freeze_path),
        "manifest_sha256": replay.digest(manifest_path),
        "declared_input_sha256": {role: value["sha256"] for role, value in artifacts.items()},
        "execution_evidence": "externally_supplied_unverified",
        "prediction_unit": "synthetic_units",
        "observed_predictions": artifact(observed_path),
    }
    run_path = directory / "SYNTHETIC_run.json"
    write_json(run_path, run)
    return {"manifest": manifest_path, "freeze": freeze_path, "run": run_path, "freeze_sha256": run["freeze_sha256"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New directory; existing directories are preserved")
    args = parser.parse_args()
    try:
        result = create_demo(args.out)
    except (OSError, replay.InvalidPacket, ValueError) as exc:
        parser.exit(2, f"Synthetic fixture creation failed: {exc}\n")
    for key, value in result.items():
        print(f"{key}: {value}")
    print("SYNTHETIC ONLY. No model executed; no scientific prediction or reproduction PASS.")


if __name__ == "__main__":
    main()
