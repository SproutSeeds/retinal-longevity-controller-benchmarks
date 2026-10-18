# Donors, genes and recovery measurements

This packet extends the [October 18 independent comparator](https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks/tree/main/research/2026-10-independent-comparator) with separate, bounded analyses. Original experiments belong to Xu et al. and Lu et al. Our contribution is the reproducible reanalysis, source reconciliation and explicit interpretation checks. Claims of biological novelty require further review.

## Mouse neural single-cell cohorts

[GSE224438](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE224438) and the [Zenodo deposit](https://doi.org/10.5281/zenodo.10626910) provide raw RNA assays and animal identities for 3,857 cohort-2 cells and 1,194 cohort-1 cells. Counts are summed within animal and deposited cell type. Each animal receives equal weight. Cells and genes do not supply additional animal replicates.

Cohort 2 uses two same-lane treated/control differences as its primary estimator. All three old untreated animals enter a separate sensitivity. Cohort 1 compares two treated and two untreated animals in one multiplexed library. Its animals differ in age, sex composition and chemistry from cohort 2. This is a comparison across independent animals in the same study, with these differences retained. Both young cohort-2 animals occur in lane 3 and provide no identified age-reversal comparison.

The four inherited panels cover cell-cycle markers, stress markers, reprogramming markers, and the latter panel with POU5F1/SOX2 overlap excluded. Orthology requires exactly one HGNC-supported HCOP mouse candidate. All alternatives and exclusions remain in [orthology.json](analysis/orthology.json). CXCL8 has no eligible mapping. The 36 eligible mouse panel genes are present. The full reprogramming panel includes factor-overlapping genes, whose counts do not identify transcript origin.

Primary support requires 20 cells and 500 detected genes per required animal/type. A separate 10-cell sensitivity uses the same gene floor. Missing support produces a failure row. Scores average log2(1 + CPM) across fixed present genes, including zero-expression genes. Median-ratio CPM-equivalent normalization is a sensitivity. Neither measures absolute RNA abundance. All donor, lane and gene omissions remain visible. The 0.25 descriptive effect floor is a heuristic, without a biological calibration or power guarantee.

[The main contract](analysis/contract.json) and [decomposition contract](decomposition/contract.json) were committed before neural expression outcomes. The cohort-1 compatibility contract was committed after cohort-2 outcomes, while retaining the original panels and reserved cross-cohort question. Freeze receipts preserve that chronology. The [complete analysis](analysis/ANALYSIS.md) reports every available and unavailable comparison.

## Recovered-cell composition

Per-animal composition first uses every recovered cell, including unresolved numeric clusters. A second denominator includes only named cell types. Fractions describe the recovered collection and may reflect capture, dissociation, filtering or subtype differences.

The separate decomposition averages per-cell log2(1 + CP10k) panel scores, with a CP1M sensitivity. For each support floor, retain only named types supported in all four primary animals, and renormalize their fractions to one. For treated/control fractions p and q and type means a and b:

```
total       = sum(p*a - q*b)
composition = sum((p-q)*(a+b)/2)
within_type = sum((p+q)*(a-b)/2)
total       = composition + within_type
```

This is an exact algebraic partition of a conditional cell-average summary. It does not decompose the pseudobulk score, identify causal composition effects, or separate states within an annotated type. All retained fractions and excluded cells are reported. The two lane contrasts receive equal weight. [Results](decomposition/results.json) include both support floors, both scales and all four panels.

## Human bulk marker audit

[GSE297233](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE297233) has eight libraries from one 96-year-old donor. This post hoc audit independently replays the original arithmetic, then decomposes each score into gene contributions. Every original numerical artifact is preserved. The score after a gene omission has a different denominator, so additive contribution and omission magnitude reduction are reported separately.

The new rank and top-abundance sensitivities were specified after the original outcomes were known. They diagnose dependence on expression scaling and concentration. They do not identify technical artifacts or calibrated cell states. Every original panel, normalization, per-gene value and omission-by-library comparison remains available in [the addendum](human/ADDENDUM.md).

## Additional donor and per-cell analyses

The [bulk contract](bulk/contract.json) specifies all nine A18h donor pairs in [GSE245385](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE245385), with four old and five young mice. Donor response is the treated-minus-untreated panel score. The age statistic compares mean responses, and enumerates the 126 possible old-label assignments under an exchangeability assumption. Age was not randomized. Sex and unmeasured donor differences may violate that assumption. Holm adjustment covers the four fixed CPM panels. An exact donor sign test is a separate secondary family. Median-ratio and rank variants remain sensitivities. A nonsignificant age contrast does not establish equivalence. Differentiation samples retained doxycycline and cannot answer withdrawal stability.

The human per-cell extension uses [GSE297234](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE297234), with one donor at each of two ages and four collection times. The five endogenous markers and five fibroblast markers differ from the seven-gene bulk panel and reuse the prior local time-course specification. The extension measures joint marker detection and a donor-baseline identity score. It supplies no trained classifier, true state prevalence or age-effect estimate. Every donor/time denominator remains separate. Detection, panel omission, baseline cutoff, gene-detection QC and fixed-depth thinning are explicit sensitivities. Thinning resamples measured counts for a detection diagnostic and creates no new biological observations.

## Source recovery and biological authority

The [recovery audit](recovery/RECOVERY.md) compares the author code, published sample table, GEO headers, SRA/ENA inventory and both Zenodo versions. The publisher lists seven samples absent from the shared whole-body objects. Five have a `2Dox5` author label. The label alone does not verify final removal-to-harvest timing. Public GEX barcodes without verified sample assignments cannot reconstruct these animals. A missing LMO file in the inventory does not establish that relevant barcode reads are absent from every FASTQ.

The frozen source files support exact computation on the admitted observations. Biological interpretations remain Heuristic. CX004-R01 through R04 remain `insufficient_signal` because these analyses do not supply the required matched late human recovery, calibrated unusual-state assessment and trajectory evidence. Code tests and synthetic fixtures check software behavior. They add no observed biological ground truth.
