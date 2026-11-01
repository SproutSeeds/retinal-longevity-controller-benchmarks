# Claim: donor-specific RNA/respiration correspondence

**Verified numerical description.** In the fixed, untreated source subset, the unweighted mean of all 125 original human SenMayo genes has raw Spearman correlations with oxidative spare respiratory capacity of −0.6272727272727273 in HC1 (11 observations) and +0.5515151515151515 in HC2 (10 observations). The raw sign difference survives every one-record deletion. The respective linear-day-residual Pearson coefficients are −0.2805980092217136 and +0.1483332456862626; adjacent per-day-change rank correlations are −0.04242424242424243 and +0.047619047619047616. The two donors were both 18 years old; observations are repeated culture timepoints.

**Heuristic readout.** The arithmetic mean summarizes a source-defined transcript panel. The published panel's validation does not establish validity of this custom mean as a senescence diagnosis, biological-age estimate, functional benefit or intervention outcome in these cultures. The verified coefficients support a bounded descriptive result about this measure and source subset.

Canonical evidence: [frozen specification](ANALYSIS_CONTRACT.json), [gene coverage](GENE_COVERAGE.json), [source expression cells](panel-expression-source.tsv), [source-bound scores](sample-scores.tsv), [results](RESULTS.json), [all deletions](leave-one-out.tsv), [all adjacent intervals](adjacent-changes.tsv), [independent checker](INDEPENDENT_CHECK.json).

Verification hook, from the repository root:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/sturm-senmayo-calibration-2026-11-01/verify.py
```

Expected: twelve tests pass and `PASS offline calibration`. Full source replay uses `analyze.py --sources /path/to/originals`; independent numerical checking uses `independent_check.py` with NumPy 2.2.6 and SciPy 1.16.3. [VERIFICATION_RECORD.md](VERIFICATION_RECORD.md) states what these checks establish. Serialized primary outputs are deterministic in the recorded environment; cross-implementation comparisons allow absolute error 1e-10.

Original experimental and panel credit remains with Sturm and colleagues and Saul and colleagues. Gill joint admissions, formal Phase 483, intervention efficacy, safety, lineage retention and withdrawal persistence remain separate requirements. No population inference, causal conclusion or new biological clock is claimed.
