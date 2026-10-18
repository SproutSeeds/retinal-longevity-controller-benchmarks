#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["numpy==2.5.4", "scipy==1.18.1", "h5py==3.16.0"]
# ///
"""Check serialized cell arithmetic, donor tables and a complete byte replay."""
import argparse
from collections import Counter
import csv
import gzip
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

import percell_audit as audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--h5-dir", type=Path, default=audit.HERE.parents[2] / "tmp/observed-to-synthetic-public-expansion-intake/GSE297234/raw_h5")
    parser.add_argument("--output", type=Path, default=audit.HERE / "percell")
    parser.add_argument("--freeze", type=Path, default=audit.HERE / "PERCELL_FREEZE.json")
    args = parser.parse_args()
    contract_path = audit.HERE / "percell-contract-proposal.json"
    scout_path = audit.HERE / "timecourse-scout.json"
    audit.require_freeze(contract_path, scout_path, args.freeze)
    contract = json.loads(contract_path.read_text())
    result = json.loads((args.output / "results.json").read_text())
    tests = json.loads((audit.HERE / "PERCELL_TESTS.json").read_text())
    checks = []
    def check(name, passed):
        checks.append({"name": name, "status": "PASS" if bool(passed) else "FAIL"})
    check("synthetic_tests", tests["status"] == "PASS" and tests["tests_run"] == 12)
    check("synthetic_tested_analysis_hash", tests["source_sha256"]["percell_audit.py"] == audit.sha(audit.HERE / "percell_audit.py"))
    check("observed_analysis_hash", result["analysis_sha256"] == audit.sha(audit.HERE / "percell_audit.py"))
    check("frozen_contract_hash", result["contract_sha256"] == audit.sha(contract_path))
    check("primary_cell_artifact_hash", result["primary_cells_sha256"] == audit.sha(args.output / "primary-cells.tsv.gz"))
    check("joint_table_artifact_hash", result["joint_tables_sha256"] == audit.sha(args.output / "joint-tables.csv"))
    expected_samples = {(r["gsm"], r["donor"], r["day"]) for r in result["sample_qc"]}
    rows = result["sample_variant_results"]
    check("eight_distinct_donor_time_samples", len(expected_samples) == 8 and len({(d, day) for _, d, day in expected_samples}) == 8)
    check("all_frozen_variants_present", len(result["variants"]) == 22 and len(rows) == 176)
    for variant in result["variants"]:
        current = [r for r in rows if r["variant"] == variant["id"]]
        check("variant_samples:" + variant["id"], {(r["gsm"], r["donor"], r["day"]) for r in current} == expected_samples and len(current) == 8)
    for row in rows:
        tag = f"{row['variant']}:{row['gsm']}"
        for family in ["binary_2x2", "count_bins_2x4", "binary_with_factor_overlap"]:
            table = [t for t in row["joint_tables"] if t["table"] == family]
            n = row["n_retained"]
            check(f"{tag}:{family}:denominator", sum(t["count"] for t in table) == n and all(t["denominator"] == n for t in table))
            check(f"{tag}:{family}:fraction", all(t["fraction"] == (t["count"] / n if n else None) for t in table))
            check(f"{tag}:{family}:identity_margin", sum(t["count"] for t in table if t["identity"] == "identity_low") == row["identity_low_count"])
        binary = [t for t in row["joint_tables"] if t["table"] == "binary_2x2"]
        check(tag + ":codetection_margin", sum(t["count"] for t in binary if t["coexpression"] == "at_least_two") == row["coexpression_at_least_two_count"])
        if row["day"] == 0 and row["n_retained"]:
            check(tag + ":realized_D0_fraction", row["realized_D0_identity_low_fraction_in_this_variant"] == row["identity_low_count"] / row["n_retained"])
    primary = {r["gsm"]: r for r in rows if r["variant"] == "primary"}
    cell_counts, low_counts, co_counts, joint_counts = Counter(), Counter(), Counter(), Counter()
    max_score_error, mislabels = 0.0, 0
    marker_core = contract["features"]["endogenous_marker_panel"]
    marker_identity = contract["features"]["identity_marker_panel"]
    marker_factor = contract["features"]["factor_overlap_report_only"]
    seen = set()
    with gzip.open(args.output / "primary-cells.tsv.gz", "rt") as stream:
        for cell in csv.DictReader(stream, delimiter="\t"):
            gsm = cell["gsm"]
            pair = (gsm, cell["barcode"])
            if pair in seen:
                raise ValueError("Duplicate serialized sample/barcode")
            seen.add(pair)
            row = primary[gsm]
            total = int(cell["Gene_Expression_UMIs"])
            score = sum(math.log1p(int(cell[g]) / total * 10000) for g in marker_identity) / len(marker_identity)
            co = sum(int(cell[g]) >= 1 for g in marker_core)
            factor = any(int(cell[g]) >= 1 for g in marker_factor)
            low = float(cell["identity_score"]) <= row["baseline"]["threshold"]
            max_score_error = max(max_score_error, abs(score - float(cell["identity_score"])))
            mislabels += int(cell["donor"] != row["donor"] or int(cell["day"]) != row["day"]
                             or int(cell["identity_low"]) != int(low)
                             or int(cell["endogenous_codetected_marker_count"]) != co
                             or int(cell["factor_overlap_detected"]) != int(factor))
            cell_counts[gsm] += 1
            low_counts[gsm] += low
            co_counts[gsm] += co >= 2
            joint_counts[gsm] += low and co >= 2
    check("independent_serialized_cell_identity_arithmetic", max_score_error <= 1e-12)
    check("independent_serialized_cell_metadata_and_codetection", mislabels == 0)
    for gsm, row in primary.items():
        check("cell_table_recount:" + gsm, cell_counts[gsm] == row["n_retained"] and low_counts[gsm] == row["identity_low_count"] and co_counts[gsm] == row["coexpression_at_least_two_count"])
        target = next(t["count"] for t in row["joint_tables"] if t["table"] == "binary_2x2" and t["identity"] == "identity_low" and t["coexpression"] == "at_least_two")
        check("cell_joint_recount:" + gsm, joint_counts[gsm] == target)
    output_names = ["results.json", "joint-tables.csv", "primary-cells.tsv.gz"]
    original_hashes = {name: audit.sha(args.output / name) for name in output_names}
    with tempfile.TemporaryDirectory(prefix="cx004-percell-replay-", dir="/tmp") as folder:
        command = [sys.executable, str(audit.HERE / "percell_audit.py"), "--h5-dir", str(args.h5_dir),
                   "--freeze", str(args.freeze), "--output", folder]
        replay = subprocess.run(command, capture_output=True, text=True)
        check("full_replay_exit", replay.returncode == 0)
        replay_hashes = {name: audit.sha(Path(folder) / name) for name in output_names} if replay.returncode == 0 else {}
    check("byte_identical_complete_replay", original_hashes == replay_hashes)
    passed = all(row["status"] == "PASS" for row in checks)
    receipt = {"status": "PASS" if passed else "FAIL", "checks": checks,
               "check_count": len(checks), "synthetic_test_count": 12,
               "serialized_cells_checked": len(seen), "identity_score_max_absolute_error": max_score_error,
               "output_sha256": original_hashes, "replay_output_sha256": replay_hashes,
               "replay_stdout": replay.stdout, "replay_stderr": replay.stderr,
               "analysis_sha256": audit.sha(audit.HERE / "percell_audit.py"),
               "verification_sha256": audit.sha(Path(__file__)),
               "interpretation": "Computational verification of observed marker detections; no calibrated biological state or donor-level inference."}
    audit.save(args.output / "VERIFICATION.json", receipt)
    print(f"{receipt['status']}: {len(checks)} checks; {len(seen)} serialized barcodes; full byte replay {'PASS' if original_hashes == replay_hashes else 'FAIL'}")
    if not passed:
        print([row for row in checks if row["status"] == "FAIL"])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
