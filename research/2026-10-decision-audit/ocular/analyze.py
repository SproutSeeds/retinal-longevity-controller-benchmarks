#!/usr/bin/env python3
"""Frozen, animal-level fixed-panel audit of public GSE276656 matrices.

Only our independently written code is executed. Source matrices stay in a
user-selected cache; aggregate numerical outputs are portable. Marker bins are
heuristic partitions and never reported as validated cell identities.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
FROZEN = ("contract.json", "admission.json", "panels.json", "analyze.py")
ENCODER = json.JSONEncoder(indent=2, sort_keys=True, allow_nan=False)


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, data):
    Path(path).write_text(ENCODER.encode(data) + "\n")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def gate():
    record = read_json(HERE / "FREEZE.json")
    assert record["expression_execution_authorized"] is True
    for name in FROZEN:
        assert record["sha256"][name] == sha(HERE / name), f"Frozen bytes changed: {name}"
    return record


def write_csv(path, rows):
    assert rows, f"No rows for {path}"
    with Path(path).open("w", newline="") as stream:
        w = csv.DictWriter(stream, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def fetch(cache):
    gate()
    admission = read_json(HERE / "admission.json")
    contract = read_json(HERE / "contract.json")
    cache.mkdir(parents=True, exist_ok=True)
    rows = []
    total = sum(x["expected_bytes"] for x in admission["samples"])
    assert total == admission["total_matrix_bytes"]
    assert total <= contract["storage"]["max_total_download_bytes"]
    for s in admission["samples"]:
        path = cache / s["filename"]
        if not path.exists():
            assert shutil.disk_usage(cache).free >= (
                contract["storage"]["min_free_cache_bytes"] + s["expected_bytes"]
            ), "Cache free-space floor would be crossed"
            partial = path.with_suffix(path.suffix + ".partial")
            request = urllib.request.Request(s["url"], headers={"User-Agent": "CX004-research-replay/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as stream:
                received = 0
                while True:
                    block = response.read(4 * 1024 * 1024)
                    if not block:
                        break
                    received += len(block)
                    assert received <= s["expected_bytes"], "Source grew beyond frozen byte count"
                    stream.write(block)
            assert received == s["expected_bytes"], "Incomplete download"
            partial.rename(path)
        assert path.stat().st_size == s["expected_bytes"]
        rows.append({"gsm": s["gsm"], "animal_id": s["animal_id"], "filename": s["filename"],
                     "url": s["url"], "bytes": path.stat().st_size, "sha256": sha(path)})
        print(f"Verified acquisition {s['gsm']} {rows[-1]['bytes']} bytes", flush=True)
    receipt = {"source": "GSE276656", "expected_bytes": total, "files": rows,
               "frozen_hashes": gate()["sha256"], "expression_parsed": False}
    write_json(cache / "acquisition.json", receipt)
    return receipt


def decode(values):
    return [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in values]


def average_ranks(values):
    import numpy as np
    values = np.asarray(values)
    order = np.argsort(values, kind="stable")
    ordered = values[order]
    starts = np.r_[0, np.flatnonzero(ordered[1:] != ordered[:-1]) + 1]
    ends = np.r_[starts[1:], len(values)]
    ranked = np.empty(len(values), dtype=float)
    for start, end in zip(starts, ends):
        ranked[order[start:end]] = (start + end - 1) / 2
    return ranked / (len(values) - 1)


def exact_permutation(values, labels):
    import numpy as np
    values = np.asarray(values, dtype=float)
    labels = np.asarray(labels, dtype=bool)
    n_t = int(labels.sum())
    observed = float(values[labels].mean() - values[~labels].mean())
    tolerance = 1e-12 * max(1.0, abs(observed))
    stats = []
    for choice in itertools.combinations(range(len(values)), n_t):
        selected = np.zeros(len(values), dtype=bool)
        selected[list(choice)] = True
        delta = float(values[selected].mean() - values[~selected].mean())
        stats.append({"treated_indices": ",".join(str(x) for x in choice), "delta": delta,
                      "at_least_observed": abs(delta) >= abs(observed) - tolerance})
    numerator = sum(x["at_least_observed"] for x in stats)
    return observed, numerator, len(stats), stats


def holm(values):
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    adjusted = [1.0] * len(values)
    running = 0.0
    for rank, (original, value) in enumerate(indexed):
        running = max(running, min(1.0, (len(values) - rank) * value))
        adjusted[original] = running
    return adjusted


def marker_partition(selected, marker_indices, threshold):
    import numpy as np
    eligible = np.asarray([(selected[idx] >= threshold).sum(axis=0) >= 2
                           for idx in marker_indices], dtype=bool)
    number = eligible.sum(axis=0)
    labels = np.full(selected.shape[1], len(marker_indices) + 1, dtype=int)
    labels[number > 1] = len(marker_indices)
    single = number == 1
    labels[single] = eligible[:, single].argmax(axis=0)
    return labels


def extract(path, sample, contract, panels):
    """Read CSC blocks without creating a dense cells-by-all-genes matrix."""
    import h5py
    import numpy as np
    with h5py.File(path, "r") as handle:
        m = handle["matrix"]
        types = decode(m["features"]["feature_type"][:])
        raw_ids = decode(m["features"]["id"][:])
        raw_symbols = decode(m["features"]["name"][:])
        gene_rows = np.flatnonzero(np.asarray(types) == "Gene Expression")
        ids = [re.sub(r"\.\d+$", "", raw_ids[x]) for x in gene_rows]
        symbols = [raw_symbols[x] for x in gene_rows]
        assert len(ids) == len(set(ids)), "Duplicate normalized RNA feature identifiers"
        assert len(ids) >= 500
        barcodes = decode(m["barcodes"][:])
        assert len(barcodes) == len(set(barcodes)), "Duplicate barcode inside one animal library"
        n_gene, n_cell = len(gene_rows), len(barcodes)
        shape = tuple(int(x) for x in m["shape"][:])
        assert shape == (len(types), n_cell)
        row_to_gene = np.full(len(types), -1, dtype=int)
        row_to_gene[gene_rows] = np.arange(n_gene)
        mt = np.asarray([s.startswith("mt-") for s in symbols])
        gene_index = {g: i for i, g in enumerate(ids)}
        present_panel = sorted({g["mouse_ensembl_gene"] for p in panels["panels"].values()
                                for g in p["genes"] if g["mouse_ensembl_gene"] in gene_index})
        wanted_indices = [gene_index[g] for g in present_panel]
        wanted_lookup = {g: i for i, g in enumerate(wanted_indices)}
        bins = contract["composition"]["marker_bins"]
        marker_symbols = sorted({s for values in bins.values() for s in values})
        missing_markers = [s for s in marker_symbols if symbols.count(s) != 1]
        marker_gene_indices = [] if missing_markers else [symbols.index(s) for s in marker_symbols]
        marker_positions = [[marker_symbols.index(s) for s in values] for values in bins.values()]
        # Panel and marker matrices contain only fixed genes; these are the only dense cell arrays.
        small_indices = sorted(set(wanted_indices + marker_gene_indices))
        small_to_pos = {g: i for i, g in enumerate(small_indices)}
        sparse_to_small = np.full(n_gene, -1, dtype=int)
        for g, i in small_to_pos.items():
            sparse_to_small[g] = i
        panel_pos = [small_to_pos[g] for g in wanted_indices]
        marker_pos = [small_to_pos[g] for g in marker_gene_indices]
        nbin = len(bins) + 2
        counts = {"qc": np.zeros(n_gene, dtype=np.int64), "all": np.zeros(n_gene, dtype=np.int64)}
        bin_counts = {t: np.zeros((nbin, len(wanted_indices)), dtype=np.int64) for t in (1, 2)}
        bin_depth = {t: np.zeros(nbin, dtype=np.int64) for t in (1, 2)}
        bin_n = {t: np.zeros(nbin, dtype=np.int64) for t in (1, 2)}
        qc_n = 0
        total_by_cell = []
        feature_by_cell = []
        qc_by_cell = []
        failing = {"low_counts": 0, "high_counts": 0, "low_features": 0,
                   "high_features": 0, "mitochondrial": 0}
        pointers = m["indptr"][:]
        assert len(pointers) == n_cell + 1 and pointers[0] == 0
        assert np.all(np.diff(pointers) >= 0)
        assert pointers[-1] == len(m["data"]) == len(m["indices"])
        for first in range(0, n_cell, 256):
            last = min(n_cell, first + 256)
            lo, hi = int(pointers[first]), int(pointers[last])
            raw_rows = m["indices"][lo:hi].astype(np.int64)
            raw_values = m["data"][lo:hi]
            assert np.all(np.isfinite(raw_values)) and np.all(raw_values >= 0)
            assert np.all(raw_values == np.floor(raw_values))
            assert np.all((raw_rows >= 0) & (raw_rows < len(types)))
            cols = np.repeat(np.arange(last - first), np.diff(pointers[first:last + 1]))
            rows = row_to_gene[raw_rows]
            keep = rows >= 0
            rows, cols, data = rows[keep], cols[keep], raw_values[keep].astype(np.int64)
            # Valid 10X CSC must contain no duplicate or unsorted RNA rows within a cell.
            if len(rows) > 1:
                assert np.all((np.diff(cols) > 0) | (np.diff(rows) > 0)), "Noncanonical sparse RNA entries"
            n = last - first
            depth = np.bincount(cols, weights=data, minlength=n).astype(np.int64)
            features = np.bincount(cols[data > 0], minlength=n)
            mt_depth = np.bincount(cols[mt[rows]], weights=data[mt[rows]], minlength=n)
            mt_fraction = np.divide(mt_depth, depth, out=np.ones(n, dtype=float), where=depth > 0)
            qc = (depth > 500) & (depth < 30000) & (features > 200) & (features < 9000) & (mt_fraction < .02)
            for name, test in [("low_counts", depth <= 500), ("high_counts", depth >= 30000),
                               ("low_features", features <= 200), ("high_features", features >= 9000),
                               ("mitochondrial", mt_fraction >= .02)]:
                failing[name] += int(test.sum())
            qc_n += int(qc.sum())
            counts["all"] += np.bincount(rows, weights=data, minlength=n_gene).astype(np.int64)
            use = qc[cols]
            counts["qc"] += np.bincount(rows[use], weights=data[use], minlength=n_gene).astype(np.int64)
            small = np.zeros((len(small_indices), n), dtype=np.int64)
            pos = sparse_to_small[rows]
            picked = pos >= 0
            small[pos[picked], cols[picked]] = data[picked]
            if not missing_markers:
                for threshold in (1, 2):
                    classes = marker_partition(small[marker_pos][:, qc], marker_positions, threshold)
                    selected = small[panel_pos][:, qc]
                    qdepth = depth[qc]
                    for b in range(nbin):
                        which = classes == b
                        bin_n[threshold][b] += int(which.sum())
                        bin_depth[threshold][b] += int(qdepth[which].sum())
                        bin_counts[threshold][b] += selected[:, which].sum(axis=1)
            total_by_cell.extend(depth.tolist())
            feature_by_cell.extend(features.tolist())
            qc_by_cell.extend(qc.tolist())
    qc_depth = [x for x, keep in zip(total_by_cell, qc_by_cell) if keep]
    qc_features = [x for x, keep in zip(feature_by_cell, qc_by_cell) if keep]
    info = {"gsm": sample["gsm"], "animal_id": sample["animal_id"], "group": sample["group"],
            "n_deposited": n_cell, "n_rna_qc": qc_n, "n_rna_features": n_gene,
            "detected_pseudobulk_genes": int((counts["qc"] > 0).sum()),
            "all_rna_umi": int(counts["all"].sum()), "qc_rna_umi": int(counts["qc"].sum()),
            "median_qc_umi": float(np.median(qc_depth)) if qc_depth else None,
            "median_qc_features": float(np.median(qc_features)) if qc_features else None,
            **{f"fail_{k}": v for k, v in failing.items()},
            "primary_qc_eligible": qc_n >= 100 and int((counts["qc"] > 0).sum()) >= 500 and counts["qc"].sum() > 0,
            "marker_partition_available": not missing_markers,
            "missing_marker_symbols": ";".join(missing_markers)}
    return {"ids": ids, "symbols": symbols, "counts": counts, "qc": info, "bin_n": bin_n,
            "bin_counts": bin_counts, "bin_depth": bin_depth, "bin_panel_ids": present_panel}


def run(cache, output):
    freeze = gate()
    import h5py
    import numpy as np
    output.mkdir(parents=True, exist_ok=True)
    contract, admission, panels = [read_json(HERE / x) for x in FROZEN[:3]]
    acquisition = read_json(cache / "acquisition.json")
    acquired = {r["gsm"]: r for r in acquisition["files"]}
    records = []
    for sample in admission["samples"]:
        p = cache / sample["filename"]
        assert p.stat().st_size == sample["expected_bytes"] == acquired[sample["gsm"]]["bytes"]
        assert sha(p) == acquired[sample["gsm"]]["sha256"]
        record = extract(p, sample, contract, panels)
        if records:
            assert record["ids"] == records[0]["ids"] and record["symbols"] == records[0]["symbols"]
        records.append(record)
        print(f"Read {sample['gsm']}: {record['qc']['n_rna_qc']} RNA-QC nuclei", flush=True)
    ids, symbols = records[0]["ids"], records[0]["symbols"]
    index = {g: i for i, g in enumerate(ids)}
    qcs = [r["qc"] for r in records]
    write_csv(output / "sample_qc.csv", qcs)
    source_samples = admission["samples"]
    primary_i = [i for i, s in enumerate(source_samples) if s["group"] != "WT_GFP"]
    treated = np.asarray([source_samples[i]["group"] == "APP_OSK" for i in primary_i])
    assert len(primary_i) == 7 and int(treated.sum()) == 4
    primary_ok = all(qcs[i]["primary_qc_eligible"] for i in primary_i)
    arrays = {variant: np.asarray([r["counts"][variant] for r in records]).T for variant in ("qc", "all")}
    depths = arrays["qc"].sum(axis=0)
    normalized = {"CPM": np.log2(1 + 1e6 * arrays["qc"] / depths),
                  "rank": np.column_stack([average_ranks(arrays["qc"][:, i]) for i in range(10)])}
    all_cpm = np.log2(1 + 1e6 * arrays["all"] / arrays["all"].sum(axis=0))
    p_counts = arrays["qc"][:, primary_i]
    positive = np.all(p_counts > 0, axis=1)
    factors = np.ones(7)
    mr_ok = int(positive.sum()) >= 100
    mr = np.full((len(ids), 10), np.nan)
    if mr_ok:
        geo = np.exp(np.log(p_counts[positive]).mean(axis=1))
        factors = np.median(p_counts[positive] / geo[:, None], axis=0)
        factors /= np.exp(np.log(factors).mean())
        effective = factors * np.exp(np.log(depths[primary_i]).mean())
        mr[:, primary_i] = np.log2(1 + 1e6 * p_counts / effective)
    normalized["median_ratio"] = mr
    write_csv(output / "normalization.csv", [
        {"gsm": source_samples[i]["gsm"], "animal_id": source_samples[i]["animal_id"],
         "rna_depth": int(depths[i]), "median_ratio_factor": float(factors[primary_i.index(i)]) if i in primary_i and mr_ok else None,
         "median_ratio_positive_genes": int(positive.sum()), "median_ratio_eligible": i in primary_i and mr_ok}
        for i in range(10)])
    # Full-gene aggregate counts are sufficient to independently recalculate all main contrasts.
    with (output / "pseudobulk_counts.csv.gz").open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as stream:
            import io
            text = io.TextIOWrapper(stream, encoding="utf-8", newline="")
            w = csv.writer(text)
            w.writerow(["gene_id", "symbol"] + [s["gsm"] + "_" + v for v in ("qc", "all") for s in source_samples])
            for gi, gene in enumerate(ids):
                w.writerow([gene, symbols[gi]] + [int(arrays[v][gi, i]) for v in ("qc", "all") for i in range(10)])
            text.flush()
    coverage, scores, contrasts, permutations, gene_rows, gene_omits, animal_omits = [], [], [], [], [], [], []
    panel_idx = {}
    for panel in contract["primary"]["family"]:
        spec = panels["panels"][panel]
        mapped = [g for g in spec["genes"] if g["mouse_ensembl_gene"]]
        present = [g for g in mapped if g["mouse_ensembl_gene"] in index]
        pidx = [index[g["mouse_ensembl_gene"]] for g in present]
        eligible = len(present) >= 3 and len(present) / len(mapped) >= .8 and len(present) / len(spec["source_human_genes"]) >= .8
        panel_idx[panel] = pidx if eligible else []
        coverage.append({"panel": panel, "original_human_genes": len(spec["source_human_genes"]),
                         "mapped_genes": len(mapped), "present_genes": len(present), "eligible": eligible,
                         "missing_ids": ";".join(g["mouse_ensembl_gene"] for g in mapped if g not in present)})
        for method, matrix in normalized.items():
            method_ok = eligible and primary_ok and (method != "median_ratio" or mr_ok)
            vals = matrix[pidx].mean(axis=0) if eligible else np.full(10, np.nan)
            for i, s in enumerate(source_samples):
                scores.append({"panel": panel, "method": method, "gsm": s["gsm"], "animal_id": s["animal_id"],
                               "group": s["group"], "score": float(vals[i]) if np.isfinite(vals[i]) else None})
            delta, numerator, denominator, statrows = (None, None, None, [])
            if method_ok:
                delta, numerator, denominator, statrows = exact_permutation(vals[primary_i], treated)
                for x in statrows:
                    permutations.append({"panel": panel, "method": method, **x})
            contrasts.append({"panel": panel, "method": method, "status": "available" if method_ok else "unavailable",
                              "n_OSK": 4, "n_GFP": 3,
                              "OSK_mean": float(vals[np.array(primary_i)[treated]].mean()) if method_ok else None,
                              "GFP_mean": float(vals[np.array(primary_i)[~treated]].mean()) if method_ok else None,
                              "delta": delta, "p_numerator": numerator, "p_denominator": denominator,
                              "p": numerator / denominator if method_ok else None, "holm_p": None})
            if method_ok:
                for local, gene in enumerate(present):
                    gi = pidx[local]
                    gene_delta = float(matrix[gi, np.array(primary_i)[treated]].mean() - matrix[gi, np.array(primary_i)[~treated]].mean())
                    gene_rows.append({"panel": panel, "method": method, "gene_id": gene["mouse_ensembl_gene"],
                                      "symbol": gene["mouse_symbol"], "delta": gene_delta,
                                      "contribution": gene_delta / len(pidx)})
                    remain = pidx[:local] + pidx[local + 1:]
                    rem = matrix[remain][:, primary_i].mean(axis=0)
                    gene_omits.append({"panel": panel, "method": method, "omitted_gene": gene["mouse_symbol"],
                                       "delta": float(rem[treated].mean() - rem[~treated].mean())})
                if method == "CPM":
                    for local, i in enumerate(primary_i):
                        retain = np.arange(7) != local
                        v, t = vals[primary_i][retain], treated[retain]
                        animal_omits.append({"panel": panel, "omitted_gsm": source_samples[i]["gsm"],
                                             "omitted_animal": source_samples[i]["animal_id"], "n_OSK": int(t.sum()),
                                             "n_GFP": int((~t).sum()), "delta": float(v[t].mean() - v[~t].mean())})
        noc = all_cpm[pidx][:, primary_i].mean(axis=0) if eligible and primary_ok else None
        contrasts.append({"panel": panel, "method": "CPM_no_extra_RNA_QC", "status": "available" if noc is not None else "unavailable",
                          "n_OSK": 4, "n_GFP": 3,
                          "OSK_mean": float(noc[treated].mean()) if noc is not None else None,
                          "GFP_mean": float(noc[~treated].mean()) if noc is not None else None,
                          "delta": float(noc[treated].mean() - noc[~treated].mean()) if noc is not None else None,
                          "p_numerator": None, "p_denominator": None, "p": None, "holm_p": None})
    for method in normalized:
        rows = [r for r in contrasts if r["method"] == method]
        assert len(rows) == 4
        for row, adjusted in zip(rows, holm([r["p"] if r["p"] is not None else 1 for r in rows])):
            row["holm_p"] = adjusted
    bins = list(contract["composition"]["marker_bins"]) + ["ambiguous", "unassigned"]
    mix_rows, bin_scores, bin_effects = [], [], []
    bfeature_idx = {g: i for i, g in enumerate(records[0]["bin_panel_ids"])}
    for threshold in (1, 2):
        for b, name in enumerate(bins):
            for i, r in enumerate(records):
                n, depth = int(r["bin_n"][threshold][b]), int(r["bin_depth"][threshold][b])
                mix_rows.append({"threshold_umi": threshold, "bin": name, "gsm": source_samples[i]["gsm"],
                                 "animal_id": source_samples[i]["animal_id"], "group": source_samples[i]["group"],
                                 "partition_available": r["qc"]["marker_partition_available"], "n": n,
                                 "fraction_of_RNA_QC": n / r["qc"]["n_rna_qc"] if r["qc"]["n_rna_qc"] else None,
                                 "rna_umi": depth})
            for panel, pidx in panel_idx.items():
                vals = []
                for i, r in enumerate(records):
                    bg = [bfeature_idx[ids[g]] for g in pidx]
                    depth = int(r["bin_depth"][threshold][b])
                    value = float(np.log2(1 + 1e6 * r["bin_counts"][threshold][b, bg] / depth).mean()) if depth and bg else None
                    vals.append(value)
                    bin_scores.append({"threshold_umi": threshold, "bin": name, "panel": panel,
                                       "gsm": source_samples[i]["gsm"], "group": source_samples[i]["group"], "score": value})
                for support in (20, 50):
                    good = (bool(pidx) and primary_ok and all(
                        records[i]["qc"]["marker_partition_available"] and records[i]["bin_n"][threshold][b] >= support
                        and vals[i] is not None for i in primary_i))
                    v = np.asarray([vals[i] for i in primary_i], dtype=float) if good else None
                    bin_effects.append({"threshold_umi": threshold, "minimum_cells_each_animal": support,
                                        "bin": name, "panel": panel, "status": "available" if good else "insufficient_support",
                                        "n_OSK": 4, "n_GFP": 3,
                                        "minimum_observed_cells": min(int(records[i]["bin_n"][threshold][b]) for i in primary_i),
                                        "delta": float(v[treated].mean() - v[~treated].mean()) if good else None})
    outputs = {"panel_coverage.csv": coverage, "animal_scores.csv": scores, "contrasts.csv": contrasts,
               "permutations.csv": permutations, "gene_contributions.csv": gene_rows,
               "gene_leaveouts.csv": gene_omits, "animal_leaveouts.csv": animal_omits,
               "marker_bin_composition.csv": mix_rows, "marker_bin_scores.csv": bin_scores,
               "marker_bin_contrasts.csv": bin_effects}
    for filename, rows in outputs.items():
        if rows:
            write_csv(output / filename, rows)
    files = {p.name: sha(p) for p in output.iterdir() if p.is_file() and p.name not in {"execution.json", "verification.json"}}
    write_json(output / "execution.json", {"claim_level": "Verified", "scope": "numerical reanalysis only",
               "schema": "cx004-mpfc-expression-audit/v1", "source_files": acquired,
               "frozen_hashes": freeze["sha256"], "primary_eligible": bool(primary_ok),
               "software": {"python": sys.version.split()[0], "numpy": np.__version__, "h5py": h5py.__version__},
               "output_sha256": files, "total_deposited_nuclei": sum(q["n_deposited"] for q in qcs),
               "total_RNA_QC_nuclei": sum(q["n_rna_qc"] for q in qcs),
               "experimental_units_primary": 7, "total_independent_animals": 10,
               "gates": contract["gates"]})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["fetch", "run"])
    p.add_argument("--cache", type=Path, required=True)
    p.add_argument("--output", type=Path, default=HERE / "results")
    args = p.parse_args()
    if args.action == "fetch":
        fetch(args.cache)
    else:
        run(args.cache, args.output)


if __name__ == "__main__":
    main()
