# Matched RNA and respiration in adult-origin fibroblast cultures

<!--
Title: Matched RNA and respiration in adult-origin fibroblast cultures
-->

**Verified source admission:** 21 source-matched RNA/physiology records from two 18-year-old fibroblast donors are available for a separate calibration analysis of aging in culture. This packet establishes input availability and source matching. Molecular/function outcome analysis has not been performed.

The [Cellular Lifespan Study](https://www.nature.com/articles/s41597-022-01852-y) supplies an author-integrated sampling table, explicit RNA identifiers and measured respiratory spare capacity. The [GSE179848](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE179848) processed matrix contains 28,633 unique gene rows, 345 RNA columns and **9,878,385** finite expression values. Values retain the investigator-provided log2 VST normalization. They are expression measurements, with no biological-age conversion in this packet.

Exact study-sample IDs link GEO metadata to both the versioned [Figshare table](https://doi.org/10.6084/m9.figshare.18441998.v2) and the study's current [public export](https://columbia-picard.shinyapps.io/shinyapp-Lifespan_Study/). The admitted subset agrees in donor, RNA ID, culture-record label, study phase, replicate label, treatment, oxygen, passage and collection date/time. Elapsed culture days agree within the source table's rounding precision. RNA matrix labels match the GEO sample descriptions exactly; row order and nearest-date matching are unused.

The bounded cohort is untreated Phase II at 21% oxygen. Of **22** eligible RNA records, 21 have finite source-reported oxidative spare respiratory capacity: 11 from HC1 and 10 from HC2. Sample 372 / RNA Sample_36 / GSM5435626 lacks that functional measurement and remains in the coverage table. Physiology values match the versioned and current author tables exactly as source strings. Units are pmol O2/min/20,000 cells. These are processed assay summaries; technical wells have not been reanalyzed as independent biological units.

The full 345-record audit also retains **300** records with unresolved source-label differences or missing context, including replicate-code differences. Their biological meaning is not inferred. Pediatric donor lines, incomplete technical-reference records and other treatment/phase contexts remain outside this admitted subset. Those records are accounted for in [rna-link-audit.tsv](rna-link-audit.tsv), with source-supported coverage in [eligible-untreated-records.tsv](eligible-untreated-records.tsv) and the usable observations in [matched-records.tsv](matched-records.tsv).

The authors' shared sampling records support a culture/passage linkage across parallel assays. RNA collection and respiratory measurements use separate material; same-cell continuity and identical assay times are not established. Repeated culture timepoints remain observations from two people. The donors were young adults, so this is a baseline comparator of replicative culture aging rather than an intervention in older donors.

The bounded search stopped after this subset qualified. [CANDIDATES.json](CANDIDATES.json) records the three other leads and their review extent. [FOLLOW_ON_SPEC.json](FOLLOW_ON_SPEC.json) fixes the source scope and next decision: define an independently justified RNA readout before calculating its relationship with function, with donor and elapsed culture time explicit. A source-complete RNA/physiology table does not by itself supply a transcriptomic-age clock or a rejuvenation result.

Original investigators retain credit for the source experiment, measurements and biological findings. The [Gill comparison](../gill-migration-comparison-2026-10-31/README.md) remains DEFERRED with zero joint admissions. Phase 483 continues to require a real supervised external exchange. Source admission advances the available calibration inputs while preserving those separate requirements.

Offline verification, from the repository root:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/alternative-function-screen-2026-11-01/verify.py
```

Full source replay after acquiring the originals named in [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json):

```sh
python3 programs/partial-reprogramming-controller/benchmarks/alternative-function-screen-2026-11-01/audit.py --sources /path/to/originals
```

The full replay verifies source fingerprints, gzip integrity, every expression value's numeric validity, all RNA labels, context matching and exact regeneration of the published intake tables. Eleven synthetic tests check identity, collection context, scope and matrix rejection behavior. Investigator code was inspected as text to corroborate sample labeling and was not executed. No raw well-level physiology reproduction is claimed.

The versioned Figshare dataset and primary article use CC BY 4.0. Source archives, the full expression matrix and browser-session links are excluded from this public packet. [ACQUISITION.json](ACQUISITION.json) retains the failed requests and the successful exact download URL; HTTP success alone was insufficient for acceptance. Future endpoint availability and mutable exports may change; accepted source hashes stay fixed.
