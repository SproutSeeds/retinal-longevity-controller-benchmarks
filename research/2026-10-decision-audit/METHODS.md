# Methods and evidence scope

The underlying experiments belong to their source investigators. This packet adds independently written numerical analysis, structured extraction and a bounded source audit. Exact sources, retrieval times and hashes are retained per lane. No private correspondence is part of the public evidence.

## Human references

Read publisher spreadsheets as typed cell values, retaining workbook, sheet, row and source hash. Distinguish a row appearing in multiple source tables from a new biological observation. Check raw predicted-age subtraction for the five-on/two-off reference table; preserve other source-defined `AgeDiff` fields without assuming the same adjustment. Bind available sample IDs to the deposited metadata; retain unmatched and group-only matches. A post-analysis review retains 12 source-local replicate-numbering differences without treating those numbers as cross-file row keys.

The original reference audit had a prospective extraction contract. A necessary metadata-manifest binding was missing from that initial freeze; its later addition is explicitly dated after inspection. The five-on/two-off source discovery also has a retrospective addendum. Neither addition is presented as a prospective biological test. The three donor lines are the independent units in the descriptive recovery reference comparison; two technical replicates per construct do not double that number. [Human report](human/REPORT.md).

A published prediction is a reference output, not proof that an independent implementation reproduced it. No tAge, TACO or SRSF1 clock was executed in this campaign. Required preprocessing, historical versions and sample joins remain explicit dependencies.

## Independent mouse expression

Design and implementation were frozen before parsing the new expression matrices. The final admission corrected sex and known processing batches using the primary paper before outcomes. The original design receipt, metadata amendment and final freeze are preserved.

Use RNA features only, exact gene identifiers, unique barcodes within each library and prespecified RNA QC. Sum counts within animal; equal-weight animal means define the comparison. The primary seven animals comprise four APP/PS1 OSK and three APP/PS1 GFP. Three WT GFP animals are context. Matched ATAC libraries are additional assays of these same animals.

Four inherited panels are assessed with a primary log2(1+CPM) mean, median-ratio and rank sensitivity, all single-gene omissions and all single-animal omissions, plus the deposited-barcode sensitivity before extra RNA QC. All 35 label allocations are enumerated with four-panel Holm adjustment. Missing batch/subset assignment limits the exchangeability assumption. These calculations are descriptive conditional sensitivities, not a powered confirmatory design.

Six frozen marker bins, plus ambiguous and unassigned categories, expose mixture sensitivity. Eligibility requires two distinct markers, with one- and two-UMI versions, and minimum support in every primary animal. Bins are heuristic classifications. The raw recount uses a separately implemented cell-at-a-time reader, checks RNA-only library totals and aggregates, and verifies bin membership accounting. [Mouse report](ocular/REPORT.md); [reproduction](ocular/REPRODUCTION.md).

## Existing-data recovery

Rebuild the author repository history, GEO/SRA/ENA inventory, Zenodo versions and publisher metadata from saved public records. Record negative searches with their scope. Reconcile the seven omitted sample labels without assigning missing cell barcodes from expression. The Stanford thesis supplies design-level withdrawal timing; matching four named candidates by count remains heuristic. Published outcomes encountered in that review are disclosed. [Recovery report](recovery/REPORT.md).

The GSE350289 recheck hashes fresh workbook bytes against the previously audited artifact. Identical bytes justify carrying forward that workbook's existing content findings, without claiming that all repositories contain no correction. [Assignment report](assignment/REPORT.md).

## Verification and inference

Software verification has a deliberately narrow target: files, joins, arithmetic, permutations, support rules and claim-boundary consistency. Synthetic failure controls test code behavior. A PASS does not establish rejuvenation, calibrated cell identity, clinical efficacy, safety or experimental replacement. The integrated decision retains every insufficient-signal readout and names the changed input needed to reopen it.

These are deterministic saved-output computations under pinned versions, with tolerances documented in code. Source retrievals can change with repository updates; hash mismatch requires a new source revision and admission. Scientific figures are descriptive views of archived results with source hashes, without new fits or selected favorable endpoints.
