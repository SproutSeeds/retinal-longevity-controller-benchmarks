# Retinal Longevity Controller Benchmarks

Public data, reproducible analysis and explicit evidence requirements for lineage-preserving reprogramming research. Maintained by SproutSeeds / [Fractal Research Group](https://frg.earth).

**Current checkpoint — October 17, 2026:** public data support substantial analysis and a smaller, better-defined measurement request. The matched late human recovery observation remains unresolved. Biological conclusions are **Heuristic**; experiment replacement is **INCONCLUSIVE**.

- **[Research results and reproduction](research/2026-10-public-data/README.md)** — guide-assignment correction, ocular sensitivities, donor-held-out diagnostics and synthetic sampling.
- **[Presentation PDF](presentation/retinal-public-data.pdf)** · [editable PowerPoint](presentation/retinal-public-data.pptx) · [spoken notes](presentation/spoken-notes.txt).
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
