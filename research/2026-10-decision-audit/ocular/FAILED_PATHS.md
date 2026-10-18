# Failed or incomplete paths

## FP-OCULAR-001: full author RNA-processing reproduction

- Claim level: **Heuristic** for any explanation; numerical mismatch **Verified**.
- Status: **INCONCLUSIVE** for the author pipeline; our independently checked frozen QC is **PASS**.
- Attempt: apply the reported RNA count, feature, and mitochondrial thresholds to the ten deposited filtered matrices.
- Observation: 34,210 retained nuclei, compared with 34,603 described in the paper; discrepancy 393. Both our block reader and an independent cell-at-a-time reader produce 34,210.
- Missing inputs: exact author barcode inclusion/annotation table, complete per-barcode metrics and object/reference versions. Published scripts refer to local objects that are not in the inspected repository or retrieved GEO file listing.
- What this rules out: describing this audit as an exact replay of the full author RNA/ATAC integration, annotation or engram pipeline.
- Next hook: obtain the original included barcodes and processing metadata, then compare memberships before changing thresholds or interpreting the difference. No source error or biological failure is inferred from the mismatch.

## FP-OCULAR-002: decisive four-panel significance from this sample count

- Claim level: **Exact** combinatorial constraint under the frozen test.
- Status: **FAIL** for a decisive corrected-significance claim.
- Blocking condition: four treated and three control animals provide 35 complete label assignments. The minimum p is at least 1/35, exceeding the first four-test Holm threshold 0.0125.
- Next hook: independent animals and prespecified design, if available; retain this estimate as descriptive. Removing panels after seeing results or treating nuclei as independent animals is not an admissible remedy.
- Verification hook: `python test_analysis.py` in the pinned environment; six tests pass, including the 35-assignment calculation.

## FP-OCULAR-003: target recovery experiment replacement

- Claim level: **Heuristic** for replacement; status **INCONCLUSIVE**.
- Blocking condition: the admitted data are mouse mPFC endpoint observations after an intended OSK pulse. They do not jointly measure the target adult human/ocular age, identity, unusual-state and verified withdrawal-recovery outcomes.
- Next hook: recover compatible already-collected target observations, or specify the smallest missing measurement. The current audit alone cannot establish that new wet-lab work is unavoidable worldwide.
