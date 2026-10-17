# Analysis and verification

The frozen `analysis-contract.json` predates the new outcome runs but follows inspection of the prior pass and newly recovered guide methods. This is a source-informed reanalysis, not an independent preregistered experiment. `liver-contract.json` separately records admission of the mouse withdrawal comparator. All biological interpretations remain Heuristic.

## Guide reconstruction

Raw RNA and 804 guide columns come from the authors' [Figshare deposit](https://doi.org/10.6084/m9.figshare.30898748). Target identity is reconstructed from channel names and CRA/CRI machinery. Every guide channel contributes to the dominance denominator. The primary threshold is a target sum of at least 5 UMIs and at least 80% of guide UMIs, with both expected targeting channels detected. NT channels are pooled and require two detected channels; the original NT vector pairing remains unknown. DLX5_CRI and PHOX2A_CRA each lack a complete pair and are excluded under every variant.

All 36,514 cells remain accounted for, including 6,809 WT cells and unassigned cells. Comparisons require at least 20 target cells and 20 matched NT cells. Summed RNA counts are converted to CPM and log2(CPM+1); perturbation-minus-NT effects are correlated across genes with WT PD32-minus-PD14. Genes require at least 1 CPM in both WT pseudobulks. This is a passage-associated contrast, not a chronological-age predictor or donor-replicated causal estimate.

Primary, permissive, strict and no-pair-required variants admit 208, 232, 158 and 280 comparisons. `guide-call-comparison.tsv.gz` preserves old/new assignments for every barcode. Correlations, target-expression checks, group sizes and cycle-panel exclusions are all retained. Exact replication needs the authors' assignment table and numerical thresholds.

## Human treatment diagnostic

Three donors each contribute two SRSF1 and two BFP libraries at the source-labeled 5-day-on/2-day-off schedule. Mapping comes from public GEO metadata and the paper's deposited gene mapping. Ambiguous identifiers are excluded. Fixed identity, reprogramming, cycle and stress panels determine features; there is no outcome-driven feature selection or parameter tuning.

Each fold trains on two donors and tests the third. Scaling is fitted only to training data. Balanced logistic regression uses C=1 and seed 171026. Cycle-excluded and library-size/detected-gene models are fitted independently. All 216 balanced within-donor 2-versus-2 relabelings are enumerated and the entire cross-validation pipeline is refitted. Their mean AUROC is 0.5. The fraction meeting the observed score is an algorithmic label control, not a biological efficacy p-value.

All 12 libraries share a sequencing batch; experimental batch is unrecorded. The admission guard treats identical missingness explicitly, rather than inventing a batch identifier. Repeated libraries do not increase the donor count. The classifier is a serialized diagnostic (coefficients, scaling, features, splits and predictions), not a therapeutic ranking or deployable aging model.

## Mouse RPE

GSE304038 supplies 18 libraries: 7 young, 4 old untreated, 3 old vector controls and 4 old OSK. Raw matrix totals include all rows; ambiguous gene symbols are excluded from feature contrasts. Compute old-minus-young and OSK-minus-vector differences in mean log2(CPM+1), then Pearson and Spearman correlations across genes. Sensitivities use baseline CPM thresholds 1/5/10 and fixed cycle/reprogramming exclusions. Every library is omitted once in a separate diagnostic.

PCA describes library structure without batch correction. The correlation of old-minus-young with vector-minus-old shares the old group with opposite signs and is algebraically coupled; it cannot independently demonstrate a batch effect. Libraries lack verified animal/eye/sex identifiers. None of these calculations reproduces the authors' clock or vision endpoints.

## Observed liver withdrawal

The [source study](https://doi.org/10.1016/j.celrep.2022.110730) describes one day of induction and one day after withdrawal. GSE144600 supplies 8,277 untreated and 7,765 exposed deposited barcodes. The frozen primary performs only nonempty-library QC and reports whole-library marker summaries. These are composition-sensitive diagnostics, not inferred cell types or calibrated state frequencies.

After the deposited total differed from the paper's 2,284 analyzed cells, we added an explicitly post hoc source-method sensitivity. Interpreting its stated 2,000-read and 45% mitochondrial cutoffs using deposited UMI counts retains 1,261 untreated and 1,027 exposed cells, totaling 2,288. The paper reports 1,258 and 1,026. The exact four-cell difference, original filtered barcode list and reads-versus-UMIs interpretation remain unresolved. We retain both counts and do not present 16,042 as the authors' final analyzed cohort.

## Synthetic sampling

Each hypothetical donor has a latent state prevalence drawn from a Beta distribution with mean p and latent intraclass correlation rho. Conditional on that prevalence, cells are independently sampled with detector sensitivity s. For d independent donors and n cells each, the probability of at least one true detection is `1 - E[(1-s*q)^n]^d`. At rho=0 the closed form is `1-(1-s*p)^(d*n)`.

Gauss-Jacobi quadrature evaluates the expectation. Four scenarios are checked against 512-node integration and seeded 100,000-draw Monte Carlo. The 36 scenarios vary p, rho and donor count while fixing 1,200 total cells. Independent false flags use `1-specificity^N` when true prevalence is zero. At 99.9% specificity, 373 cells have a 31.1% chance of at least one false flag under these assumptions. Detector specificity therefore needs calibration as well as sensitivity.

These synthetic records describe assumptions. They are never merged with observed expression, treated as validation labels, or used to close a biological readout. Generative expression models are deferred until compatible independent data can test whether they add useful predictive information beyond simple baselines.

## Verification hook

Run `python3 verify.py` for the recorded 75 computational checks and `uv run test_analysis.py` for 12 failure-case tests. Expected outputs are `PASS 75/75` and `OK`. Checks cover contract binding, count conservation, guide exclusions, donor separation, complete negative controls, numerical integration and unchanged readout verdicts. The receipt is Verified only for its stated computational scope. Biological experiment replacement remains INCONCLUSIVE.

Source downloads and raw matrices are excluded from Git. Input hashes pin the observed files; dynamic article/code inventories are dated source observations. Deterministic seeds and coefficients are recorded. Floating-point variation across numerical libraries is expected; no claim depends on the last decimal place.
