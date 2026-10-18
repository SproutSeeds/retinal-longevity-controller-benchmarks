# Endogenous-marker co-detection with fibroblast-marker expression

**Verified computation; Heuristic biological interpretation.** The frozen post hoc analysis describes 57,317 deposited barcodes from two human donors at four collection times. It adds an isolated endogenous-marker co-detection-by-identity table to the earlier mixed marker-gate audit. [Lu et al., Cell 2025](https://doi.org/10.1016/j.cell.2025.07.031) generated the experiment; [GSE297234](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE297234) supplies the public matrices.

This time-course panel is distinct from the seven-gene bulk panel in the [bulk correction](../ADDENDUM.md). The time-course co-detection panel reuses NANOG, LIN28A, DNMT3B, DPPA4 and UTF1 from the June 18 audit. The fibroblast-marker panel is COL1A1, COL1A2, DCN, LUM and THY1. POU5F1 and SOX2 remain separate factor-overlap expression markers. No classifier was calibrated from these panels.

The primary observation is detection of at least one UMI for at least two of the five endogenous markers. `identity_low` means the mean log1p(CP10k) fibroblast-marker score is at or below that donor's D0 10th-percentile cutoff. `identity_not_low` is the complementary category; neither category establishes cell fate. All counts below use each donor/time sample's own denominator.

| Donor | Day | Barcodes | At least two endogenous markers detected | Also identity-low |
|---|---:|---:|---:|---:|
| GM00731 | 0 | 5,021 | 0 (0%) | 0 (0%) |
| GM00731 | 3 | 6,318 | 94 (1.488%) | 93 (1.472%) |
| GM00731 | 7 | 6,915 | 852 (12.321%) | 812 (11.743%) |
| GM00731 | 10 | 4,399 | 117 (2.660%) | 105 (2.387%) |
| GM23815 | 0 | 7,782 | 0 (0%) | 0 (0%) |
| GM23815 | 3 | 6,738 | 308 (4.571%) | 308 (4.571%) |
| GM23815 | 7 | 12,209 | 2,851 (23.352%) | 2,687 (22.008%) |
| GM23815 | 10 | 7,935 | 1,112 (14.014%) | 1,005 (12.665%) |

The primary co-detection fraction peaks at D7 in each donor. Most D7 co-detected barcodes also meet the low fibroblast-marker definition. These are different destructive samples, so the D10 reduction cannot establish recovery or the fate of a D7 cell. Sendai OSKM elapsed time is not a controlled withdrawal interval. The donors are ages 96 and 22, respectively, with one donor at each age; the observed between-donor difference does not estimate an age effect.

## Detection and definition sensitivity

The observed fractions depend substantially on detection depth and marker definitions. Requiring at least two UMIs for each of two endogenous markers changes D7 co-detection to 321/6,915 (4.642%) for GM00731 and 1,392/12,209 (11.401%) for GM23815. Across the three frozen 1,000-UMI thinning seeds, the corresponding fractions are 35–51/6,774 (0.517–0.753%) and 299–311/11,552 (2.588–2.692%). These thinned denominators retain only cells with at least 1,000 original Gene Expression UMIs. Sampling uses an exact multivariate-hypergeometric marginal over all twelve distinct panel markers plus one remainder category, so every original Gene Expression UMI participates in the sampling model.

In the frozen numerical schema, `marker_summary.mean_raw_UMI` means mean analyzed UMI count. For `thin1000` variants it summarizes the post-thinning counts; for the other variants it summarizes the original counts among the retained barcodes. The field name is preserved for reproducibility.

Within D0-defined UMI strata, D7 co-detection increases from 4.738% to 32.022% between the lowest and highest strata for GM00731, and from 6.027% to 63.286% for GM23815. This depth association and the thinning response show that detection assumptions materially affect the readout. They do not identify a technical cause, establish that a biological signal is artifactual, or calibrate detection sensitivity/specificity for a true state.

Every single endogenous-marker omission retains observed D7 co-detection: 8.098–11.945% for GM00731 and 16.562–21.451% for GM23815, with the requirement still set to at least two of the four remaining markers. All identity-marker omissions, D0 q05/q20 bounds, the >500-detected-gene filter, four depth strata, and three thinning seeds are retained in [results.json](results.json) and [joint-tables.csv](joint-tables.csv). These variants remain sensitivity analyses; none replaces the frozen primary definition.

The realized D0 identity-low fractions are reported explicitly. For the primary definition they are 503/5,021 (10.018%) and 779/7,782 (10.010%). Quantile ties are more pronounced after thinning: seed 181026 yields 554/5,008 (11.062%) and 792/7,760 (10.206%), despite the nominal q10 cutoff. The output never substitutes “10%” for the observed fraction.

## Interpretation and verification

The result supports joint observations of chosen transcripts and marker scores within barcodes. It does not measure true pluripotent-cell prevalence, rare dangerous-state prevalence, stable identity, transformation risk, rejuvenation or retinal benefit. Zero D0 co-detections provide neither biological-absence proof nor an estimated false-positive rate without ground truth. Ordinary POU5F1/SOX2 counts do not distinguish vector-derived transcripts from endogenous transcripts. Ambient RNA, doublets, selection of deposited barcodes, and dropout remain relevant uncertainties.

The [contract](../percell-contract-proposal.json) and [freeze receipt](../PERCELL_FREEZE.json) precede the new observed computation. Twelve synthetic tests pass. The observed verifier checks every serialized barcode's marker arithmetic and reconstructs the table margins; it also regenerates all numerical outputs byte-for-byte. [VERIFICATION.json](VERIFICATION.json) records 1,854 computational checks and the replay hashes. The original study data and prior June 18 output remain unchanged. All CX004 readouts remain `insufficient_signal`.

Run from this packet's root. Full raw replay first recreates the internal per-barcode derivative:

```sh
uv run human/verify_percell.py
uv run human/percell_audit.py --h5-dir /path/to/GSE297234/raw_h5
uv run human/verify_percell_observed.py --h5-dir /path/to/GSE297234/raw_h5
```

The observed verifier accepts `--h5-dir`, `--freeze` and `--output` overrides. Source matrices must match the cached SHA-256 manifest. The compressed per-barcode derived table is retained internally and excluded from the public package. This is a local-output extension; field novelty is unestablished.

Public aggregate verification requires only the standard library and shipped artifacts:

```sh
python3 human/verify_saved_percell.py
```

That mode checks all 176 donor/time/variant denominators, the full table identities, CSV/JSON equality, and current code/contract/result hashes against the historical full-replay receipt. It opens neither H5 matrices nor the internal per-barcode table. [SAVED_VERIFICATION.json](SAVED_VERIFICATION.json) records that narrower check separately.
