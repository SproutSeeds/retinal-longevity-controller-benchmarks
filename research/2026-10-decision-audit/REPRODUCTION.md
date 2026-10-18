# Reproduce the decision packet

Use this directory as the working directory. The public path is `research/2026-10-decision-audit`. Saved-output checks require no biological download. They verify the stated calculations and provenance; the biological decision remains INCONCLUSIVE.

```sh
python3 verify.py
python3 run_checks.py
```

The first uses the standard library and checks the reviewed publication allowlist, file hashes, source bindings, key counts and decision projection. The second uses a temporary copy and runs eight commands: the integrated projection, human arithmetic, replicate-numbering audit, human failure controls, recovery metadata, recovery failure controls, mouse failure controls and mouse saved-aggregate verification. It requires `uv`; numerical dependencies are pinned to Python 3.12, NumPy 2.5.4 and h5py 3.15.1. It downloads no biological matrices and changes no published artifact.

See `VERIFICATION.json` and `PORTABLE_CHECKS.json` for the actual outcome and command results. There are 28 synthetic regression/failure-control tests across the three lanes. Individual arithmetic-check counts are implementation checks, not experimental replications.

## Source-based checks

- **Human:** [VERIFICATION.md](human/VERIFICATION.md) describes retrieving 48 successful source objects, authenticating their bytes and replaying ten derived outputs. Publisher workbooks are fetched from their own URLs. All frozen receipts and post-inspection corrections are preserved.
- **Mouse:** [REPRODUCTION.md](ocular/REPRODUCTION.md) provides acquisition, full analysis and independent raw recount commands. The ten public H5 matrices total 721,204,825 bytes. The original source run and its independently implemented recount both passed. Keep at least 8 GB free on the chosen cache filesystem after acquisition.
- **Withdrawal inventory:** [REPORT.md](recovery/REPORT.md) describes the portable rebuild and strict source-byte check. Full PDFs stay at their primary sources; the indexed inventory snapshots are included. Thesis interpretation is a recorded source review, separate from code arithmetic.
- **GSE350289 recheck:** fetch the three objects in the assignment plan into a temporary cache, then compare the exact source bytes with the recorded checkpoint:

```sh
python3 human/fetch_sources.py assignment/source-plan.json \
  --cache /tmp/cx004-assignment-inputs --receipt /tmp/cx004-assignment-fetch.json
python3 assignment/inspect_assignment.py --cache /tmp/cx004-assignment-inputs
```

A changed live source should fail the recorded hash requirement. Preserve the old checkpoint, audit the new source, and create a new evidence revision. Do not overwrite a published receipt to force equality.

## Figures and review

`uv run plot_results.py` regenerates two PNG/PDF figure pairs from the saved numerical outputs. Their input and generator hashes are in [figures/SOURCES.json](figures/SOURCES.json). These are descriptive figures; they add no model fit, hypothesis test or inferred biological observation. Both figure layouts were visually inspected after rendering.

Independent cross-lane review and disposition of its findings are recorded in [REVIEW.md](REVIEW.md). Original study code was inspected for methods/dependencies, without executing unlicensed author code. No private correspondence, raw human barcode table or original count matrix is needed for the portable public check.
