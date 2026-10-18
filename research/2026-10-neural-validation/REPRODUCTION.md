# Repeating the saved checks and observed analyses

Run commands from this packet's root directory. Python 3.12 and `uv` are required for pinned scientific environments. The public repository also retains the preceding `2026-10-independent-comparator` packet beside this directory; six of its immutable files are checked by the human bulk audit.

```sh
python3 verify.py
python3 run_checks.py --receipt /tmp/neural-validation-checks.json
```

`verify.py` reads the published hash manifest and selected summaries. `run_checks.py` copies the explicit public allowlist and the six required historical inputs into temporary storage, then runs every saved-output verifier and synthetic suite. It leaves the released receipts and data unchanged. Python dependencies may be fetched by `uv`; no biological source download runs in this mode.

The original checks include 3,534 neural checks/43 tests, 284 parent-decomposition checks/10 tests, 24,732 extension checks/25 tests, 16 human bulk tests, 12 per-cell tests, 4,129 saved per-cell checks, 100 saved paired-bulk checks and 20 paired-bulk tests. Recovery also runs nine barcode adversaries; its portable mode verifies the shipped source snapshots and explicitly skips unavailable raw-cache inputs. Check counts describe implementation coverage, not statistical evidence strength.

## Optional observed-data replay

`inputs.json` specifies 14 inputs totaling 593,168,342 bytes across all four groups. The human time course accounts for 279,039,125 bytes. The fetcher keeps at least 8 GiB free after each bounded acquisition and rejects changed hashes or conflicting cache files. Live metadata or HGNC snapshots can change: a hash mismatch requires retrieving the original version or documenting a new analysis revision, rather than substituting current bytes.

Choose only the required groups and a cache with enough space:

```sh
python3 fetch_inputs.py --list
python3 fetch_inputs.py --group neural --cache /tmp/retinal-replay-inputs
python3 fetch_inputs.py --group neural-bulk --cache /tmp/retinal-replay-inputs
python3 fetch_inputs.py --group human-bulk --cache /tmp/retinal-replay-inputs
python3 fetch_inputs.py --group human-timecourse --cache /tmp/retinal-replay-inputs
```

Run full replay from a disposable copy of this packet to preserve historical verification receipts. The saved outputs are deterministic under the pinned software; execution receipts distinguish original Git chronology checks from public archived-hash replay. Original private Git commits are not claimed to have been independently reconstructed by the public mode.

```sh
uv run --script analysis/reproduce.py --cohort1-cache /tmp/retinal-replay-inputs --cohort2-cache /tmp/retinal-replay-inputs
uv run --script decomposition/reproduce.py --cache /tmp/retinal-replay-inputs
uv run --script decomposition/extension.py --replay-frozen-hashes --cache /tmp/retinal-replay-inputs --output /tmp/extension-replay.json
uv run --script bulk/analyze.py --replay-frozen-hashes --cache /tmp/retinal-replay-inputs --output /tmp/bulk-replay
uv run --script bulk/verify_results.py --cache /tmp/retinal-replay-inputs --result-dir /tmp/bulk-replay --output /tmp/bulk-replay-checks
python3 human/verify_marker_audit.py --cache /tmp/retinal-replay-inputs
uv run --script human/percell_audit.py --h5-dir /tmp/retinal-replay-inputs --output /tmp/human-percell-replay
uv run --script human/verify_percell_observed.py --h5-dir /tmp/retinal-replay-inputs --output /tmp/human-percell-replay
```

The first two replay tools compare regenerated numerical bytes to their archived references. The bulk independent verifier recalculates from raw counts; historical portable replay also compared the numerical arrays and contribution CSV, while excluding provenance fields that correctly differ by execution mode. Human bulk verification independently reproduces the earlier arithmetic and checks its immutable input hashes. The per-cell verifier recounts the complete observed matrix and compares the generated outputs.

The raw recovery audit has a separate source manifest, including an 83.4-MB publisher workbook, metadata snapshots and small GEO barcode/feature files. It is not required for numerical replay above. Its full local result is recorded in `recovery/verification.json`; the public command `python3 recovery/verify_recovery.py --artifacts-only --output /tmp/recovery-checks.json` states which raw inputs it did not inspect.

## Figures and presentation

`uv run --script plot_results.py` rebuilds the three standalone scientific figures from saved results. `figures/SOURCES.json` binds the numerical sources and plotting code. The editable PowerPoint and PDF are provided in `presentation/`; `presentation/build.mjs` records the native charts/tables and source values. Rebuilding that deck requires the Artifact Tool runtime described in `presentation/README.md`. The spoken `.txt` and `.md` companions contain identical wording.
