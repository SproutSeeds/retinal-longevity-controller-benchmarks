# Claim: public parameters and sample identities narrow the replay gap

**Verified:** 295 numerical clock terms were extracted from the cited supplement; all 292 gene terms match the pinned human count matrix. Seventy-two human withdrawal libraries map to exact count columns, with 32 mouse withdrawal libraries separated. Source receipts, `srsf1-clock-parameters.json` and `srsf1-recovery-samples.json` are the evidence.

**Heuristic:** the recovered inputs reduce exact-replay dependencies but do not establish age reversal, safety, retinal function or matched late human recovery. All four readouts remain insufficient_signal; experiment replacement is INCONCLUSIVE.

Verification hook: `python3 verify.py` and `python3 test_recovery.py`; expected PASS and eight tests OK. Extraction hook: `python3 recover_metadata.py --cache <verified-source-cache> --counts <pinned-human-counts> --clock-git <pinned-source-history>`. Standard-library parsing and exact hashes are deterministic; metadata is a dated snapshot. `VERIFICATION.json` records the actual result.

Next falsification/update hook: provide a new source artifact with exact sample IDs, source-native chronology, model preprocessing or a compatible matched late human cohort, then rerun the corresponding admission check. External Phase 483 and the mitochondrial program remain unchanged.
