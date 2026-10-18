# Retinal Longevity Controller Benchmarks

Public data, reproducible analysis and explicit evidence requirements for lineage-preserving reprogramming research. Maintained by SproutSeeds / [Fractal Research Group](https://frg.earth).

**Current checkpoint — October 18, 2026 UTC:** public data support substantial analysis and a smaller, better-defined measurement request. The matched late human recovery observation remains unresolved. Biological conclusions are **Heuristic**; experiment replacement is **INCONCLUSIVE**.

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
