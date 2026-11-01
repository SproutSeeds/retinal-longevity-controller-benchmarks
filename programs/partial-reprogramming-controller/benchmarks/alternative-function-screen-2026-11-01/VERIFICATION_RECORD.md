# Alternative source intake verification

Record date: November 1, 2026. Claim level: **Verified source admission**. Verification: **PASS** for the pinned source intake. Molecular/function outcome analysis: **NOT RUN**.

Hooks:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/alternative-function-screen-2026-11-01/verify.py
python3 programs/partial-reprogramming-controller/benchmarks/alternative-function-screen-2026-11-01/audit.py --sources programs/partial-reprogramming-controller/.data/alternative-function-screen-2026-11-01
```

Full replay checks twelve source fingerprints, including the 60,622,846-byte final expression archive, 11,198,396-byte GEO family record, and both investigator sampling tables. The versioned Figshare table also matches its supplied MD5. The archive SHA-256 is `b5731fa1253a2bd32f0b64c3bd58770e833a3da59dc90c4f8c8d858944b30109`. All 9,878,385 expression values are finite, all 28,633 gene labels are nonempty and unique, and all 345 sample columns match exact GEO descriptions. Original normalization and numeric source text are preserved; no biological expression output is computed.

The source-ID audit accounts for every GEO RNA record, retains unresolved context-label differences, and identifies 22 eligible untreated adult records. Twenty-one have finite physiology values and an assay identifier. The source summary contains 11 HC1 and 10 HC2 records; the independent donor count is two. Both donor ages are 18. One eligible record, GSM5435626 / Sample_36 / study sample 372, lacks function and is never filled from an adjacent passage.

The source-matched physiology values and assay IDs are byte-identical strings across the versioned and current author tables. Shared exact sampling identifiers, passage and collection context establish the declared culture-record link. Source rounding is used only to check consistency of elapsed days after the exact ID join; it never determines a match. The 300 full-roster context-issue records remain documented and outside the admitted subset. Replicate codes are preserved rather than reinterpreted.

Eleven synthetic tests pass. They reject donor/RNA identity substitution, adjacent-date or clock-time matching, incompatible elapsed-day precision, silent replicate-code reconciliation, missing technical-reference context, duplicate study IDs, wrong species/age/treatment/phase/oxygen context, repeated matrix IDs and non-finite expression. Column-order invariance is tested. Synthetic fixtures are not biological observations.

An independent read-back checks the 21 released observations against the original author rows and GEO sample IDs without using the admission functions. Full replay is repeated to verify deterministic output. The original Gill freeze and prior admission results remain hash-preserved. The publication posture checks pass for the source-intake note and updated public index.

Limits: observed source summaries are admitted; raw Seahorse wells were not independently processed. The 234MB raw assay archive, raw read files and raw WGS were not downloaded. Six technical-reference RNA records and pediatric or other cohort contexts supply no additional adult donor replication. A companion pre-QC abundance matrix was acquired but remains outside this admission. Earlier HTTP 403, empty-body and HTML-challenge responses remain rejected, with receipts retained. No scientific-source code was executed.

The source review advances calibration input readiness. It establishes no functional improvement, age reversal, safety, persistence, clinical validity or completed external supervised evaluation.
