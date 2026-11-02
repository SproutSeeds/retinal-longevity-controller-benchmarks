# GSE350289 workbook recovered; assignment fields remain empty

<!--
Title: GSE350289 workbook recovered; assignment fields remain empty
-->

**Verified:** two successful requests through GEO's file-download endpoint returned the same **1,725,954-byte** workbook. Both payloads match the **October 17** retained copy byte for byte. The newly retrieved workbook contains age values without cell-barcode assignments. Download access was sufficient to verify this file; reliable future availability remains unestablished.

The first accepted response arrived at **2026-11-02 01:16:36 UTC**, followed by a matching independent request at **01:17:56 UTC**. These were November 1 evening in America/Chicago. [ACQUISITION.json](ACQUISITION.json) keeps the actual successful-transfer times. The raw file is retained outside the public repository. Its SHA-256 is `f48a3eba3416110afae897a4df78796379d01211e0b9a436f65d7f4b1f44e76d`.

| Data sheet | Populated data cells | Content | Exact retained barcode strings |
| --- | ---: | --- | ---: |
| Ctrl | 139,938 | Column D ages: 25 or 55 | 0 |
| Sample 1 | 161,422 | Column D age: 55 | 0 |
| Sample 2 | 0 | Empty | 0 |
| Sample 3 | 0 | Empty | 0 |

Columns A through C have no populated values in these data sheets. All 301,360 populated data cells are ages. The README sheet has one separate note. An independent openpyxl 3.1.5 reader agrees with the primary XML census on every sheet, row count, populated column and age count. [INDEPENDENT_CHECK.json](INDEPENDENT_CHECK.json) binds that check to the newly downloaded file.

The barcode comparison uses **546,362** unique strings from the four explicitly retained October 17 barcode archives. Those archives were not newly acquired in this recovery. Their dates and fingerprints remain separate from the newly retrieved workbook in [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json). This workbook supplies no barcode/treatment/donor join. Zero assignments are admitted, and treatment-outcome analysis remains deferred.

## What the download troubleshooting established

The [GEO record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE350289) names `GSE350289_metadata_individual_cells.xlsx`. Two ordinary `curl` requests through the [GEO file-download endpoint](https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE350289&format=file&file=GSE350289%5Fmetadata%5Findividual%5Fcells%2Exlsx) followed a 301 redirect to the official FTP-over-HTTPS file and received complete XLSX payloads. A direct request to that final URL returned 403. A paired Python urllib request through GEO also returned 403. Later curl attempts ended before the advertised workbook bytes arrived.

[TRANSPORT_DIAGNOSIS.json](TRANSPORT_DIAGNOSIS.json) preserves both successes and failures. The observed access depends on client, entry route or time; the exact upstream rule remains **INCONCLUSIVE**. These observations do not identify a browser setting, a user-agent rule or permanent source availability. No authentication control was changed and no CAPTCHA was solved. The successful payloads resolve the earlier acquisition uncertainty for the bytes actually received.

`recover.py` provides one bounded acquisition attempt through the observed successful route. It checks process completion, HTTP status, byte budget, XLSX structure and full archive CRC before admitting a file. It preserves failed attempts, refuses to overwrite an existing cache and does not silently retry or change sources. Network success remains dependent on the host. Seven tests exercise HTTP error and partial-response rejection, empty/HTML bodies, a generic ZIP, CRC corruption, the expanded-size budget and a successful structural case.

## Consequence for the research

The useful next question is the exact intended supplementary filename/direct URL containing the full cell-barcode, perturbation, donor/pool and assignment-QC fields. The [input specification](../gse350289-assignment-recheck-2026-11-01/NEXT_INPUT_SPEC.json) retains the required experimental identities and coverage checks; its earlier acquisition limitation is superseded by this recovery. Another export may exist. The differing pool descriptions in GEO and the preprint still need clarification before individual-donor or biological-replicate claims.

Original investigators retain credit for the experiment, source data and biological findings. This packet contributes source retrieval, exact byte comparison and verification tooling. It redistributes no source workbook, barcode archives, correspondence, original article text or expression matrices. No biological effect, clock result or model training was computed. Gill's missing inputs and the Phase 483 real supervised external exchange remain separate requirements.

Offline verification:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-download-recovery-2026-11-01/verify.py
```

Replay the recorded source comparison with the downloaded workbook and its recorded acquisition receipt, plus the four retained barcode archives:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-download-recovery-2026-11-01/compare.py --cache /path/to/recorded-workbook-and-receipt --retained-barcodes /path/to/retained-barcode-archives
```

A new network attempt uses a new empty cache:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-download-recovery-2026-11-01/recover.py --cache /path/to/new-empty-cache
```

The new network receipt belongs to its own time and must be reviewed separately. A network failure does not erase the recorded successful acquisitions or establish the contents of a file that was never received.
