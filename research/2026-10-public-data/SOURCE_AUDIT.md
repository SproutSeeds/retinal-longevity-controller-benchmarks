# Public sources and remaining inputs

**October 18 update:** the [metadata recovery pass](../2026-10-metadata-recovery/README.md) extracts all 295 SRSF1 coefficient terms, resolves 72 human recovery library identities, and clarifies the distinct OSK/GSTA4 findings. Exact clock preprocessing and late human recovery remain open.

Checked October 17, 2026. This targeted audit followed primary deposits, linked papers, supplements and author code. It is not an exhaustive absence proof. `source-resolution.json` records admission decisions; `source-manifest.json` records retrieved-byte hashes and failures. New resources should be admitted against the same four readouts before expanding downloads.

| Resource | Usable role | Remaining limitation / exact next input |
|---|---|---|
| [GSE350289](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE350289) | Human pooled perturbation screen | All 769 library records and the current file inventory were checked. Need exact cell barcode → hash → perturbation mapping, donor-pool provenance and populated workbook sheets. Do not infer assignments from expression or row order. |
| [SRSF1 / GSE325735](https://www.nature.com/articles/s43587-026-01234-8) | Human bulk recovery and three-donor diagnostics | Reconcile caption 6/12-day recovery with GEO 8/16-day labels. Supply fitted clock, gene filters, training/calibration objects and experimental batch metadata. [Pinned clock code](https://github.com/saschajung/Clock/tree/7ae5f38b7ea74f76cb13076b64350d5930bb152f). |
| [Sengstack / Figshare 30898748](https://doi.org/10.1073/pnas.2515183123) | Measured human single-cell perturbations | Dual-guide SI recovered. Need original assignment table and NT-vector pair map. Neonatal replicative-passage cells have no relevant late withdrawal arm. |
| [Ocular GSE304044](https://doi.org/10.1101/2025.08.30.673239) | Mouse RPE, ARPE-19 and fibroblast comparators | Need animal/eye/sex/cohort manifest, timing reconciliation, historical fitted clock and imputation references, vector sequences and exact functional outcome data. Current [tAge](https://github.com/Gladyshev-Lab/tAge) license requires separate review before reuse. |
| [Mouse epidermal study](https://www.nature.com/articles/s41467-026-69047-2) / PRJNA1139235 | Skin/niche single-cell analogue | Recovery histology and pooled-condition single-cell assays do not establish a human late recovery ladder. [Author code](https://github.com/CB-postech/scRNA-seq_mouse_Epi-iOSKM). |
| [Mouse SVZ / GSE224438](https://www.nature.com/articles/s43587-024-00594-3) | Cyclic exposure and animal-aware neural analysis | Ten library entries; multiplexed whole-body and targeted designs require source-specific animal mappings. [Author code](https://github.com/gitlucyxu/SVZreprogramming). Separate neural replication question. |
| [GSE245385](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE245385) | 65-library mouse neural stem-cell time course | Bulk, different species and lineage. Retain as mechanism context; do not pool with human donors. |
| [GSE276656](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE276656) | Mouse mPFC multiome, WT / APP-PS1 / OSK | Twenty RNA/ATAC entries represent ten paired samples, not twenty independent animals. [Source paper](https://doi.org/10.1016/j.neuron.2025.11.028). |
| [GSE297233](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE297233) | Eight-library early human OSK/OCT4YR comparator | One 96-year-old donor line, four-day exposure, no late withdrawal. [Source paper](https://doi.org/10.1016/j.cell.2025.07.031). |
| [GSE144600](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE144600) | Measured mouse liver factor-off comparator | One early off endpoint; four-cell QC discrepancy remains. [Source paper](https://doi.org/10.1016/j.celrep.2022.110730). |

Earlier human Gill recovery and GSE147564 late-state observations remain useful supporting evidence. Their separate studies cannot establish same-cell lineage continuity or create an unmeasured joint late recovery cohort. Public single-cell snapshots are destructive; donor matching alone does not track individual cells.

## Exact metadata requests, ready for a later authorized contact

No messages have been sent. The following concise requests specify artifacts that could eliminate further work:

1. GSE350289: machine-readable barcode, hash identity, perturbation, donor/pool, sample and batch mapping; clarify missing workbook sheets and unmatched rows.
2. SRSF1: sample-level induction start, stop and harvest dates; experimental batches; exact clock coefficients/model, calibration and imputation objects; preprocessing versions.
3. Perturb-seq: cell-to-target assignment table, guide UMI thresholds, both guide sequences per vector, NT pair mapping and source QC barcode list.
4. Ocular: animal and eye identifiers, age/sex, vector/construct and harvest timing per library; exact historical clock weights and reference distribution; transgene alignment reference; linked functional endpoint measurements.
5. Liver: final 2,284-barcode list and exact QC commands to resolve the four-cell mismatch under our UMI interpretation.

Reanalysis should resume when a specific input arrives. Search status alone does not justify repeating a large download or fitting a larger model.
