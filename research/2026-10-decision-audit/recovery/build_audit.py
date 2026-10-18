#!/usr/bin/env python3
"""Rebuild bounded public-file inventories without reading expression data."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
WHOLE_BODY = {f"GSM7022367", "GSM7022368", "GSM7022369", "GSM7022370"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    # A 200 HTML challenge is a failed JSON route, never an empty inventory.
    value = json.loads(path.read_text())
    if not isinstance(value, (dict, list)):
        raise ValueError(f"unexpected JSON inventory type: {path.name}")
    return value


def tree_files(tree: dict) -> list[dict]:
    if tree.get("truncated") is not False:
        raise ValueError("GitHub tree is truncated or completeness is unspecified")
    if not isinstance(tree.get("tree"), list):
        raise ValueError("missing GitHub entries")
    paths = [entry["path"] for entry in tree["tree"]]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate GitHub paths")
    return [{key: row[key] for key in ("path", "sha", "size")}
            for row in tree["tree"] if row["type"] == "blob"]


def geo_files(body: str) -> dict:
    rows = list(csv.DictReader(io.StringIO(body), delimiter="\t"))
    archives = [r for r in rows if r["#Archive/File"] == "Archive"]
    files = [r for r in rows if r["#Archive/File"] == "File"]
    groups: dict[str, set[str]] = {}
    for row in files:
        match = re.fullmatch(r"(.+)_(barcodes.tsv|features.tsv|matrix.mtx)\.gz", row["Name"])
        if match is None:
            raise ValueError("unclassified GEO archive member; inspect before a negative claim")
        groups.setdefault(match[1], set()).add(match[2])
    if any(parts != {"barcodes.tsv", "features.tsv", "matrix.mtx"} for parts in groups.values()):
        raise ValueError("incomplete GEO matrix triplet")
    if len({r["Name"] for r in files}) != len(files):
        raise ValueError("duplicate GEO filenames")
    return {"archives": [{"name": r["Name"], "bytes": int(r["Size"])} for r in archives],
            "members": [{"name": r["Name"], "bytes": int(r["Size"])} for r in files],
            "member_count": len(files), "matrix_triplet_count": len(groups),
            "whole_body_triplets": sorted(g for g in groups if g.split("_")[0] in WHOLE_BODY),
            "unclassified_members": []}


def sra_inventory(body: str) -> dict:
    root = ET.fromstring(body)
    if root.tag != "EXPERIMENT_PACKAGE_SET":
        raise ValueError("unexpected SRA response root")
    experiments = {}
    runs = {}
    raw_files = {}
    observed_run_elements = 0
    for package in root.findall("EXPERIMENT_PACKAGE"):
        experiment = package.find("EXPERIMENT")
        sample = package.find("SAMPLE")
        if experiment is None or sample is None:
            raise ValueError("missing experiment or sample")
        exp_id, geo = experiment.attrib["accession"], sample.attrib["alias"]
        experiments[exp_id] = geo
        for run in package.findall("RUN_SET/RUN"):
            observed_run_elements += 1
            run_id = run.attrib["accession"]
            row = {"run": run_id, "experiment": exp_id, "geo_sample": geo,
                   "library_strategy": experiment.findtext("DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_STRATEGY"),
                   "whole_body": geo in WHOLE_BODY}
            if run_id in runs and runs[run_id] != row:
                raise ValueError("conflicting duplicated SRA run")
            runs[run_id] = row
            for f in run.findall("SRAFiles/SRAFile"):
                if f.attrib.get("supertype") != "Original":
                    continue
                item = {"run": run_id, "geo_sample": geo, "filename": f.attrib["filename"],
                        "bytes": int(f.attrib["size"]), "md5": f.attrib["md5"]}
                key = (run_id, item["filename"])
                if key in raw_files and raw_files[key] != item:
                    raise ValueError("conflicting duplicated original-file metadata")
                raw_files[key] = item
    if not experiments or not runs:
        raise ValueError("empty SRA inventory is not completeness evidence")
    whole = [f for f in raw_files.values() if f["geo_sample"] in WHOLE_BODY]
    return {"experiment_count": len(experiments), "run_count": len(runs),
            "run_elements_before_deduplication": observed_run_elements,
            "runs": sorted(runs.values(), key=lambda r: r["run"]),
            "original_files": sorted(raw_files.values(), key=lambda r: (r["run"], r["filename"])),
            "whole_body_run_count": sum(r["whole_body"] for r in runs.values()),
            "whole_body_original_file_count": len(whole),
            "whole_body_original_bytes": sum(f["bytes"] for f in whole),
            "whole_body_named_lmo_or_undetermined_files": [f for f in whole if re.search(r"LMO|Undetermined", f["filename"], re.I)],
            "read_contents_inspected": False}


def build(cache: Path) -> dict:
    commits = read_json(cache / "github-commits.json")
    if len(commits) >= 100:
        raise ValueError("commit page may be incomplete")
    history = []
    for commit in commits:
        sha = commit["sha"]
        tree = read_json(cache / f"github-tree-{sha}.json")
        history.append({"commit": sha, "files": tree_files(tree)})
    files_by_version = []
    versions = read_json(cache / "zenodo-versions-default.json")
    hits = versions["hits"]["hits"]
    total = versions["hits"]["total"]
    if isinstance(total, dict):
        total = total["value"]
    if total != len(hits):
        raise ValueError("Zenodo version list incomplete")
    for record in hits:
        files_by_version.append({"record": record["id"], "doi": record["doi"],
                                 "files": [{"name": f["key"], "bytes": f["size"], "checksum": f["checksum"]} for f in record["files"]]})
    ena = list(csv.DictReader(io.StringIO((cache / "ena-SRP420832.tsv").read_text()), delimiter="\t"))
    sra = sra_inventory((cache / "sra-entire-project.xml").read_text())
    if {r["run_accession"] for r in ena} != {r["run"] for r in sra["runs"]}:
        raise ValueError("independent ENA/SRA run inventories disagree")
    if len(ena) != len({r["run_accession"] for r in ena}):
        raise ValueError("duplicated ENA runs would inflate file sizes")
    sra_search = ET.fromstring((cache / "sra-project-search.xml").read_text())
    if int(sra_search.findtext("Count", "-1")) != sra["experiment_count"]:
        raise ValueError("SRA search and fetched experiment counts disagree")
    ena_whole = {sample: sum(int(value) for row in ena
                            if row["library_name"] == sample
                            for value in row["fastq_bytes"].split(";") if value)
                 for sample in sorted(WHOLE_BODY)}
    files = []
    def walk(value):
        if isinstance(value, dict):
            if {"path", "size", "type"} <= value.keys() and value["type"] == "file":
                files.append({"path": value["path"], "bytes": value["size"]})
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(read_json(cache / "biostudies-S-EPMC12036604.json"))
    return {
        "schema": "cx004-recovery-inventory/v1",
        "scope": "Metadata/file inventories only; completeness applies to these returned resources, not every public repository.",
        "github": {"head": commits[0]["sha"], "history": history,
                   "branches": [r["name"] for r in read_json(cache / "github-branches.json")],
                   "tags": read_json(cache / "github-tags.json"),
                   "releases": read_json(cache / "github-releases.json"),
                   "forks": read_json(cache / "github-forks.json"),
                   "issues": read_json(cache / "github-issues.json")},
        "zenodo": {"versions": files_by_version, "latest": read_json(cache / "zenodo-latest.json")["id"]},
        "geo": geo_files((cache / "geo-filelist.txt").read_text()),
        "sra": sra,
        "ena_matches_sra_run_set": True,
        "ena_whole_body_fastq_bytes_by_geo_sample": ena_whole,
        "ena_whole_body_fastq_bytes": sum(ena_whole.values()),
        "biostudies_supplements": files,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=ROOT / "inventory-sources")
    parser.add_argument("--output", type=Path, default=ROOT / "INVENTORY.json")
    args = parser.parse_args()
    args.output.write_text(json.JSONEncoder(indent=2, sort_keys=True).encode(build(args.cache)) + "\n")
    print("PASS: metadata inventories rebuilt; no expression outcomes computed")


if __name__ == "__main__":
    main()
