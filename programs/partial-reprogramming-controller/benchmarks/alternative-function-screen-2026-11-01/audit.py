#!/usr/bin/env python3
"""Reproduce the bounded Sturm RNA/physiology source admission, offline.

Reads original sources as data. Preserves signed source values and source sample
identities. Performs no molecular/function association or effect calculation.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCES = HERE.parents[1] / ".data/alternative-function-screen-2026-11-01"
FUNCTION = "Oxidative_spare_capacity_UpmolO2_per_min_per_20kcells"
UNIT = "pmol_O2_per_min_per_20000_cells"
CONTEXT = {
    "cell_line": "Cell_line", "unique_variable_name": "Unique_variable_name",
    "inhouse_cell_line_name": "Cell_line_inhouse", "study_part": "Study_part",
    "rnaseq_sampleid": "RNAseq_sampleID", "percent_oxygen": "Percent_oxygen",
    "passage": "Passage", "treatments": "Treatments", "Sex": "Sex",
    "donor_age": "Donor_age", "replicate_line": "Replicate_line",
}
MATCH_FIELDS = ["gsm", "rna_column", "rna_id", "study_sample_id", "culture_record",
                "donor", "donor_age_years", "study_phase", "replicate_line",
                "treatment", "percent_oxygen", "collection_date", "collection_time",
                "passage", "days_grown_source", "seahorse_run", "function_value_source",
                "function_units", "function_present", "admitted", "reason"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(obj):
    return json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n"


def unique(rows, key):
    result = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            raise ValueError("Missing or duplicated " + key + ": " + value)
        result[value] = row
    return result


def table(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("Duplicate CSV column")
        rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError("Malformed CSV row")
    return rows


def geo_samples(path):
    result = []
    for block in re.split(r"(?=\^SAMPLE = )", path.read_text(encoding="utf-8")):
        if not block.startswith("^SAMPLE = "):
            continue
        lines = block.splitlines()
        sample = {"gsm": lines[0].split(" = ", 1)[1], "attributes": {}}
        for line in lines:
            if line.startswith("!Sample_characteristics_ch1 = "):
                key, value = line.split(" = ", 1)[1].split(": ", 1)
                if key in sample["attributes"]:
                    raise ValueError("Duplicate GEO characteristic: " + key)
                sample["attributes"][key] = value
            for prefix, key in [("!Sample_description = ", "description"),
                                ("!Sample_title = ", "title"),
                                ("!Sample_organism_ch1 = ", "organism")]:
                if line.startswith(prefix):
                    sample[key] = line[len(prefix):]
        result.append(sample)
    unique(result, "gsm")
    unique([s["attributes"] for s in result], "rnaseq_sampleid")
    return result


def finite(value):
    try:
        return math.isfinite(float(value))
    except (ValueError, TypeError):
        return False


def local_time(value):
    # Source labels use both 9:00 and 09:00:00; preserve local clock meaning.
    pattern = "%H:%M:%S" if value.count(":") == 2 else "%H:%M"
    return datetime.strptime(value, pattern).time()


def conflicts(sample, author):
    attributes = sample["attributes"]
    issues = []
    for geo_key, author_key in CONTEXT.items():
        g, a = attributes.get(geo_key, ""), author.get(author_key, "")
        if not g or not a or g == "NA" or a == "NA":
            issues.append(geo_key + ":missing")
        elif g != a:
            issues.append(geo_key + ":different")
    if sample.get("organism") != "Homo sapiens":
        issues.append("species:outside_scope")
    try:
        if attributes["date_of_passage"] != datetime.strptime(author["Date_of_Passage"], "%m/%d/%y").date().isoformat():
            issues.append("collection_date:different")
        if local_time(attributes["time_of_passage"]) != local_time(author["Time_of_Passage"]):
            issues.append("collection_time:different")
    except (KeyError, ValueError):
        issues.append("collection_date_or_time:missing")
    try:
        # Consistency check after an exact source-ID join, never nearest-time matching.
        delta = abs(Decimal(attributes["days_grown_udays"]) - Decimal(author["Days_grown_Udays"]))
        if not delta.is_finite() or delta > Decimal("0.0051"):
            issues.append("days_grown:incompatible_source_precision")
    except (KeyError, InvalidOperation):
        issues.append("days_grown:missing")
    if sample.get("description") != "Sample_" + attributes["rnaseq_sampleid"]:
        issues.append("rna_column:unverified_source_label")
    return issues


def target_scope(sample, author):
    g = sample["attributes"]
    return (g.get("cell_line") in {"HC1", "HC2"}
            and g.get("donor_age") == author.get("Donor_age") == "18"
            and g.get("study_part") == author.get("Study_part") == "2"
            and g.get("treatments") == author.get("Treatments") == "Control"
            and g.get("percent_oxygen") == author.get("Percent_oxygen") == "21")


def inspect_matrix(path, expected_columns):
    with gzip.open(path, "rt", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        columns = header[1:]
        if len(columns) != len(set(columns)) or set(columns) != set(expected_columns):
            raise ValueError("RNA matrix columns do not match the exact GEO descriptions")
        genes = set()
        values = 0
        for line, row in enumerate(reader, 2):
            if len(row) != len(header) or not row[0] or row[0] in genes:
                raise ValueError("Malformed, blank or repeated gene label at row " + str(line))
            genes.add(row[0])
            if not all(finite(v) for v in row[1:]):
                raise ValueError("Non-finite or non-numeric expression at row " + str(line))
            values += len(columns)
    return {"gene_rows": len(genes), "sample_columns": len(columns),
            "finite_expression_values": values, "nonfinite_values": 0,
            "gene_labels_unique": True, "blank_gene_labels": 0,
            "source_transform": "Investigator-provided log2 VST normalized expression; preserved without renormalization",
            "column_identity": "Exact GEO Sample_description labels; source order is not a pairing rule",
            "gzip_crc": "PASS"}


def tsv(rows, fields):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def build(sources):
    manifest = json.loads((HERE / "SOURCE_MANIFEST.json").read_text())
    for name, expected in manifest["files"].items():
        data = (sources / name).read_bytes()
        if len(data) != expected["bytes"] or sha(data) != expected["sha256"]:
            raise ValueError("Pinned source changed: " + name)
        if expected.get("md5") and hashlib.md5(data).hexdigest() != expected["md5"]:
            raise ValueError("Repository MD5 mismatch: " + name)
    samples = geo_samples(sources / "GSE179848-family.txt")
    current = unique(table(sources / "sturm-current-author-export.csv"), "Sample")
    stable = unique(table(sources / "Lifespan_Study_Data.csv"), "Sample")
    if set(current) != set(stable):
        raise ValueError("Author export study-sample rosters differ")
    matrix = inspect_matrix(sources / "GSE179848_processed_cell_lifespan_RNAseq_data.csv.gz",
                            [s["description"] for s in samples])
    audit, eligible = [], []
    for sample in samples:
        g = sample["attributes"]
        sample_id = g["study_sample_id"]
        if sample_id not in current:
            raise ValueError("GEO study-sample ID absent from author table")
        author = current[sample_id]
        issues = conflicts(sample, author)
        scoped = target_scope(sample, author)
        value = author[FUNCTION]
        present = finite(value)
        if scoped:
            prior = stable[sample_id]
            if prior["Replicate_Line"] != author["Replicate_line"]:
                issues.append("stable_export_replicate:different")
            if prior["Oxidative_Spare_Capacity"] != value:
                issues.append("stable_export_function:different")
            if prior["Seahorse_Run_Number"] != author["Seahorse_run_number"]:
                issues.append("stable_export_assay_id:different")
            if value.strip() not in {"", "NA"} and not present:
                issues.append("function_value:nonfinite_or_invalid")
        admitted = scoped and not issues and present and bool(author["Seahorse_run_number"])
        reason = ("admitted_source_record" if admitted else
                  "context_unresolved" if scoped and issues else
                  "missing_function" if scoped else "outside_bounded_untreated_adult_cohort")
        audit.append({"gsm": sample["gsm"], "rna_column": sample.get("description", ""),
                      "study_sample_id": sample_id, "donor": g.get("cell_line", ""),
                      "in_target_scope": str(scoped).lower(),
                      "context_issues": ";".join(issues), "admitted": str(admitted).lower(),
                      "reason": reason})
        if scoped:
            eligible.append({
                "gsm": sample["gsm"], "rna_column": sample["description"],
                "rna_id": g["rnaseq_sampleid"], "study_sample_id": sample_id,
                "culture_record": author["Unique_variable_name"], "donor": author["Cell_line"],
                "donor_age_years": author["Donor_age"], "study_phase": author["Study_part"],
                "replicate_line": author["Replicate_line"], "treatment": author["Treatments"],
                "percent_oxygen": author["Percent_oxygen"],
                "collection_date": g.get("date_of_passage", ""),
                "collection_time": g.get("time_of_passage", ""), "passage": author["Passage"],
                "days_grown_source": author["Days_grown_Udays"],
                "seahorse_run": author["Seahorse_run_number"], "function_value_source": value,
                "function_units": UNIT, "function_present": str(present).lower(),
                "admitted": str(admitted).lower(), "reason": reason})
    matched = [r for r in eligible if r["admitted"] == "true"]
    unique(matched, "rna_column")
    unique(matched, "study_sample_id")
    summary = {"schema": "controller.alternative-source-admission/1",
               "claim_level": "Verified source matching and bounded input availability",
               "candidate": "STURM2022", "disposition": "source_complete_for_separate_comparator",
               "source_GEO_RNA_records": len(samples), "author_table_rows": len(current),
               "eligible_untreated_adult_records": len(eligible), "matched_RNA_physiology_records": len(matched),
               "records_missing_function": sum(r["reason"] == "missing_function" for r in eligible),
               "donor_record_counts": dict(sorted(Counter(r["donor"] for r in matched).items())),
               "independent_donors": len(set(r["donor"] for r in matched)),
               "donor_age_years": [18], "cross_source_context_issue_records": sum(bool(r["context_issues"]) for r in audit),
               "link_scope": "Author-integrated culture/passage records and seeded assay aliquots; no same-cell continuity",
               "functional_readout": "Investigator-reported oxidative spare respiratory capacity, normalized to cell number; summary values, not raw well replication",
               "functional_units": UNIT, "RNA_age_clock_admitted": False,
               "outcome_analysis_executed": False, "rejuvenation_intervention": False,
               "Gill_joint_admissions": 0, "Phase_483": "Unchanged; real supervised external exchange required"}
    return {"MATRIX_QC.json": encode(matrix), "ADMISSION.json": encode(summary),
            "rna-link-audit.tsv": tsv(audit, list(audit[0])),
            "eligible-untreated-records.tsv": tsv(eligible, MATCH_FIELDS),
            "matched-records.tsv": tsv(matched, MATCH_FIELDS)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        outputs = build(args.sources)
        for name, content in outputs.items():
            if args.write:
                (HERE / name).write_text(content, encoding="utf-8")
            elif (HERE / name).read_text(encoding="utf-8") != content:
                raise ValueError("Derived source audit differs: " + name)
        print("PASS source replay: 345 RNA records; 22 eligible adult control records; 21 paired source records; two donors; no outcome analysis.")
        return 0
    except FileNotFoundError as error:
        print("INCONCLUSIVE: " + str(error))
        return 2
    except (ValueError, KeyError, OSError, EOFError) as error:
        print("FAIL: " + str(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())
