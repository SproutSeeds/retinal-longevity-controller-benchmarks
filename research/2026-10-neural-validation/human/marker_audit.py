#!/usr/bin/env python3
"""Source-pinned, post hoc decomposition; independent standard-library replay."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

HERE = Path(__file__).resolve().parent
PRIOR_CANDIDATES = [HERE.parent.parent / "cx004-independent-comparator-2026-10-18",
                    HERE.parent.parent / "2026-10-independent-comparator"]
PRIOR = next((path for path in PRIOR_CANDIDATES if path.is_dir()), PRIOR_CANDIDATES[0])


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def check_hash(path, expected):
    actual = sha(path)
    if actual != expected:
        raise ValueError(f"Checksum mismatch: {path.name}")
    return actual


def read_counts(path):
    with gzip.open(path, "rt") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        columns = header[1:]
        if len(set(columns)) != len(columns):
            raise ValueError("Duplicate column")
        rows = {}
        for row in reader:
            gene = re.sub(r"\.\d+$", "", row[0])
            if not gene or gene in rows:
                raise ValueError("Duplicate/missing feature ID after suffix removal")
            values = [float(value) for value in row[1:]]
            if len(values) != len(columns) or any(not math.isfinite(v) or v < 0 for v in values):
                raise ValueError("Invalid count values")
            rows[gene] = values
    if any(sum(values[j] for values in rows.values()) <= 0 for j in range(len(columns))):
        raise ValueError("Empty library")
    return columns, rows


def validate_samples(text, columns):
    manifest = []
    for chunk in text.split("^SAMPLE = ")[1:]:
        lines = chunk.splitlines()
        fields = {}
        for line in lines[1:]:
            if line.startswith("!Sample_") and " = " in line:
                name, value = line[len("!Sample_"):].split(" = ", 1)
                fields.setdefault(name, []).append(value)
        aliases = [v.split(": ", 1)[1] for v in fields.get("description", [])
                   if v.startswith("Column name in raw_counts_matrix.csv: ")]
        if len(aliases) != 1:
            raise ValueError("Missing/ambiguous sample column declaration")
        match = re.fullmatch(r"(OSK|O4YRSK)_([04])D_([12])", aliases[0])
        if not match:
            raise ValueError("Unadmitted sample alias")
        construct, day, rep = match.groups()
        condition = "dox" if day == "4" else "no dox"
        title = f"{construct}, {condition}, 4 days, rep{rep}"
        if fields.get("title") != [title] or fields.get("organism_ch1") != ["Homo sapiens"]:
            raise ValueError("Incompatible title/species")
        chars = fields.get("characteristics_ch1", [])
        if "cell line: GM00731" not in chars or f"treatment: {construct}, {condition}, 4 days" not in chars:
            raise ValueError("Incompatible donor/treatment")
        manifest.append({"accession": lines[0].strip(), "title": title,
                         "column": f"{construct}_D{day}_{rep}", "construct": construct,
                         "condition": condition, "donor": "GM00731"})
    if len(manifest) != 8 or len(set(columns)) != 8 or sorted(row["column"] for row in manifest) != sorted(columns):
        raise ValueError("Expected one-to-one eight-library sample join")
    return sorted(manifest, key=lambda row: row["accession"])


def approved_map(path, symbols):
    found = {symbol: [] for symbol in symbols}
    with path.open() as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            if row["symbol"] in found and row["status"] == "Approved":
                found[row["symbol"]].append(row["ensembl_gene_id"])
    if any(len(values) != 1 or not re.fullmatch(r"ENSG\d+", values[0]) for values in found.values()):
        raise ValueError("Missing/ambiguous HGNC mapping")
    result = {symbol: values[0] for symbol, values in found.items()}
    if len(set(result.values())) != len(result):
        raise ValueError("Many-to-one panel mapping")
    return result


def geomean(values):
    if not values or any(value <= 0 for value in values):
        raise ValueError("Geometric mean requires positive values")
    return math.exp(statistics.fmean(math.log(value) for value in values))


def zero_anchored_ranks(values):
    if not values or any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("Ranks require nonnegative finite values")
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    z = sum(value == 0 for value in values)
    if z == n:
        return [0.0] * n
    zero_rank = (z + 1) / 2 if z else 0.0
    result = [0.0] * n
    i = z
    while i < n:
        stop = i + 1
        while stop < n and values[order[stop]] == values[order[i]]:
            stop += 1
        mean_rank = ((i + 1) + stop) / 2
        for index in order[i:stop]:
            result[index] = (mean_rank - zero_rank) / (n - zero_rank)
        i = stop
    return result


def transforms(rows, top_k):
    genes = sorted(rows)
    n = len(next(iter(rows.values())))
    totals = [sum(rows[g][j] for g in genes) for j in range(n)]
    positive = [rows[g] for g in genes if all(v > 0 for v in rows[g])]
    if not positive:
        raise ValueError("No all-positive rows for median ratio")
    positive_geomeans = [geomean(row) for row in positive]
    factors = [statistics.median(row[j] / gm for row, gm in zip(positive, positive_geomeans)) for j in range(n)]
    center = geomean(factors)
    factors = [value / center for value in factors]
    geometric_depth = geomean(totals)
    depths = {"log2_cpm": totals,
              "log2_median_ratio_cpm_equivalent": [factor * geometric_depth for factor in factors]}
    mean_cpm = {g: statistics.fmean(rows[g][j] / totals[j] * 1e6 for j in range(n)) for g in genes}
    abundance_order = sorted(genes, key=lambda g: (-mean_cpm[g], g))
    exclusions = {}
    for k in top_k:
        if not 0 < k < len(genes):
            raise ValueError("Top-k must leave features in the denominator")
        excluded = set(abundance_order[:k])
        trimmed = [sum(rows[g][j] for g in genes if g not in excluded) for j in range(n)]
        scale = geometric_depth / geomean(trimmed)
        name = f"log2_top{k}_excluded_cpm_equivalent"
        depths[name] = [value * scale for value in trimmed]
        exclusions[name] = {"excluded_features": sorted(excluded),
                            "excluded_fraction": [1 - t / l for t, l in zip(trimmed, totals)],
                            "effective_depth": depths[name]}
    result = {name: {g: [math.log2(1 + count / depth * 1e6) for count, depth in zip(rows[g], ds)] for g in genes}
              for name, ds in depths.items()}
    rank_columns = [zero_anchored_ranks([rows[g][j] for g in genes]) for j in range(n)]
    result["within_library_zero_anchored_midrank"] = {
        g: [rank_columns[j][i] for j in range(n)] for i, g in enumerate(genes)}
    return result, {"library_depths": totals, "median_ratio_size_factors": factors,
                    "median_ratio_positive_genes": len(positive), "top_abundance_exclusions": exclusions}


def mean_difference(values, treated, controls):
    return statistics.fmean(values[i] for i in treated) - statistics.fmean(values[i] for i in controls)


def decompose(values, treated, controls):
    genes = list(values)
    n = len(genes)
    if n < 2:
        raise ValueError("Decomposition requires at least two genes")
    scores = [statistics.fmean(values[g][j] for g in genes) for j in range(len(next(iter(values.values()))))]
    effect = mean_difference(scores, treated, controls)
    deltas = {g: mean_difference(values[g], treated, controls) for g in genes}
    signed_total = sum(deltas.values())
    absolute_total = sum(abs(value) for value in deltas.values())
    details = []
    for gene in genes:
        omitted_scores = [statistics.fmean(values[g][j] for g in genes if g != gene) for j in range(len(scores))]
        omitted_effect = mean_difference(omitted_scores, treated, controls)
        pairs = [omitted_scores[t] - omitted_scores[c] for t in treated for c in controls]
        details.append({"gene": gene, "gene_delta": deltas[gene],
                        "additive_contribution": deltas[gene] / n,
                        "signed_share": deltas[gene] / signed_total if signed_total else None,
                        "absolute_share": abs(deltas[gene]) / absolute_total if absolute_total else None,
                        "omission_effect": omitted_effect,
                        "omission_four_library_differences": pairs,
                        "omission_preserves_full_mean_sign": omitted_effect * effect > 0,
                        "omission_retained_magnitude": abs(omitted_effect / effect) if effect else None})
    return {"panel_size": n, "mean_difference": effect, "library_scores": scores,
            "four_library_differences": [scores[t] - scores[c] for t in treated for c in controls],
            "gene_details": details,
            "contribution_sum_minus_panel_effect": sum(row["additive_contribution"] for row in details) - effect}


def write_csv(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build(cache, output, prior_path=None):
    prior_path = Path(prior_path) if prior_path is not None else PRIOR
    contract = json.loads((HERE / "posthoc-contract.json").read_text())
    immutable = {name: check_hash(prior_path / name, expected) for name, expected in contract["prior_sha256"].items()}
    sources = {row["id"]: row for row in json.loads((prior_path / "input-files.json").read_text())["sources"]}
    source_hashes = {name: check_hash(cache / name, sources[name]["expected_sha256"]) for name in contract["required_sources"]}
    prior = json.loads((prior_path / "human-results.json").read_text())
    columns, raw = read_counts(cache / "GSE297233_raw_counts_matrix.csv.gz")
    manifest = validate_samples((cache / "GSE297233-samples.txt").read_text(), columns)
    all_panels = json.loads((prior_path / "panels.json").read_text())
    panels = {name: all_panels[name] for name in ["fibroblast_identity", "cycle_panel", "stress_panel", "reprogramming_state"]}
    panels["reprogramming_without_OSK_overlap"] = [g for g in panels["reprogramming_state"] if g not in {"POU5F1", "SOX2"}]
    symbols = sorted({g for panel in panels.values() for g in panel})
    mapping = approved_map(cache / "hgnc_complete_set.txt", symbols)
    if any(gene_id not in raw for gene_id in mapping.values()):
        raise ValueError("Previously present panel feature is missing")
    if any(prior["gene_map"][g]["ensembl_gene_id"] != gene_id for g, gene_id in mapping.items()):
        raise ValueError("Original gene mapping differs")
    transformed, normalization = transforms(raw, contract["normalizations"]["top_k"])
    gene_values = {method: {g: {column: values[mapping[g]][i] for i, column in enumerate(columns)} for g in symbols}
                   for method, values in transformed.items()}
    replay_errors = [abs(gene_values[m][g][c] - value)
                     for m, values in prior["gene_values"].items()
                     for g, by_column in values.items() for c, value in by_column.items()]
    rows, contributions = [], []
    for construct in ["OSK", "O4YRSK"]:
        treated = [columns.index(r["column"]) for r in manifest if r["construct"] == construct and r["condition"] == "dox"]
        controls = [columns.index(r["column"]) for r in manifest if r["construct"] == construct and r["condition"] == "no dox"]
        for panel, genes in panels.items():
            for method, values in transformed.items():
                result = decompose({g: values[mapping[g]] for g in genes}, treated, controls)
                rows.append({"construct": construct, "panel": panel, "method": method, **result})
                for detail in result["gene_details"]:
                    contributions.append({"construct": construct, "panel": panel, "method": method,
                                          "panel_size": len(genes), "full_panel_effect": result["mean_difference"],
                                          **{k: v for k, v in detail.items() if k != "omission_four_library_differences"}})
                original = next(row for row in prior["contrasts"] if row["construct"] == construct and row["panel"] == panel)
                if method in original["methods"]:
                    replay_errors.append(abs(result["mean_difference"] - original["methods"][method]["mean_difference"]))
                    replay_errors.extend(abs(d["omission_effect"] - original["methods"][method]["single_gene_omission_differences"][d["gene"]]) for d in result["gene_details"])
    if max(replay_errors) > 1e-10:
        raise ValueError("Original arithmetic replay mismatch")
    availability = [{"gene": g, "ensembl_gene_id": mapping[g], "present_in_matrix": True,
                     "detected_libraries": sum(v > 0 for v in raw[mapping[g]]),
                     "all_zero_observed_counts": all(v == 0 for v in raw[mapping[g]]),
                     "raw_count_sum": sum(raw[mapping[g]]),
                     **dict(zip(columns, raw[mapping[g]]))} for g in symbols]
    for value in normalization["top_abundance_exclusions"].values():
        value["excluded_panel_genes"] = sorted(g for g in symbols if mapping[g] in value["excluded_features"])
    output.mkdir(parents=True, exist_ok=True)
    result = {"contract_id": contract["id"], "contract_sha256": sha(HERE / "posthoc-contract.json"),
              "analysis_sha256": sha(HERE / "marker_audit.py"), "claim_level": "Heuristic",
              "computation_level": "Verified", "evidence_class": "derived_observed_posthoc",
              "source_hashes": source_hashes, "immutable_prior_hashes": immutable,
              "source_study": contract["source_study"], "rows": len(raw), "library_order": columns,
              "independent_donors": 1, "sample_manifest": manifest,
              "original_replay_max_absolute_error": max(replay_errors),
              "normalization": normalization, "availability": availability,
              "gene_values": gene_values, "contrasts": rows,
              "authority": "Observed marker expression and score-decomposition diagnostics; no calibrated cell-state, age, safety or recovery classification.",
              "readouts": {f"CX004-R0{i}": "insufficient_signal" for i in range(1, 5)}}
    save(output / "marker-audit.json", result)
    write_csv(output / "gene-contributions.csv", contributions)
    write_csv(output / "gene-availability.csv", availability)
    for name, expected in immutable.items():
        check_hash(prior_path / name, expected)
    print(f"PASS: {len(raw)} features, {len(columns)} libraries, {len(rows)} panel/normalization contrasts; replay error {max(replay_errors):.3g}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=Path("/tmp/cx004-independent-comparator-2026-10-18"))
    parser.add_argument("--prior", type=Path, default=PRIOR)
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    build(args.cache, args.output, args.prior)
