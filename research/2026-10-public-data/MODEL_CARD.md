# SRSF1 treatment-recognition diagnostic

**Intended use:** inspect whether fixed expression panels recognize treatment in donor-held-out public libraries. **Claim level: Heuristic.** The model does not predict lifespan, visual function, therapeutic benefit or safety.

Data: GSE325735, three donor lines, two SRSF1 and two BFP libraries per donor, source-labeled five days on/two days off. All 12 libraries share the reported sequencing batch. Experimental batch is missing. These are three biological donor units; the libraries are repeated observations.

Training: three leave-one-donor-out folds; StandardScaler fitted on training donors; balanced logistic regression, C=1, fixed seed, no tuning. Features come from frozen short gene panels. Missing/ambiguous gene identifiers are excluded. All feature names, coefficients, intercepts, scaler statistics, split memberships and held-out probabilities are in `donor-model-results.json`.

| Variant | Mean held-donor AUROC |
|---|---:|
| Fixed expression panels | 1.000 |
| Fixed panels excluding cycle genes | 1.000 |
| Depth and detected genes only | 0.833 |

The 216 balanced within-donor label controls average 0.5 for every variant. They evaluate algorithmic dependence on the labels; their technical-label exchangeability is not a donor-level efficacy test. With four test libraries per fold and only three donors, the perfect observed score has limited generalization authority. Unknown experimental batch, culture conditions and sample handling could contribute.

No trained age clock or foundation model is supplied. Larger training requires a compatible independent study, prespecified labels and a measurable improvement over simpler/nuisance models. Synthetic expression would remain hypothesis-generating and could not serve as the biological test set. The current synthetic work instead evaluates sampling design under explicit assumptions.

Reproduce with `uv run analyze.py human --cache .cache`; use `fetch_inputs.py --group small` first. Source attribution: [original study](https://www.nature.com/articles/s43587-026-01234-8).
