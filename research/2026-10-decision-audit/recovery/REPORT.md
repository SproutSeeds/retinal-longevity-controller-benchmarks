# Existing five-day withdrawal observations and their missing assignments

**Verified:** Lucy Xu's public 2022 thesis describes mouse SVZ experiments with collection five days after the final doxycycline pulse. This recovers a meaningful piece of the experimental design. The public files inspected still do not provide the omitted cells' animal assignments. **Heuristic decision:** request that specific existing input before considering a new experiment for this mouse withdrawal question. The human retinal target remains separate.

## What changed

The thesis's Figures 3-1 and 3-6 describe three cycles of two days of doxycycline followed by five days without it, with an additional collection after the final five-day withdrawal. Figure 3-1 reports four old OSKM withdrawal animals across two experiments; Figure 3-6 identifies the first experiment as 18–20-month-old mice, two per condition, using 10x v3. Figure pages and source hashes are recorded in [timing-evidence.json](timing-evidence.json). [Primary thesis](https://purl.stanford.edu/ck834ff5386)

The publisher's reporting summary explains that additional samples sequenced with cohorts 1 and 2 were omitted from the paper because they belonged to a separate study. Its Supplementary Table 1 identifies those sequenced samples. This is a study-scope exclusion; it does not establish that the missing observations are unusable. [Reporting summary, page 2](https://static-content.springer.com/esm/art%3A10.1038%2Fs43587-024-00594-3/MediaObjects/43587_2024_594_MOESM1_ESM.pdf)

The timing search also exposed the thesis's reported outcomes: its narrative describes the neuroblast proportion returning to the old-control baseline after withdrawal. That is an author-reported result, with possible migration or transient-response interpretations. It is not a reconstructed numerical result or independent replication. Any future analysis of these samples must acknowledge this prior exposure. Doxycycline removal also does not prove immediate cessation of reprogramming-factor expression.

## Exact sample reconciliation

The table combines previously verified publisher metadata with the pinned author code. Five samples carry the label `2Dox5`; one of those is labeled `old_BL6`. Four are therefore candidates for the thesis's four old iOSKM withdrawal animals. This count match is **Heuristic**, with no verified named-animal link to the thesis figures.

| Cohort | Author label | Publisher label | Code treatment | Code age/genotype | GEO library |
|---|---|---|---|---|---|
| 1 | 928L | 928L | 2Dox5 | old; genotype blank in table | GSM7022367 |
| 1 | 929L | 929L | 2Dox5 | old; genotype blank in table | GSM7022367 |
| 2 | 999L | 999L | 2Dox5 | old_OSKM | GSM7022368 |
| 2 | BL61 | B1 | untr | old_BL6 | GSM7022369 |
| 2 | BL62 | B2 | 2Dox0 | old_BL6 | GSM7022368 |
| 2 | BL63 | B3 | 2Dox5 | old_BL6 | GSM7022369 |
| 2 | L0034 | L0034 | 2Dox5 | old_OSKM | GSM7022370 |

[Reconciled records](sample-reconciliation.json) preserve unknown sex, exact collection times and barcode assignments. [Pinned author code](https://github.com/gitlucyxu/SVZreprogramming/tree/011586aea2e8612c794e57d2a260fa1a29d417a0) and [publisher table](https://static-content.springer.com/esm/art%3A10.1038%2Fs43587-024-00594-3/MediaObjects/43587_2024_594_MOESM2_ESM.xlsx) are the underlying sources.

## Bounded search disposition

The acquisition log contains 79 named source attempts: 78 acquired and one failed Zenodo pagination URL. The unpaginated versions endpoint succeeded. [SOURCES.json](SOURCES.json) preserves timestamps, URLs, failures and hashes. These counts describe retrievals, not independent studies.

| Route checked on October 18, 2026 | Result and implication |
|---|---|
| Author GitHub repository, all six returned commits, branch/tag/release/fork/issue inventories | Pinned head `011586aea2e8612c794e57d2a260fa1a29d417a0`; scripts expose sample labels and local LMO input paths, but no missing assignment file was located. A local path in code is not a deposited artifact. |
| Both Zenodo versions and latest/files/media endpoints | The two whole-body objects have unchanged checksums across both versions. The SVZ-targeted object changed; that change must not be described as a whole-body recovery update. |
| GEO series and four whole-body sample pages/directories | Ten matrix triplets across the series, four whole-body. Earlier feature/barcode inspection found gene-expression data and no complete omitted-animal join. More RNA counts cannot supply the missing multiplexing assignment by themselves. |
| Full SRA project and independent ENA inventory | Ten experiments, 13 runs; seven whole-body runs. No original file is named LMO or Undetermined. Filenames are not a read-content assay. No FASTQ download was performed. |
| Publisher supplements and BioStudies mirror | Reporting-summary exclusion explanation recovered. The mirror lists the same source-data and supplementary workbooks; no extra assignment object was identified. |
| Stanford catalog, thesis landing page and public thesis PDF | Five-day withdrawal design recovered. Named animals and cell barcodes remain unlinked. |
| Author-related PubMed records and Zenodo title search | No additional assignment deposit identified within those returned records. |
| Related spatial-aging-clock paper, repository and Zenodo inventory | The MERFISH reprogramming experiment collected at the end of the final doxycycline pulse. Its 3.18 GB object therefore does not answer the withdrawal question and was not downloaded. [Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11798877/) |

The ENA total for all four whole-body libraries is 129,370,260,434 bytes; 44,207,239,760 bytes refers to cohort 1 alone. Neither download is justified until a route to the relevant LMO observations or assignments is established. No claim is made that every public repository or author-held archive has been exhausted.

## Minimal input that reopens computation

Any one assignment route can suffice: (1) a complete library-plus-RNA-barcode to animal table with QC and demultiplexing provenance; (2) the complete prefilter RNA/LMO object with matching barcode columns; or (3) specifically identified LMO/Undetermined sequencing files with read structure, sample sheet and oligo map. The original code references LMO counts recovered from Undetermined files, making that specificity important.

Each route also needs author confirmation of animal identities, genotype, sex, age, induction/removal/collection times, exclusions and data-reuse terms. First verify that the recovered assignments reproduce the published included animals and retain uncertain/rejected cells. Then freeze eligible contrasts and support thresholds before examining newly available outcomes. [Machine-readable dependency and acceptance rules](decision.json)

**Final lane disposition:** existing observations plausibly support further mouse withdrawal analysis, conditional on a precise data response. New outcome computation is currently blocked by that input. A universal requirement for new wet-lab work has not been established. This lane sent no messages, arranged no experiments and used no paid compute.

## Verification hook

From this directory:

```sh
python3 verify.py
python3 -m unittest test_audit.py
```

The portable check rebuilds inventories from 19 saved metadata snapshots, reconciles seven omitted labels, checks source hashes and verifies that missing evidence remains explicit. Six negative-control tests reject incomplete/error inventories. For an original-source audit, pass the retained acquisition cache to `verify.py --cache <cache-directory>`; this also verifies every acquired original hash, including the thesis and reporting-summary PDFs. Figure interpretation remains a documented visual review.

Expected result: `PASS`; biological recovery verdict: `INCONCLUSIVE`. See [VERIFICATION.json](VERIFICATION.json) and [VERIFICATION_STRICT.json](VERIFICATION_STRICT.json). These are provenance and integrity checks, not experimental validation.
