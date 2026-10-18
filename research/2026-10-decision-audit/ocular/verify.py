#!/usr/bin/env python3
"""Independent saved-artifact checks; optionally verify original source hashes.

Checks numerical reproducibility and support accounting. Passing these checks
does not certify a biological interpretation, cell identity, safety or recovery.
"""
import argparse
import csv
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    import numpy as np
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=HERE / "results")
    p.add_argument("--cache", type=Path)
    p.add_argument("--receipt", type=Path)
    args = p.parse_args()
    out = args.output
    checks = []

    def check(ok, name):
        checks.append({"name": name, "status": "PASS" if bool(ok) else "FAIL"})

    def close(a, b, name):
        check(math.isclose(float(a), float(b), rel_tol=1e-11, abs_tol=1e-12), name)

    execution = json.loads((out / "execution.json").read_text())
    original_acquisition = json.loads((HERE / "acquisition.json").read_text())
    for source in original_acquisition["files"]:
        check(execution["source_files"].get(source["gsm"]) == source,
              "source manifest matches original acquisition " + source["gsm"])
    admission = json.loads((HERE / "admission.json").read_text())
    contract = json.loads((HERE / "contract.json").read_text())
    panels = json.loads((HERE / "panels.json").read_text())
    for name, expected in execution["frozen_hashes"].items():
        check(hash_file(HERE / name) == expected, "frozen " + name)
    for name, expected in execution["output_sha256"].items():
        check(hash_file(out / name) == expected, "output " + name)
    if args.cache:
        for source in execution["source_files"].values():
            path = args.cache / source["filename"]
            check(path.stat().st_size == source["bytes"], "source bytes " + source["gsm"])
            check(hash_file(path) == source["sha256"], "source hash " + source["gsm"])
    samples = admission["samples"]
    gsms = [s["gsm"] for s in samples]
    groups = [s["group"] for s in samples]
    primary = [i for i, g in enumerate(groups) if g != "WT_GFP"]
    treated = [i for i, g in enumerate(groups) if g == "APP_OSK"]
    control = [i for i, g in enumerate(groups) if g == "APP_GFP"]
    check(len(samples) == 10 and len(set(s["animal_id"] for s in samples)) == 10, "ten distinct mice")
    check(len(treated) == 4 and len(control) == 3, "seven experimental units")
    check(len(set(s["paired_atac_gsm"] for s in samples)) == 10, "ten paired ATAC identifiers")
    check(admission["total_matrix_bytes"] == sum(s["expected_bytes"] for s in samples), "source byte sum")
    check(admission["total_matrix_bytes"] < 5_000_000_000, "bounded source byte budget")
    with gzip.open(out / "pseudobulk_counts.csv.gz", "rt", newline="") as stream:
        count_rows = list(csv.DictReader(stream))
    ids = [r["gene_id"] for r in count_rows]
    check(len(ids) == len(set(ids)), "unique full aggregate gene IDs")
    raw = {v: np.array([[int(r[g + "_" + v]) for g in gsms] for r in count_rows]) for v in ("qc", "all")}
    check(np.all(raw["qc"] >= 0) and np.all(raw["all"] >= 0), "nonnegative aggregate counts")
    check(np.all(raw["qc"] <= raw["all"]), "QC is subset for every gene and animal")
    qc = read(out / "sample_qc.csv")
    check([x["gsm"] for x in qc] == gsms, "QC row exact sample order")
    for i, row in enumerate(qc):
        check(int(row["qc_rna_umi"]) == int(raw["qc"][:, i].sum()), "QC depth " + row["gsm"])
        check(int(row["all_rna_umi"]) == int(raw["all"][:, i].sum()), "all-barcode depth " + row["gsm"])
        check(int(row["detected_pseudobulk_genes"]) == int((raw["qc"][:, i] > 0).sum()), "detected genes " + row["gsm"])
    check(sum(int(x["n_rna_qc"]) for x in qc) == execution["total_RNA_QC_nuclei"], "RNA QC nucleus total")
    check(sum(int(x["n_deposited"]) for x in qc) == execution["total_deposited_nuclei"], "deposited nucleus total")
    gene_index = {g: i for i, g in enumerate(ids)}
    cpm = np.log2(1 + 1e6 * raw["qc"] / raw["qc"].sum(axis=0))
    allcpm = np.log2(1 + 1e6 * raw["all"] / raw["all"].sum(axis=0))
    # Independently derive averaged tied ranks from unique value multiplicities.
    ranked = np.zeros(cpm.shape)
    for i in range(10):
        vals, inverse, counts = np.unique(raw["qc"][:, i], return_inverse=True, return_counts=True)
        end = np.cumsum(counts)
        ranks = (end - counts + end - 1) / (2 * (len(ids) - 1))
        ranked[:, i] = ranks[inverse]
    primary_counts = raw["qc"][:, primary]
    positive = np.all(primary_counts > 0, axis=1)
    gm = np.exp(np.log(primary_counts[positive]).mean(axis=1))
    ratios = np.median(primary_counts[positive] / gm[:, None], axis=0)
    factors = ratios / np.exp(np.log(ratios).mean())
    effective = factors * np.exp(np.log(raw["qc"][:, primary].sum(axis=0)).mean())
    median_ratio = np.full(cpm.shape, np.nan)
    median_ratio[:, primary] = np.log2(1 + 1e6 * primary_counts / effective)
    matrices = {"CPM": cpm, "rank": ranked, "median_ratio": median_ratio, "CPM_no_extra_RNA_QC": allcpm}
    score_lookup = {(x["panel"], x["method"], x["gsm"]): x for x in read(out / "animal_scores.csv")}
    contrast_rows = read(out / "contrasts.csv")
    contribution_rows = read(out / "gene_contributions.csv")
    omission_rows = read(out / "gene_leaveouts.csv")
    animal_rows = read(out / "animal_leaveouts.csv")
    for panel in contract["primary"]["family"]:
        genes = [g for g in panels["panels"][panel]["genes"] if g["mouse_ensembl_gene"] in gene_index]
        idx = [gene_index[g["mouse_ensembl_gene"]] for g in genes]
        for method, matrix in matrices.items():
            vals = matrix[idx].mean(axis=0)
            if method != "CPM_no_extra_RNA_QC":
                for i, gsm in enumerate(gsms):
                    row = score_lookup[(panel, method, gsm)]
                    if method == "median_ratio" and i not in primary:
                        check(row["score"] == "", "WT excluded from median-ratio " + gsm + panel)
                    else:
                        close(vals[i], row["score"], "independent score " + gsm + panel + method)
            row = next(r for r in contrast_rows if r["panel"] == panel and r["method"] == method)
            delta = float(vals[treated].mean() - vals[control].mean())
            close(delta, row["delta"], "independent delta " + panel + method)
            if method == "CPM_no_extra_RNA_QC":
                check(row["p"] == row["holm_p"] == "", "no extra QC sensitivity p value " + panel)
                continue
            stats = []
            for choice in itertools.combinations(primary, 4):
                other = [i for i in primary if i not in choice]
                stats.append(float(vals[list(choice)].mean() - vals[other].mean()))
            numerator = sum(abs(x) >= abs(delta) - 1e-12 * max(1, abs(delta)) for x in stats)
            check(int(row["p_denominator"]) == len(stats) == 35, "all 35 labels " + panel + method)
            check(int(row["p_numerator"]) == numerator, "independent exceedance count " + panel + method)
            close(row["p"], numerator / 35, "independent p " + panel + method)
            contributions = [r for r in contribution_rows if r["panel"] == panel and r["method"] == method]
            close(sum(float(r["contribution"]) for r in contributions), delta, "gene contribution sum " + panel + method)
            for local, gene in enumerate(genes):
                other_idx = idx[:local] + idx[local + 1:]
                other_values = matrix[other_idx].mean(axis=0)
                expected = float(other_values[treated].mean() - other_values[control].mean())
                omit = next(r for r in omission_rows if r["panel"] == panel and r["method"] == method and r["omitted_gene"] == gene["mouse_symbol"])
                close(omit["delta"], expected, "independent gene omission " + panel + method + gene["mouse_symbol"])
        vals = cpm[idx].mean(axis=0)
        for i in primary:
            t, c = [j for j in treated if j != i], [j for j in control if j != i]
            row = next(r for r in animal_rows if r["panel"] == panel and r["omitted_gsm"] == gsms[i])
            close(row["delta"], vals[t].mean() - vals[c].mean(), "animal omission " + panel + gsms[i])
    for method in ("CPM", "rank", "median_ratio"):
        rows = sorted([r for r in contrast_rows if r["method"] == method], key=lambda x: float(x["p"]))
        bound = 0
        for i, row in enumerate(rows):
            bound = min(1, max(bound, (4 - i) * float(row["p"])))
            close(row["holm_p"], bound, "four-test Holm " + row["panel"] + method)
    mix = read(out / "marker_bin_composition.csv")
    bscores = read(out / "marker_bin_scores.csv")
    beffects = read(out / "marker_bin_contrasts.csv")
    bins = list(contract["composition"]["marker_bins"]) + ["ambiguous", "unassigned"]
    check(len(mix) == 2 * 8 * 10, "complete composition rows")
    check(len(beffects) == 2 * 2 * 8 * 4, "complete supported and unsupported bin contrasts")
    for threshold in (1, 2):
        for i, gsm in enumerate(gsms):
            rows = [r for r in mix if r["gsm"] == gsm and int(r["threshold_umi"]) == threshold]
            check(sum(int(r["n"]) for r in rows) == int(qc[i]["n_rna_qc"]), "partition nucleus sum " + gsm + str(threshold))
            check(sum(int(r["rna_umi"]) for r in rows) == int(qc[i]["qc_rna_umi"]), "partition RNA sum " + gsm + str(threshold))
            close(sum(float(r["fraction_of_RNA_QC"]) for r in rows), 1, "partition frequency sum " + gsm + str(threshold))
    for row in beffects:
        threshold, name, panel = int(row["threshold_umi"]), row["bin"], row["panel"]
        counts = [int(r["n"]) for r in mix if int(r["threshold_umi"]) == threshold and r["bin"] == name and r["gsm"] in [gsms[i] for i in primary]]
        check(len(counts) == 7, "bin has seven animals " + str(row))
        expected_support = min(counts) >= int(row["minimum_cells_each_animal"])
        check((row["status"] == "available") == expected_support, "all-animal support rule " + str(row))
        if expected_support:
            values = {r["gsm"]: float(r["score"]) for r in bscores if int(r["threshold_umi"]) == threshold and r["bin"] == name and r["panel"] == panel}
            expected = sum(values[gsms[i]] for i in treated) / 4 - sum(values[gsms[i]] for i in control) / 3
            close(row["delta"], expected, "bin animal mean delta " + str(row))
        else:
            check(row["delta"] == "", "unsupported bin keeps unavailable effect " + str(row))
    for key in ("CX004-R01", "CX004-R02", "CX004-R03", "CX004-R04"):
        check(execution["gates"][key] == "insufficient_signal", "gate unchanged " + key)
    check(execution["gates"]["wetlab_replacement"] == "INCONCLUSIVE", "replacement claim bounded")
    failed = [r for r in checks if r["status"] == "FAIL"]
    result = {"status": "PASS" if not failed else "FAIL", "checks": len(checks), "passed": len(checks) - len(failed),
              "failed": failed, "source_hashes_checked": bool(args.cache),
              "limits": "Saved-aggregate arithmetic, original acquisition manifest, provenance and support accounting; no biological validity certification."}
    receipt = args.receipt or out / "verification.json"
    receipt.write_text(json.JSONEncoder(indent=2, sort_keys=True).encode(result) + "\n")
    print(json.JSONEncoder(indent=2, sort_keys=True).encode(result))
    raise SystemExit(bool(failed))


if __name__ == "__main__":
    main()
