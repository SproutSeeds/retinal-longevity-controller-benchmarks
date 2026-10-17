# Contributing

The most useful contribution is an exact public observation that resolves a named gap, or a reproducible correction to an existing analysis.

For a dataset, include its primary paper/deposit, species and lineage, donor and sample identifiers, intervention/withdrawal timing, assay, relevant file URLs and reuse terms. Explain which of the four readouts it supplies. A study's title or abstract alone is not admission evidence.

For code, use a scoped pull request with the problem, change, verification and remaining scientific limits. Preserve negative results. Keep source-native identifiers and distinguish biological donors from cells, libraries, pooled animals and paired modalities. Test splits must separate the relevant biological unit.

Run `python3 research/2026-10-public-data/verify.py` and `uv run research/2026-10-public-data/test_analysis.py`. Larger reanalyses should freeze their comparison, exclusions and stopping rule before outcome inspection. Record source hashes, methods and dependencies. An altered source hash requires explicit review rather than bypassing verification.

Synthetic data belong in separate artifacts with assumptions and seeds. They cannot act as observed ground truth or close a biological evidence requirement. Model contributions need a compatible independent test set and comparisons with simple/nuisance baselines.

Publish only material you have the right to share. Keep patient identifiers, restricted datasets, credentials and private correspondence out of issues, commits and attachments. See the source audit for metadata requests that could materially change the current decision.
