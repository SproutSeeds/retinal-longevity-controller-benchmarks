# Human recovery references and the remaining input requirements

**Verified:** published age-reference outputs are available, including a short withdrawal experiment that the earlier audit had not extracted. We recovered 12 reference rows for three human fibroblast donors after five days of induction and two days without doxycycline. They improve the reference benchmark for existing experiments. The independent clock replay and the intended joint late per-cell recovery claim remain unresolved.

## Newly usable reference outputs

The [SRSF1 paper](https://www.nature.com/articles/s43587-026-01234-8) links six main-figure source workbooks and nine supplementary workbooks. We inventoried all 15 workbooks, covering 46 sheets. [SOURCES.json](SOURCES.json) preserves retrieval times, URLs and byte hashes; [complete-workbook-inventory.json](complete-workbook-inventory.json) preserves sheet names, dimensions, headers and relevant text matches.

| Source | Extracted row occurrences | Identity status |
| --- | ---: | --- |
| Source Data Fig. 1, sheets 1c–g | 471 | External/group references or insufficient/conflicting study-library metadata |
| Source Data Fig. 3, sheet 3a | 76 | 66 exact library and metadata joins; 10 absent library IDs |
| Supplementary Table 4, Predicted ages | 480 | Screen outputs without individual library keys in the table |
| Source Data Fig. 4, sheet 4c, added after inspection | 12 | Six donor/construct/schedule groups, with two technical replicates each |

The original three-workbook extraction contains **1,027 row occurrences**. These are neither 1,027 independent donors nor a deduplicated set of biological samples. Reference rows may repeat experiments or lack uniquely resolvable identities. The additional 12 short-recovery rows are recorded separately.

Fig. 3a contains 76 unique table SampleIDs across six donor lines. Exact accession-scoped library keys, donor, age, passage, construct, dose and deposited count-column presence support 66 joins. The ten absent BFP IDs are S138, S139, S148, S149, S158, S159, S172, S173, S182 and S183. They remain in [validation-reference-joins.csv](validation-reference-joins.csv). A matching recycled identifier without sufficient metadata is rejected. This is reference alignment, not independent reproduction of the age estimates.

Independent source review found 12 NTg rows whose workbook replicate labels are 1/2 while the GEO titles use 3/4. Their exact library keys and the biological fields listed above agree. [replicate-label-review.json](replicate-label-review.json) retains every discrepancy; the numbering convention remains unconfirmed and is not used as a row key. The 66 accepted library joins are preserved. `AgeDiff` is retained as a source-defined field: the raw subtraction check below applies specifically to Fig. 4c, rather than assuming every figure uses the same adjustment.

The [Fig. 3 caption](https://www.nature.com/articles/s43587-026-01234-8/figures/3) defines its age change relative to a line-matched NTg baseline. For S232, subtracting its reported AgeDiff from its prediction yields 50.6866903265, matching the mean predictions of NTg S232/S233/S284/S285. This confirms the distinction in one block; it is not a reconstruction of every Fig. 3 baseline grouping.

## The recovered withdrawal reference

The [Fig. 4 caption](https://www.nature.com/articles/s43587-026-01234-8/figures/4) identifies sheet 4c as the five-days-on/two-days-off experiment. Its three donor lines are M55, M68 and M79. Each has SRSF1 and BFP samples with two technical replicates. The individual donor is the biological unit.

| Donor | Mean reported SRSF1 age | Mean reported BFP age | Paired reported difference |
| --- | ---: | ---: | ---: |
| M55 / AG12657 | 54.442893 | 64.369468 | −9.926576 |
| M68 / AG13369 | 61.339598 | 68.465248 | −7.125650 |
| M79 / AG16359 | 73.677717 | 88.725699 | −15.047982 |
| Equal mean across three donors | | | **−10.700069** |

Units are the source model's predicted years. The arithmetic agrees with the caption's rounded 11-year difference. It does not measure how many years a cell was biologically rejuvenated. The age estimates are the authors' published outputs; our code has not generated them from RNA counts. No new p-value or confidence interval was calculated.

[recovery-reference-audit.json](recovery-reference-audit.json) preserves all 12 values and coordinates. Each published AgeDiff agrees with Predicted_age minus Line_age within 1e−10. [recovery-reference-groups.csv](recovery-reference-groups.csv) identifies the corresponding sets of deposited libraries. The table has no library identifier, and replicate numbers are not an independently established cross-file key, so no individual reference-to-library join is asserted.

Two days after withdrawal provides short population-level follow-up. It does not establish late durability, same-cell lineage continuity, a calibrated unusual-state frequency or retinal function. The study also reports identity-related expression at this schedule, but bulk marker summaries do not supply the missing joint per-cell observations.

## Timing is partly resolved

The 72 human factor-off libraries comprise 30 SRSF1, 30 BFP and 12 OSKM libraries across three donors. Twelve libraries carry the five-on/two-off schedule and agree with Fig. 4c and Extended Data Fig. 5e.

The other short-induction series still needs clarification. GEO explicitly assigns 1–3 days ON with 8 or 16 days OFF. For example, [GSM9612108](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM9612108) gives the treatment field `Dox_1000ng/mL, 1d-ON/8d-OFF`. The current [Extended Data Fig. 5d caption](https://www.nature.com/articles/s43587-026-01234-8/figures/11) instead describes 6 and 12 days after withdrawal following 1–3-day inductions. Treating 8/16 as elapsed calendar days does not reconcile all three induction lengths with 6/12 days OFF. [chronology-audit.json](chronology-audit.json) preserves both descriptions and all schedule counts.

The older metadata synopsis called this Extended Data Fig. 6d. The current publisher labels the relevant withdrawal panels **Extended Data Fig. 5d/e**. This audit records that correction while preserving the historical artifacts. A sample-level chronology map, rather than arithmetic guesswork, would resolve the remaining discrepancy.

## Why a full clock replay still waits

The [current author repository](https://github.com/saschajung/Clock/tree/7ae5f38b7ea74f76cb13076b64350d5930bb152f) is pinned to commit `7ae5f38b7ea74f76cb13076b64350d5930bb152f`. The new outputs narrow the previously stated reference gap. They do not supply the entire preprocessing path.

- `ProcessFibroblastData.R:85–90` derives `gl` from the Geneid/Length columns of a local featureCounts table. The deposited matrix has Geneid plus 807 unique count columns and no Length field. The inspected repository does not contain that featureCounts table.
- `GetGenesForRemoval.R` queries live, unversioned Ensembl and writes a filter list. Recreating it today need not reproduce the original list.
- `TrainClock.R:81–93` filters before TPM normalization and natural-log transformation, writes `GenesForTPMNorm.rds`, and then applies an expression threshold. The exact normalization universe matters because TPM uses a sum across retained genes.
- `ApplyNewData.R:14–24` calls frozen surrogate-variable correction and then replaces that result with the uncorrected matrix. The intended published path needs clarification; this audit does not silently repair it or infer that the published results are wrong.

[clock-readiness.json](clock-readiness.json) lists the exact dependencies. The inspected current tree has six script/readme files; the current forks and issues queries returned none. The previous repository-history audit remains relevant. No author script, serialized model or paid service was executed.

The most useful reply would provide the processed clock-input matrix or the exact gene lengths, filter and normalization universe, together with library-preparation encoding, the intended correction path and uniquely keyed predictions. A fresh replay contract would then fix the numerical tolerance and held-out reference checks before testing outcomes.

## Other public-data routes

The bounded search retrieved 84 and 257 Europe PMC records from two explicit queries, plus 263 GEO series records. These are retrieval counts, not counts of eligible independent studies. [search-ledger.json](search-ledger.json) preserves all returned titles/identifiers and the screening rule. [candidate-dispositions.json](candidate-dispositions.json) records the relevant primary-source follow-ups.

Gill's human fibroblast data already provide useful bulk population recovery after four or five weeks without doxycycline, and the project has already reused them. The human mesenchymal-drift single-cell series remains an informative two-donor trajectory. Neither creates the unobserved joint late per-cell outcome by being combined across studies. An NGN2 conversion study reuses induction-stage single-cell data for a different lineage endpoint.

A 2026 MSC study supplies public RNA runs and verified vector-clearance experiments, but uses umbilical-cord MSCs and hTERT/BMI1/SV40T. It is a different cell source and intervention. Its raw data are a possible contextual comparison, not a replacement for the adult retinal/controller target. The bounded source audit identified no additional dataset that closes that target. It does not prove that no compatible data exist elsewhere.

## Decision and next trigger

**Verified source-audit decision:** the available reference extraction and arithmetic are complete. Further clock outcome computation needs specific preprocessing and mapping inputs. **Experiment replacement remains INCONCLUSIVE.**

**Heuristic next action:** obtain those inputs, validate the intended clock calculation against held-out reference outputs, and reevaluate the compatible withdrawal comparisons. The coordinator owns the actual correspondence status. This lane sent no messages.

**Conditional measurement requirement:** if existing studies cannot supply matched human age improvement, adult identity, calibrated unusual-state assessment and late follow-up after verified withdrawal, new observations are needed to test that joint claim. Ocular conclusions also require the relevant retinal/RPE system and function. Simulations can test analysis failure modes; they cannot fill an unobserved biological outcome.

## Audit amendments and verification

The original workbook extraction contract and input hashes were recorded before numerical inspection in the packet's `FREEZES.jsonl`. Two amendments remain explicit:

1. The original frozen input list pinned a raw 72-row recovery manifest, while the extractor needed the larger normalized study manifest. [reference-input-addendum.json](reference-input-addendum.json) binds that 807-row input **after inspection**. It also records the literal-NTg alias correction and count-column requirement. The original freeze is unchanged.
2. Fig. 4c was discovered during follow-up inspection. [recovery-reference-addendum.json](recovery-reference-addendum.json) labels its extraction and descriptive arithmetic as a **post-inspection extension**. It is not presented as a prospective biological replication.

From the public packet root, `python3 human/verify.py` performs 24 portable integrity/bookkeeping checks without source downloads or packages. `python3 -m unittest discover -s human -p 'test_*.py'` runs 16 synthetic regression tests. [VERIFICATION.md](VERIFICATION.md) gives source-byte checks and replay commands. These verify the extraction and arithmetic, with biological scope unchanged.
