# The measurement public data still need

**Status: proposed design for funding discussion; Conjecture until measured.** Public-data analysis can continue now. New wet-lab work is conditional on unresolved data gaps, a qualified experimental partner, feasibility review, funding and separate authorization. No purchases, bookings or wet-lab arrangements are part of this package.

## Goal and reason

Determine whether a bounded late reprogramming response in adult human fibroblasts preserves identity and recovers after factor withdrawal, while measuring heterogeneous cell states that bulk averages can hide. This would expand the public dataset with a matched trajectory that the inspected sources currently do not provide.

This is a controller-validation step toward retinal longevity research. Human fibroblast results would validate the measurement and decision framework in that system. A later retinal/RPE bridge needs its own relevant cells, perturbation conditions and functional readouts before supporting an ocular intervention claim.

The original benchmark asks for D0, D8, D10, D13, D15, D17, D20, D28 and D35, with untreated reference, late exposure through D28, and withdrawal/recovery through D35. A smaller pilot can estimate feasibility and donor variability. It cannot retire the full nine-timepoint requirement.

## Reuse before new experiments

First seek exact source metadata, corrected assignments, existing compatible single-cell data, and banked material from the relevant studies. A collaborator would need to establish provenance, consent/use rights where applicable, sample compatibility and sufficient material. Metadata recovery could resolve analysis blockers; banked material could avoid repeating cell culture. No contact has been made on the basis of this proposal.

## Candidate design and quantities

Planning assumes three independent adult human donors, matched conditions within donor, and a proposed branch at D17 from common induced cultures into continued exposure and withdrawal. The biological feasibility of that branch and the factor regime must be agreed with an experimental PI before execution. This is an analysis design, not a bench protocol.

| Timepoint | Untreated reference | Common induced / continued exposure | Withdrawal branch | Libraries per donor |
|---|---:|---:|---:|---:|
| D0 | 1 shared baseline | — | — | 1 |
| D17 | 1 | 1 before branching | — | 2 |
| D20 | 1 | 1 | 1 | 3 |
| D28 | 1 | 1 | 1 | 3 |
| D35 | 1 | — | 1 | 2 |
| Focused pilot total | 5 | 3 | 3 | **11** |

**Focused pilot: 3 × 11 = 33 single-cell libraries.** Sharing the D0 baseline and pre-branch D17 induced condition is an explicit assumption; independent culture replicates would add libraries. D20 is three days after the proposed withdrawal, D28 eleven days, and D35 eighteen days. A D35 observation alone cannot prove long-term stability.

**Full nine-timepoint benchmark: 57 libraries.** Add reference and induced libraries at D8, D10, D13 and D15: 4 times × 2 conditions × 3 donors = 24 additional libraries. This yields 33 + 24 = 57. The continued-exposure arm runs through D28; recovery runs through D35. A D49 reference/recovery extension would add six libraries for the three-donor design, for 39 or 63 total respectively. These quantities describe biological collections, not guaranteed sequencing runs or technical replicates.

Three donors are a feasibility starting point, not a power calculation. Donor-level variance, expected effect size, loss rate and the calibrated rare-state detector determine a confirmatory donor/sample count. Added cells within one donor improve sampling of that donor but do not add independent biological replication.

## Required measurements

- Single-cell expression with donor, condition, sampling time, induction/withdrawal chronology, batch, viability and QC metadata. Randomize processing and balance conditions across batches; retain sample-level exclusions.
- The frozen marker families: adult fibroblast identity, pluripotency, EMT/plasticity, cycle, DNA damage/stress, fetal/developmental drift and age-associated signatures. Prespecify which are primary endpoints and which are exploratory.
- An age endpoint with a documented, licensed, frozen model and relevant calibration. Joint per-cell claims require identity and age assessment in the same cells or an explicitly justified paired assay; a matched bulk clock cannot establish which individual cells improved.
- Orthogonal identity/structure and viability/damage measurements. Paired chromatin/regulator information and a matched 3D imaging subset are preferred. Assay choices, repeat counts and acceptable precision remain partner decisions.
- Independent calibration/annotation for unusual states, including positive/negative reference controls. Cell-state flags are screening observations; transcriptomics alone cannot certify transformation safety.

Repeated destructive snapshots support donor-matched population trajectories. They do not follow the same cell. If the scientific claim requires lineage continuity rather than population continuity, a compatible lineage-tracing or equivalent design is an additional requirement with its own feasibility, cost and oversight review.

## Predefined decisions

Before data collection, freeze the primary contrasts, endpoints, exclusions, missing-data rules, donor-aware inference and multiplicity handling. Choose numerical effect/identity equivalence margins from assay validation and biological review, rather than fitting them to the observed results. Synthetic scenarios can guide this design but cannot supply biological ground truth.

1. **Reuse gate:** admit an existing dataset only if it supplies the matched system, timing, conditions, identifiers and readouts. Partial coverage reduces the new collection scope; it does not automatically satisfy all four readouts.
2. **Feasibility gate:** pilot data must retain interpretable identity/age measures, recover enough cells, resolve batch effects and estimate donor variation. Failures trigger a documented redesign or stop.
3. **Scientific gate:** evaluate late identity, unusual-state prevalence, recovery durability and population continuity separately. Improved age-associated scores alongside unresolved identity or stress leave the controller in support-only status.
4. **Retinal bridge gate:** choose a relevant human retinal/RPE model with independent donors and function appropriate to that lineage. RPE barrier/polarity or photoreceptor-support assays and neuronal function address different systems; a specialist should choose the endpoint. Fibroblast success does not choose a retinal intervention.

## Funding work packages and budget template

The funding ask is staged: recover reusable inputs; establish partner feasibility and calibrated assays; fund the missing collection only after those checks; release the deidentified, permitted dataset and reproducible analysis. Dollar amounts require actual institutional/core quotes. No invented price estimate is included.

| Budget line | Planning basis | Quote / decision still required |
|---|---|---|
| Donor material and culture setup | 3 independent donor lines initially | Availability, provenance, eligibility, licensing and culture replicate plan |
| Pilot single-cell capture/library prep | 33 biological collections | Core platform, batching, capture targets, sample losses and rerun allowance |
| Sequencing | 33 libraries initially | Reads per library from platform/core and pilot complexity; multiplexing plan |
| Full ladder extension | +24 collections | Only if early windows remain needed after reuse and pilot review |
| Longer recovery extension | +6 collections at D49 | Whether D35 duration is sufficient for the proposed claim |
| Orthogonal assays / imaging | Matched subset, count TBD | Endpoint, assay precision, controls, equipment and staff effort |
| Analysis and independent review | Fixed contract, QC, donor models and replication report | Personnel effort, reviewer availability and compute/storage quote |
| Data stewardship | Metadata, permitted raw/processed deposit, documentation | Repository, consent/use restrictions, archival storage and publication costs |
| Contingency / indirect costs | Explicit quote-based calculation | Institution-specific policy and named risk allowances |

`budget-quantities.json` is the machine-readable quantity basis. A submission-ready budget also needs a named PI/partner, signed scope, realistic schedule, applicable approvals, funder fit and actual quotes. The present package supplies the scientific rationale, reusable evidence, sample arithmetic and decision gates for that discussion.

## Deliverables a funder could inspect

A frozen protocol/analysis contract; complete sample manifest; source-linked QC report; donor-level estimates with uncertainty; every unresolved and negative result; a public permitted dataset; executable analysis and model cards; a readout-by-readout decision; and a clear statement of what further retinal evidence would be needed. Success includes a reproducible result that rejects an intervention or narrows the design.
