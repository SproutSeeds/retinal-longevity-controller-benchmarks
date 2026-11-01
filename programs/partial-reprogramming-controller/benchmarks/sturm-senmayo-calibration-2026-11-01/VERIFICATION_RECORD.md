# Verification: fixed RNA panel and respiration

**Status: PASS for source-bound numerical calculation.** The biological readout remains **Heuristic**. This record verifies a two-donor descriptive reanalysis; it supplies no intervention, causal, clinical, diagnostic or population validation.

| Check | Record | Result |
| --- | --- | --- |
| Specification precedes panel scoring | `FREEZE.json`; private freeze commit `e69e9decd6728f05bd49944729b74b4ba778121b` | PASS |
| Human panel source | Original Supplementary Data 1, `Gene(human)` sheet; 125 unique symbols; original XLSX fingerprint in `REFERENCE_SOURCE.json` | PASS |
| RNA/source scope | Original GSE179848 matrix hash; exact admitted RNA labels; all 22 eligible records and all 21 source function strings | PASS |
| Panel coverage | 125 of 125 exact source symbols; no missing genes, aliases or substitutes | PASS |
| Full primary replay | `analyze.py --sources /path/to/originals` regenerates all six numeric/data outputs from pinned originals | PASS |
| Independent source-value readback | 2,750 expression strings, 22 source-derived means and 21 original function strings | PASS |
| Independent association checks | NumPy 2.2.6 / SciPy 1.16.3; 56 coefficients, absolute tolerance 1e-10; primary math not imported | PASS |
| Missing-function accounting | Study 372 remains RNA-only; two touching intervals excluded, no bridging | PASS |
| Rejection and synthetic behavior | Twelve tests: ties, exact column identity, nonfinite values, gene duplicates, missing/duplicate RNA labels, time-confounding reversal, coverage threshold, constant residuals, donor permutation and complete leave-one-out accounting | PASS |
| Figure | Source-bound score/respiration trajectories, raw relations and time residuals; PNG visually inspected; matching vector PDF exported | PASS |

Offline verification from the public packet:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/sturm-senmayo-calibration-2026-11-01/verify.py
```

Expected output includes twelve passing tests and `PASS offline calibration`. The offline verifier checks the artifact/freeze fingerprints and recalculates the score and prescribed statistics from the released source strings. This establishes released-data arithmetic; it does not independently reacquire the original matrix.

Full source verification after acquiring the originals identified in the preceding intake and `REFERENCE_SOURCE.json`:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/sturm-senmayo-calibration-2026-11-01/analyze.py --sources /path/to/originals
python3 programs/partial-reprogramming-controller/benchmarks/sturm-senmayo-calibration-2026-11-01/independent_check.py --sources /path/to/originals
```

The second command requires NumPy 2.2.6 and SciPy 1.16.3. Plot regeneration additionally uses Matplotlib 3.10.7. Primary source replay was run with Python 3.14.7; the independent checker used Python 3.12.14. Primary numeric/data outputs are deterministic in the recorded environment; independent comparisons allow absolute error 1e-10. PDF creation timestamps are omitted. Plot metadata or rendering may differ across library/font environments without changing the numeric analysis.

The independently published panel and the source culture study were known before the analysis freeze. No holdout confirmation, prospective preregistration, original GSEA reproduction, clock-age conversion, raw respiration-well reanalysis or investigator experiment replication is claimed. Linear time adjustment leaves nonlinear trends and other culture covariates unresolved. The two donors are the independent people represented; overlapping intervals and repeated measurements do not increase that count.

The observed raw sign difference is confined to this fixed mean-expression index, these source records and this physiological endpoint. It does not establish a general failure of SenMayo, a diagnostic measure of senescence, or a cause of respiratory changes. Gill admissions remain zero and Phase 483 remains a separate supervised-exchange requirement.
