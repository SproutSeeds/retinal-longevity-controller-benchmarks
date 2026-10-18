#!/usr/bin/env python3
"""Freeze small factual inventories and derive the omitted-sample reconciliation.

The thesis PDF remains in the cache; this script does not redistribute it or
compute expression outcomes. Hand-read design evidence is in timing-evidence.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from build_audit import build

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent.parent / "cx004-neural-validation-2026-10-18" / "recovery"
PUBLIC_PRIOR = "https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks/blob/main/research/2026-10-neural-validation/recovery/"
INVENTORY_INPUTS = [
    "github-commits.json", "github-branches.json", "github-tags.json",
    "github-releases.json", "github-forks.json", "github-issues.json",
    "zenodo-versions-default.json", "zenodo-latest.json", "ena-SRP420832.tsv",
    "sra-entire-project.xml", "sra-project-search.xml",
    "biostudies-S-EPMC12036604.json", "geo-filelist.txt",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value) -> None:
    path.write_text(json.JSONEncoder(indent=2, sort_keys=True).encode(value) + "\n")


def reconcile(source: dict) -> dict:
    omitted = []
    for original in source["samples"]:
        if original["observed_in_shared_object"]:
            continue
        row = dict(original)
        row["geo_sample"] = ("GSM7022367" if row["cohort"] == 1 else
                             f"GSM702236{7 + row['tenx_lane']}" if row["tenx_lane"] < 3 else "GSM7022370")
        row["thesis_candidate_group"] = (
            "old_OSKM_five_day_withdrawal_candidate" if row["treatment_author_code"] == "2Dox5"
            and row["age_genotype_author_code"] != "old_BL6" else
            "BL6_five_day_withdrawal_label_control" if row["treatment_author_code"] == "2Dox5"
            else "BL6_control")
        row["thesis_named_animal_link_verified"] = False
        row["barcode_to_animal_join_recovered"] = False
        row["withdrawal_days_after_final_pulse"] = None
        row["timing_limit"] = (
            "The thesis establishes a five-day withdrawal design. It does not name this animal or supply its collection timestamps; do not impute a row-level timing value.")
        omitted.append(row)
    return {
        "schema": "cx004-omitted-sample-reconciliation/v1",
        "claim_level": "Verified",
        "claim_scope": "Author-code and publisher-table label reconciliation only; the thesis-to-animal matching is Heuristic.",
        "prior_source_map": "dependency-snapshots/full-animal-source-map.json",
        "prior_source_map_public_url": PUBLIC_PRIOR + "full-animal-source-map.json",
        "samples": omitted,
        "omitted_count": len(omitted),
        "withdrawal_labeled_count": sum(r["treatment_author_code"] == "2Dox5" for r in omitted),
        "candidate_old_OSKM_withdrawal_count": sum(r["thesis_candidate_group"] == "old_OSKM_five_day_withdrawal_candidate" for r in omitted),
        "named_thesis_animal_links_verified": 0,
        "barcode_to_animal_joins_recovered": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--prior", type=Path, default=PRIOR)
    args = parser.parse_args()
    acquisition = json.loads((ROOT / "acquisition.json").read_text())
    entries = {r["id"]: r for r in acquisition["sources"]}
    source_names = INVENTORY_INPUTS + [f"github-tree-{r['sha']}.json"
                                      for r in json.loads((args.cache / "github-commits.json").read_text())]
    target = ROOT / "inventory-sources"
    target.mkdir(exist_ok=True)
    for name in source_names:
        if digest(args.cache / name) != entries[name]["sha256"]:
            raise ValueError(f"source digest mismatch: {name}")
        shutil.copyfile(args.cache / name, target / name)
    save(ROOT / "INVENTORY.json", build(target))

    deps = ROOT / "dependency-snapshots"
    deps.mkdir(exist_ok=True)
    previous = []
    for name in ("full-animal-source-map.json", "publisher-sample-metadata.json", "raw-availability.json"):
        shutil.copyfile(args.prior / name, deps / name)
        previous.append({"id": name, "sha256": digest(deps / name),
                         "bytes": (deps / name).stat().st_size,
                         "snapshot": f"dependency-snapshots/{name}",
                         "url": PUBLIC_PRIOR + name,
                         "kind": "previous_verified_project_extraction_not_primary_source"})
    save(ROOT / "sample-reconciliation.json", reconcile(json.loads((deps / "full-animal-source-map.json").read_text())))

    rows = []
    for original in acquisition["sources"]:
        row = {k: v for k, v in original.items() if k != "cache_path"}
        row["snapshot"] = f"inventory-sources/{row['id']}" if row["id"] in source_names else None
        rows.append(row)
    save(ROOT / "SOURCES.json", {
        "schema": "cx004-recovery-sources/v1", "search_cutoff_date": "2026-10-18",
        "claim_level": "Verified", "sources": rows, "prior_extractions": previous,
        "attempted_count": len(rows), "acquired_count": sum(r["result"] == "acquired" for r in rows),
        "failed_count": sum(r["result"] != "acquired" for r in rows),
        "bounded_scope": "Named resources and returned inventories; this is not proof that no other public or author-held data exist.",
        "raw_expression_outcome_analysis_performed": False,
        "published_outcome_exposure": {
            "occurred": True, "source": "stanford-Xu-thesis.pdf", "pdf_pages_one_based": [88, 97, 98, 106, 107],
            "reason": "Metadata-targeted thesis inspection exposed narrative and plotted withdrawal outcomes.",
            "consequence": "A future reanalysis of these samples is hypothesis-informed; these figures are not independent replication or reconstructed numerical evidence."
        },
    })
    # Preserve the acquisition history and correct the scope flag after visual review.
    acquisition["expression_outcomes_read"] = True
    acquisition["expression_outcomes_read_scope"] = "Published thesis narrative and plotted summary outcomes encountered; no raw expression outcome analysis in this lane."
    save(ROOT / "acquisition.json", acquisition)
    print(f"PASS: {len(source_names)} metadata snapshots and 3 prior extractions frozen")


if __name__ == "__main__":
    main()
