#!/usr/bin/env python3
"""Metadata/prior-artifact audit only: do not read expression arrays or run gates."""
import csv
import json
from pathlib import Path

from marker_audit import HERE, save, sha, check_hash

CONTROLLER = HERE.parents[2]
REPO = CONTROLLER.parents[1]
MODELING = CONTROLLER / "benchmarks/observed-to-synthetic-modeling-v0"
OLD = MODELING / "cx004-public-expansion-return-v0"
FIXTURE = MODELING / "cx004-gse297234-early-oskm-support-fixture-v0"


def read_csv(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def main():
    receipt_path = OLD / "gse297234_single_cell_marker_burden_receipt-v0.json"
    receipt = json.loads(receipt_path.read_text())
    burden_path = OLD / "gse297234_single_cell_rare_state_burden-v0.csv"
    prior_burdens = read_csv(burden_path)
    manifest_path = FIXTURE / "gse297234_fixture_sample_manifest-v0.csv"
    manifest = read_csv(manifest_path)
    shapes_path = FIXTURE / "gse297234_fixture_matrix_shape_table-v0.csv"
    shapes = {row["h5_file"]: row for row in read_csv(shapes_path)}
    panel_path = MODELING / "controller-benchmark-phase-one-marker-panel-v0.json"
    panel = json.loads(panel_path.read_text())
    old_script = CONTROLLER / "scripts/controller_cx004_gse297234_single_cell_marker_burden.py"
    sources = [receipt_path, burden_path, manifest_path, shapes_path, panel_path, old_script]
    files = []
    for row in receipt["h5_files"]:
        path = REPO / row["path"]
        check_hash(path, row["sha256"])
        if path.stat().st_size != row["size_bytes"]:
            raise ValueError("Source size differs from old receipt")
        sample = next(sample for sample in manifest if sample["h5_file"] == path.name)
        if sample["h5_sha256"] != row["sha256"]:
            raise ValueError("Prior fixture and receipt hashes disagree")
        files.append({"path": row["path"], "sha256": row["sha256"], "size_bytes": row["size_bytes"],
                      "gsm": sample["gsm_accession"], "donor": sample["donor"], "day": int(sample["timepoint_day"]),
                      "deposited_barcode_count_from_prior_shape_audit": int(shapes[path.name]["barcode_rows"]),
                      "feature_rows_from_prior_shape_audit": int(shapes[path.name]["features_rows"])})
    core = [row["marker_symbol"] for row in panel["markers"] if row["marker_family_id"] == "pluripotency_escape" and row["marker_tier"] == "core"]
    factor = [row["marker_symbol"] for row in panel["markers"] if row["marker_family_id"] == "pluripotency_escape" and row["marker_tier"] == "extension"]
    identity = [row["marker_symbol"] for row in panel["markers"] if row["marker_family_id"] == "adult_identity"]
    result = {
        "id": "CX004-GSE297234-METADATA-SCOUT-20261018-R1",
        "claim_level": "Verified file/provenance audit; Heuristic proposed marker interpretation",
        "expression_computed_this_scout": False,
        "source_study": {"doi": "10.1016/j.cell.2025.07.031", "accession": "GSE297234", "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE297234"},
        "local_files": files,
        "total_bytes": sum(row["size_bytes"] for row in files),
        "donors": [{"id": "GM00731", "age_years": 96}, {"id": "GM23815", "age_years": 22}],
        "replication": "One donor per age; four destructive sampling times D0/D3/D7/D10 per donor. No donor-level age comparison or longitudinal tracking of the same cell.",
        "exposure": "Sendai OSKM; elapsed time is not a controlled withdrawal interval. POU5F1/SOX2 expression is not a validated vector-specific load measurement.",
        "prior_analysis": {
            "generated_at": receipt["generated_at"], "git_commit_from_receipt": receipt["git_commit"],
            "receipt_sha256": sha(receipt_path), "source_hashes_reverified": True,
            "n_deposited_barcodes_from_prior": sum(int(row["cell_count"]) for row in prior_burdens),
            "donor_counts_from_prior": receipt["summary"]["donor_cell_counts"],
            "core_marker_panel": core, "factor_overlap_panel": factor, "identity_panel": identity,
            "normalization": "Mean of per-marker log1p(count/library_UMI*10000). Deposited 10x filtered barcodes; no >500-detected-gene filter is implemented in the prior marker-burden script.",
            "marginals_already_computed": "All 32 marker detection fractions, 8 family summaries, donor D0 q10 identity-low, q90 other markers, and separate D0 q95 positive endogenous-core and factor-overlap flags.",
            "joint_already_computed": "multi_risk_high=(core_high OR factor_overlap_high) AND (identity_low OR proliferation_high OR stress_high OR plasticity_high OR developmental_high). This is a joint marker flag, not a measured true rare-state prevalence.",
            "joint_gap": "The audited script and saved outputs contain no isolated endogenous-only coexpression-by-identity 2x2 table, no 0/1/2/3+ endogenous-marker count distribution, and no depth/downsampling sensitivity. The combined OR gate does not recover those distributions.",
            "legacy_naming_warning": "The prior filename and fields use rare_state and multi_risk wording. Interpret these as heuristic marker-gate fractions; they do not establish classifier specificity, true prevalence or transformation risk.",
            "frozen_original_burden_rows": prior_burdens,
        },
        "metadata_sources": [{"path": str(path.relative_to(REPO)), "sha256": sha(path)} for path in sources],
        "proposed_delta": "Preserve prior results, compute a separately frozen endogenous-marker coexpression-by-identity diagnostic, report donor/time denominators and detection/depth sensitivity, and avoid state or risk labels.",
        "novelty": "No field-novelty claim. The primary study already reports mesenchymal-drift and reprogramming analyses. Full figure/supplement comparison remains a prerequisite to any novelty assertion; this audit establishes only a local-output gap.",
        "next_gate": "Root review/freeze of percell-contract-proposal.json before extension expression computation.",
        "readouts": {f"CX004-R0{i}": "insufficient_signal" for i in range(1, 5)},
    }
    save(HERE / "timecourse-scout.json", result)
    print(f"PASS: {len(files)} source hashes; {result['total_bytes']} bytes; prior per-cell computation found; no new cell-state outcomes computed")


if __name__ == "__main__":
    main()
