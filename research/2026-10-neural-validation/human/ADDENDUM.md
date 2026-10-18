# Human marker-score revision: magnitude and observed availability

**Claim level: Heuristic interpretation; Verified computation after the linked verification hook passes.** This post hoc revision preserves the October 18 independent-comparator packet as an immutable historical result. It changes the interpretation and adds diagnostics; the original arithmetic is reproduced to a maximum absolute difference of 7.11e-15.

The seven-gene panel excluding POU5F1 and SOX2 has a positive mean difference under both original normalizations. CD24 supplies 79.59–89.50% of that signed difference. Thus the panel establishes an increase in this chosen expression summary, dominated by CD24, rather than broad activation of an endogenous pluripotency program. A calibrated reprogramming classifier was never established. Source experiment and biological interpretation belong to [Lu et al., Cell 2025](https://doi.org/10.1016/j.cell.2025.07.031); the count data are [GSE297233](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE297233).

| Construct | Normalization | Original seven-gene difference | CD24 additive contribution | CD24 signed share | Mean after omitting CD24 | Mean magnitude reduction |
|---|---|---:|---:|---:|---:|---:|
| OSK | log2(1 + CPM) | 0.627504 | 0.524605 | 83.60% | 0.120049 | 80.87% |
| OSK | Median ratio | 0.526740 | 0.471440 | 89.50% | 0.064517 | 87.75% |
| O4YRSK | log2(1 + CPM) | 0.427164 | 0.339993 | 79.59% | 0.101699 | 76.19% |
| O4YRSK | Median ratio | 0.353628 | 0.289935 | 81.99% | 0.074308 | 78.99% |

For a seven-gene mean, a gene's additive contribution is its treated-minus-control transformed-expression difference divided by seven. The signed share divides that contribution by the full panel difference; it can differ from an absolute contribution share when genes move in opposing directions. The omission mean uses six genes, so the omission magnitude reduction and the additive share are distinct quantities. Both are reported for every gene in [gene-contributions.csv](gene-contributions.csv).

The earlier statement that the reprogramming direction survives every omission is correct for condition means. It establishes sign stability, not stable magnitude or independent confirmation across markers. It also does not establish joint stability across omissions and individual library comparisons. After removing CD24, the four library contrasts span negative and positive values in every original normalization/construct combination:

| Construct | Normalization | Minimum library difference after CD24 omission | Maximum |
|---|---|---:|---:|
| OSK | CPM | -0.016455 | 0.256553 |
| OSK | Median ratio | -0.078473 | 0.207507 |
| O4YRSK | CPM | -0.018757 | 0.222155 |
| O4YRSK | Median ratio | -0.038289 | 0.186905 |

The phrase “expression robustness” in the prior claim title is therefore narrowed to the specific separately tested sign properties. A reading of its headline as robust activation of a multi-gene endogenous reprogramming program would overstate the data.

## Feature presence and sparse detection

All seven features map to rows in the count matrix. Feature coverage is not evidence of expression detection. The exact raw-count vectors below follow library order OSK no-dox rep1/rep2, OSK dox rep1/rep2, O4YRSK no-dox rep1/rep2, O4YRSK dox rep1/rep2.

| Gene | Raw counts in the eight libraries | Libraries with counts > 0 |
|---|---|---:|
| CD24 | 47, 49, 819, 782, 845, 1020, 5061, 4970 | 8 |
| CDH1 | 5, 11, 2, 14, 4, 1, 5, 2 | 8 |
| EPCAM | 0, 0, 16, 7, 0, 2, 2, 2 | 5 |
| NANOG | 0, 0, 1, 0, 0, 0, 1, 0 | 2 |
| PRDM14 | 0, 0, 0, 0, 0, 0, 0, 0 | 0 |
| SALL4 | 1, 20, 5, 11, 2, 6, 26, 3 | 8 |
| ZFP42 | 0, 0, 0, 0, 0, 0, 0, 0 | 0 |

The proposed review claim that NANOG, PRDM14, SALL4 and ZFP42 are all zero in all eight libraries is false. NANOG is sparsely detected and SALL4 is detected in every library. PRDM14 and ZFP42 have zero observed counts in this bulk matrix. These observations do not identify an inactive network, absence in every cell, or absence at protein level. Every original panel denominator remains fixed, including zero-valued genes. Full availability and per-library values are in [gene-availability.csv](gene-availability.csv).

## Explicitly post hoc sensitivity

The [new contract](posthoc-contract.json) was written after the original outcomes and the raw seven-gene values were known, before computing the new rank and top-abundance sensitivities. These sensitivities remain exploratory.

Excluding the top 10 or top 100 features from normalization denominators, with one common exclusion set and geometric-depth rescaling, retains positive seven-gene means: OSK 0.577446 / 0.560428; O4YRSK 0.395143 / 0.383490. CD24 still supplies 86.28% / 87.30% for OSK and 80.61% / 80.99% for O4YRSK. These exclusions include highly expressed fibroblast genes in the normalization denominator; they retain the original panel numerators. The result is a composition sensitivity, not identification of a technical artifact or a correction of biology.

The zero-anchored within-library rank summary changes by +0.147664 for OSK and +0.086297 for O4YRSK. These rank units are not comparable to log-expression units. CD24 supplies 16.93% / 12.47% of the rank difference because rank scaling gives sparse detections much more influence. Removing CD24 yields +0.143108 / +0.088124 in rank units. Rank scores are invariant to uniform library scaling, but depend on detection and expression composition; a small count changing from zero to one can have a substantial relative-rank effect. This transform does not turn the marker panel into evidence for a pluripotent state.

All five original panels, all five transforms, per-gene contributions, and omission-by-library contrasts are retained in [marker-audit.json](marker-audit.json). Fibroblast-marker decreases and cell-cycle-marker increases retain their mean direction across these transforms. OSK stress-marker direction remains normalization-sensitive, including a negative rank change. None of these patterns distinguishes technical quality effects from biological change.

## Scope and reproduction

There is one 96-year-old donor and eight libraries, with two libraries per condition. This design does not support donor-level inference, p-values, a young/old contrast, or paired-replicate assumptions. It has no withdrawal/recovery sample and does not validate retinal efficacy, safety, true rare-state prevalence, or the SRSF1 treatment classifier. CX004-R01 through R04 remain `insufficient_signal`.

Run from this packet's root:

```sh
python3 human/marker_audit.py --cache /path/to/GSE297233-cache
python3 -m unittest discover -s human -p 'test_marker_audit.py' -v
python3 human/verify_marker_audit.py --cache /path/to/GSE297233-cache
```

Expected: original arithmetic agreement within 1e-10; pinned inputs and historical files unchanged; all tests pass. Numerical outputs use deterministic Python standard-library operations and sorted serialization. [VERIFICATION.json](VERIFICATION.json) records execution and byte-identical replay.

For a different checkout, both `marker_audit.py` and `verify_marker_audit.py` accept `--prior /path/to/prior-packet --cache /path/to/source-cache`. The default prior resolver accepts the private sibling packet or the exported sibling `2026-10-independent-comparator`. Unit tests use a synthetic sample-metadata fixture and the shipped derived artifacts; they do not need the raw cache. Full replay requires the three hash-pinned public source files named in the contract.
