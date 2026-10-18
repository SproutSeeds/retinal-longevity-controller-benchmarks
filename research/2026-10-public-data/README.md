Title: Retinal longevity and the missing recovery measurement

**October 18 update:** the [metadata recovery pass](../2026-10-metadata-recovery/README.md) extracts all 295 SRSF1 coefficient terms, resolves 72 human recovery library identities, and clarifies the distinct OSK/GSTA4 findings. Exact clock preprocessing and late human recovery remain open.

Public data let us examine reprogramming responses, correct analysis assumptions, and narrow the experiment. They still do not supply the matched late human single-cell recovery measurements needed to resolve the four CX004 questions. This is the **October 17, 2026** evidence checkpoint. Biological interpretations are **Heuristic**; replacement of the complete experiment is **INCONCLUSIVE**.

Our contribution is the reproducible analysis and evidence decision. The source experiments belong to their original researchers. Fibroblast, liver, neural and retinal observations retain their separate biological scope.

## Results that change the next step

| Analysis | Computed result | What it supports |
|---|---|---|
| Human Perturb-seq, 36,514 deposited cells | Correcting for the documented two-guide design increases eligible comparisons from 97 under our earlier single-guide rule to **208** under the primary paired rule | Better use of existing measurements. The exact author assignments remain unavailable. |
| Three-donor SRSF1 diagnostic | Mean donor-holdout AUROC **1.00** with fixed expression panels; **0.83** using depth/detected genes alone | Treatment recognition in 12 libraries. Three donors and unknown experimental batches cannot establish rejuvenation or independent study validation. |
| Mouse RPE sensitivity analysis | Broad expression correlation **+0.663 to +0.694** across six fixed variants; **+0.509 to +0.731** across library omissions | A stable descriptive result for this endpoint. The authors' transcriptomic clock is a different endpoint and has not been reproduced here. |
| Mouse liver withdrawal comparator | **16,042** deposited nonempty barcodes; source-method QC sensitivity retains **2,288**, versus **2,284** reported by the paper | Directly observed factor-off data exist. This early mouse liver snapshot cannot replace late human or retinal recovery measurements. Exact four-cell discrepancy remains open. |
| Synthetic donor clustering | At fixed 1,200 cells, hypothetical 1% prevalence, 80% sensitivity and 0.05 latent donor correlation: detection rises **53% → 81% → 92%** across 1, 3 and 6 donors | Sampling design depends on donors, detector quality and assumptions. These are synthetic probabilities, not observed biological risk. |

The numerical outputs, source hashes, fixed analysis contract and model coefficients are included here. `python3 verify.py` checks computational consistency; `uv run test_analysis.py` checks scientific failure cases. Neither test suite establishes biological efficacy or safety.

## What changed after checking the methods

The [PNAS study](https://doi.org/10.1073/pnas.2515183123) uses two targeting guides per vector. We recovered its supplementary methods and replaced our earlier single-guide interpretation. The primary rule sums the two channels, requires both to be detected, and compares each eligible target with machinery-matched controls. Two incomplete target groups are excluded. The earlier EZH2 correlation moves from an apparently negative signal toward zero under the paired rule; E2F3's target-expression direction fails the expected activation check. Both findings remain visible in [paired-guide-results.json](paired-guide-results.json). This correction increases usable comparisons without certifying the authors' original assignments or increasing donor replication.

The [ocular full text](https://doi.org/10.1101/2025.08.30.673239) specifies RLE/log/YuGene preprocessing and a Bayesian Ridge clock. Our gene-wise correlation uses a different quantity. It therefore cannot establish failure of that clock. Current [tAge resources](https://www.nature.com/articles/s41586-026-10542-3) are available, but the historical model, imputation references, exact cohort mapping and license conditions require resolution before an exact replay. Endogenous gene counts also do not establish whether a vector-derived transcript was expressed.

The [SRSF1 paper](https://www.nature.com/articles/s43587-026-01234-8) provides useful human recovery data. Its public clock scripts lack the fitted model/calibration objects needed for exact replication. The three-donor treatment classifier is deliberately a different diagnostic. Full coefficients, held-out predictions and all 216 balanced label controls are in [donor-model-results.json](donor-model-results.json). See the [model card](MODEL_CARD.md).

## Public-data decision

| Readout | Observation still required | Current verdict |
|---|---|---|
| R01: late identity | Adult identity in the relevant age-positive late human cells, including D28 | insufficient_signal |
| R02: rare states | Calibrated per-cell annotations and adequate effective sampling under that protocol | insufficient_signal |
| R03: withdrawal stability | Matched late human factor-off cells and a sufficiently long recovery follow-up | insufficient_signal |
| R04: continuity | A common measured trajectory connecting the relevant intermediate and late windows | insufficient_signal |

The [source audit](SOURCE_AUDIT.md) covers ten priority resources and records their exact next missing inputs. This is a dated, targeted search, not proof that no suitable dataset exists anywhere. GSE350289 remains blocked on exact barcode-to-perturbation assignments; downloading its large matrix would not repair that omission. Existing human bulk recovery and late-state nuclei are useful comparators, but joining different experiments does not create a matched observation.

The [measurement proposal](MEASUREMENT_PLAN.md) explains the conditional next experiment, sample quantities, decision criteria and quote requirements. It is a funding discussion package. No wet-lab work has been purchased, booked or initiated. The [next steps](NEXT_STEPS.md) prioritize metadata reuse and banked material before new measurements.

## Reproduce

Python 3.12 and `uv` are used for numerical analyses; dependencies are pinned in each runnable script. Offline verification uses the Python standard library only.

```sh
python3 verify.py
uv run test_analysis.py
python3 fetch_inputs.py --group small --cache .cache
uv run analyze.py human --cache .cache
uv run analyze.py ocular --cache .cache
uv run analyze.py liver --cache .cache
uv run analyze.py synthetic
python3 fetch_inputs.py --group perturbation --allow-large --cache .cache
uv run analyze.py perturbation --cache .cache
python3 verify.py --write
```

The large Perturb-seq file is 1.427 GB; the small group is approximately 45 MB. Downloads verify recorded bytes and SHA-256, enforce a free-space floor, and never execute author code. `all` runs the four original diagnostic tasks; run `liver` separately. Counts are actual deposited measurements; synthetic scenarios are saved separately. Results overwrite their corresponding local derived files. Floating-point details can vary across platforms; the contract, source hashes, discrete assignments and checks are the reproducibility anchors.

See [METHODS.md](METHODS.md), [FAILED_PATHS.md](FAILED_PATHS.md), [THIRD_PARTY.md](THIRD_PARTY.md) and [VERIFICATION.json](VERIFICATION.json). The [public repository](https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks) also hosts the presentation and existing controller packages. The older Zenodo DOI archives an earlier package release; this October research revision is identified by its Git commit until separately archived.
