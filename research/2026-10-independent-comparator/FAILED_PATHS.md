# Failed paths and next hooks

| Attempt | Finding | Consequence and next hook |
|---|---|---|
| Original exact-string human sample join | GEO uses `OSK_0D_1`; matrix uses `OSK_D0_1` | Exact match FAIL preserved. The committed amendment admits only a reversible format permutation, with title/treatment/species/donor agreement. Other mismatches still fail. |
| First download into the external-drive cache | Available space was below the 8 GB floor | Zero files fetched. New inputs used a separate internal temporary cache; existing data were untouched. |
| Historical HGNC FTP endpoint | HTTP 404 | Official current download endpoint succeeded; freeze its exact SHA-256 and stop if the upstream snapshot changes. |
| OSK stress direction robust to normalization | Primary +0.258; sensitivity -0.113 | Robust direction FAIL. Report both methods and retain the ambiguity; no favorable method selection. |
| Author-code groups equal deposited groups | Twelve source labels, seven retained animals; withdrawal and BL6 labels have zero cells | Source labels/factor levels cannot create observations. Retrieve broader compatible data before any withdrawal analysis. |
| Young/old age comparison independent of lane | Both young animals are in lane 3 | No unconfounded age-reversal inference. Old treated/control comparisons require a lane-matched sensitivity. |
| Perfect-zero flag boundary via quadrature | Floating-point integration returned 0.9999999999999998 instead of 1 for no-flag probability | Added the analytic constant-q branch when sensitivity equals false-positive rate. Boundary test now passes; published scenario results are unchanged. |
| New public sources replace the full late-human experiment | Human data have one donor and no recovery arm; neural data are mouse and omit withdrawal | Replacement INCONCLUSIVE. Continue explicit reuse checks and fund only remaining matched measurements if needed. |

All failed assumptions remain visible alongside successful computations. Numerical correctness is a narrower claim than biological validity.
