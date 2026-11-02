# Claim: dated assignment-source availability

**Verified:** the exact retained GSE350289 workbook from October 17 has zero exact deposited barcode strings among its cell values. Ctrl and Sample 1 contain 139,938 and 161,422 populated age cells respectively; Sample 2 and Sample 3 have none. The four retained barcode files contain 546,362 unique full strings. A separate openpyxl census agrees with the primary XML reader.

**Verified within named primary-source scope:** the current browser-visible GEO page lists the metadata workbook; the freshly retrieved preprint v1 and its appendix were inspected. GEO describes three donors per age group, while the preprint describes three male plus three female donors per group. This discrepancy remains unresolved.

**INCONCLUSIVE:** fresh workbook content. Current acquisition attempts did not yield an accepted XLSX. The retained-source result does not establish that today's downloadable file is unchanged or that an assignment export is absent from every source.

**Heuristic next action:** ask for the exact intended supplementary file or a corrected barcode-assignment export, plus pool-composition clarification. [NEXT_INPUT_SPEC.json](NEXT_INPUT_SPEC.json) records the required identities and checks. No biological outcome or current mapping is admitted.

Verification hook:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-assignment-recheck-2026-11-01/verify.py
```

Expected: six tests pass and `PASS offline assignment recheck`. Full replay uses `audit.py --cache /path/to/originals`; an independent source census uses `independent_check.py` with openpyxl 3.1.5. [VERIFICATION_RECORD.md](VERIFICATION_RECORD.md) records PASS for retained-source checks and INCONCLUSIVE for current acquisition. Numeric counts and input strings are deterministic; no random, biological or inferential calculation is performed.
