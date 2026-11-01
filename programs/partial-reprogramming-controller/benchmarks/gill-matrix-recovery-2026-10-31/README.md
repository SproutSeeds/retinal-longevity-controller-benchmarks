# Gill RNA recovery and the remaining link to function

<!--
Title: Gill RNA recovery and the remaining link to function
-->

Both original processed RNA matrices from [GSE165177](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE165177) are recovered and integrity checked. They supply **26/26 RNA arms for all 13 frozen comparisons**, with 95 expression columns and 3,401,475 finite numeric values across 35,805 feature rows. The molecular-age/function comparison remains **DEFERRED** pending original clock values, migration measurements and authoritative culture matching.

This is a **Verified source-recovery result**. The [Gill study](https://elifesciences.org/articles/71624) is a known-outcome challenge. Original investigators retain credit for the experiments, clock and published biological findings. This recovery does not establish a new rejuvenation, identity, safety or persistence result, and leaves Phase 483 unchanged.

## Recovered inputs

| Source | Feature rows | RNA columns | Finite values |
| --- | ---: | ---: | ---: |
| Original processed matrix | 35,805 | 24 | 859,320 |
| Part 2 processed matrix | 35,805 | 71 | 2,542,155 |
| Locus-aligned combination | 35,805 | 95 | 3,401,475 |

The values are the source's **log2 RPM**, with original numeric text and negative values retained. They are processed expression measurements. Obtaining them does not reproduce the custom transcriptome clock or establish comparability between experimental batches.

[sample-columns.tsv](sample-columns.tsv) records 90 exact source-title matches to GEO IDs and five provisional space/underscore aliases. Those five columns are starting-fibroblast or iPSC references outside the frozen comparison. Every eligible comparison arm matches exactly. These are within-RNA labels; they supply no function-culture crosswalk.

[contrast-coverage.tsv](contrast-coverage.tsv) accounts for all 13 comparisons. These 95 columns represent RNA libraries, not 95 independent donors. The frozen comparisons retain three donor labels, with donor coverage 3, 2, 1 and 3 at induction durations 10, 13, 15 and 17 days respectively.

## Feature identity

The input files reverse the order of two feature rows, `ENSG00000280101` and `ENSG00000280358`. They have **identical expression vectors within each source**, so this permutation produces zero observed numerical differences under a positional merge. [reordered-features.tsv](reordered-features.tsv) preserves the source row locations. The implementation joins unique compound keys consisting of chromosome, start, end, strand and gene ID, then checks all annotations for each key.

There are **77 repeated nonempty gene IDs across 157 rows**, plus two rows with blank gene IDs. [gene-id-issues.tsv](gene-id-issues.tsv) retains all 159 affected feature rows. The full locus keys remain unique. No rows are collapsed into a single gene-level record. Any later model using one value per gene needs its own explicit handling rule.

## Reproduce

From this folder, run the offline artifact and rejection checks with Python 3.12 or later:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 verify.py
```

This checks the released extraction and software, without downloading biological data. To verify original source bytes and replay the full matrix QC:

```sh
python3 recover.py --download --verify
```

This downloads only the two pinned processed files, about 16 MB compressed, into the ignored controller `.data/` cache. The successful acquisition used the named FTP HTTPS URLs with `?download=1`; the bare URLs had returned headers with incomplete bodies. The query variant is an observed working route, not a proven diagnosis of the server failure. Every retained file must match its size and SHA-256 and pass complete gzip validation. Changed cached sources are preserved and rejected.

To create the original-value, locus-aligned working matrix in that cache:

```sh
python3 recover.py --download --write --merge
python3 verify_merged.py
```

The downloaded matrices, merged expression table and source text are outside this public package. [MATRIX_CONTRACT.json](MATRIX_CONTRACT.json) identifies source hashes and prior frozen dependencies. The recovery contract was written after source QC, rather than preregistered before observing the data.

[FULL_SOURCE_VERIFICATION.json](FULL_SOURCE_VERIFICATION.json) records an independent comparison of every original expression cell and annotation with the merged table. The verifier uses a separate CSV reader and original column names without importing the recovery implementation. It observed zero changed cells. The retained merged file's hash establishes this working derivative's identity, rather than clock or biological validation.

## Remaining source recovery

Cambridge's [article deposit](https://www.repository.cam.ac.uk/items/3017f847-bae8-426e-955b-dc3e5058b370) lists a supporting-information ZIP. Gill's [doctoral thesis deposit](https://www.repository.cam.ac.uk/items/e8d345db-7cd0-4d6d-aae7-a3495ba9ca33) lists the thesis and extracted text. Repository metadata was retrieved, but content endpoints returned HTTP 500 with an internal file-read/write error. Their contents remain uninspected. [ARCHIVE_SEARCH.json](ARCHIVE_SEARCH.json) records exact object IDs, declared sizes/checksums, failures and the next recovery hook. The thesis's all-rights-reserved notice does not authorize redistribution.

The next scientific intake needs all three source-compatible inputs: existing per-sample Figure 3C clock outputs, technical-replicate migration speeds and a source-confirmed culture-to-RNA mapping with experimental context. This package does not alter the [frozen Gill comparison](../gill-migration-comparison-2026-10-31/README.md) or its exclusions, permissions and donor-weighting rules.
