#!/usr/bin/env python3
"""Verify released intake artifacts and meaningful rejection tests, offline."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def main():
    manifest = json.loads((HERE / "ARTIFACT_MANIFEST.json").read_text())
    for name, expected in manifest["files"].items():
        if Path(name).name != name or hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Released artifact changed: " + name)
    freeze = json.loads((HERE / "SCREEN_FREEZE.json").read_text())
    if hashlib.sha256((HERE / "SCREEN_CONTRACT.json").read_bytes()).hexdigest() != freeze["contract_sha256"]:
        raise ValueError("Screen contract changed")
    for name, expected in freeze["protected_dependencies"].items():
        if hashlib.sha256((HERE.parent / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Prior dependency changed: " + name)
    with (HERE / "matched-records.tsv").open(newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 21 or len({r["rna_column"] for r in rows}) != 21 or len({r["study_sample_id"] for r in rows}) != 21:
        raise ValueError("Matched source coverage differs")
    if {r["donor"] for r in rows} != {"HC1", "HC2"} or any(r["donor_age_years"] != "18" for r in rows):
        raise ValueError("Adult donor scope differs")
    if any(r["study_phase"] != "2" or r["treatment"] != "Control" or r["percent_oxygen"] != "21" for r in rows):
        raise ValueError("Untreated culture context differs")
    admission = json.loads((HERE / "ADMISSION.json").read_text())
    if admission["outcome_analysis_executed"] or admission["rejuvenation_intervention"] or admission["Gill_joint_admissions"]:
        raise ValueError("Source admission promoted into an intervention result")
    result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_audit.py"], text=True, capture_output=True)
    if result.returncode:
        raise ValueError(result.stdout + result.stderr)
    print(result.stderr.strip())
    print("PASS offline intake: 21 source-matched RNA/physiology records; two donors; no biological outcome analysis. Full source replay: python3 audit.py --sources /path/to/originals")


if __name__ == "__main__":
    main()
