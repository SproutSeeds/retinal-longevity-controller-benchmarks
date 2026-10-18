# Independent mouse mPFC fixed-panel audit

The additional public dataset supports a **Verified, sign-stable descriptive cell-cycle score decrease** in a different mouse neural setting. It leaves the target human and retinal recovery questions open. The effect is a relative RNA summary, with seven experimental units and substantial biological and measurement limits.

## What became computable

[GSE276656](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE276656), associated with [Berdugo-Vega et al., Neuron 2026](https://doi.org/10.1016/j.neuron.2025.11.028), contains ten individually named mouse RNA libraries: three WT GFP, three APP/PS1 GFP, and four APP/PS1 OSK. The matched ATAC libraries are assays of the same animals. All ten sequencing animals are female, approximately ten months old; the RNA tissue is medial prefrontal cortex. The author paper states two processing batches, but an animal-to-batch table was not recovered.

The primary comparison uses all four APP/PS1 OSK animals against all three APP/PS1 GFP animals, with equal animal weights. WT animals provide descriptive context. This differs from the earlier paired acute SVZ OSKM culture experiment in region, disease, treatment, timing, and cellular mixture. It is an independent-study cross-context comparison.

The ten count matrices total **721,204,825 bytes**. No FASTQ or ATAC-fragment archive was downloaded. Acquisition followed root review of the frozen design, a documented pre-outcome metadata correction, and a separate implementation freeze. See [FREEZE.json](FREEZE.json), [metadata-amendment.json](metadata-amendment.json), and [acquisition.json](acquisition.json).

## Results

The primary score averages fixed-panel gene values after computing log2(1 + gene counts per million total RNA counts) from each animal's pseudobulk. The following are OSK-minus-GFP animal-mean differences. Rank scores use a different scale and are sensitivity results.

| Fixed panel | Primary CPM difference | Exact conditional p | Four-panel Holm p | Median-ratio difference | Rank difference |
|---|---:|---:|---:|---:|---:|
| Cell cycle | -0.123987 | 13/35 | 1.0 | -0.096347 | -0.010135 |
| Stress | +0.008254 | 33/35 | 1.0 | +0.039307 | +0.009985 |
| Reprogramming, full panel | +0.105311 | 9/35 | 1.0 | +0.117502 | -0.004693 |
| Reprogramming, excluding OSKM overlap | -0.067432 | 12/35 | 1.0 | -0.062729 | -0.024455 |

All mapped genes are present: 20 cycle, 7 stress, 9 full reprogramming, and 7 overlap-excluded genes. The original human stress panel includes CXCL8, for which the inherited mapping has no supported mouse ortholog; it remains excluded under the frozen rule.

There are only 35 possible four-versus-three label allocations. Even a minimum p of 1/35 cannot pass the first threshold of the frozen four-test Holm procedure. The paper reports random group assignment, but allocation restrictions, sequencing-subset selection, and animal-to-batch mapping are unavailable. Unrestricted label enumeration is therefore a conditional sensitivity calculation. These values do not establish equivalence or absence of a biological effect.

**Cell-cycle direction survives the specified whole-library checks.** All 20 single-gene omissions remain negative, ranging from -0.131246 to -0.115758. All seven single-animal omissions remain negative, ranging from -0.217125 to -0.006480. The latter range includes an almost-zero estimate, so sign retention should not conceal magnitude sensitivity. Using all deposited barcodes before additional RNA QC gives -0.136116.

**Reprogramming-panel direction depends on the measurement definition.** The full panel is positive under CPM, while removing Pou5f1 alone gives -0.023010. Pou5f1 contributes +0.125764 to the net full-panel difference of +0.105311. The fixed overlap-excluded panel is negative and remains so under every gene or animal omission. Because the experiment expresses OSK and the reference contains vector features, none of these summaries alone identifies endogenous pluripotency, retained identity, or a safe cell state.

**Stress is unstable around zero.** Its sign changes under the no-extra-QC sensitivity and across gene and animal omissions. It does not supply a consistent direction here.

The complete scores, contributions, omissions, and 420 label-permutation rows are in [results/](results/). No favorable subgroup or normalization replaces the primary analysis.

## Cell mixture and marker partitions

We prespecified six broad marker-defined bins plus ambiguous and unassigned bins. These are **Heuristic partitions**, not the authors' annotations or validated cell identities. A cell requires two distinct markers at the selected count threshold and assignment to exactly one eligible bin. We report both one- and two-UMI thresholds. A bin comparison requires at least 20, or separately 50, nuclei in **every one of the seven primary animals**.

The audit retains all 128 bin/panel/threshold/support rows: 112 have adequate support and 16 are unavailable. The astrocyte marker bin fails support; it is not dropped from the record.

| Cell-cycle comparison | At least 1 UMI per qualifying marker | At least 2 UMI per qualifying marker |
|---|---:|---:|
| Excitatory marker bin | -0.073139 | -0.100257 |
| Inhibitory marker bin | -0.089173 | -0.209225 |
| Microglial marker bin | +0.126825 | +0.098889 |
| Oligodendrocyte marker bin | -0.189868 | -0.090594 |
| Precursor marker bin | -0.945400 | -0.307674 |

Each displayed bin passes both animal-level support thresholds. The microglial-bin direction opposes the pooled direction at both detection thresholds. The precursor magnitude changes substantially with the detection rule. Group-average marker-bin fractions also differ: at the one-UMI rule, the excitatory bin averages 30.05% in OSK and 34.35% in GFP animals, and the oligodendrocyte bin averages 17.83% versus 14.51%. These are fractions of recovered RNA-QC nuclei, not tissue cell abundance estimates.

The partitions therefore expose heterogeneity without eliminating mixture, depth, or classification effects. They do not isolate infected engram cells. A treatment-associated whole-library score cannot be interpreted as a universal or cell-autonomous response.

## A distinct author-pipeline reproduction condition

The deposited matrices contain **35,907 nuclei**. Our frozen RNA QC retains **34,210**, whereas the paper reports 34,603 after its RNA processing. An independent cell-at-a-time source recount reproduces our 34,210 exactly, including every full-gene aggregate and every fixed marker-bin count and score.

The **393-nucleus discrepancy remains unresolved**. The published scripts reference additional local metadata, reference objects, and annotated objects. We did not reconstruct the complete author pipeline or force a match by changing thresholds. This is a separate pipeline-reproduction condition, not evidence that either biological conclusion is false. See [FAILED_PATHS.md](FAILED_PATHS.md).

## Timing and the recovery decision

The primary methods describe OSK induction around learning, Dox reintroduction afterward, remote recall two weeks later, and tissue collection the following day. Combining those descriptions suggests a roughly 15-day endpoint after Dox reintroduction; this is an **inference from the group schedule**, not a measured factor-off interval for each sequenced animal. See the qualified timing note in [SOURCES.json](SOURCES.json).

This endpoint is useful context for a temporally limited OSK experiment. The new analysis does not provide matched induction/on/off trajectories, same-cell longitudinal recovery, a validated age change in these nuclei, human recovery, or retinal function. All four CX004 readouts remain **insufficient_signal**, and replacement of the target recovery experiment remains **INCONCLUSIVE**.

The next useful inputs for this dataset are the animal-to-batch and behavioral-cohort map, exact collection/induction metadata, author barcode annotations and QC inclusion flags, and the relevant reference/custom genome specification. Those can make an engram- and batch-aware reanalysis more faithful. They cannot by themselves turn this mouse mPFC dataset into a matched human retinal recovery experiment.

Other checked public leads are recorded in [SOURCES.json](SOURCES.json): retinal Xenium/constitutive glial OSK, the existing RPE OSK/GSTA4 series, a cyclic neural OSKM raw-read study, and a newer sustained-OSK brain RRBS dataset. None was admitted as a substitute for the missing target observations. This is a bounded search disposition, not a claim that all existing data everywhere have been exhausted.

## Verification hook

See [REPRODUCTION.md](REPRODUCTION.md). Six synthetic tests pass; saved-artifact and source-hash verification passes **897/897** checks; an independently implemented cell-at-a-time raw recount passes **646,760/646,760** comparisons. These checks establish arithmetic, source integrity, and support accounting. Biological recovery and safety remain separate questions.
