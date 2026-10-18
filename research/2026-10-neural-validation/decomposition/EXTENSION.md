# Post hoc convention and depth sensitivity

**Verified computation; post hoc interpretation.** The [extension contract](posthoc-contract.json) was committed at `60a4fc5f1dc86f73e18d137f6bf50a2e8a92a63a` after the original decomposition outcomes were known. [EXTENSION_FREEZE.json](EXTENSION_FREEZE.json) authorized these additional calculations. The original contracts, code and results remain unchanged.

[extension-results.json](extension-results.json) contains all 16 original panel/support/scale rows, three decomposition conventions, 172 gene-contribution records with both lanes and equal-lane means, and the separate depth diagnostic. Zero gene contributions retain their fixed panel weight. Every original support-failure table is copied into the extension result.

For conditional recovered-cell fractions `p` and type means `mu`, the control-reference composition term is `sum((pT-pC)*muC)` and its within-type term is `sum(pT*(muT-muC))`. The treated-reference composition term is `sum((pT-pC)*muT)` and its within-type term is `sum(pC*(muT-muC))`. Each pair sums to the same observed cell-average difference. Their arithmetic average equals the original symmetric partition. Each gene is decomposed on the same cells, fractions and scale, then weighted by the reciprocal of the unchanged panel size.

All four original stress rows retain negative composition and positive within-type equal-lane components under both reference conventions. That sign pattern is less general for other panels: the lower-support cycle row at CP10k has composition −0.000533 under the control reference and +0.000353 under the treated reference, with the same total −0.005044. The result records every convention without choosing a preferred one or assigning percentages of an opposing total.

Gene contributions expose heterogeneity inside a panel. For the original 20-cell/CP10k stress row, the symmetric within-type contributions are Cdkn1a +0.001576, Cdkn2a +0.001898, Il6 +0.001828, Gadd45a +0.000802, Trp53 −0.009658, Timp1 0 and Timp2 +0.016052. These sum to +0.012498. The opposing gene contributions support reading this as a fixed expression summary rather than a single biological state.

The depth diagnostic retains the original Oligodendrocyte and Microglia support, 20 cells and 500 detected genes per animal/type, assessed before thinning. **All 907 support cells already have at least 1,000 RNA UMIs**, so the depth threshold excludes no additional cells and the unthinned-subset effects equal the original 20-cell/CP10k effects. The support still represents a conditional subset of each animal's recovered cells:

| Animal | Lane / arm | Oligodendrocytes | Microglia | Retained / all recovered | Retained fraction |
|---|---|---:|---:|---:|---:|
| L0002 | 1 / treated | 44 | 58 | 102 / 171 | 59.65% |
| L0003 | 1 / control | 98 | 171 | 269 / 395 | 68.10% |
| L0004 | 2 / treated | 152 | 178 | 330 / 561 | 58.82% |
| L0011 | 2 / control | 80 | 126 | 206 / 327 | 63.00% |

Sampling uses exactly 1,000 UMIs without replacement per cell. The categories are the sorted union of all fixed panel genes plus one remainder containing every other raw RNA gene. Cells are sorted by their unique deposited ID. NumPy 2.5.4 PCG64 with independent seeds 181026, 181027 and 181028 uses the [`multivariate_hypergeometric` marginal method](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.multivariate_hypergeometric.html). The saved original category counts and all three draw matrices permit checks of every bound, 1,000-count total and seeded replay without reopening the raw RDS. Shared gene draws remain identical across overlapping panels.

The table reports equal-lane **total** differences in mean log2(1+CP10k) panel expression; each total is shared by all three conventions. The complete result also retains every component and individual lane.

| Fixed panel | Original / unthinned subset | Seed 181026 | Seed 181027 | Seed 181028 |
|---|---:|---:|---:|---:|
| Cycle | −0.008461 | −0.004481 | −0.004037 | −0.000185 |
| Reprogramming markers, full | −0.000581 | −0.001931 | +0.000831 | −0.001173 |
| Reprogramming markers, Pou5f1/Sox2 excluded | −0.001901 | −0.000901 | 0 | −0.003037 |
| Stress | −0.004811 | −0.011113 | −0.002529 | −0.001193 |

The stress total remains negative across the three seeds, with lane-level discordance in two seeds. Its symmetric within-type term remains positive (+0.001369, +0.009180, +0.009279); the seed-181026 treated-reference within-type term is −0.000623 while the control-reference term is +0.003362. The full reprogramming-panel total changes sign across seeds, and its overlap-excluded version is exactly zero in seed 181027. These are sensitivity observations, with no hypothesis test or estimate of biological certainty.

The three-seed experiment measures how these summaries change after imposed count thinning. It does not identify the origin of an observed difference or remove capture bias. Named types can contain subtype/state mixtures, and selection into common support can itself differ by treatment. Treated animals received OSKM induction plus doxycycline; absent dox-only controls prevent separating drug and construct effects. All four CX004 readouts remain `insufficient_signal`.

Verification hook, from this directory in the original repository:

```sh
uv run --script verify_extension.py
uv run --script verify_extension.py --reproduce --cache /tmp/cx004-independent-comparator-2026-10-18
```

The first command opens saved outputs and runs synthetic tests; it does not open or download raw RDS data. [EXTENSION_VERIFICATION.json](EXTENSION_VERIFICATION.json) records **PASS: 24,732 saved-output checks and 25 synthetic tests**. Tests cover reference sign reversal, gene additivity including zeros, absent support, an individual sparse or low-gene stratum invalidating the fixed diagnostic, sorted sampling, zero categories, the RNA remainder, exact seed replay, authorization/hash failures and internal scratch limits.

The second command separately reruns the observed calculation from the pinned cached raw RNA in strict original-commit mode and explicit archived-hash mode. [EXTENSION_REPRODUCTION.json](EXTENSION_REPRODUCTION.json) records byte identity for both runs: SHA-256 `912f86da5b183a7eb2e1884a5bd33ff843a307312a1755a332e0649a249e262e`, 3,907,820 bytes. The source RDS hash is `2471fbd531edd80f0f3aa480c1782dcedce811cfadc132eff09d8d029c6711a6`.

For a public export that has the archived files but lacks the original repository history, verification is explicit:

```sh
uv run --script verify_extension.py --replay-frozen-hashes --output /tmp/extension-verification.json
uv run --script extension.py --cache /tmp/cx004-independent-comparator-2026-10-18 --replay-frozen-hashes --output /tmp/extension-replay.json
```

This mode verifies all archived input bindings and labels historical git proof as not rerun. Default execution requires the original committed inputs. Full observed replay also requires the pinned raw source; saved-output CI does not. Large scratch remains on internal `/tmp`, with an 8-GiB free-space guard.
