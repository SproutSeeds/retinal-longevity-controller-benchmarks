# Claim: independent mPFC panel reanalysis

- **Verified:** fixed analysis of ten public RNA matrices, with seven primary animal units, produces a cell-cycle CPM difference of -0.1239870991 (OSK minus GFP), conditional p 13/35 and four-panel Holm p 1.0. All specified whole-library normalization and gene/animal omission checks retain a negative sign. Magnitude and mixture limitations remain explicit.
- **Verified:** the microglial marker-bin direction is positive at both prespecified detection thresholds, while several other marker bins have negative directions. All biological comparisons use animal means and retain unsupported bins.
- **Heuristic:** interpreting those marker bins as broad cellular partitions. They are not validated annotations or a safety/identity classifier.
- **Conjecture:** durable human or ocular rejuvenation. The present data do not test that joint claim.

Canonical evidence: [results/](results/), [RAW_AUDIT.json](RAW_AUDIT.json), [REPORT.md](REPORT.md), [decision.json](decision.json). Source and freeze evidence: [SOURCES.json](SOURCES.json), [acquisition.json](acquisition.json), [FREEZE.json](FREEZE.json).

Verification hook: the commands in [REPRODUCTION.md](REPRODUCTION.md) produce six passing synthetic tests, 877 saved-artifact checks, 897 checks when source hashes are included, and 646,760 passing independent raw comparisons. Checks are deterministic under fixed bytes and pinned dependencies. They verify numerical implementation and provenance within the stated design; they do not establish causal benefit or biological safety.

Verification record: **PASS** for scoped computational claims. Full author-pipeline reproduction and target experiment replacement are **INCONCLUSIVE**. See [FAILED_PATHS.md](FAILED_PATHS.md).
