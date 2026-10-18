# Methods and interpretation limits

The prospective analysis contract was committed as `3023637` before downloading the human count matrix. It is a frozen reanalysis specification, not a registered biological experiment. After the matrix header and one row were printed, the metadata/count-name mismatch required a separate amendment, committed as `9b43737` before panel outcomes were calculated. The original contract remains unchanged. `analysis-contract.json` and `join-amendment.json` disclose this sequence.

## Human expression

Join all eight GEO sample records to count columns through the admitted `construct_0D_rep` to `construct_D0_rep` permutation, and its day-4 counterpart. Require exact title, construct, dox-status, species and donor agreement. No matrix-order join or assumed cross-condition replicate pairing is permitted. GEO describes both groups at four days. The counts use unique Ensembl gene IDs; version suffix removal changes zero IDs. There are no fractional entries. Source columns and genes must be unique, finite, nonnegative and nonempty by library.

Map the 46 predefined symbols to unique approved Ensembl genes using the frozen HGNC complete set. Every panel gene is present. No expression-based gene selection or imputation occurs. The RPE panel stored in the reused panel file is outside this human-fibroblast analysis.

For library j with counts c, primary expression is log2(1 + 1,000,000 c / sum(c)). Each panel is the unweighted mean of its genes' transformed expression. The contrast is the mean of two treated library scores minus the mean of two controls. These are differences of average log-expression scores; exponentiating a panel difference does not yield a measured age or identity ratio.

The sensitivity estimator uses each strictly positive gene's geometric mean across all eight libraries, takes the median count/geometric-mean ratio per library, and rescales those size factors to geometric mean one. Multiply each factor by the geometric-mean library count sum to obtain an effective depth, then use the same log2(1 + CPM-equivalent) transformation. Both estimators have composition assumptions; agreement increases descriptive robustness, while disagreement is retained. There are no spike-ins or total-RNA-per-cell measurements to infer absolute transcript levels.

Every panel reports its genes, per-library score, all four treated/control library differences and all single-gene omissions under both normalizations. Neither the four differences nor the eight libraries become independent donors. Error bars show the four-library range, never a confidence interval. The full reprogramming panel overlaps the introduced OSK factors through POU5F1 and SOX2; the seven-gene sensitivity removes both. A remaining positive score still does not establish pluripotency or benefit.

## Neural admission

The pure-Python `rdata` parser reads the serialized Seurat object without running deposited R scripts. The scout extracts `meta.data` and raw `RNA@counts`, not integrated/scaled SCT expression. Sparse count dimensions, identifiers, nonnegative integer values, canonical sparse coordinates and every cell's count sum must agree with the metadata. Singlet cell IDs must match count-column order exactly. The `hash.ID` mappings are extracted as text from pinned author code, then checked against age, genotype, treatment and lane for every animal. Cohort/lane titles are joined to exact GEO accessions.

Animal and cell-type totals are admission metadata. They describe recovered sequenced cells and may reflect dissociation, sorting, capture and QC. They do not estimate unbiased tissue composition. Numeric clusters remain numeric. Deposited factor levels with zero cells are never counted as observed groups. No neural expression contrast, age clock or p-value is part of this pass.

## Synthetic probabilities

For an allocation of n cells from each donor, let the donor-specific true-state prevalence P follow a beta distribution with mean p and correlation rho: alpha = p(1/rho - 1), beta = (1-p)(1/rho - 1). Conditional on P, a cell is flagged with probability sensitivity × P + false-positive-rate × (1-P). The probability of no flag is the expectation of (1-q)^n. Rho zero uses the binomial closed form. Equal sensitivity and false-positive rate also have a direct constant-q closed form.

Donors are independent in this model. Multiply donor no-flag probabilities to obtain zero flagged donors; sum the mutually exclusive single-donor cases to obtain exactly one. Their complements give at-least-one and at-least-two probabilities. Null scenarios separately place independent errors or beta-correlated false-positive rates within donors. Between-donor shared batch errors are outside this model and could invalidate an independence-based confirmation rule.

The numerical integral uses 256-point Gauss-Jacobi quadrature and must agree with 512 points within 1e-6. The observed maximum absolute discrepancy is below 2.9e-8. A separate 100,000-trial seeded Monte Carlo example must agree within five binomial standard errors plus one trial. These are numerical verification tolerances, not biological uncertainty intervals.

All sensitivity, specificity, prevalence and correlation settings are hypothetical. No generated cell profile is mixed into observed data, and no synthetic label supplies age, identity, recovery or safety ground truth.
