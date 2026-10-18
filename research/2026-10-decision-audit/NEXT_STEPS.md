# The next observation to recover

**Recommendation — Heuristic:** use the completed public-data work to recover four precise missing inputs. Keep new measurement conditional on what those inputs actually contain. The campaign has reached an input-dependent decision point, rather than a proof that all public-data routes are exhausted.

## Existing-data work with an explicit restart trigger

| Priority | Required input | What becomes possible | Acceptance check before outcomes |
|---|---|---|---|
| 1 | Complete verified library-and-barcode-to-animal assignments with QC and demultiplexing provenance; alternatively, full prefilter RNA/LMO data plus the oligo map, or identified LMO sequencing files | Reanalyze the omitted five-day withdrawal comparison and its controls | Confirm named animals, genotype, induction/withdrawal/harvest dates, correct controls and independent biological units; preserve ambiguous cells. An authoritative assignment table can suffice without original LMO counts. |
| 2 | Historical GSE304044 tAge pipeline, preprocessing, missing-gene reference values, control-centering values and a keyed input/output example | Test the reported GSTA4 clock result with the relevant historical method | Match version, genes, scales, reference cohorts and prediction IDs before comparing values; join animal/eye/cohort identifiers before functional interpretation |
| 3 | SRSF1 featureCounts gene lengths, TPM-normalization inputs, frozen gene-selection reference and keyed clock outputs | Independently replay published human predictions, including the short withdrawal result | Validate all preprocessing inputs; reconcile the longer withdrawal schedules; require exact sample joins or explicitly group-level comparisons |
| 4 | Corrected GSE350289 cell/library/perturbation assignment table with donor or pool provenance and assignment QC | Analyze the intended perturbations in the public matrices | Reject barcode collisions, missing libraries and ambiguous assignments; do not infer treatment from its expression outcome |

These are data requirements, not a public record of correspondence. Repository and literature searches are dated in the lane reports. A new source version, supplied file or corrected metadata can reopen a lane immediately. Source authors may also establish that an input was never retained; record that as an unavailable input rather than silently reconstructing ground truth.

For GSE276656, animal-to-processing-batch assignments and validated author cell annotations would strengthen interpretation of the completed comparison. The source methods imply a group-level interval of about 15 days from doxycycline reintroduction to harvest. That is not an individual molecular confirmation of factor shutdown or a matched on/off trajectory. ATAC data use the same animals and do not add biological replication. A new ATAC analysis should have a specific admitted chromatin question, rather than being treated as closure of human recovery.

## What the new evidence reduces

An existing five-day mouse withdrawal experiment and a three-donor two-day human withdrawal reference comparison make a blanket request to repeat all withdrawal work inappropriate. Their recoverable data should be evaluated first. Neither supplies the required matched late human single-cell observations by itself.

The focused human feasibility design remains **33 biological collections for three donors**: 11 collections per donor under its explicit shared-baseline and D17-branch assumptions. The full nine-timepoint design remains 57. These are planning quantities, not a powered confirmatory design or a purchase request. Reuse should remove only collections/readouts that genuinely match the intended claim, with the reason recorded. [Existing measurement plan](../2026-10-public-data/MEASUREMENT_PLAN.md).

## When a new experiment is justified

Freeze the intended claim first. For donor-matched population recovery, obtain joint interpretable age/identity/state observations, verified factor withdrawal, appropriate controls, enough independent donors, and a follow-up interval justified by the claim. The exact CX004 schedule is one explicit target; it is not a universal definition of rejuvenation.

If compatible existing data can supply those observations, reanalysis remains the first route. If compatible banked material exists, assess whether it can supply the missing assay. If neither exists, prepare the smallest new collection that addresses the remaining observation. A scientific partner must establish feasibility, calibration, independent replication, scope and actual quotes before any funding or execution decision.

Same-cell persistence requires an additional defensible longitudinal or lineage link. Destructive snapshots measure populations. Retinal translation additionally requires a relevant human retinal/RPE system and a functional endpoint suited to that system. Successful fibroblast measurements would validate the controller framework in fibroblasts, without selecting a retinal treatment.

## Models and synthetic data

The useful current role of synthetic data is stress-testing missingness, donor imbalance, false positives, batch confounding and the planned measurement precision. It cannot create observed recovery, supply a true animal assignment or validate a biological safety label.

A custom predictive model should wait for a defined target with trustworthy labels, donor/study-separated evaluation, a frozen independent test set, a simple baseline and a prespecified decision that predictions would change. The present seven-animal contrast and reference age outputs do not justify training a rejuvenation or safety predictor. The existing public synthetic sampling analyses remain available; no additional biological evidence is gained by resampling the same small cohorts.

## Completion condition for this stage

The practical endpoint is a verified public packet, a complete record of what was computed, exact dependencies for each blocked comparison, and a conditional measurement package. Software PASS results certify their named arithmetic/provenance checks. All four CX004 human readouts remain insufficient_signal, and experiment replacement remains INCONCLUSIVE. A compelling public result can be a narrower reproducible finding or a failed durability hypothesis; it does not require calling the work a breakthrough.
