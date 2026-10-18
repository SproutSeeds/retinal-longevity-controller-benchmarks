#!/usr/bin/env python3
"""Independent per-barcode recount of source H5, including marker partitions.

This deliberately uses a cell-at-a-time reader rather than the frozen analysis
block aggregation. It checks stored outputs without selecting new endpoints.
"""
import argparse
import csv
import json
from pathlib import Path
import re
import gzip

import h5py
import numpy as np

HERE = Path(__file__).resolve().parent


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=HERE / "results")
    parser.add_argument("--receipt", type=Path, default=HERE / "RAW_AUDIT.json")
    args = parser.parse_args()
    admission = json.loads((HERE / "admission.json").read_text())
    contract = json.loads((HERE / "contract.json").read_text())
    panel_specs = json.loads((HERE / "panels.json").read_text())["panels"]
    names = list(contract["composition"]["marker_bins"]) + ["ambiguous", "unassigned"]
    markers = sorted({g for x in contract["composition"]["marker_bins"].values() for g in x})
    marker_groups = [[markers.index(g) for g in contract["composition"]["marker_bins"][name]] for name in names[:-2]]
    with gzip.open(args.output / "pseudobulk_counts.csv.gz", "rt", newline="") as stream:
        count_rows = list(csv.DictReader(stream))
    observed = {r["gene_id"]: r for r in count_rows}
    qc_rows = {r["gsm"]: r for r in read_csv(args.output / "sample_qc.csv")}
    bin_comp = read_csv(args.output / "marker_bin_composition.csv")
    bin_scores = read_csv(args.output / "marker_bin_scores.csv")
    checks = 0
    failures = []
    animals = []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not bool(ok):
            failures.append(label)

    for s in admission["samples"]:
        gsm = s["gsm"]
        with h5py.File(args.cache / s["filename"], "r") as h:
            m = h["matrix"]
            ids = [re.sub(r"\.\d+$", "", x.decode()) for x in m["features"]["id"][:]]
            symbols = [x.decode() for x in m["features"]["name"][:]]
            types = [x.decode() for x in m["features"]["feature_type"][:]]
            data, indices, pointer = m["data"][:], m["indices"][:], m["indptr"][:]
            rna_mask = np.array([x == "Gene Expression" for x in types])
            mito_mask = np.array([x.startswith("mt-") for x in symbols]) & rna_mask
            gene_order = [i for i, yes in enumerate(rna_mask) if yes]
            counts_all = np.zeros(len(ids), dtype=np.int64)
            counts_qc = np.zeros(len(ids), dtype=np.int64)
            marker_index = np.full(len(ids), -1, dtype=int)
            for pos, symbol in enumerate(markers):
                which = [i for i in gene_order if symbols[i] == symbol]
                assert len(which) == 1
                marker_index[which[0]] = pos
            panel_feature_ids = sorted({g["mouse_ensembl_gene"] for p in panel_specs.values() for g in p["genes"] if g["mouse_ensembl_gene"] in ids})
            panel_source = [ids.index(g) for g in panel_feature_ids]
            panel_index = np.full(len(ids), -1, dtype=int)
            for pos, source in enumerate(panel_source):
                panel_index[source] = pos
            bin_n = np.zeros((2, len(names)), dtype=np.int64)
            bin_depth = np.zeros_like(bin_n)
            bin_gene = np.zeros((2, len(names), len(panel_feature_ids)), dtype=np.int64)
            qc_n, all_n = 0, len(pointer) - 1
            for cell in range(all_n):
                lo, hi = int(pointer[cell]), int(pointer[cell + 1])
                raw_rows, raw_values = indices[lo:hi], data[lo:hi]
                keep = rna_mask[raw_rows]
                rows, values = raw_rows[keep], raw_values[keep].astype(np.int64)
                depth = int(values.sum())
                detected = int(np.count_nonzero(values))
                mitochondrial = int(values[mito_mask[rows]].sum())
                np.add.at(counts_all, rows, values)
                # Integer cross-product avoids floating-point threshold rounding.
                good = 500 < depth < 30000 and 200 < detected < 9000 and 100 * mitochondrial < 2 * depth
                if not good:
                    continue
                qc_n += 1
                np.add.at(counts_qc, rows, values)
                marker_values = np.zeros(len(markers), dtype=np.int64)
                where = marker_index[rows]
                take = where >= 0
                marker_values[where[take]] = values[take]
                selected_panel = np.zeros(len(panel_feature_ids), dtype=np.int64)
                pwhere = panel_index[rows]
                ptake = pwhere >= 0
                selected_panel[pwhere[ptake]] = values[ptake]
                for ti, threshold in enumerate((1, 2)):
                    eligible = [bi for bi, member in enumerate(marker_groups) if sum(marker_values[j] >= threshold for j in member) >= 2]
                    assigned = eligible[0] if len(eligible) == 1 else len(names) - (1 if len(eligible) == 0 else 2)
                    bin_n[ti, assigned] += 1
                    bin_depth[ti, assigned] += depth
                    bin_gene[ti, assigned] += selected_panel
        check(qc_n == int(qc_rows[gsm]["n_rna_qc"]), gsm + " exact independently counted RNA QC")
        check(all_n == int(qc_rows[gsm]["n_deposited"]), gsm + " deposited nucleus count")
        for source in gene_order:
            gene = ids[source]
            check(int(counts_qc[source]) == int(observed[gene][gsm + "_qc"]), gsm + " QC aggregate " + gene)
            check(int(counts_all[source]) == int(observed[gene][gsm + "_all"]), gsm + " all aggregate " + gene)
        for ti, threshold in enumerate((1, 2)):
            for bi, name in enumerate(names):
                row = next(r for r in bin_comp if r["gsm"] == gsm and r["bin"] == name and int(r["threshold_umi"]) == threshold)
                check(bin_n[ti, bi] == int(row["n"]), gsm + " independently assigned bin nuclei " + name + str(threshold))
                check(bin_depth[ti, bi] == int(row["rna_umi"]), gsm + " independently assigned bin RNA " + name + str(threshold))
                for panel, spec in panel_specs.items():
                    source = [panel_feature_ids.index(g["mouse_ensembl_gene"]) for g in spec["genes"] if g["mouse_ensembl_gene"] in panel_feature_ids]
                    row = next(r for r in bin_scores if r["gsm"] == gsm and r["bin"] == name and r["panel"] == panel and int(r["threshold_umi"]) == threshold)
                    if bin_depth[ti, bi] > 0:
                        score = float(np.mean(np.log2(1 + 1e6 * bin_gene[ti, bi, source] / bin_depth[ti, bi])))
                        check(np.isclose(score, float(row["score"]), rtol=1e-11, atol=1e-12), gsm + " independent bin score " + name + str(threshold) + panel)
                    else:
                        check(row["score"] == "", gsm + " empty bin score " + name + str(threshold) + panel)
        animals.append({"gsm": gsm, "animal_id": s["animal_id"], "n_deposited": all_n, "n_RNA_QC": qc_n})
        print(f"Independent source recount {gsm}: {qc_n}/{all_n} nuclei", flush=True)
    receipt = {"claim_level": "Verified", "status": "PASS" if not failures else "FAIL", "checks": checks,
               "passed": checks - len(failures), "failures": failures, "animals": animals,
               "reader": "Cell-at-a-time from raw CSC; integer RNA QC ratios; exact full-gene count comparison and all fixed-bin counts/scores.",
               "source_expression_new_endpoints": False}
    args.receipt.write_text(json.JSONEncoder(indent=2, sort_keys=True).encode(receipt) + "\n")
    print(f"{receipt['status']} {receipt['passed']}/{checks}")
    raise SystemExit(bool(failures))


if __name__ == "__main__":
    main()
