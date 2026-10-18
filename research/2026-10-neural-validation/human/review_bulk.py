#!/usr/bin/env python3
"""Independent standard-library numerical review of the adjacent bulk packet.

Reads the bulk artifacts and their already cached source; writes only this
human lane's review receipt. Does not rerun the bulk implementation or alter it.
"""
import csv
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import statistics

HERE = Path(__file__).resolve().parent
BULK = HERE.parent / "bulk"


def read(name):
    return json.loads((BULK / name).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def avg(values):
    return statistics.fmean(values)


def geometric(values):
    return math.exp(avg([math.log(v) for v in values]))


def normalized_ranks(values):
    indexed = sorted(enumerate(values), key=lambda pair: pair[1])
    ranks = [0.0] * len(values)
    position = 0
    for _, tied in itertools.groupby(indexed, key=lambda pair: pair[1]):
        members = list(tied)
        rank = (position + (len(members) - 1) / 2) / (len(values) - 1)
        for original, _ in members:
            ranks[original] = rank
        position += len(members)
    return ranks


def age_delta(delta, old):
    return avg([v for v, flag in zip(delta, old) if flag]) - avg([v for v, flag in zip(delta, old) if not flag])


def age_p(delta, old):
    observed = age_delta(delta, old)
    distribution = [abs(age_delta(delta, [i in group for i in range(len(delta))]))
                    for group in itertools.combinations(range(len(delta)), sum(old))]
    count = sum(value >= abs(observed) - 1e-12 * max(1, abs(observed)) for value in distribution)
    return observed, count, len(distribution)


def sign_p(delta):
    positive = sum(v > 1e-12 for v in delta)
    negative = sum(v < -1e-12 for v in delta)
    n = positive + negative
    return min(1, 2 * sum(math.comb(n, k) for k in range(min(positive, negative) + 1)) / 2 ** n)


def adjusted_holm(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    adjusted = [None] * len(values)
    for rank, index in enumerate(order):
        adjusted[index] = min(1, max((len(values) - j) * values[order[j]] for j in range(rank + 1)))
    return adjusted


def main():
    results, admission, panels, freeze = read("results.json"), read("admission.json"), read("panels.json"), read("FREEZE.json")
    contract = read("contract.json")
    source = read("count-source-receipt.json")
    raw_path = Path(source["cache_path"])
    if sha(raw_path) != source["sha256"]:
        raise ValueError("Bulk cached source changed")
    for name, field in [("contract.json", "contract_sha256"), ("admission.json", "admission_sha256"),
                        ("panels.json", "panels_sha256"), ("analyze.py", "analysis_sha256")]:
        if sha(BULK / name) != freeze[field]:
            raise ValueError("Bulk frozen artifact changed: " + name)
    pairs = admission["pairs"]
    old = [p["age_group"] == "old" for p in pairs]
    selected = [p[arm + "_count_column"] for p in pairs for arm in ["control", "treated"]]
    data = {}
    with gzip.open(raw_path, "rt") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        indices = [header.index(column) for column in selected]
        for row in reader:
            gene = re.sub(r"\.\d+$", "", row[0]) if row[0].startswith("ENSMUSG") else row[0]
            if gene in data:
                raise ValueError("Duplicate bulk feature")
            data[gene] = [float(row[index]) for index in indices]
    genes = sorted(data)
    totals = [sum(data[g][j] for g in genes) for j in range(18)]
    all_positive = [data[g] for g in genes if all(v > 0 for v in data[g])]
    geometric_features = [geometric(values) for values in all_positive]
    ratios = [statistics.median(row[j] / gm for row, gm in zip(all_positive, geometric_features)) for j in range(18)]
    center = geometric(ratios)
    effective = [r / center * geometric(totals) for r in ratios]
    ranks_by_column = [normalized_ranks([data[g][j] for g in genes]) for j in range(18)]
    rank_lookup = {gene: [ranks_by_column[j][i] for j in range(18)] for i, gene in enumerate(genes)}
    discrepancies = []
    check_count = 0
    errors = []
    reviewed = []
    for row in results["panel_results"]:
        if row["status"] != "available":
            raise ValueError("This review expects the observed fully available packet")
        names = [g["mouse_ensembl_gene"] for g in panels["panels"][row["panel"]]["genes"] if g["status"] == "mapped" and g["mouse_ensembl_gene"] in data]
        if row["method"] == "within_library_rank":
            values = {g: rank_lookup[g] for g in names}
        else:
            depth = totals if row["method"] == "log2_cpm" else effective
            values = {g: [math.log2(1 + v / d * 1e6) for v, d in zip(data[g], depth)] for g in names}
        scores = [avg([values[g][j] for g in names]) for j in range(18)]
        delta = [scores[2*i+1] - scores[2*i] for i in range(9)]
        gene_delta = {g: [values[g][2*i+1] - values[g][2*i] for i in range(9)] for g in names}
        for i, stored in enumerate(row["scores"]):
            errors.extend([abs(scores[2*i] - stored["control"]), abs(scores[2*i+1] - stored["treated"]), abs(delta[i] - stored["delta"])])
        effect, numerator, denominator = age_p(delta, old)
        errors.append(abs(effect - row["age_test"]["signed_effect"]))
        check_count += 2
        if (numerator, denominator) != (row["age_test"]["numerator"], row["age_test"]["denominator"]):
            discrepancies.append(row["method"] + ":" + row["panel"] + ":age_enumeration")
        if not math.isclose(sign_p(delta), row["overall_sign_test"]["p"], abs_tol=1e-14):
            discrepancies.append(row["method"] + ":" + row["panel"] + ":sign_test")
        for contribution in row["gene_contributions"]:
            errors.append(abs(age_delta(gene_delta[contribution["mouse_ensembl_gene"]], old) / len(names) - contribution["age_difference_contribution"]))
        symbol_to_id = {g["mouse_symbol"]: g["mouse_ensembl_gene"] for g in row["coverage"]["present"]}
        for omission in row["gene_omissions"]:
            omitted = symbol_to_id[omission["omitted_mouse_gene"]]
            remaining = [avg([gene_delta[g][i] for g in names if g != omitted]) for i in range(9)]
            errors.append(abs(age_delta(remaining, old) - omission["age_difference"]))
            errors.extend(abs(v - expected) for v, expected in zip(remaining, omission["donor_deltas"]))
        for omission in row.get("donor_omissions", []):
            keep = [i for i, pair in enumerate(pairs) if pair["donor_id"] != omission["omitted_donor"]]
            errors.append(abs(age_delta([delta[i] for i in keep], [old[i] for i in keep]) - omission["age_difference"]))
        reviewed.append({"method": row["method"], "panel": row["panel"], "age_difference": effect,
                         "permutation_numerator": numerator, "permutation_denominator": denominator,
                         "permutation_p": numerator / denominator, "sign_p": sign_p(delta),
                         "gene_omission_age_difference_range": [min(g["age_difference"] for g in row["gene_omissions"]), max(g["age_difference"] for g in row["gene_omissions"])],
                         "all_zero_panel_genes": [g["mouse_symbol"] for g in row["coverage"]["present"] if all(v == 0 for v in data[g["mouse_ensembl_gene"]])]})
    for method in ["log2_cpm", "log2_median_ratio", "within_library_rank"]:
        current = [r for r in reviewed if r["method"] == method]
        stored = [r for r in results["panel_results"] if r["method"] == method]
        for source_field, target in [("permutation_p", "age_test_holm_p"), ("sign_p", "overall_sign_test_holm_p")]:
            calculated = adjusted_holm([r[source_field] for r in current])
            for r, value in zip(stored, calculated):
                check_count += 1
                if not math.isclose(value, r[target], abs_tol=1e-14):
                    discrepancies.append(method + ":" + r["panel"] + ":" + target)
    passed = not discrepancies and max(errors) <= 1e-10
    review = {"status": "PASS" if passed else "FAIL", "claim_level": "Verified numerical reconstruction within admitted metadata; Heuristic effect interpretation",
              "reviewed_artifact_hashes": {name: sha(BULK / name) for name in ["analyze.py", "contract.json", "admission.json", "panels.json", "results.json", "gene-contributions.csv"]},
              "source_sha256": source["sha256"], "source_read_only": True, "bulk_files_modified": False,
              "independent_implementation": "Python standard library; raw counts to all 18 selected library transforms, donor panel scores, exact age enumeration/sign tests, Holm adjustments, gene contributions and gene/donor omissions.",
              "max_absolute_numeric_error": max(errors), "numeric_comparisons": len(errors),
              "exact_test_and_Holm_comparisons": check_count, "discrepancies": discrepancies, "reviewed_rows": reviewed,
              "interpretation_findings": [
                  "All four primary CPM age-response tests have Holm p <= 0.047619 under the stated exchangeability assumption; these are small descriptive differences, not a causal age effect or safety/identity result.",
                  "Cycle scores decrease in all nine donor pairs under every frozen normalization. The old mean decrement is smaller than the young mean decrement; describe the signed response rather than a generic rejuvenation benefit.",
                  "The overlap-excluded reprogramming CPM age difference is dominated by Nanog; removing Nanog changes its sign. Its rank sensitivity has adjusted p=1. This is not broad endogenous-network confirmation.",
                  "Stress age-difference direction reverses under the rank transform, so direction is not invariant across the frozen score definitions.",
                  "Rank includes average ranks for zero ties. Relative ranks are detection/composition dependent and are not an independent measure of absolute RNA or endogenous state.",
                  "Well layout is associated with age/treatment assignments; the frozen caveat correctly calls technical confounding possible rather than proven. The exchangeability-dependent p-values do not eliminate that path."
              ]}
    (HERE / "BULK_REVIEW.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    print(f"{review['status']}: {len(errors)} independent numerical comparisons; max error {max(errors):.3g}; {check_count} exact/adjusted tests")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
