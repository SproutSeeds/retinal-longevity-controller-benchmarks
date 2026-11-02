# Verification: workbook acquisition recovered

**PASS:** received workbook bytes and content. **INCONCLUSIVE:** upstream access rule and persistent availability. No biological assignment or outcome is admitted.

| Check | Result |
| --- | --- |
| Two accepted complete workbook transfers, at 01:16:36 and 01:17:56 UTC on November 2 | PASS |
| Payload byte comparison between the two newly retrieved responses | PASS |
| Newly retrieved workbook bytes equal retained October 17 workbook | PASS |
| HTTP 200, complete process exit, XLSX parts and all ZIP member CRCs | PASS |
| All five workbook sheets parsed with the primary XML reader | PASS |
| Independent openpyxl 3.1.5 census of every sheet, row, populated column and age count | PASS |
| 301,360 data cells, all age entries; two empty data sheets | PASS |
| Four retained barcode archive fingerprints and all 546,362 unique full strings checked | PASS; retained inputs only |
| Four current barcode files newly acquired | INCONCLUSIVE; optional attempt failed and expansion stopped |
| Seven transfer/format-admission tests | PASS |
| Exact upstream explanation for differing transfer outcomes | INCONCLUSIVE |
| Current workbook provides a usable cell-to-treatment/donor/pool assignment | FAIL; no keys, zero assignments admitted |

Offline hook:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-download-recovery-2026-11-01/verify.py
```

Pinned-source replay:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-download-recovery-2026-11-01/compare.py --cache /path/to/recorded-workbook-and-receipt --retained-barcodes /path/to/retained-barcode-archives
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-download-recovery-2026-11-01/independent_check.py --cache /path/to/recorded-workbook-and-receipt
```

The second command requires openpyxl 3.1.5 and imports no primary census implementation. Public offline verification binds the recorded counts, freshness fields and receipts; it does not perform a new network acquisition or independent biological replication. Full source replay requires the original downloaded bytes and acquisition receipt. The comparison of source bytes, archive fingerprints and counts is deterministic.

The rejected empty transfers remain explicit failed paths in TRANSPORT_DIAGNOSIS.json. Two full source responses remain available and pass integrity checks. Successful format admission alone does not infer experimental identities. No row-order matching, expression-based label inference, model training or raw-matrix acquisition was performed.
