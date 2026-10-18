# Cell-cycle responses and the missing recovery measurement

<!--
Title: Cell-cycle responses and the missing recovery measurement
-->

The fixed cell-cycle score decreases in **all nine paired mouse neural donors** after 18 hours of Dox/OSKM exposure. That direction survives CPM, median-ratio and within-library rank scoring, plus every single-gene omission. It is the most consistent observed response in this extension. Its connection to lasting rejuvenation remains an open biological question.

This October 18, 2026 reanalysis combines two mouse neural tissue cohorts, paired mouse neural cultures, a human bulk comparison and a human single-cell time course. The original experiments belong to [Xu et al., Nature Aging](https://doi.org/10.1038/s43587-024-00594-3) and [Lu et al., Cell](https://doi.org/10.1016/j.cell.2025.07.031). Our contribution is the reproducible analysis and the checks that constrain its interpretation. Biological novelty has not been established.

**Claim level:** Verified computation; Heuristic biological interpretation. **Experiment replacement: INCONCLUSIVE.** All four CX004 readouts remain `insufficient_signal`.

[Presentation PDF](presentation/retinal-validation-results.pdf) · [editable PowerPoint](presentation/retinal-validation-results.pptx) · [spoken notes](presentation/spoken-notes.txt) · [next measurements and funding decision](NEXT_STEPS.md)

## What the comparisons establish

| Question | Observed result | Interpretation limit |
|---|---|---|
| Do paired neural cultures share a cell-cycle response? | 9/9 donor responses are negative under all three methods. Every single-gene omission preserves every donor's sign. | Acute relative-expression response; drug and construct effects are bundled. Functional arrest and rejuvenation were not measured here. |
| Does age modify the response? | All four primary CPM age contrasts pass their Holm rule; rank sensitivity leaves cycle Holm p = 0.063492 and the other panels at 1. Stress reverses direction under rank scoring. | Four old and five young donors; observational age groups, unverified processing order and method dependence constrain interpretation. |
| Do neural tissue cohorts agree? | Microglial cycle means are negative in both cohorts. Cohort 1 changes sign after omitting individual animals. | Same study, different ages, sex composition and chemistry; two treated and two controls per primary comparison. |
| Is the earlier human bulk score broadly distributed across genes? | CD24 contributes 79.59–89.50% of the seven-gene score change across constructs and original normalizations. | One donor; a positive panel mean does not identify a calibrated pluripotent state. |
| Do endogenous markers occur together in human barcodes? | Day-7 co-detection is 852/6,915 and 2,851/12,209 in the two donors. Counts and fractions drop markedly under stricter detection and equal-depth thinning. | Marker co-detection is observed; true state prevalence, trajectories and recovery are uncalibrated. |
| Can recovered-cell composition conceal opposing changes? | In the primary conditional stress summary, the symmetric composition term is −0.017309 and within-type term +0.012498. | Exact algebra on two admitted types, retaining 58.8–68.1% of recovered cells. Convention and depth sensitivities limit biological attribution. |

The paired-culture result is documented in [bulk/RESULTS.md](bulk/RESULTS.md). The secondary four-panel donor sign-test family gives cell-cycle Holm p = 0.015625. Primary age-label permutation tests enumerate all 126 assignments under an exchangeability assumption. The age comparison does not inherit treatment randomization. The overlap-excluded reprogramming age contrast is dominated by Nanog and reverses when Nanog is omitted.

The [two-cohort analysis](analysis/ANALYSIS.md) retains every support failure and animal/lane/gene sensitivity. The [human correction](human/ADDENDUM.md) preserves the earlier arithmetic and numerical artifacts while narrowing the interpretation. The [human time course](human/percell/REPORT.md) reports all 22 frozen measurement variants across eight samples and 57,317 barcodes. GM00731 also supplies the bulk comparison, so these analyses represent two human donors in total.

The [composition analysis](decomposition/README.md) and its [post hoc extension](decomposition/EXTENSION.md) report both one-sided conventions, every gene contribution and three fixed-depth repetitions. These are different summaries from pseudobulk and do not estimate causal tissue-composition effects.

## Existing samples could still fill part of the gap

The [source reconciliation](recovery/RECOVERY.md) identifies **seven already-sequenced samples** missing from the shared whole-body analysis objects. Five carry a `2Dox5` author label. Complete barcode-to-animal assignments and exact removal-to-harvest timing are required before using them as withdrawal evidence. The [missing-input specification](recovery/missing-inputs.json) lists the smallest useful deliverables. It is a data specification, not a sent request.

The current datasets expand the reusable evidence, but do not establish the required matched late human recovery observation. Adult identity, age improvement, calibrated unusual-state assessment and persistence after factor withdrawal still need compatible measurements. Mouse neural findings also require an explicit ocular bridge. [NEXT_STEPS.md](NEXT_STEPS.md) gives the decision rules for recovering existing data and, if necessary, preparing a funding package for new measurements. No wet-lab operations were purchased or arranged.

## Reproduce and inspect

Run from this directory with Python 3.12:

```sh
python3 verify.py
python3 run_checks.py
```

The first command verifies artifact hashes and the reported numerical claims without third-party Python dependencies or biological downloads. The second uses `uv` and pinned script environments to run the saved-output and synthetic checks in a temporary copy. It does not fetch biological matrices or alter the published receipts. Dependency installation may use the network.

Observed-data replay is separate and opt-in. [REPRODUCTION.md](REPRODUCTION.md) lists source sizes, hashes and exact commands. [`fetch_inputs.py`](fetch_inputs.py) requires an explicit source group and cache path; it fails if the source bytes have changed. Tests and thinning diagnostics create no new biological observations.

Contracts were frozen before their respective new outcome runs. The cohort-1 contract followed cohort-2 results; the human concentration audit and decomposition extension are explicitly post hoc. [METHODS.md](METHODS.md), [CLAIM.md](CLAIM.md), [FAILED_PATHS.md](FAILED_PATHS.md) and [REVIEW.md](REVIEW.md) preserve those distinctions. Code and authored text use the repository's MIT license; [third-party terms](THIRD_PARTY.md) remain separate.
