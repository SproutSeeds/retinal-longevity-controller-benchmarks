# Perturbation assignments still require a corrected source

**Verified source comparison:** the current [GSE350289 cell metadata workbook](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE350nnn/GSE350289/suppl/GSE350289_metadata_individual_cells.xlsx) is byte-identical to the workbook audited earlier on October 18. SHA-256 is `f48a3eba3416110afae897a4df78796379d01211e0b9a436f65d7f4b1f44e76d`. The [GEO series record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE350289) lists its last update as October 13, 2026.

The earlier content audit therefore still applies: the Ctrl and Sample 1 sheets contain age entries, while Sample 2 and Sample 3 contain no nonempty rows. Exact library/barcode-to-treatment and donor/pool assignments were not recovered. The refreshed supplement directory lists the same assignment workbook alongside the four matrix/barcode/feature sets and the target-gene list. A target list is insufficient to label individual cells.

The next useful artifact is a corrected assignment table keyed by library and cell barcode, with perturbation, donor or pool provenance, and assignment QC. Exact joins must be verified before a treatment analysis. Gene-expression matrices were not downloaded during this pass because their size does not resolve the missing assignment.

This is a dated check of named public records, not a conclusion that a corrected file cannot exist elsewhere. Targeted web searches and GitHub code search did not identify a replacement in the inspected results. The discovery record is in [searches.json](searches.json); the byte comparisons are in [results.json](results.json).

## Verification

`inspect_assignment.py --cache <cache>` verifies all three fresh source hashes and reproduces the saved result exactly. `source-plan.json` lists the three bounded URLs; `retrieval-2.json` records their byte counts and hashes. The initial fetch stopped at the existing 8 GB free-space floor on the code drive; its failure receipt is retained as `retrieval.json`. The successful fetch used the internal temporary volume. No storage guard was lowered and no unrelated files were deleted.

The original detailed workbook content audit is [public](https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks/blob/main/research/2026-10-metadata-recovery/geo350289-mapping-audit.json). Reusing that content interpretation is conditional on exact byte equality; a changed workbook requires a new content audit.
