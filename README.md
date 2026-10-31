# Retinal Longevity Controller Benchmarks

<!--
Title: Retinal Longevity Controller Benchmarks
-->

Public data, reproducible analysis and explicit evidence requirements for lineage-preserving reprogramming research. Maintained by SproutSeeds / [Fractal Research Group](https://frg.earth).

**Current scientific checkpoint — October 31, 2026:** [RNA and measured function across eight human-cell studies](programs/partial-reprogramming-controller/benchmarks/linked-function-admission-2026-10-31/REPORT.md) provides a ranked dataset intake table, 177 recovered RNA metadata records and 13 source-labeled RNA comparisons across three Gill donor labels. All eight joint RNA/function admissions remain deferred for missing source-compatible inputs. Acquisition priority is **Heuristic**, with human priority review pending.

The [Gill RNA age and migration function contract](programs/partial-reprogramming-controller/benchmarks/gill-migration-comparison-2026-10-31/README.md) now fixes the molecular readout, culture mapping, duration-specific donor weighting and missing-input rules. Thirteen synthetic software tests check arithmetic and rejection behavior; observed joint comparison remains **DEFERRED**. The published biological outcome is already known.

The [October 26 RPE controller release](research/2026-10-rpe-controller/README.md) contains executable evidence evaluators, source-result tables and exact replay tests. Nine v2 packets retain uncertainty across 23 distinct observations; 56 actual CLI rejection cases enforce the evidence boundary. Biological conclusions remain **Heuristic**; experiment replacement is **INCONCLUSIVE**.

A current-release tAge diagnostic has run. **Exact historical tAge6 reproduction remains pending** on authoritative historical artifacts and preprocessing. No TACO execution is claimed. Earlier preparation documents preserve their original dated status.

- **[Latest reusable RPE controller release](research/2026-10-rpe-controller/README.md)** · [source attribution](research/2026-10-rpe-controller/THIRD_PARTY.md) · [release manifest](research/2026-10-rpe-controller/public-package.json).
- **[Linked RNA/function input audit](programs/partial-reprogramming-controller/benchmarks/linked-function-admission-2026-10-31/README.md)** · [ranked CSV](programs/partial-reprogramming-controller/benchmarks/linked-function-admission-2026-10-31/dataset-shortlist.csv) · [exact next input](programs/partial-reprogramming-controller/benchmarks/linked-function-admission-2026-10-31/NEXT_INPUT_SPEC.json).
- **[Gill frozen comparison](programs/partial-reprogramming-controller/benchmarks/gill-migration-comparison-2026-10-31/ANALYSIS_PLAN.md)** · [input guide](programs/partial-reprogramming-controller/benchmarks/gill-migration-comparison-2026-10-31/README.md) · [observed readiness](programs/partial-reprogramming-controller/benchmarks/gill-migration-comparison-2026-10-31/READINESS.json).
- **[Public research checks](https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks/actions/workflows/research-checks.yml)** run on every public push and pull request. The configured source checkpoint hook publishes approved scientific content after local checks; [update scope and limits](research/2026-10-rpe-controller/README.md#how-updates-reach-this-repository).

- **[Historical clock reproduction preparation](research/2026-10-tage-replay-preparation/README.md)** — input checks, a frozen comparison plan and synthetic software tests; the historical model adapter remains unresolved.
- **[Proposed collaboration brief](research/2026-10-tage-replay-preparation/COLLABORATION_BRIEF.md)** · [plain text](research/2026-10-tage-replay-preparation/COLLABORATION_BRIEF.txt).

- **[Latest evidence and experiment decision](research/2026-10-decision-audit/README.md)** — newly recovered human withdrawal references, an independent seven-animal comparison, and precise remaining data requirements.
- **[Next inputs and conditional measurements](research/2026-10-decision-audit/NEXT_STEPS.md)** · [mouse results figure](research/2026-10-decision-audit/figures/mouse-cycle-comparison.pdf) · [human reference figure](research/2026-10-decision-audit/figures/human-short-withdrawal-reference.pdf).
- **[Earlier neural and human validation](research/2026-10-neural-validation/README.md)** — nine paired neural donors, two tissue cohorts, human marker concentration and 57,317 human barcodes.
- **[Six-slide results presentation](research/2026-10-neural-validation/presentation/retinal-validation-results.pdf)** · [editable PowerPoint](research/2026-10-neural-validation/presentation/retinal-validation-results.pptx) · [next measurements](research/2026-10-neural-validation/NEXT_STEPS.md).
- **[Earlier expression and neural-data checkpoint](research/2026-10-independent-comparator/README.md)** — one-donor human comparison, 3,857 mouse neural cells mapped to seven animals, and donor-balance simulations.
- **[October 18 presentation addendum](research/2026-10-independent-comparator/presentation/retinal-comparator-update.pdf)** · [editable PowerPoint](research/2026-10-independent-comparator/presentation/retinal-comparator-update.pptx) · [next analysis](research/2026-10-independent-comparator/NEXT_STEPS.md).
- **[Latest metadata recovery](research/2026-10-metadata-recovery/README.md)** — 295 recovered clock terms, complete gene coverage, explicit sample joins and remaining replay dependencies.
- **[Research results and reproduction](research/2026-10-public-data/README.md)** — guide-assignment correction, ocular sensitivities, donor-held-out diagnostics and synthetic sampling.
- **[October 17 presentation PDF](presentation/retinal-public-data.pdf)** · [editable PowerPoint](presentation/retinal-public-data.pptx) · [spoken notes](presentation/spoken-notes.txt).
- **[Conditional measurement and funding package](research/2026-10-public-data/MEASUREMENT_PLAN.md)** — 33-library feasibility design, 57-library full ladder, exact missing observations and quote requirements.
- **[Source audit](research/2026-10-public-data/SOURCE_AUDIT.md)** · [next steps](research/2026-10-public-data/NEXT_STEPS.md) · [contribute](CONTRIBUTING.md).

The paired-guide reanalysis yields 208 eligible comparisons; a three-donor classifier recognizes treatment but does not establish benefit. Mouse RPE results depend on which endpoint is being evaluated. Synthetic scenarios show how donor clustering and false positives affect sampling. All four human late-state/recovery readouts remain open.

Our contribution is the analysis, benchmark and evidence decision. Original experiments retain their authorship. No wet-lab operations have been purchased or arranged through this checkpoint.

Quick check, without downloading biological matrices:

```sh
cd research/2026-10-public-data
python3 verify.py
uv run test_analysis.py
```

Existing [controller packages and CLI](docs/previous-overview-2026-10-17.md), [public index](docs/ocular-controller-public-index-v0.md) and [archived release DOI](https://doi.org/10.5281/zenodo.19633942) remain available. The DOI covers an earlier release; cite this research revision by Git commit and date. Our code and authored documentation use [MIT](LICENSE); [third-party terms](research/2026-10-public-data/THIRD_PARTY.md) remain separate.
