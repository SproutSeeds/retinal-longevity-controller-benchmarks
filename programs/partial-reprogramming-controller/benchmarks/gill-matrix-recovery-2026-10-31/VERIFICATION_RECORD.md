# Gill matrix recovery verification

Verification date: October 31, 2026, America/Chicago.

Claim level: Verified source recovery. Scientific joint comparison: INCONCLUSIVE / DEFERRED.

| Check | Result | Observed evidence |
| --- | --- | --- |
| Original compressed source identity | PASS | Both byte lengths and SHA-256 hashes in MATRIX_CONTRACT.json match downloaded files. Full gzip streams validate. |
| Complete matrix shape and numeric validity | PASS | 35,805 feature rows in each source, 24 plus 71 RNA columns, 3,401,475 finite numeric values. |
| Within-RNA source-label mapping | PASS within stated scope | 90 exact GEO title matches; five explicit provisional formatting aliases outside the frozen comparisons. |
| Frozen contrast RNA coverage | PASS | Every arm of all 13 comparisons is available under an exact source label, totaling 26 distinct RNA IDs. |
| Feature alignment | PASS | Unique chromosome/start/end/strand/gene-ID keys match across sources, with identical per-key annotations. Two source row identities are reordered. |
| Numerical effect of observed source permutation | PASS: zero difference | The two reordered features have identical expression vectors within each source. The locus join preserves identity without claiming an observed numerical correction. |
| Gene-ID ambiguity retention | PASS | 77 repeated nonempty gene IDs across 157 rows plus two blank-ID rows remain separate loci. No gene-level model adapter is admitted. |
| Independent original-value preservation | PASS | verify_merged.py compares every source cell and annotation by named source column and compound key without importing recover.py. FULL_SOURCE_VERIFICATION.json binds 3,401,475 comparisons, zero changed cells and merged SHA-256. |
| Counterexample tests | PASS | 15 tests cover source truncation, HTTP denial, changed evidence preservation, reordered rows, repeated IDs, missing keys, conflicting annotations, malformed cells and non-admitted sample matches. |
| Fresh-cache public CLI reacquisition | INCONCLUSIVE | A release smoke check using published commit bbaf51227ef3e514255f246a4bc6eadea976f52d received HTTP 403 from the primary GEO endpoint. The temporary cache was removed. The later error-reporting fix adds no alternate source or retry. Retained originals still pass their recorded hashes and full source replay. |
| Institutional archive content inspection | INCONCLUSIVE | Metadata identifies an article ZIP and thesis files; content requests return HTTP 500 with an internal read/write error. Their contents are not inferred. |
| New clock estimates or functional effects | INCONCLUSIVE / DEFERRED | No original per-sample custom clock values, migration speeds or function-culture crosswalk recovered. |

Run `python3 verify.py` for released artifact integrity, within-RNA consistency and executable counterexamples. Run `python3 recover.py --download --verify` for original source hashes and full matrix QC. After creating the merged cache with `--write --merge`, run `python3 verify_merged.py` for the independent all-cell comparison. Offline release replay checks retained evidence and software; it does not independently reacquire data or reproduce the source biology.

The acquisition/QC contract follows observation of these source files. This known-outcome package preserves the previous Gill analysis freeze and leaves Phase 483, permissions, human review and prior biological verdicts unchanged.
