# Gill archives and the missing matched measurements

<!--
Title: Gill archives and the missing matched measurements
-->

The Cambridge article archive, thesis PDF and repository-extracted thesis text were recovered on November 1, 2026. Each matches its repository-recorded byte count and MD5 checksum, and now has a retained SHA-256 fingerprint. The matched molecular-age/function comparison remains **DEFERRED: 0/13 frozen contrasts admitted**.

Claim level: **Verified** for file identity, inspected contents and the bounded intake decision. Biological interpretation remains **INCONCLUSIVE**.

The article archive contains **13 members**: nine figure images, three workbooks and a transparent-reporting form. The accepted-manuscript publisher ZIP contains **8 members**: four figure PDFs, the same three workbooks and the same reporting form. The workbooks contain a comparison of earlier studies, morphology statistics and gene lists. Both archives pass ZIP CRC checks. Neither supplies the required numerical migration table or culture-to-RNA crosswalk. Published migration plots identify four biological-replicate groups without an authoritative RNA-sample assignment. Plotted points have not been digitized or admitted as original measurements.

The thesis adds an important version boundary. Printed page 134 (PDF page 158) presents scratch-wound testing as future work. Its clock description reports a median absolute error of **13.48** years; the final paper reports **12.57** years. Thesis Figure 4.16 shows 13-, 15- and 17-day groups, while final-paper Figure 3C also includes 10 days and different sample counts. These observations leave clock-output equivalence unestablished. The thesis therefore cannot substitute for the final paper's per-RNA predicted ages.

Original investigators retain credit for the data, experiments, clock and biological findings. This known-outcome reanalysis keeps the [October 31 contract](../gill-migration-comparison-2026-10-31/ANALYSIS_CONTRACT.json) unchanged. The [recovered RNA matrices](../gill-matrix-recovery-2026-10-31/README.md) cover all 26 required RNA arms, while three inputs remain necessary:

1. Original technical-replicate migration speeds, units, culture identifiers and exclusions.
2. An authoritative culture-to-RNA crosswalk with experimental context.
3. Existing final-paper Figure 3C predicted ages with exact RNA identifiers and provenance.

The next useful input is one source-complete matched pair; running the frozen comparison also requires source-backed accounting for all 13 contrasts. Phase 483 continues to require a real supervised external packet exchange. This archive review supplies no new functional effect, safety or persistence finding.

The dated [acquisition receipt](ACQUISITION.json), [member inventory](ARCHIVE_INVENTORY.json) and [review decisions](REVIEW.json) make the search result reusable. The scope is these inspected objects; it does not establish that the missing data are absent from every public or investigator-held location. The October 31 HTTP 500 receipt remains a historical access observation. Today's successful recovery supersedes it for these exact objects. A speculative publisher `supp-v2.zip` URL returned 404 and supplied no source file.

Run the offline artifact and frozen-dependency checks from the repository root:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gill-archive-review-2026-11-01/verify.py
```

For a full replay, download the four successful URLs in `ACQUISITION.json` to one directory using their recorded filenames, then pass `--sources /path/to/downloads`. The verifier checks source sizes, SHA-256, MD5, both archive member inventories and CRCs, and the thesis text markers. It reads source documents as data and executes no supplied research code. Missing files return **INCONCLUSIVE**; changed bytes return **FAIL**. Live acquisition availability can change.

The public package contains derived provenance and review code. The full thesis, its extracted text and source archives remain outside this export. The thesis repository records All Rights Reserved; inspection grants no new redistribution permission.

Primary sources: [article](https://elifesciences.org/articles/71624), [Cambridge article deposit](https://www.repository.cam.ac.uk/items/3017f847-bae8-426e-955b-dc3e5058b370), [thesis deposit](https://www.repository.cam.ac.uk/items/e8d345db-7cd0-4d6d-aae7-a3495ba9ca33).
