#!/usr/bin/env python3
"""Check the frozen inventory, source provenance, and unresolved evidence gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_audit import build
from finalize_audit import reconcile

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, help="Also hash-check every acquired original source, including PDFs")
    parser.add_argument("--emit", type=Path)
    args = parser.parse_args()
    checks = []

    def check(condition, name):
        checks.append({"name": name, "result": "PASS" if condition else "FAIL"})

    sources = read("SOURCES.json")
    records = sources["sources"]
    by_id = {r["id"]: r for r in records}
    check(len(by_id) == len(records), "source IDs are unique")
    check(sources["attempted_count"] == len(records), "attempted source count")
    check(sources["acquired_count"] == sum(r["result"] == "acquired" for r in records), "acquired source count")
    check(sources["failed_count"] == sum(r["result"] != "acquired" for r in records), "failed source count retained")
    for record in records:
        if record["result"] == "acquired":
            check(bool(record.get("checked_at")) and record["url"].startswith("https://"), f"retrieval provenance: {record['id']}")
        paths = []
        if record.get("snapshot"):
            paths.append(ROOT / record["snapshot"])
        if args.cache is not None and record["result"] == "acquired":
            paths.append(args.cache / record["id"])
        for path in paths:
            check(path.is_file(), f"source exists: {path.name}")
            if path.is_file():
                check(hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], f"source SHA-256: {path.name}")
                check(path.stat().st_size == record["bytes"], f"source bytes: {path.name}")
    for record in sources["prior_extractions"]:
        path = ROOT / record["snapshot"]
        check(hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], f"prior extraction SHA-256: {path.name}")
        check(record["kind"] == "previous_verified_project_extraction_not_primary_source", f"prior extraction attribution: {path.name}")

    inventory = read("INVENTORY.json")
    check(build(ROOT / "inventory-sources") == inventory, "complete inventory rebuild equality")
    check(inventory["github"]["head"] == "011586aea2e8612c794e57d2a260fa1a29d417a0", "pinned author head")
    check(len(inventory["github"]["history"]) == 6, "all six returned commits inspected")
    check(inventory["geo"]["member_count"] == 30 and inventory["geo"]["matrix_triplet_count"] == 10, "GEO complete triplets")
    check(inventory["sra"]["experiment_count"] == 10 and inventory["sra"]["run_count"] == 13, "SRA project inventory")
    check(inventory["sra"]["whole_body_run_count"] == 7, "whole-body SRA runs")
    check(inventory["sra"]["whole_body_named_lmo_or_undetermined_files"] == [], "no named LMO or Undetermined original file in inspected inventory")
    check(inventory["sra"]["read_contents_inspected"] is False, "filename inventory not promoted to read-content proof")
    check(inventory["ena_whole_body_fastq_bytes"] == 129370260434, "all whole-body ENA file-size sum")
    check(inventory["ena_whole_body_fastq_bytes_by_geo_sample"]["GSM7022367"] == 44207239760, "cohort 1 ENA size scope")
    versions = inventory["zenodo"]["versions"]
    for name in ("svz_iOSKM_cohort1_toshare.rds", "svz_iOSKM_cohort2_toshare.rds"):
        checksums = {f["checksum"] for v in versions for f in v["files"] if f["name"] == name}
        check(len(checksums) == 1, f"whole-body file unchanged across two records: {name}")
    targeted = {f["checksum"] for v in versions for f in v["files"] if f["name"] == "svz_ciOSKM_toshare.rds"}
    check(len(targeted) == 2, "changed SVZ-targeted object is not called unchanged")

    sample = read("sample-reconciliation.json")
    check(sample == reconcile(read("dependency-snapshots/full-animal-source-map.json")), "sample reconciliation rebuild equality")
    check(sample["omitted_count"] == 7 and sample["withdrawal_labeled_count"] == 5, "omitted and withdrawal-label counts separated")
    check(sample["candidate_old_OSKM_withdrawal_count"] == 4, "four candidate old OSKM withdrawal animals")
    check(all(r["withdrawal_days_after_final_pulse"] is None for r in sample["samples"]), "row-level timing remains unknown")
    check(all(r["barcode_to_animal_join_recovered"] is False for r in sample["samples"]), "unrecovered barcode assignments retained")
    check({r["animal_label_author_code"]: r["animal_label_publisher"] for r in sample["samples"] if r["animal_label_author_code"].startswith("BL6")} == {"BL61": "B1", "BL62": "B2", "BL63": "B3"}, "publisher and author BL6 aliases preserved")

    timing = read("timing-evidence.json")
    for record in timing["sources"]:
        if "sha256" in record:
            check(record["sha256"] == by_id[record["source_id"]]["sha256"], f"timing primary source binding: {record['id']}")
    check(timing["sources"][0]["facts"]["post_final_pulse_withdrawal_days"] == 5, "design-level five-day withdrawal recorded")
    check(timing["sources"][1]["claim_level"] == "Heuristic" and timing["sources"][1]["named_animal_match_verified"] is False, "count matching is explicitly heuristic")
    check(sources["published_outcome_exposure"]["occurred"] is True, "published outcome exposure disclosed")
    check(timing["thesis_is_independent_replication"] is False, "thesis is not independent replication")
    decision = read("decision.json")
    check(decision["new_existing_experiment_found"] is True, "existing withdrawal experiment recognized")
    check(decision["new_outcome_computation_runnable"] is False, "no new outcome computation admitted without assignments")
    check(decision["wetlab_necessity_proven"] is False, "bounded search not universal wet-lab necessity")
    check(decision["human_retinal_recovery_established"] is False, "mouse neural lead not human retinal closure")
    check(decision["messages_sent_by_this_lane"] is False, "no author send by this lane")
    check(set(decision["omitted_animals"]) == {r["animal_label_author_code"] for r in sample["samples"]}, "decision animal list reconciles")
    if args.cache is not None:
        for row in sample["samples"]:
            file = "author-iOSKM_cohort1__seurat_part2.R" if row["cohort"] == 1 else "author-iOSKM_cohort2__iOSKM2_seurat_part2.R"
            check(row["hash_id"] in (args.cache / file).read_text(), f"exact animal hash label in pinned author code: {row['animal_label_author_code']}")
    result = {
        "schema": "cx004-recovery-verification/v1", "result": "PASS" if all(c["result"] == "PASS" for c in checks) else "FAIL",
        "mode": "strict_cached_sources" if args.cache is not None else "portable_saved_metadata",
        "checks_passed": sum(c["result"] == "PASS" for c in checks), "checks_total": len(checks),
        "checks": checks,
        "scope": "Source hashes, factual inventories and evidence-gate consistency. Visual figure interpretations are recorded human/agent review; software checks are not biological validation.",
        "scientific_recovery_verdict": "INCONCLUSIVE"
    }
    if args.emit:
        args.emit.write_text(json.JSONEncoder(indent=2, sort_keys=True).encode(result) + "\n")
    print(f"{result['result']}: {result['checks_passed']}/{result['checks_total']} checks; biological recovery INCONCLUSIVE")
    raise SystemExit(0 if result["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
