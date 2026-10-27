# RPE RNA, function and uncertainty

<!--
Title: RPE RNA, function and uncertainty
-->

Scientific checkpoint: October 26, 2026. Maintained by [Fractal Research Group](https://frg.earth).

RPE expression changes can be measured without establishing that a cell has recovered its function. This release makes that distinction executable: source-bound RNA and functional observations retain their experimental units, uncertainty and missing links as they pass through the controller.

**Verified software result:** nine version-2 packets replay exactly over 23 distinct source observations. Those observations resolve to ten uncertain directions, two heterogeneous-unit results, eight source-bounded directions and three descriptive functional observations. The verifier independently reconstructs 937 numerical values from the included source-result tables and exercises 56 rejection cases through the actual CLI. These checks were written and executed by the same research agent; they are software verification, rather than independent biological replication or a held-out performance estimate.

**Heuristic biological interpretation:** the current evidence challenges the use of RNA panels as a substitute for functional recovery. The four human late-withdrawal readouts remain `insufficient_signal`; experiment replacement remains **INCONCLUSIVE**. Restoration remains unestablished.

## What the data permit

| Source | Analytical unit and result | Remaining constraint |
|---|---|---|
| GSE132828, hESC-derived RPE | 21 deposited libraries; the primary ramoplanin/POS contrast has three libraries per condition. All ten primary panel/normalization intervals span zero. | Cross-condition differentiation-round pairing and RNA/function links are unverified. GEO and the RNA supplement disagree on exposure concentrations. This is an unpaired, condition-level comparison. |
| GSE126633, adult-primary RPE | Three named donor-line pairs. Primary identity and stress panel directions agree across the three pairs; cell-cycle direction differs between donors. | Two patient membranes remain outside the primary model. No deposited inhibitor-rescue RNA arm or admitted RNA/function unit join. |
| GSE159435 and GSE297557 | Thirteen adult donors supply age associations; four paired experiments in one iPSC-derived line supply an impairment comparison. | Age association and an induced impairment contrast answer different questions. Shared condition names do not identify the same RNA and functional units. |
| GSE90889, NAM challenge | Seven paired hiPSC-RPE lines, using the authors' normalized expression scale. | These data do not supply withdrawal samples or a sample-level RNA/function join. |
| Published impairment/rescue assays | Six impairment pairs in each of two assay scales, and four separate rescue pairs. The evaluator retains three assay-specific descriptive observations. | Local experiment numbers are assay-qualified. The assays cannot be pooled into one donor cohort or used to infer a percentage of complete recovery. |
| GSE224438, mouse withdrawal | Animal-level panel comparisons retain the two cohorts separately. Microglial cell-cycle directions differ between cohorts; none of 24 predeclared type/panel/contrast summaries meets the descriptive stability rule in both. | Exact ages, sex and intended controls for the four shared withdrawal animals need clarification. Persistence and complete molecular reversion remain unresolved. |

Original experiments, data generation and discoveries belong to the source investigators. Our contribution is the analysis, explicit evidence bindings and controller logic. [Sources and reuse terms](THIRD_PARTY.md) distinguish project code from third-party data.

## Reproduce the released result

Use Python 3.12 and run these commands from the repository root:

```sh
python3 -m pip install jsonschema==4.25.1
python3 research/2026-10-rpe-controller/verify_public.py
```

This quick replay downloads no biological matrices and needs no model weights, email access or credentials. It checks released hashes, replays the nine v2 packets, performs the source-table numerical checks and CLI rejection cases, and replays seven earlier controller packets against their exact recorded outputs. Temporary rejection fixtures stay in an ignored directory.

Run one packet directly:

```sh
python3 programs/partial-reprogramming-controller/scripts/controller_rpe_uncertainty_evaluator_v2.py \
  --packet programs/partial-reprogramming-controller/benchmarks/rpe-uncertainty-controller-v2-2026-10-26/packets/GSE126633_CPM.json \
  --catalog programs/partial-reprogramming-controller/benchmarks/rpe-uncertainty-controller-v2-2026-10-26/ADMISSION_CATALOG.json
```

The included tables are derived analysis results and selected published functional values. Replaying them verifies numerical consumption and evidence handling; it does not repeat the complete raw-matrix analysis. The public `FREEZE.json` is an explicitly labeled excerpt of the historical source freeze. The public protection ledger covers the exported subset, so its administrative check count differs from the source repository's larger preservation audit. The schemas, executable evaluators, source-result tables, packets and expected CLI outputs are byte-for-byte source artifacts.

## Clock reproduction and next evidence

A diagnostic using the current released tAge model has run. It remains separate from an exact replay of the historical tAge6 result, which still needs authoritative historical model/reference artifacts and preprocessing. Historical preparation documents in this repository describe their earlier checkpoint. No TACO execution is claimed.

The next biological decision needs a documented, same-unit adult-primary RNA/function comparison with an appropriate rescue or withdrawal endpoint. We will first seek existing source tables, authoritative sample crosswalks and design clarification. New measurements require a separate experimental plan and human approval.

Contributors can open an issue identifying a public dataset, its experimental units, the relevant endpoint and its reuse terms. Please keep participant information, private correspondence and unpublished attachments out of public issues.

## How updates reach this repository

The source project's commit hook pushes its configured clean research branch, then checks a fixed export allowlist. When approved scientific files change, it verifies and publishes the curated public package. Unchanged scientific content produces no duplicate public commit. Hosted [research checks](https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks/actions/workflows/research-checks.yml) run on every public push and pull request.

This is a project-scoped checkpoint sync. It requires an installed local hook, the configured branch, network access, matching repository visibility, clean checkouts and passing checks. Failures leave a receipt and preserve the commit. A commit elsewhere, or an uncommitted edit, does not by itself publish here. The reusable [sync implementation](../../tools/research-sync/sync.py) and [safety checks](../../tools/research-sync/test_sync.py) are available for review; each additional repository needs its own reviewed configuration and export policy.

The [package manifest](public-package.json) records the scientific source commit, content fingerprint and file hashes. The Git commit identifies this public release. A green hosted check verifies the tested software revision; it does not establish rejuvenation efficacy, clinical safety or permission to recommend a protocol.
