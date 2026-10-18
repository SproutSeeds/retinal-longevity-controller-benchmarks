# Claim: expression robustness and animal-resolved reuse

**Verified computational claim:** the eight-library human matrix joins to one donor under a disclosed reversible metadata alias; all 46 fixed-panel genes are present; the ten panel contrasts are reproducible. The OSK stress contrast reverses sign between the two fixed normalizations. The mouse neural cohort-2 object joins 3,857 cells to raw counts and seven animal identities, with no retained withdrawal cells. Seventy-two hypothetical sampling scenarios pass numerical checks.

Canonical evidence: `human-results.json`, `neural-admission.json`, `synthetic-results.json`, the original source receipts and frozen `input-files.json`. ORP/process documents do not supply biological evidence.

**Heuristic interpretation:** the human panels describe expression changes and normalization sensitivity; the neural object supports a future animal-level comparator; donor balance and classifier calibration matter under the specified synthetic assumptions. These results do not establish age reversal, retinal benefit, transformation safety or stable late human recovery. Experiment replacement remains INCONCLUSIVE.

Verification hook: `python3 verify.py` and `uv run test_analysis.py`, expected PASS and 15 tests OK. Complete observed-data replay: `python3 run_validation.py --cache <verified-input-cache>`, expected three byte-identical result JSON files. `VERIFICATION.json`, `TESTS.json` and `REPRODUCTION.json` record the actual outcomes. Runtime dependencies and source hashes are pinned; graphical/PDF byte identity is not promised.

Falsification/update hook: a changed source checksum, conflicting sample identity, missing panel coverage, arithmetic discrepancy or incompatible animal metadata fails the corresponding gate. A compatible observed late human dataset can change readout admission. A normalization-sensitive score must retain its failed robustness finding. No controller phase or root mitochondrial claim is advanced by this checkpoint.
