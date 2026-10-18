#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["numpy==2.5.4", "scipy==1.18.1", "h5py==3.16.0"]
# ///
"""Frozen post hoc co-detection diagnostics, not a biological state classifier.

Preparing/importing this module performs no input reads. The CLI checks the
committed-contract receipt before it opens any observed expression matrix.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import gzip
import io
import json
from pathlib import Path
import re

import h5py
import numpy as np
from scipy.sparse import csc_matrix

from marker_audit import HERE, check_hash, save, sha


@dataclass
class Sample:
    gsm: str
    donor: str
    day: int
    barcodes: np.ndarray
    markers: list[str]
    counts: np.ndarray
    totals: np.ndarray
    detected: np.ndarray
    mito: np.ndarray
    feature_ids: dict[str, str]
    deposited_barcodes: int
    source_sha256: str


def require_freeze(contract, scout, freeze_path):
    if not freeze_path.is_file():
        raise ValueError("Observed expression is gated: PERCELL_FREEZE.json is absent")
    freeze = json.loads(freeze_path.read_text())
    if freeze.get("expression_execution_authorized") is not True:
        raise ValueError("Observed expression execution is not authorized")
    if not re.fullmatch(r"[0-9a-f]{40}", freeze.get("commit", "")):
        raise ValueError("Committed analysis freeze ID is missing")
    check_hash(contract, freeze.get("contract_sha256"))
    check_hash(scout, freeze.get("scout_sha256"))
    return freeze


def decode(values):
    return [value.decode("utf-8") if isinstance(value, bytes) else str(value) for value in values]


def load_h5(path, info, markers):
    check_hash(path, info["sha256"])
    with h5py.File(path, "r") as h5:
        node = h5["matrix"]
        counts = node["data"][:]
        indices = node["indices"][:]
        indptr = node["indptr"][:]
        shape = tuple(int(value) for value in node["shape"][:])
        names = decode(node["features/name"][:])
        ids = decode(node["features/id"][:])
        kinds = decode(node["features/feature_type"][:])
        barcodes = decode(node["barcodes"][:])
    if shape != (len(names), len(barcodes)) or len(ids) != len(names) or len(kinds) != len(names):
        raise ValueError("Feature/barcode dimensions disagree")
    if len(set(barcodes)) != len(barcodes) or any(not b for b in barcodes):
        raise ValueError("Duplicate/missing barcodes within sample")
    if len(set(ids)) != len(ids) or any(not feature for feature in ids):
        raise ValueError("Duplicate/missing feature IDs")
    if not np.isfinite(counts).all() or np.any(counts < 0) or np.any(counts % 1 != 0):
        raise ValueError("Invalid nonnegative integer UMI counts")
    if np.any(counts > np.iinfo(np.int64).max):
        raise ValueError("UMI count overflow")
    matrix = csc_matrix((counts.astype(np.int64), indices, indptr), shape=shape)
    matrix.check_format(full_check=True)
    if not matrix.has_canonical_format:
        raise ValueError("Duplicated or unsorted sparse coordinates")
    matrix.eliminate_zeros()
    expression_rows = np.array([kind == "Gene Expression" for kind in kinds])
    if not expression_rows.any():
        raise ValueError("No Gene Expression features")
    gene_matrix = matrix if expression_rows.all() else matrix[expression_rows, :]
    totals = np.asarray(gene_matrix.sum(axis=0)).ravel().astype(np.int64)
    detected = np.asarray(gene_matrix.getnnz(axis=0)).ravel().astype(np.int64)
    mito_rows = [i for i, name in enumerate(names) if name.startswith("MT-") and expression_rows[i]]
    mito = np.asarray(matrix[mito_rows, :].sum(axis=0)).ravel().astype(np.int64)
    marker_indices = []
    for gene in markers:
        matches = [i for i, name in enumerate(names) if name == gene and expression_rows[i]]
        if len(matches) != 1:
            raise ValueError(f"Missing/ambiguous Gene Expression marker: {gene}")
        marker_indices.append(matches[0])
    marker_counts = matrix[marker_indices, :].toarray().T.astype(np.int64)
    keep = totals > 0
    order = np.argsort(np.asarray(barcodes)[keep], kind="stable")
    def select(values):
        return np.asarray(values)[keep][order]
    return Sample(info["gsm"], info["donor"], int(info["day"]), select(barcodes), list(markers),
                  select(marker_counts), select(totals), select(detected), select(mito),
                  {gene: ids[index] for gene, index in zip(markers, marker_indices)},
                  len(barcodes), info["sha256"])


def feature_columns(sample, genes):
    if not genes or len(genes) != len(set(genes)):
        raise ValueError("A panel must contain unique marker names")
    return [sample.markers.index(gene) for gene in genes]


def expression_scores(counts, totals, columns):
    if len(totals) == 0:
        return np.zeros(0, dtype=float)
    if np.any(totals <= 0):
        raise ValueError("Nonpositive normalization denominator")
    return np.log1p(counts[:, columns] / totals[:, None] * 10000).mean(axis=1)


def coexpression_counts(counts, columns, umi_threshold=1):
    if umi_threshold < 1:
        raise ValueError("Detection requires positive UMI threshold")
    return (counts[:, columns] >= umi_threshold).sum(axis=1)


def donor_cutoffs(samples, score_by_sample, mask_by_sample, q):
    result = {}
    for donor in sorted({sample.donor for sample in samples}):
        baselines = [sample for sample in samples if sample.donor == donor and sample.day == 0]
        if len(baselines) != 1:
            raise ValueError("Each donor needs exactly one D0 sample")
        baseline = baselines[0]
        scores = score_by_sample[baseline.gsm][mask_by_sample[baseline.gsm]]
        if len(scores) == 0:
            raise ValueError("No retained donor D0 baseline")
        threshold = float(np.quantile(scores, q, method="linear"))
        realized = int((scores <= threshold).sum())
        result[donor] = {"nominal_quantile": q, "threshold": threshold,
                         "D0_denominator": len(scores), "D0_identity_low_count": realized,
                         "D0_identity_low_fraction": realized / len(scores),
                         "tie_count_at_threshold": int((scores == threshold).sum())}
    return result


def joint_tables(identity_low, coexpression, factor_overlap):
    identity_low = np.asarray(identity_low, dtype=bool)
    coexpression = np.asarray(coexpression)
    factor_overlap = np.asarray(factor_overlap, dtype=bool)
    n = len(identity_low)
    if coexpression.shape != (n,) or factor_overlap.shape != (n,):
        raise ValueError("Cell masks differ in shape")
    if np.any(coexpression < 0) or np.any(coexpression % 1 != 0):
        raise ValueError("Invalid co-detected marker counts")
    bins = np.minimum(coexpression, 3)
    flagged = coexpression >= 2
    tables = []
    for family in ["binary_2x2", "count_bins_2x4", "binary_with_factor_overlap"]:
        for low in [False, True]:
            for category in range(4 if family == "count_bins_2x4" else 2):
                marker_mask = bins == category if family == "count_bins_2x4" else flagged == bool(category)
                levels = [None] if family != "binary_with_factor_overlap" else [False, True]
                for factor in levels:
                    mask = (identity_low == low) & marker_mask
                    if factor is not None:
                        mask &= factor_overlap == factor
                    count = int(mask.sum())
                    tables.append({"table": family,
                                   "identity": "identity_low" if low else "identity_not_low",
                                   "coexpression": ["0", "1", "2", "3+"][category] if family == "count_bins_2x4" else ("at_least_two" if category else "fewer_than_two"),
                                   "factor_overlap_detected": factor, "count": count,
                                   "denominator": n, "fraction": count / n if n else None})
    return tables


def thin_markers(counts, totals, target, rng):
    counts = np.asarray(counts)
    totals = np.asarray(totals)
    if counts.ndim != 2 or totals.shape != (len(counts),):
        raise ValueError("Thinning dimensions disagree")
    if target < 1 or np.any(totals < target) or np.any(counts < 0) or np.any(counts % 1 != 0):
        raise ValueError("Invalid thinning counts/target")
    remainder = totals - counts.sum(axis=1)
    if np.any(remainder < 0) or np.any(totals % 1 != 0):
        raise ValueError("Markers exceed Gene Expression total")
    thinned = np.zeros_like(counts, dtype=np.int64)
    sampled_remainder = np.zeros(len(counts), dtype=np.int64)
    for i, row in enumerate(counts):
        categories = np.append(row, remainder[i]).astype(np.int64)
        draw = rng.multivariate_hypergeometric(categories, target, method="marginals")
        thinned[i] = draw[:-1]
        sampled_remainder[i] = draw[-1]
    if np.any(thinned.sum(axis=1) + sampled_remainder != target) or np.any(thinned > counts):
        raise ValueError("Hypergeometric count conservation failed")
    return thinned, sampled_remainder


def variant_specs(core, identity):
    variants = [{"id": "primary", "q": .10, "umi": 1}]
    variants.append({"id": "endogenous_min2_umi", "q": .10, "umi": 2})
    variants.extend({"id": f"omit_endogenous_{gene}", "q": .10, "umi": 1, "omit_core": gene} for gene in core)
    variants.extend({"id": f"omit_identity_{gene}", "q": .10, "umi": 1, "omit_identity": gene} for gene in identity)
    variants.extend({"id": f"identity_q{int(q * 100):02d}", "q": q, "umi": 1} for q in [.05, .20])
    variants.append({"id": "detected_genes_gt500", "q": .10, "umi": 1, "min_genes_exclusive": 500})
    variants.extend({"id": f"D0_UMI_quartile_{i + 1}", "q": .10, "umi": 1, "depth_bin": i} for i in range(4))
    variants.extend({"id": f"thin1000_seed{seed}", "q": .10, "umi": 1, "thin": 1000, "seed": seed} for seed in [181026, 181027, 181028])
    return variants


def depth_cutoffs(samples):
    cuts = {}
    for donor in sorted({sample.donor for sample in samples}):
        baseline = [sample for sample in samples if sample.donor == donor and sample.day == 0]
        if len(baseline) != 1 or not len(baseline[0].totals):
            raise ValueError("Missing unique donor D0 for depth strata")
        totals = baseline[0].totals
        cuts[donor] = {"quartiles": np.quantile(totals, [.25, .5, .75], method="linear").tolist(),
                       "minimum": int(totals.min()), "maximum": int(totals.max())}
    return cuts


def analyze_variant(samples, spec, core, identity, factor, depth):
    core = [gene for gene in core if gene != spec.get("omit_core")]
    identity = [gene for gene in identity if gene != spec.get("omit_identity")]
    scores, coexpressed, overlaps, masks, transformed_counts, transformed_totals = {}, {}, {}, {}, {}, {}
    rng = np.random.Generator(np.random.PCG64(spec["seed"])) if "seed" in spec else None
    for sample in samples:
        counts = sample.counts.copy()
        totals = sample.totals.copy()
        mask = np.ones(len(totals), dtype=bool)
        if "min_genes_exclusive" in spec:
            mask &= sample.detected > spec["min_genes_exclusive"]
        if "depth_bin" in spec:
            mask &= np.searchsorted(depth[sample.donor]["quartiles"], totals, side="left") == spec["depth_bin"]
        if "thin" in spec:
            mask &= totals >= spec["thin"]
            counts[mask], _ = thin_markers(counts[mask], totals[mask], spec["thin"], rng)
            totals[mask] = spec["thin"]
        scores[sample.gsm] = expression_scores(counts, totals, feature_columns(sample, identity))
        coexpressed[sample.gsm] = coexpression_counts(counts, feature_columns(sample, core), spec["umi"])
        overlaps[sample.gsm] = (counts[:, feature_columns(sample, factor)] > 0).any(axis=1)
        masks[sample.gsm] = mask
        transformed_counts[sample.gsm], transformed_totals[sample.gsm] = counts, totals
    # Depth stratification preserves the primary donor-wide D0 identity cutoff.
    baseline_masks = {sample.gsm: np.ones(len(sample.totals), dtype=bool) for sample in samples} if "depth_bin" in spec else masks
    baselines = donor_cutoffs(samples, scores, baseline_masks, spec["q"])
    output, cells = [], {}
    for sample in samples:
        mask = masks[sample.gsm]
        current_scores = scores[sample.gsm][mask]
        current_coexpression = coexpressed[sample.gsm][mask]
        current_factor = overlaps[sample.gsm][mask]
        low = current_scores <= baselines[sample.donor]["threshold"]
        n = int(mask.sum())
        tables = joint_tables(low, current_coexpression, current_factor)
        for name in {row["table"] for row in tables}:
            if sum(row["count"] for row in tables if row["table"] == name) != n:
                raise ValueError("Joint table does not conserve sample denominator")
        marker_values = transformed_counts[sample.gsm][mask]
        umi = transformed_totals[sample.gsm][mask]
        detection = [{"gene": gene, "cells_detected": int((marker_values[:, i] > 0).sum()),
                      "fraction_detected": float((marker_values[:, i] > 0).mean()) if n else None,
                      "mean_raw_UMI": float(marker_values[:, i].mean()) if n else None,
                      "mean_log1p_CP10k": float(np.log1p(marker_values[:, i] / umi * 10000).mean()) if n else None}
                     for i, gene in enumerate(sample.markers)]
        output.append({"variant": spec["id"], "gsm": sample.gsm, "donor": sample.donor, "day": sample.day,
                       "n_retained": n, "n_primary_nonempty": len(sample.totals),
                       "identity_panel": identity, "endogenous_panel": core, "coexpression_UMI_threshold": spec["umi"],
                       "baseline": baselines[sample.donor], "identity_low_count": int(low.sum()),
                       "identity_low_fraction": float(low.mean()) if n else None,
                       "realized_D0_identity_low_fraction_in_this_variant": float(low.mean()) if n and sample.day == 0 else None,
                       "coexpression_at_least_two_count": int((current_coexpression >= 2).sum()),
                       "coexpression_at_least_two_fraction": float((current_coexpression >= 2).mean()) if n else None,
                       "original_UMI_below_D0_range": int((sample.totals[mask] < depth[sample.donor]["minimum"]).sum()),
                       "original_UMI_above_D0_range": int((sample.totals[mask] > depth[sample.donor]["maximum"]).sum()),
                       "joint_tables": tables, "marker_summary": detection})
        if spec["id"] == "primary":
            cells[sample.gsm] = {"mask": mask, "identity_score": current_scores, "identity_low": low,
                                 "coexpression_count": current_coexpression, "factor_overlap": current_factor}
    return output, cells


def write_primary_cells(path, samples, cells):
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
                writer.writerow(["gsm", "donor", "day", "barcode", "Gene_Expression_UMIs", "detected_genes",
                                 "mitochondrial_UMI_fraction", "identity_score", "identity_low",
                                 "endogenous_codetected_marker_count", "factor_overlap_detected", *samples[0].markers])
                for sample in samples:
                    values = cells[sample.gsm]
                    for i, barcode in enumerate(sample.barcodes):
                        writer.writerow([sample.gsm, sample.donor, sample.day, barcode, int(sample.totals[i]), int(sample.detected[i]),
                                         float(sample.mito[i] / sample.totals[i]), float(values["identity_score"][i]),
                                         int(values["identity_low"][i]), int(values["coexpression_count"][i]),
                                         int(values["factor_overlap"][i]), *sample.counts[i].tolist()])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=HERE / "percell-contract-proposal.json")
    parser.add_argument("--scout", type=Path, default=HERE / "timecourse-scout.json")
    parser.add_argument("--freeze", type=Path, default=HERE / "PERCELL_FREEZE.json")
    parser.add_argument("--h5-dir", type=Path, default=HERE.parents[2] / "tmp/observed-to-synthetic-public-expansion-intake/GSE297234/raw_h5")
    parser.add_argument("--output", type=Path, default=HERE / "percell")
    args = parser.parse_args()
    freeze = require_freeze(args.contract, args.scout, args.freeze)
    contract = json.loads(args.contract.read_text())
    scout = json.loads(args.scout.read_text())
    core = contract["features"]["endogenous_marker_panel"]
    identity = contract["features"]["identity_marker_panel"]
    factor = contract["features"]["factor_overlap_report_only"]
    markers = sorted(set(core + identity + factor))
    if set(core) & set(factor):
        raise ValueError("Endogenous panel overlaps factor-expression panel")
    infos = sorted(scout["local_files"], key=lambda row: row["gsm"])
    expected = {(row["id"], day) for row in contract["donors"] for day in contract["days"]}
    if (len(infos) != len(expected) or len({row["gsm"] for row in infos}) != len(infos)
            or {(row["donor"], row["day"]) for row in infos} != expected):
        raise ValueError("Source manifest does not uniquely cover specified donors/times")
    samples = []
    for info in infos:
        sample = load_h5(args.h5_dir / Path(info["path"]).name, info, markers)
        if sample.deposited_barcodes != info["deposited_barcode_count_from_prior_shape_audit"]:
            raise ValueError("Deposited barcode count differs from prior audit")
        samples.append(sample)
        print(f"Loaded {sample.gsm}: {len(sample.totals)} nonempty deposited barcodes")
    depth = depth_cutoffs(samples)
    rows, primary_cells = [], {}
    for spec in variant_specs(core, identity):
        current, cells = analyze_variant(samples, spec, core, identity, factor, depth)
        rows.extend(current)
        primary_cells.update(cells)
    args.output.mkdir(parents=True, exist_ok=True)
    write_primary_cells(args.output / "primary-cells.tsv.gz", samples, primary_cells)
    flat = [{"variant": row["variant"], "gsm": row["gsm"], "donor": row["donor"], "day": row["day"], **table}
            for row in rows for table in row["joint_tables"]]
    with (args.output / "joint-tables.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flat[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(flat)
    result = {"claim_level": "Heuristic", "computation_level": "Verified after dedicated verification passes",
              "evidence_class": "derived_observed_posthoc", "contract_id": contract["id"],
              "contract_sha256": sha(args.contract), "scout_sha256": sha(args.scout),
              "analysis_sha256": sha(Path(__file__)), "freeze": freeze,
              "library_versions": {"numpy": np.__version__, "h5py": h5py.__version__},
              "source_study": contract["source_attribution"], "donor_D0_UMI_bounds": depth,
              "sample_qc": [{"gsm": s.gsm, "donor": s.donor, "day": s.day,
                             "deposited_barcodes": s.deposited_barcodes, "nonempty_barcodes": len(s.totals),
                             "empty_barcodes_excluded": s.deposited_barcodes - len(s.totals),
                             "UMI_quantiles": np.quantile(s.totals, [0, .25, .5, .75, 1]).tolist(),
                             "detected_gene_quantiles": np.quantile(s.detected, [0, .25, .5, .75, 1]).tolist(),
                             "mitochondrial_fraction_quantiles": np.quantile(s.mito / s.totals, [0, .25, .5, .75, 1]).tolist(),
                             "feature_mapping": s.feature_ids, "source_sha256": s.source_sha256} for s in samples],
              "variants": variant_specs(core, identity), "sample_variant_results": rows,
              "primary_cells_sha256": sha(args.output / "primary-cells.tsv.gz"),
              "joint_tables_sha256": sha(args.output / "joint-tables.csv"),
              "authority": "Observed endogenous-marker co-detection and fibroblast-marker expression, stratified by donor/time. No calibrated state, true rare-state prevalence, age effect, vector-specific load, recovery or safety estimate.",
              "readouts": {f"CX004-R0{i}": "insufficient_signal" for i in range(1, 5)}}
    save(args.output / "results.json", result)
    print(f"Computed {len(rows)} donor/time/variant diagnostics; no donor-level inference")


if __name__ == "__main__":
    main()
