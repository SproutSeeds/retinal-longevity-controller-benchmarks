# Claim: recovered GSE350289 workbook content

**Verified:** two successful ordinary curl transfers through the named GEO download endpoint returned identical 1,725,954-byte XLSX payloads. The payload is byte-identical to the October 17 retained workbook. Its data sheets contain only age values or are empty; no exact string from the four retained barcode archives occurs among their values. Independent openpyxl and primary XML readers agree on all five sheets and 301,360 age data cells. See [RESULTS.json](RESULTS.json), [ACQUISITION.json](ACQUISITION.json) and [INDEPENDENT_CHECK.json](INDEPENDENT_CHECK.json).

**INCONCLUSIVE:** the exact upstream cause of the mixed transfer outcomes and future download reliability. Successful acquisition of this file does not establish that all supplementary exports have been found. [TRANSPORT_DIAGNOSIS.json](TRANSPORT_DIAGNOSIS.json) records successes, later failures and the optional barcode-refresh attempt that did not acquire new barcode data.

**Heuristic next action:** ask which exact export contains the required experimental assignment keys. Current workbook inspection now supports that specific question. Zero assignments and zero biological outcomes are admitted. Original donor/pool and assignment-QC requirements remain intact.

Verification hook:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-download-recovery-2026-11-01/verify.py
```

Expected: seven tests pass and `PASS recovered workbook`. Raw-source replay uses `compare.py` with the pinned newly downloaded workbook/acquisition receipt and separately dated barcode archives. Independent source replay uses `independent_check.py` with openpyxl 3.1.5. [VERIFICATION_RECORD.md](VERIFICATION_RECORD.md) records PASS for recovered content and INCONCLUSIVE for the upstream cause. Hashes and scalar counts are deterministic; network success is not guaranteed.
