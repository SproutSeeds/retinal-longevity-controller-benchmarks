#!/usr/bin/env python3
"""Independently read back the 21 observations; imports no admission functions."""
import argparse
import csv
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", required=True, type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    with (here / "matched-records.tsv").open(newline="") as handle:
        released = list(csv.DictReader(handle, delimiter="\t"))
    with (args.sources / "sturm-current-author-export.csv").open(newline="") as handle:
        current = {r["Sample"]: r for r in csv.DictReader(handle)}
    with (args.sources / "Lifespan_Study_Data.csv").open(newline="") as handle:
        stable = {r["Sample"]: r for r in csv.DictReader(handle)}
    text = (args.sources / "GSE179848-family.txt").read_text()
    geo = {}
    for block in re.split(r"(?=\^SAMPLE = )", text):
        if not block.startswith("^SAMPLE = "):
            continue
        lines = block.splitlines()
        gsm = lines[0].split(" = ", 1)[1]
        attributes = {}
        for line in lines:
            if line.startswith("!Sample_characteristics_ch1 = "):
                key, value = line.split(" = ", 1)[1].split(": ", 1)
                attributes[key] = value
        geo[gsm] = attributes
    assert len(released) == 21
    assert len({r["gsm"] for r in released}) == len({r["study_sample_id"] for r in released}) == 21
    for row in released:
        cur, old, g = current[row["study_sample_id"]], stable[row["study_sample_id"]], geo[row["gsm"]]
        assert g["study_sample_id"] == row["study_sample_id"]
        assert g["rnaseq_sampleid"] == row["rna_id"] == cur["RNAseq_sampleID"]
        assert row["rna_column"] == "Sample_" + g["rnaseq_sampleid"]
        assert row["function_value_source"] == cur["Oxidative_spare_capacity_UpmolO2_per_min_per_20kcells"] == old["Oxidative_Spare_Capacity"]
        assert row["seahorse_run"] == cur["Seahorse_run_number"] == old["Seahorse_Run_Number"]
        assert row["donor"] == g["cell_line"] == cur["Cell_line"]
        assert row["culture_record"] == g["unique_variable_name"] == cur["Unique_variable_name"]
        assert row["passage"] == g["passage"] == cur["Passage"]
        assert row["treatment"] == cur["Treatments"] == g["treatments"] == "Control"
        assert row["study_phase"] == cur["Study_part"] == g["study_part"] == "2"
        assert row["donor_age_years"] == cur["Donor_age"] == g["donor_age"] == "18"
    assert "372" not in {r["study_sample_id"] for r in released}
    print("PASS independent read-back: 21 source observations; zero changed physiological values or study/RNA identifiers; no effects calculated.")


if __name__ == "__main__":
    main()
