Title: Retinal recovery: the clock parameters are available

**October 18 wording clarification:** historical retinal tAge replication remains pending because the required inputs are unconfirmed. No tAge or TACO model has been executed here, and there is no competing GSTA4 clock estimate. The recovered coefficient table below belongs to the separate human SRSF1 study. [Current status and reproduction preparation](../2026-10-tage-replay-preparation/README.md).

**October 18, 2026 UTC.** The SRSF1 supplement provides all **295 numeric model terms: 292 genes, an intercept and two library-type adjustments**. All 292 genes occur once in the deposited 807-library human count matrix after Ensembl version suffixes are removed. This resolves the parameter-discovery task. Exact clock replay still depends on preprocessing and reference outputs.

Parameter extraction, file hashes and sample joins are **Verified** within the checks below. Biological interpretation remains **Heuristic**; replacement of the proposed late human recovery experiment remains **INCONCLUSIVE**. All four CX004 readouts remain `insufficient_signal`.

## What the recovery pass changed

### A complete coefficient table, with a narrower replication gap

[Supplementary Table 1](https://www.nature.com/articles/s43587-026-01234-8#MOESM4) contains raw and standardized coefficients, including the intercept and library terms. Our earlier discussion of missing clock weights was too broad. The coefficients were already public; this pass extracts and checks them as [machine-readable parameters](srsf1-clock-parameters.json). The original model belongs to Plesa and colleagues.

The public scripts still reference unavailable inputs: the exact gene-length vector (`gl`), normalization/filtering gene universe and training/calibration objects. In the pinned application script, a later assignment replaces the frozen-SVA corrected matrix with the uncorrected application matrix. That may reflect intended analysis or an exploratory script; it requires clarification before an exact replay. It does not establish an error in the published results. We need a small reference feature matrix and expected predictions to check numerical equivalence.

The [repository history audit](clock-dependency-audit.json) covers all 27 commits reachable from its one public branch and 21 distinct historical paths. It found no fitted-model artifact among those paths; there are no tags or releases in the checked snapshot. This bounded history check does not exclude an artifact stored elsewhere.

### Withdrawal metadata are now explicitly joined to count columns

The [sample manifest](srsf1-recovery-samples.json) resolves **72 human factor-off libraries** to exact columns in the deposited count matrix: 30 SRSF1, 30 BFP-control and 12 OSKM libraries. The prior 60-library analysis concerned the SRSF1/control subset. The 32 mouse factor-off libraries are recorded separately and excluded from this human manifest. These are three human donor lines across the recovery experiments, not 72 independent donors.

The brief-exposure figure caption describes 6/12 days after withdrawal, while GEO labels the corresponding schedules with 8/16-day OFF periods. We retain both descriptions and request actual induction, withdrawal and harvest dates. We do not silently relabel samples. The source batch fields are retained; they do not establish independent experimental batches.

### The ocular paper distinguishes OSK from GSTA4

The [2025 ocular preprint](https://doi.org/10.1101/2025.08.30.673239) reports increased overall transcriptomic age under OSK alongside improvements in some functional measurements and concerns with prolonged exposure. It separately reports an 8.5-month reduction in transcriptomic age after eight weeks of GSTA4 overexpression in old mouse RPE. These are the authors' findings. Historical tAge replication remains pending because the required inputs are unconfirmed; no tAge or TACO model has been executed here. The dated source records retain their original wording and hashes.

Our broad expression correlation remains a different endpoint from their fitted clock. The [clarification and source anchors](ocular-source-clarification.json) keep intervention, endpoint and timing separate. Existing 18-library OSK and seven-library GSTA4 deposits still lack the complete animal/eye/cohort mapping needed for a faithful comparison.

We located and inventoried two [public model archives](ocular-clock-artifacts.json), including [the archive cited by the 2026 clock paper](https://doi.org/10.5281/zenodo.18763485). Those deposits postdate the ocular preprint; their availability does not identify the exact historical model. No model pickle was downloaded or executed. The repository specifies restricted academic use; its models are not included in this open-source package.

### GSE350289 still needs its cell assignment table

The fresh [GEO deposit](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE350289) and workbook were checked. Ctrl and Sample 1 contain age values without usable cell/perturbation keys; Sample 2 and Sample 3 have no populated rows. [The workbook audit](geo350289-mapping-audit.json) records the exact counts and SHA-256.

We need a library + cell-barcode key joined to hash identity, perturbation, donor/pool provenance and assignment QC. Expression cannot safely reconstruct that experimental identity. The 4.6 GB expression matrices remain undownloaded. A recovered map would unlock perturbation analysis; it would not create a withdrawal experiment that was never collected.

## Next decision

The [reuse decision](reuse-decision.json) keeps all four late human readouts open. The next useful inputs are the GSE350289 assignments, the SRSF1 preprocessing/reference outputs and chronology, and the ocular historical model/cohort manifest. Specific author requests are prepared separately and remain unsent. Reanalysis resumes when one of those dependencies changes. Larger model training and new synthetic biology labels do not resolve these dependencies.

No wet-lab work has been purchased or arranged. The existing [conditional measurement plan](../2026-10-public-data/MEASUREMENT_PLAN.md) remains a proposal for discussion if compatible public data or banked material cannot supply the required observations.

## Verification and reproduction

Run the offline checks with Python 3.12; no third-party Python packages are required:

```sh
python3 verify.py
python3 test_recovery.py
```

`VERIFICATION.json` records the checks. They establish extraction, bookkeeping and intake behavior, not biological efficacy or safety. The input join rejects missing keys, partial coverage and conflicting assignments. A pooled donor ID never establishes donor-level independence.

To repeat acquisition, run `fetch_metadata.py retrieval-plan-1.json --cache .cache --receipt fresh-retrieval-1.json` and similarly for plans 2 and 3. Failed size-capped all-record GEO requests in plan 1 are preserved; plan 2 uses sample-only requests to retrieve the needed metadata. Keep fresh receipts separate from the frozen audit. Fetch the hash-bound human counts using the [existing fetcher](../2026-10-public-data/fetch_inputs.py). Then run:

```sh
python3 recover_metadata.py --cache .cache --counts ../2026-10-public-data/.cache/GSE325735_human_raw_counts.txt.gz
```

The extractor checks the frozen source hashes before use. If the provider changes a file, review the new version instead of overwriting this checkpoint. The optional `--clock-git` argument checks a read-only bare clone of the source history against all pinned commit IDs; otherwise the saved history inventory is retained. Author scripts and serialized models are never executed. See [third-party attribution](THIRD_PARTY.md), [failed paths](FAILED_PATHS.md), and the [public repository](https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks).
