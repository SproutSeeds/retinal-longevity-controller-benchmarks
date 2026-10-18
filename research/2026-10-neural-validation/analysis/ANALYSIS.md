# Animal-level neural comparator

**Verified computation; heuristic interpretation.** The frozen analysis produces a negative mean microglia cell-cycle marker difference in both mouse cohorts. Cohort 2 satisfies the predefined descriptive stability rule. Cohort 1 has a smaller negative mean, with direction reversals when individual animals are omitted. The supported finding is a narrow, animal-sensitive mean-direction comparison within one study.

The original data and experiment are credited to [Xu et al., Nature Aging 2024](https://doi.org/10.1038/s43587-024-00594-3), [GSE224438](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE224438), and [Zenodo record 10626910](https://zenodo.org/records/10626910). This packet contributes the separately frozen reanalysis. [HGNC HCOP](https://www.genenames.org/help/hcop/) supplies the pinned orthology assertions.

## Frozen design and complete output

The primary cohort-2 estimator gives equal weight to two within-lane animal differences: L0002 minus L0003 in lane 1 and L0004 minus L0011 in lane 2. The additional untreated L0042 animal enters the declared secondary comparison. Both old treated animals and both paired controls must meet the fixed minimum of 20 cells and 500 detected genes for each named cell type. The 10-cell sensitivity retains the same gene requirement and cannot repair a failed primary comparison.

Cohort 2 contributes 3,857 cells from seven animals. Its complete grid contains 98 animal-by-cell-type rows, including all 70 cells in unresolved numeric clusters and zero-cell combinations. Of 80 predefined cell-type/panel/support-tier rows, 28 are available: eight at primary support and 20 at the lower cell floor. All 52 unavailable rows retain their reasons. Primary support admits Microglia and Oligodendrocyte; the lower floor additionally admits Astrocyte_qNSC, Neuroblast and Endothelial.

Cohort 1 contributes 1,194 cells from four distinct animals in one multiplexed library. Its 80 predefined rows include 32 available rows: 12 at primary support and 20 at the lower floor. All 48 unavailable rows remain in the output. Primary support admits Astrocyte_qNSC, Microglia and Oligodendrocyte. No within-library animal pairings or extra lane replicates are invented.

The previous fixed human marker lists are reused. All 36 orthology-eligible mouse genes are present: cell cycle 20/20, stress 7/8 original human genes, full reprogramming 9/9, and reprogramming without OSKM overlap 7/7. Coverage is checked against both original and eligible lists. The fixed HGNC-supported rule excludes CXCL8; it does not substitute Cxcl15. CD24 maps to Cd24a, TP53 to Trp53, and CDKN2A to Cdkn2a, with alternative assertions retained. Zero-expression genes remain in averages. Pou5f1 and Sox2 are explicitly excluded in the endogenous-component sensitivity; the full panel remains transgene-overlapping.

Each animal/type raw pseudobulk is transformed as log2(1 + CPM), followed by an equal-weight panel mean. The median-ratio sensitivity estimates factors from genes positive in every animal in that contrast, with at least 100 such genes. Neither normalization provides absolute RNA quantities. Every eligible comparison includes individual animal scores, raw panel counts, gene values, all treated-control differences, every single-gene omission and refitted single-animal omissions. Cohort-2 lane omissions are single-pair observations. Complete per-animal CPM profiles are retained even when a sparse row cannot enter a contrast.

## Shared primary comparisons

Values are treated-minus-control mean log-expression score differences. The two columns for each cohort are CPM and median-ratio CPM equivalent. These are marker-score differences, not calibrated phenotype or age changes.

| Cell type | Fixed panel | Cohort 2 CPM | Cohort 2 median ratio | Cohort 1 CPM | Cohort 1 median ratio |
|---|---|---:|---:|---:|---:|
| Microglia | Cell cycle | -1.014 | -0.993 | -0.290 | -0.316 |
| Microglia | Stress | +0.165 | +0.184 | +0.176 | +0.155 |
| Microglia | Reprogramming, full | +0.033 | +0.037 | -0.260 | -0.266 |
| Microglia | Reprogramming, OSKM overlap excluded | -0.063 | -0.062 | -0.148 | -0.151 |
| Oligodendrocyte | Cell cycle | -0.084 | -0.086 | +0.328 | +0.327 |
| Oligodendrocyte | Stress | +0.097 | +0.093 | -0.150 | -0.150 |
| Oligodendrocyte | Reprogramming, full | -0.027 | -0.028 | -0.203 | -0.203 |
| Oligodendrocyte | Reprogramming, OSKM overlap excluded | -0.133 | -0.133 | -0.338 | -0.337 |

Only microglia cell cycle has concordant means above the fixed absolute 0.25 score floor in both cohorts under both normalizations. Cohort-2 within-lane CPM effects are -0.303 and -1.725. Its all-three-controls effect shrinks to -0.525. All cohort-2 single-animal omission means remain negative, but removing control L0011 leaves an unpaired omission effect of -0.199, below the descriptive floor.

The cohort-1 microglia mean is animal-sensitive: CPM animal-omission effects range from -1.120 to +0.539; median-ratio omissions range from -1.136 to +0.508. Removing treated animal 960L or control 953L reverses the mean direction. One of the four descriptive treated-control differences is positive. All single-gene omissions preserve the negative mean. Mean agreement and animal consistency are therefore reported separately.

At the lower 10-cell floor, the cohort-2 Neuroblast cell-cycle mean is positive (+0.268 CPM), while cohort 1 is negative (-1.130 CPM). Endothelial stress-panel means are positive in both cohorts (+0.669 and +0.307 CPM), but the cohort-2 comparison does not satisfy the animal/lane stability rule. These sensitivity results retain their weaker cell support.

## Interpretation limits

The observed contrast bundles doxycycline exposure and OSKM induction. These processed objects omit BL6 doxycycline-only controls, so drug and construct effects cannot be separated. Cohort 1 is 18–20 months/all male/10x v3.0; cohort-2 old animals are 24–26 months/mixed sex/10x v3.1. Named annotations also use different cluster collapses. These are same-study cross-cohort comparisons, with independent animal labels under those source-specific conditions.

Cohort-1 sample labels encode DOB20180508 for treated animals and DOB20180501 for controls. Birth date differs by condition; litter membership is unconfirmed. Cohort-2 pairing uses sequencing lane and the published table's matched sex; its identifier date token is not established as date of birth. Raw transcripts cannot distinguish endogenous from introduced Pou5f1 or Sox2; Sox2 also has ordinary neural-lineage roles.

Recovered-cell fractions include all unresolved cells in their primary denominator and separately report the named-cell denominator. They describe the sequenced collection, with capture, dissociation, filtering and subtype-mixture limitations. CPM/median-ratio agreement checks those size-factor choices and does not resolve compositional or absolute-RNA uncertainty. All four CX004 readouts remain `insufficient_signal`; this analysis supplies no late human recovery, retinal function, efficacy or calibrated safety measurement.

## Verification and replay

- [VERIFICATION.json](VERIFICATION.json): 3,534 arithmetic, completeness and provenance checks passed, together with 43 synthetic adversarial tests. The synthetic tests inspect corruption and failure behavior; they supply no biological observations.
- [cohort2-results.json](cohort2-results.json), [cohort1-results.json](cohort1-results.json), and [cross-cohort-results.json](cross-cohort-results.json): complete results and failures.
- [contract.json](contract.json), [cohort1-contract.json](cohort1-contract.json), and [orthology.json](orthology.json): frozen specifications and mapping assertions. The parent receipts preserve prospective freeze chronology, including the fact that cohort-2 outcomes were known when cohort-1 metadata compatibility was committed.
- [input-manifest.json](input-manifest.json): exact public URLs, hashes and attribution; raw files remain outside the repository.

The default runners verify the exact frozen files against their original commits. Exported copies can use the explicit `--replay-frozen-hashes` option, which checks all archived hashes and authorization receipts and records that historical git proof was not rerun. Execution-mode receipts remain separate from deterministic biological result artifacts.

```sh
uv run analysis/neural_analysis.py --cache /path/to/cohort2-cache --contract analysis/contract.json --freeze-receipt FREEZE.json --replay-frozen-hashes
uv run analysis/cohort1_analysis.py --cache /path/to/cohort1-cache --replay-frozen-hashes
uv run analysis/verify_analysis.py
uv run analysis/reproduce.py --cohort2-cache /path/to/cohort2-cache --cohort1-cache /path/to/cohort1-cache
```

Run these commands from the packet root. [REPRODUCTION.json](REPRODUCTION.json) records byte comparisons for both cohort JSON files, the cross-cohort file, and four QC/composition TSV files on the pinned local execution environment.
