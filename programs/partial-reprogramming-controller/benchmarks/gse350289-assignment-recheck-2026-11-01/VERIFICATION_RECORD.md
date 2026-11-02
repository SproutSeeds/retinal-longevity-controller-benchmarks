# Verification: GSE350289 assignment source recheck

**PASS for retained-source content and bounded source review. INCONCLUSIVE for current workbook acquisition.** This is source bookkeeping, not a treatment, biological-age or rejuvenation result.

| Check | Result |
| --- | --- |
| Eight source fingerprints, with five retained originals distinguished from three newly retrieved preprint records | PASS |
| Retained original workbook fingerprint equals the October 17 audit | PASS |
| All four barcode archives read through gzip validation; 546,362 unique full barcode strings counted | PASS |
| Primary XML worksheet census: five sheets, 301,360 populated age cells and zero exact barcode cells | PASS |
| Independent openpyxl 3.1.5 census of all five sheets | PASS |
| Fresh preprint v1 article XML title/version and appendix inspected | PASS within that source scope |
| Browser-visible GEO metadata and fourteen listed supplementary filenames inspected | PASS for visible discovery facts |
| Current workbook retrieved as valid XLSX | INCONCLUSIVE; no accepted body |
| Exact current library/barcode-to-treatment and donor/pool assignments verified | INCONCLUSIVE; zero admitted keys |
| Pool descriptions reconciled | INCONCLUSIVE; GEO three versus preprint six per age group |
| Six source-admission tests | PASS |

Offline hook:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-assignment-recheck-2026-11-01/verify.py
```

Full pinned-source replay:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-assignment-recheck-2026-11-01/audit.py --cache /path/to/originals
python3 programs/partial-reprogramming-controller/benchmarks/gse350289-assignment-recheck-2026-11-01/independent_check.py --cache /path/to/originals
```

The second command requires openpyxl 3.1.5. Primary parsing uses Python's standard-library ZIP/XML readers and never executes investigator code or spreadsheet formulas. Source-derived JSON is deterministic in the recorded inputs. Offline verification checks released receipts and their arithmetic/consistency; independent original acquisition requires the named source files and its own successful transport check.

Tests reject empty HTTP-success bodies, HTML download pages and generic ZIPs lacking workbook structure. They also preserve the difference between retained and current evidence, reject ages without keys as an assignment, and require explicit context/QC verification even when candidate keys exist. A filename, sender assertion, row count or source age label cannot replace an exact experimental-identity join.

The freshly inspected preprint and visible GEO page establish what those surfaces say. They do not prove that an unpublished or separately hosted assignment table is absent. No current-source byte equality is asserted, no dataset was relabeled, and no expression matrices, raw sequencing reads or biological models were downloaded or run.
