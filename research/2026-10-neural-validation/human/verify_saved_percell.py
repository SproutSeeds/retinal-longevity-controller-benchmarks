#!/usr/bin/env python3
"""Portable aggregate verification: standard library, no H5 or per-cell reads."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "percell")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    folder = args.output
    result = json.loads((folder / "results.json").read_text())
    previous = json.loads((folder / "VERIFICATION.json").read_text())
    tests = json.loads((HERE / "PERCELL_TESTS.json").read_text())
    freeze = json.loads((HERE / "PERCELL_FREEZE.json").read_text())
    contract = json.loads((HERE / "percell-contract-proposal.json").read_text())
    checks = []
    def check(name, value):
        checks.append({"name": name, "status": "PASS" if bool(value) else "FAIL"})
    check("historical_full_verification_PASS", previous["status"] == "PASS")
    check("historical_result_bytes", previous["output_sha256"]["results.json"] == sha(folder / "results.json"))
    check("historical_table_bytes", previous["output_sha256"]["joint-tables.csv"] == sha(folder / "joint-tables.csv"))
    check("result_table_hash", result["joint_tables_sha256"] == sha(folder / "joint-tables.csv"))
    check("current_code_matches_observed_result", result["analysis_sha256"] == sha(HERE / "percell_audit.py"))
    check("current_code_matches_full_verification", previous["analysis_sha256"] == sha(HERE / "percell_audit.py"))
    check("current_verifier_matches_full_verification", previous["verification_sha256"] == sha(HERE / "verify_percell_observed.py"))
    check("current_contract_matches_observed_result", result["contract_sha256"] == sha(HERE / "percell-contract-proposal.json"))
    check("current_scout_matches_observed_result", result["scout_sha256"] == sha(HERE / "timecourse-scout.json"))
    check("freeze_contract_and_scout_match", freeze["contract_sha256"] == result["contract_sha256"] and freeze["scout_sha256"] == result["scout_sha256"])
    check("freeze_receipt_matches_result", freeze == result["freeze"] and freeze["expression_execution_authorized"] is True)
    check("current_synthetic_tests_passed", tests["status"] == "PASS" and tests["tests_run"] == 12)
    for name, expected in tests["source_sha256"].items():
        check("synthetic_tested_bytes:" + name, sha(HERE / name) == expected)
    expected_samples = {(r["gsm"], r["donor"], r["day"]) for r in result["sample_qc"]}
    expected_donor_times = {(r["id"], day) for r in contract["donors"] for day in contract["days"]}
    check("expected_donor_time_inventory", len(expected_samples) == 8 and {(d, day) for _, d, day in expected_samples} == expected_donor_times)
    rows = result["sample_variant_results"]
    check("176_sample_variant_rows", len(rows) == 176 and len(result["variants"]) == 22)
    primary = {r["gsm"]: r for r in rows if r["variant"] == "primary"}
    check("primary_denominators_match_QC", all(primary[r["gsm"]]["n_retained"] == r["nonempty_barcodes"] for r in result["sample_qc"]))
    for variant in result["variants"]:
        current = [r for r in rows if r["variant"] == variant["id"]]
        check("sample_inventory:" + variant["id"], len(current) == 8 and {(r["gsm"], r["donor"], r["day"]) for r in current} == expected_samples)
        for donor in {r["id"] for r in contract["donors"]}:
            by_donor = [r for r in current if r["donor"] == donor]
            check("donor_baseline_consistency:" + variant["id"] + ":" + donor, len(by_donor) == 4 and all(r["baseline"] == by_donor[0]["baseline"] for r in by_donor))
    for row in rows:
        tag = row["variant"] + ":" + row["gsm"]
        n = row["n_retained"]
        check(tag + ":valid_count_bounds", isinstance(n, int) and 0 <= n <= primary[row["gsm"]]["n_retained"] and 0 <= row["identity_low_count"] <= n and 0 <= row["coexpression_at_least_two_count"] <= n)
        check(tag + ":sample_marginal_fractions", row["identity_low_fraction"] == (row["identity_low_count"] / n if n else None) and row["coexpression_at_least_two_fraction"] == (row["coexpression_at_least_two_count"] / n if n else None))
        baseline = row["baseline"]
        check(tag + ":baseline_actual_fraction", baseline["D0_identity_low_fraction"] == baseline["D0_identity_low_count"] / baseline["D0_denominator"] and 0 <= baseline["D0_identity_low_count"] <= baseline["D0_denominator"])
        for family, expected_n in [("binary_2x2", 4), ("count_bins_2x4", 8), ("binary_with_factor_overlap", 8)]:
            table = [t for t in row["joint_tables"] if t["table"] == family]
            identifiers = {(t["identity"], t["coexpression"], t["factor_overlap_detected"]) for t in table}
            check(tag + ":" + family + ":complete_partition", len(table) == expected_n and len(identifiers) == expected_n and sum(t["count"] for t in table) == n and all(isinstance(t["count"], int) and 0 <= t["count"] <= n and t["denominator"] == n for t in table))
            check(tag + ":" + family + ":fractions", all(t["fraction"] == (t["count"] / n if n else None) for t in table))
            check(tag + ":" + family + ":identity_margin", sum(t["count"] for t in table if t["identity"] == "identity_low") == row["identity_low_count"])
        binary = [t for t in row["joint_tables"] if t["table"] == "binary_2x2"]
        for cell in binary:
            bins = {"2", "3+"} if cell["coexpression"] == "at_least_two" else {"0", "1"}
            check(tag + ":countbin_identity:" + cell["identity"] + ":" + cell["coexpression"],
                  sum(t["count"] for t in row["joint_tables"] if t["table"] == "count_bins_2x4" and t["identity"] == cell["identity"] and t["coexpression"] in bins) == cell["count"])
            check(tag + ":factor_identity:" + cell["identity"] + ":" + cell["coexpression"],
                  sum(t["count"] for t in row["joint_tables"] if t["table"] == "binary_with_factor_overlap" and t["identity"] == cell["identity"] and t["coexpression"] == cell["coexpression"]) == cell["count"])
        check(tag + ":codetection_margin", sum(t["count"] for t in binary if t["coexpression"] == "at_least_two") == row["coexpression_at_least_two_count"])
        check(tag + ":marker_detection_denominators", all(0 <= m["cells_detected"] <= n and m["fraction_detected"] == (m["cells_detected"] / n if n else None) for m in row["marker_summary"]))
        if row["day"] == 0:
            check(tag + ":realized_D0_fraction", row["realized_D0_identity_low_fraction_in_this_variant"] == (row["identity_low_count"] / n if n else None))
        if row["variant"] in {"primary", "endogenous_min2_umi", "identity_q05", "identity_q20"} or row["variant"].startswith("omit_"):
            check(tag + ":unchanged_primary_denominator", n == primary[row["gsm"]]["n_retained"])
    for gsm, row in primary.items():
        check("depth_partition:" + gsm, sum(r["n_retained"] for r in rows if r["gsm"] == gsm and r["variant"].startswith("D0_UMI_quartile_")) == row["n_retained"])
        check("thinning_same_retained_cohort:" + gsm, len({r["n_retained"] for r in rows if r["gsm"] == gsm and r["variant"].startswith("thin1000")}) == 1)
    with (folder / "joint-tables.csv").open() as stream:
        csv_rows = list(csv.DictReader(stream))
    expected_csv = [{k: "" if v is None else str(v) for k, v in {"variant": r["variant"], "gsm": r["gsm"], "donor": r["donor"], "day": r["day"], **t}.items()} for r in rows for t in r["joint_tables"]]
    check("csv_exactly_matches_all_JSON_table_rows", csv_rows == expected_csv)
    passed = all(r["status"] == "PASS" for r in checks)
    receipt = {"status": "PASS" if passed else "FAIL", "mode": "saved_aggregate_verification",
               "raw_H5_opened": False, "per_barcode_artifact_opened": False, "new_expression_outcomes_computed": False,
               "check_count": len(checks), "sample_variant_rows_checked": len(rows), "csv_rows_checked": len(csv_rows),
               "input_sha256": {name: sha(folder / name) for name in ["results.json", "joint-tables.csv", "VERIFICATION.json"]},
               "current_source_sha256": {name: sha(HERE / name) for name in ["percell_audit.py", "percell-contract-proposal.json", "PERCELL_FREEZE.json", "timecourse-scout.json", "verify_saved_percell.py"]},
               "checks": checks,
               "authority": "Checks saved arithmetic and current code/contract hashes against the historical complete replay; does not re-read raw data or independently recreate cell observations."}
    destination = args.receipt or folder / "SAVED_VERIFICATION.json"
    destination.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"{receipt['status']}: {len(checks)} aggregate checks; {len(rows)} donor/time/variant rows; no raw or per-cell file reads")
    if not passed:
        print([r for r in checks if r["status"] == "FAIL"])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
