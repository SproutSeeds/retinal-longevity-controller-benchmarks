#!/usr/bin/env python3
"""Replay the frozen, donor-specific panel/respiration description; stdlib only."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent / "alternative-function-screen-2026-11-01"
SOURCE = HERE.parents[1] / ".data/alternative-function-screen-2026-11-01"
MATRIX = "GSE179848_processed_cell_lifespan_RNAseq_data.csv.gz"


def read_json(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_text(value):
    return json.JSONEncoder(indent=2, sort_keys=True, allow_nan=False).encode(value) + "\n"


def table_text(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows({key: "NA" if row.get(key) is None else row[key] for key in fields} for row in rows)
    return stream.getvalue()


def table(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def check_freeze():
    freeze = read_json(HERE / "FREEZE.json")
    for name, expected in [("ANALYSIS_CONTRACT.json", freeze["contract_sha256"]),
                           ("senmayo-human.tsv", freeze["panel_sha256"]),
                           ("REFERENCE_SOURCE.json", freeze["reference_source_sha256"])]:
        if sha(HERE / name) != expected:
            raise ValueError("Frozen input differs: " + name)
    for name, expected in freeze["protected_dependencies"].items():
        if sha(HERE.parent / name) != expected:
            raise ValueError("Prior source admission changed: " + name)


def finite(values):
    if any(not math.isfinite(v) for v in values):
        raise ValueError("Nonfinite analysis input")


def centered(values):
    finite(values)
    mean = math.fsum(values) / len(values)
    return [v - mean for v in values]


def pearson(x, y):
    if len(x) != len(y) or len(x) < 3:
        return None
    a, b = centered(x), centered(y)
    aa, bb = math.fsum(v*v for v in a), math.fsum(v*v for v in b)
    if aa == 0 or bb == 0:
        return None
    return max(-1.0, min(1.0, math.fsum(v*w for v, w in zip(a, b)) / math.sqrt(aa*bb)))


def ranks(values):
    finite(values)
    order = sorted(range(len(values)), key=values.__getitem__)
    output = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        for index in order[start:end]:
            output[index] = (start + 1 + end) / 2
        start = end
    return output


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def residuals(values, covariate):
    if len(values) != len(covariate) or len(values) < 3:
        return None
    v, t = centered(values), centered(covariate)
    tt = math.fsum(a*a for a in t)
    if tt == 0:
        return None
    slope = math.fsum(a*b for a, b in zip(v, t)) / tt
    result = [a - slope*b for a, b in zip(v, t)]
    if math.fsum(a*a for a in result) <= 1e-24 * max(1.0, math.fsum(a*a for a in v)):
        return None
    return result


def adjusted(x, y, covariate):
    a, b = residuals(x, covariate), residuals(y, covariate)
    return None if a is None or b is None else pearson(a, b)


def validate_records(records, paired):
    if len(records) != 22 or len({r["study_sample_id"] for r in records}) != 22 or len({r["rna_column"] for r in records}) != 22:
        raise ValueError("Eligible sample identities differ")
    present = [r for r in records if r["function_present"] == "true"]
    if len(paired) != 21 or {r["study_sample_id"]: r for r in present} != {r["study_sample_id"]: r for r in paired}:
        raise ValueError("Paired-source table differs from eligible records")
    missing = [r for r in records if r["function_present"] != "true"]
    if len(missing) != 1 or (missing[0]["study_sample_id"], missing[0]["rna_column"]) != ("372", "Sample_36"):
        raise ValueError("Missing-function identity differs")
    for row in records:
        if (row["donor"] not in {"HC1", "HC2"} or row["donor_age_years"] != "18"
                or row["study_phase"] != "2" or row["replicate_line"] != "1"
                or row["treatment"] != "Control" or row["percent_oxygen"] != "21"):
            raise ValueError("Donor or culture context differs")


def extract_matrix(path, genes, records):
    expression = {}
    seen = set()
    with gzip.open(path, "rt", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if len(header) != 346 or len(set(header[1:])) != 345:
            raise ValueError("RNA header width or uniqueness differs")
        if not {r["rna_column"] for r in records}.issubset(header[1:]):
            raise ValueError("Required exact RNA column missing")
        columns = {r["rna_column"]: header.index(r["rna_column"]) for r in records}
        for row in reader:
            if len(row) != len(header) or not row[0] or row[0] in seen:
                raise ValueError("Blank/duplicate gene or matrix width mismatch")
            seen.add(row[0])
            if row[0] in genes:
                values = {sample: row[index] for sample, index in columns.items()}
                finite([float(v) for v in values.values()])
                expression[row[0]] = values
    return expression, len(seen)


def interval_rows(records):
    intervals = []
    for donor in ["HC1", "HC2"]:
        series = sorted((r for r in records if r["donor"] == donor), key=lambda r: (r["days"], r["study_sample_id"]))
        for a, b in zip(series, series[1:]):
            elapsed = b["days"] - a["days"]
            if elapsed <= 0:
                raise ValueError("Non-increasing culture time")
            valid = a["function"] is not None and b["function"] is not None
            intervals.append({"donor":donor,"from_study_sample_id":a["study_sample_id"],"to_study_sample_id":b["study_sample_id"],
                              "elapsed_days":elapsed,"score_change_per_day":(b["score"]-a["score"])/elapsed,
                              "function_change_per_day":(b["function"]-a["function"])/elapsed if valid else None,
                              "status":"included" if valid else "missing_function_endpoint"})
    return intervals


def summarize(records):
    intervals = interval_rows(records)
    summaries, leave_out = {}, []
    for donor in ["HC1", "HC2"]:
        all_rows = sorted((r for r in records if r["donor"] == donor), key=lambda r: r["days"])
        rows = [r for r in all_rows if r["function"] is not None]
        if len(rows) < 6:
            raise ValueError("Insufficient paired observations")
        x,y,t,p = [[r[key] for r in rows] for key in ["score","function","days","passage_number"]]
        valid = [r for r in intervals if r["donor"] == donor and r["status"] == "included"]
        for drop in rows:
            kept = [r for r in rows if r["study_sample_id"] != drop["study_sample_id"]]
            a,b,c = [[r[key] for r in kept] for key in ["score","function","days"]]
            leave_out.append({"donor":donor,"excluded_study_sample_id":drop["study_sample_id"],"n":len(kept),"spearman":spearman(a,b),"linear_day_residual_pearson":adjusted(a,b,c)})
        loo = [r for r in leave_out if r["donor"] == donor]
        bounds = lambda key: [min(r[key] for r in loo if r[key] is not None), max(r[key] for r in loo if r[key] is not None)] if any(r[key] is not None for r in loo) else None
        summaries[donor] = {"eligible_records":len(all_rows),"paired_records":len(rows),"first_paired_day":min(t),"last_paired_day":max(t),
            "score_range":[min(x),max(x)],"function_range":[min(y),max(y)],"spearman_score_function":spearman(x,y),
            "linear_day_residual_pearson":adjusted(x,y,t),"linear_passage_residual_pearson":adjusted(x,y,p),
            "spearman_score_day":spearman(x,t),"spearman_function_day":spearman(y,t),"spearman_passage_day":spearman(p,t),
            "eligible_adjacent_intervals":len([r for r in intervals if r["donor"]==donor]),"included_adjacent_intervals":len(valid),
            "adjacent_rate_spearman":spearman([r["score_change_per_day"] for r in valid],[r["function_change_per_day"] for r in valid]) if len(valid)>=4 else None,
            "leave_one_out_spearman_range":bounds("spearman"),"leave_one_out_day_residual_range":bounds("linear_day_residual_pearson")}
    return summaries, intervals, leave_out


def panel_coverage(genes, expression):
    present = [gene for gene in genes if gene in expression]
    return {"reference_genes":125,"available_genes":len(present),"coverage_fraction":len(present)/125,
            "minimum_required":100,"included_genes":present,"absent_genes":[g for g in genes if g not in expression],
            "symbol_matching":"Exact case-sensitive symbols; no aliases or outcome-based selection.","status":"PASS" if len(present)>=100 else "INCONCLUSIVE"}


def products(sources=SOURCE):
    check_freeze()
    metadata = read_json(UPSTREAM / "SOURCE_MANIFEST.json")["files"][MATRIX]
    if sha(sources / MATRIX) != metadata["sha256"]:
        raise ValueError("Original RNA matrix fingerprint changed")
    records, paired = table(UPSTREAM / "eligible-untreated-records.tsv"), table(UPSTREAM / "matched-records.tsv")
    validate_records(records, paired)
    genes = [r["gene_symbol"] for r in table(HERE / "senmayo-human.tsv")]
    if len(genes) != 125 or len(set(genes)) != 125:
        raise ValueError("Expected 125 unique reference genes")
    expression, source_rows = extract_matrix(sources / MATRIX, set(genes), records)
    if source_rows != 28633:
        raise ValueError("Original gene row count changed")
    coverage = panel_coverage(genes, expression)
    present = coverage["included_genes"]
    outputs = {"GENE_COVERAGE.json":json_text(coverage)}
    if len(present)<100:
        outputs["RESULTS.json"] = json_text({"status":"INCONCLUSIVE","reason":"Frozen minimum reference coverage not met","outcome_analysis_executed":False})
        return outputs
    selected = []
    ordered = sorted(records, key=lambda r: (r["donor"],float(r["days_grown_source"])))
    for row in ordered:
        sample = row["rna_column"]
        row["score"] = math.fsum(float(expression[g][sample]) for g in present)/len(present)
        row["days"] = float(row["days_grown_source"])
        row["passage_number"] = float(row["passage"])
        row["function"] = float(row["function_value_source"]) if row["function_present"]=="true" else None
        finite([row["score"],row["days"],row["passage_number"]] + ([] if row["function"] is None else [row["function"]]))
        selected.extend({"gene_symbol":g,"study_sample_id":row["study_sample_id"],"rna_column":sample,"expression_value_source":expression[g][sample]} for g in present)
    summaries, intervals, leave_out = summarize(ordered)
    results = {"schema":"controller.donor-bounded-calibration-results/1","status":"COMPUTED; verification recorded separately","readout_claim_level":"Heuristic","numerical_verification":"See VERIFICATION_RECORD.md and INDEPENDENT_CHECK.json","readout":"Heuristic SenMayo-panel mean expression; not the published GSEA score or a biological-age estimate",
        "available_reference_genes":len(present),"eligible_records":22,"paired_records":21,"independent_donors":2,"donor_age_years":18,
        "outcome_analysis_executed":True,"rejuvenation_intervention":False,"population_inference_performed":False,"Gill_joint_admissions":0,
        "function_units":"pmol O2/min/20,000 cells","donors":summaries,"missing_function_study_sample_id":"372",
        "interpretation_limit":"Secondary descriptive analysis of two untreated culture series. Time adjustment removes only a linear component; no causal, diagnostic, safety, rejuvenation or population conclusion."}
    score_fields = ["study_sample_id","rna_column","gsm","donor","donor_age_years","days_grown_source","passage","score","function_value_source","function_present","function_units"]
    outputs.update({"RESULTS.json":json_text(results),"sample-scores.tsv":table_text(ordered,score_fields),
        "panel-expression-source.tsv":table_text(selected,["gene_symbol","study_sample_id","rna_column","expression_value_source"]),
        "adjacent-changes.tsv":table_text(intervals,["donor","from_study_sample_id","to_study_sample_id","elapsed_days","score_change_per_day","function_change_per_day","status"]),
        "leave-one-out.tsv":table_text(leave_out,["donor","excluded_study_sample_id","n","spearman","linear_day_residual_pearson"])})
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources",type=Path,default=SOURCE)
    parser.add_argument("--write",action="store_true")
    args = parser.parse_args()
    output = products(args.sources)
    for name, value in output.items():
        if args.write:
            (HERE / name).write_text(value)
        elif not (HERE / name).exists() or (HERE / name).read_text() != value:
            raise ValueError("Replay differs: " + name)
    print("PASS frozen analysis %s: %d deterministic output files" % ("write" if args.write else "replay",len(output)))
