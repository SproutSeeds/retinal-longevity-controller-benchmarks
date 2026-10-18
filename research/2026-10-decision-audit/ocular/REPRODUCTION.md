# Reproduce the independent mPFC audit

Run from this `ocular/` directory. The original computation used Python 3.12.11, NumPy 2.5.4 and h5py 3.15.1. Dependencies run locally; no cloud service or paid compute is required.

## Check the published aggregate artifacts

```sh
uv run --python 3.12 --with numpy==2.5.4 --with h5py==3.15.1 python test_analysis.py
uv run --python 3.12 --with numpy==2.5.4 --with h5py==3.15.1 python verify.py --receipt /tmp/cx004-mpfc-saved-checks.json
```

Expected: six synthetic tests `OK`; verification `PASS`, with **877 checks** when the optional raw-source hashes are omitted. This path independently recalculates normalization, animal-level scores, contrasts, gene/animal omissions, exact label enumeration, and fixed support accounting from the saved full-gene pseudobulk counts. It also checks output hashes and the original acquisition manifest. It does not reread source barcodes.

## Acquire and replay the source matrices

The ten public 10X H5 files total 721,204,825 bytes. Their RNA and ATAC count features coexist in each H5; the analysis uses RNA features and RNA library totals only. No raw sequencing reads or ATAC fragments are needed.

Choose a cache filesystem with at least 8 GB free after the downloads. On the original machine, the code drive was below that floor, so source files were stored on the internal filesystem at `/private/tmp/cx004-decision-audit-2026-10-18/ocular`.

```sh
uv run --python 3.12 --with numpy==2.5.4 --with h5py==3.15.1 python analyze.py fetch --cache /tmp/cx004-mpfc-inputs
uv run --python 3.12 --with numpy==2.5.4 --with h5py==3.15.1 python analyze.py run --cache /tmp/cx004-mpfc-inputs --output /tmp/cx004-mpfc-replay
uv run --python 3.12 --with numpy==2.5.4 --with h5py==3.15.1 python verify.py --cache /tmp/cx004-mpfc-inputs --output /tmp/cx004-mpfc-replay --receipt /tmp/cx004-mpfc-replay-checks.json
uv run --python 3.12 --with numpy==2.5.4 --with h5py==3.15.1 python raw_audit.py --cache /tmp/cx004-mpfc-inputs --output /tmp/cx004-mpfc-replay --receipt /tmp/cx004-mpfc-raw-checks.json
```

Expected: all ten acquisition checks pass; the RNA QC total is 34,210 of 35,907 deposited nuclei; aggregate/source verification is **897/897 PASS**; the independent raw recount is **646,760/646,760 PASS**.

`FREEZE.json` fixes the exact analysis, test, contract, admission and panel bytes. Execution checks the analysis, contract, admission and panels; the verifier also checks the frozen test bytes. Original design and pre-outcome amendment receipts are preserved. The source acquisition records include exact URLs, byte counts and SHA-256 hashes. The verifier compares replay sources with the published [acquisition.json](acquisition.json), as well as the execution receipt.

## Scope and determinism

There is no random seed or stochastic model training. The seven-animal comparison enumerates all 35 four-versus-three assignments. Fixed detection thresholds generate exhaustive marker-bin support records. The same source bytes, frozen code and listed software versions reproduce the numerical CSVs and compressed pseudobulk artifact; environment receipts may differ if a different interpreter is selected.

The raw audit uses an independent cell-at-a-time CSC reader and integer cross-products for mitochondrial QC. It checks every RNA gene's aggregate, every bin's nucleus count/depth, and all per-animal bin-panel scores. It evaluates the frozen endpoints without selecting additional biological outcomes.

Source metadata and all limitations are in [SOURCES.json](SOURCES.json), [admission.json](admission.json), and [REPORT.md](REPORT.md). These checks validate the numerical audit, not retinal efficacy, cell identity, a published clock, or biological safety.
