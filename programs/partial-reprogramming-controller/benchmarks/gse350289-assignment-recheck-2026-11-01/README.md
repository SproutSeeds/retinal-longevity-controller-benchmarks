# GSE350289 assignment keys remain unverified

<!--
Title: GSE350289 assignment keys remain unverified
-->

**Later source update:** [workbook recovery](../gse350289-download-recovery-2026-11-01/README.md) supersedes this audit's download status. Two successful responses received after this audit contain the same workbook bytes as October 17; the missing assignment fields are now verified in a newly retrieved copy. The original acquisition attempts below remain dated evidence.

**Verified retained-source result at the 2026-11-02 00:14 UTC audit cutoff:** the metadata workbook acquired on **October 17, 2026** contains none of the **546,362** full barcode strings in the four retained barcode files. At that cutoff, a current copy of the workbook was **not acquired successfully**. Its content was **INCONCLUSIVE**, and zero current cell-to-perturbation assignments were admitted.

The [GEO record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE350289) visibly lists the same metadata filename, `GSE350289_metadata_individual_cells.xlsx`, alongside four matrix/barcode/feature sets and a target-gene list. The browser-visible page displays an October 13 last-update date and 769 library records. These observations establish file discovery. They do not establish current file contents or a cell-assignment join.

| Processed group | Retained barcode records | Populated metadata rows in retained workbook | Exact barcode cells |
| --- | ---: | ---: | ---: |
| Ctrl | 146,838 | 139,938 | 0 |
| Sample 1 | 163,533 | 161,422 | 0 |
| Sample 2 | 109,683 | 0 | 0 |
| Sample 3 | 126,308 | 0 | 0 |

All populated data cells in Ctrl and Sample 1 are in column D and contain ages. Columns A through C have no populated values. Sample 2 and Sample 3 contain no populated cell values. The README sheet is counted separately. The retained workbook fingerprint is `f48a3eba3416110afae897a4df78796379d01211e0b9a436f65d7f4b1f44e76d`. Its source dates and the five retained file hashes are explicit in [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json).

The four barcode files have 546,362 unique full strings in total. Matching row counts or assuming worksheet order would not establish which treatment or donor/pool belongs to a barcode. The age-only workbook cannot supply those experimental identities.

The [October 23 preprint, version 1](https://doi.org/10.64898/2026.10.21.760791), was inspected through its full article XML and visible text. Its appendix contains ten supplementary figures and one table. The inspected XML has no supplementary-material download elements, and no explicit GitHub repository URL was recovered there. Its data-availability statement directs the single-cell data to GSE350289. This is a bounded inspection of these named surfaces; a separate assignment export may exist elsewhere.

The source descriptions also need reconciliation. GEO describes three pooled donors per age group. The preprint describes three male and three female donors per age group, implying six. These descriptions remain separate in [RESULTS.json](RESULTS.json). They support a clarification request, not an inferred donor count or individual donor assignment.

Current acquisition attempts produced zero-length files, HTML in place of an XLSX, a timeout or HTTP 403. The browser download reported `net::ERR_BLOCKED_BY_CLIENT`. The received bodies were not accepted as workbook data. [ACQUISITION.json](ACQUISITION.json) preserves the attempts, while [GEO_VISIBLE_FACTS.json](GEO_VISIBLE_FACTS.json) records only the relevant visible facts. The successful recheck of retained originals does not establish that today's workbook is unchanged.

The next useful input is the exact intended supplementary filename/direct URL or a corrected export. [NEXT_INPUT_SPEC.json](NEXT_INPUT_SPEC.json) names the needed library, full barcode, perturbation, donor/pool and assignment-QC fields. Explicitly excluded or unassigned cells should have source-supported dispositions. A mapping must account for coverage against each processed group's barcode file before treatment analysis proceeds. Pool membership and exposure/harvest context remain explicit requirements.

Original investigators retain credit for the experiment, data and biological findings. This packet contributes a dated source audit and an actionable input specification. It contains no correspondence, original article text, source workbook, barcode archives or expression matrices. The preprint's reported CC BY-NC terms are recorded; no original figures or article text are redistributed.

Perturbation-level outcome analysis remains paused on assignment evidence. No new biological effect, clock result or model training was computed. Gill's missing inputs and the Phase 483 supervised external exchange remain separate requirements.

Offline artifact and source-freshness checks:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-assignment-recheck-2026-11-01/verify.py
```

Full source replay with the exact originals pinned in the manifest:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-assignment-recheck-2026-11-01/audit.py --cache /path/to/originals
```

An independent read-only census with openpyxl 3.1.5 agrees on all five sheets and 301,360 populated data cells, all age entries. [INDEPENDENT_CHECK.json](INDEPENDENT_CHECK.json) and [VERIFICATION_RECORD.md](VERIFICATION_RECORD.md) distinguish that verified historical content from the unresolved current download.
