# Historical GSE304044 tAge replay preparation

This package prepares the checks needed for a historical tAge replay of the
GSTA4 mouse RPE analysis. It validates received artifact bytes and explicit
reference inputs, freezes comparison rules, and compares supplied numerical
outputs by sample identity. It uses Python 3.10 or newer and the standard
library only. It has no model execution adapter.

**Claim level — Verified, software scope only:** the named tests check intake,
provenance binding and comparator behavior on invented fixtures. Historical
reproduction and biological interpretation remain **INCONCLUSIVE**. No tAge or
TACO model has run in this package.

The ocular authors reported an 8.5-month lower transcriptomic age after eight
weeks of GSTA4 overexpression in old mouse RPE. That aggregate is already known;
this is retrospective reproduction preparation. The numerical comparisons below
must be fixed before obtaining new replay outputs. The existing OSK broad
expression correlation is a separate endpoint and supplies no GSTA4 tAge
prediction or tolerance. Public model deposits located after the ocular study
also do not identify its historical implementation.

## Separate admission stages

| Stage | What earns it | Current result |
| --- | --- | --- |
| Artifact intake | Hashes, required declarations, finite complete fixture, explicit unambiguous mappings | Testable now; declarations remain unverified |
| Reference-ready | Historical identity/preprocessing reviewed against primary records; permitted, reviewed adapter and environment ready | `BLOCKED_ADAPTER_UNRESOLVED` |
| Reference-output comparison | Exact sample key agreement and each supplied value within frozen tolerance | `MATCH` or `MISMATCH`; comparator check only |
| Reference-pass | Actual independently recorded execution of the admitted adapter on the frozen fixture matches expected outputs | `BLOCKED_NO_VERIFIED_EXECUTION` |
| Study calculation | Reference-pass plus admitted GSE304044 inputs, joins and a frozen study analysis | `NOT_RUN` |
| Biological interpretation | Appropriate independent-unit design, assay meaning, uncertainty, function, identity and safety evidence | `INCONCLUSIVE` |

These states are hard-coded in `replay.py`. A complete author packet cannot
enable an adapter by declaring its own provenance or adding a PASS flag. A
synthetic `MATCH` cannot advance reference-ready, reference-pass, study
calculation or biological interpretation. Exit zero means the requested
software check completed; it does not mean a historical reproduction passed.

## First run: the current historical dependency is blocked

Run commands from this package directory. The template deliberately preserves
the unresolved historical fields and contains no original parameter guesses:

```sh
python3 replay.py freeze \
  --manifest examples/author-packet-template.json \
  --out /tmp/cx004-historical-freeze.json
```

Expected: exit **2**, JSON `status: "REJECTED"`, an `unresolved declaration`
reason, blocked reference gates, and **no output file**. This is the present
historical baseline. A local existing file at the output path is preserved.

Run the tests:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Expected: all tests pass. The suite tests numeric boundary behavior, identity
joins, missing and extra values, ambiguity, nonfinite numbers, byte tampering,
changed provenance/tolerance, frozen-plan alteration, and gate-bypass attempts.
Every data fixture in the suite is synthetic. Temporary fixtures are removed
by the test runner. Verification is deterministic except for the recorded UTC
freeze timestamp and temporary file paths; those do not affect comparison.

## A runnable synthetic comparator demonstration

The helper writes a **new** directory containing invented genes, samples,
numbers, a text model placeholder, a frozen plan and externally supplied values.
Its numerical values are hand-authored; it performs no inference. Use a new
directory name on repeated runs:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 examples/make_synthetic_demo.py \
  --out /tmp/cx004-SYNTHETIC-demo
```

Copy the printed `freeze_sha256` into the following command. The required
explicit hash demonstrates that the freeze has an independently retained
identity; a real review should retain it in a versioned decision record before
new replay output is received.

```sh
python3 replay.py compare \
  --manifest /tmp/cx004-SYNTHETIC-demo/SYNTHETIC_manifest.json \
  --freeze /tmp/cx004-SYNTHETIC-demo/SYNTHETIC_freeze.json \
  --freeze-sha256 COPY_THE_PRINTED_64_HEX_DIGEST \
  --run /tmp/cx004-SYNTHETIC-demo/SYNTHETIC_run.json \
  --out /tmp/cx004-SYNTHETIC-comparison.json
```

Expected: exit **0**, `numeric_comparison: "MATCH"`,
`reproduction_pass: false`, `biological_pass: false`, and the blocked reference
gates. The observed rows have a different order from the expected rows to
exercise key matching. A valid keyed value outside tolerance produces exit
**1** and a `MISMATCH` receipt. Malformed or changed inputs produce exit **2**
and no new comparison receipt. Existing receipts are never overwritten.

## Minimum received packet

Use `examples/author-packet-template.json` as the intake format. Populate a
separate working copy after material is actually received. Store received
author records privately unless redistribution is authorized. The validator
reads only JSON/CSV and hashes other artifacts as opaque bytes. It never
downloads, imports, unpacks, executes or deserializes an author model or script.

Each artifact has a relative `path`, lowercase SHA-256 and positive byte count.
Paths must remain beneath the manifest directory; symlinks and `..` are rejected.
Distinct artifact roles require distinct paths. JSON duplicate keys, unexpected
fields and unresolved identity/preprocessing declarations are rejected.

| Artifact role | Required content |
| --- | --- |
| `model` | Exact historical model/coefficient bytes; opaque to this checker |
| `preprocessing` | Exact raw-to-feature steps, scales, transformations, feature filtering/order, missing-gene treatment, centering/calibration and unit conversion, with script version where available |
| `environment` | Historical software, dependency versions and platform; seeds/nondeterministic settings if relevant |
| `provenance` | Source record supporting model identity and historical use; distinguish author declarations from independent confirmation |
| `gene_map` | Explicit unique source-to-model gene mapping and contiguous model positions |
| `sample_map` | Explicit unique source-to-reference prediction sample mapping |
| `feature_matrix` | Small already-preprocessed reference input covering every declared sample and gene |
| `expected_predictions` | Author-provided keyed expected numerical outputs and declared units |
| `reference_values` | Named numeric missing-gene, centering or calibration reference values with units; completeness reviewed against the method |

Required identity fields include model ID, historical version, training target,
species, tissue scope, feature namespace, prediction unit and a historical
equivalence declaration. Required provenance fields identify the declarant,
source record, received UTC timestamp and historical basis. These are
**declarations**, not authenticated or independently established facts. The
opaque files must be read and reviewed before reference-ready admission.

CSV schemas are exact, UTF-8, comma-delimited, with one header:

```text
gene_map:             source_gene_id,model_gene_id,model_position
sample_map:           source_sample_id,reference_sample_id
feature_matrix:       source_sample_id,source_gene_id,value
expected_predictions: reference_sample_id,prediction
reference_values:     reference_key,value,unit
```

Gene and sample rows may appear in any order. `model_position` supplies the
actual model feature order; it must enumerate 1 through N exactly once. No
alias stripping, case conversion, Ensembl-version removal or many-to-one
aggregation is inferred. An original pipeline requiring aggregation needs an
authoritative mapping/aggregation specification and a reviewed adapter; this
checker accepts its explicit post-aggregation feature map only.

The supplied matrix must contain each sample/gene pair exactly once. All
values must be finite decimal strings; blanks, NaN, infinity, duplicate pairs,
unknown IDs and absent pairs fail. Numeric exponents beyond ±300 and
representations longer than 80 characters are rejected as unsupported. Nothing
is clipped or filled. This release validates an already-preprocessed input;
it does not certify or recreate raw-count preprocessing. Every reference value
key must match the manifest list exactly. An empty reference-values table is
accepted only with an explicit explanation and an empty declared list; a
reviewer must establish whether that is faithful to the original method.

The current one-to-one reference sample map is deliberately a small numerical
fixture schema. It is not an animal/eye/cohort study manifest and cannot
establish biological replication.

## Frozen comparison and externally supplied outputs

Tolerances are decimal strings chosen and justified for the declared output
units **before new replay outputs**. There are no historical defaults. The
synthetic example tolerance is invented solely to test the comparator. Review
must reject tolerances that could conceal a scientifically meaningful mismatch.
For every expected sample:

```text
abs(observed - expected) <= absolute + relative * abs(expected)
```

Each expected key must appear once in both tables, with no extra keys. The
checker records each expected/observed value, difference and allowance. It does
not round, drop samples, average discrepancies, fit offsets, retune tolerances,
or compare only the already known 8.5-month aggregate.

`freeze` binds the manifest bytes, all nine artifact hashes, declared
provenance, tolerances, validator source and workflow contract. `compare`
rechecks them. Any change requires a new explicitly reviewed revision and a
new retained freeze hash; keep the old plan and result. A changed tolerance
after viewing an output must be disclosed as a sensitivity analysis. A local
timestamp or hash alone cannot prove preregistration or prevent a person from
rewriting both a plan and its external record.

The externally supplied run declaration uses:

```json
{
  "schema": "cx004.tage_external_output.v1",
  "evidence_kind": "author_supplied_historical",
  "freeze_sha256": "RETAINED_FREEZE_DIGEST",
  "manifest_sha256": "FROZEN_MANIFEST_DIGEST",
  "declared_input_sha256": {"ALL_NINE_ARTIFACT_ROLES": "THEIR_FROZEN_DIGESTS"},
  "execution_evidence": "externally_supplied_unverified",
  "prediction_unit": "EXACT_DECLARED_UNIT",
  "observed_predictions": {"path": "observed.csv", "sha256": "OBSERVED_DIGEST", "bytes": 1}
}
```

The illustration above contains placeholders and is not runnable. The
synthetic generator provides a fully populated format example. Observed CSV
uses the same columns as expected predictions. Its bytes are hash-bound to the
run declaration. Declared input hashes must equal all frozen artifact hashes.
Neither that equality nor numeric agreement establishes how the observed file
was produced; copying expected outputs is possible and supplies no execution
evidence. The preparation report therefore always blocks reference-pass.

## Concrete future admission step

After historical material arrives, preserve its received bytes and resolve
the outstanding identity, source permission, preprocessing, missing-gene,
centering, reference-cohort, feature-order, environment and output-unit details
against the authors' records. Confirm that the files correspond to the
GSE304044 ocular analysis, rather than substituting a later tAge/TACO release.
An inability to retrieve the original should be recorded as such; a current
model analysis would be a separately labeled sensitivity analysis.

Then prepare a bounded, separately reviewed adapter change. It must implement
the reviewed historical transformations and inference, with a safe execution
environment for any supplied code or serialized models, permitted use,
versioned dependencies and explicit intermediate-value checks. Bind the
adapter, environment and all inputs to a new frozen plan. Record actual
execution provenance and keyed outputs, and require every reference check to
pass before enabling the study command. That change must be reviewed and
tested; editing this manifest's declarations cannot unlock it. This release
contains no `--execute`, `--force` or scientific PASS override.

Before a new study calculation, freeze the exact GSE304044 sample inventory,
control and GSTA4 groups, animal/eye/cohort joins, independent unit, exclusions,
age units, preprocessing universe, original control-centering values and
contrast/uncertainty method. Retain unresolved or pooled units explicitly.
Match individual original predictions where provided, then reproduce the
authors' original contrast definition. Do not infer animal identity from
expression or treat libraries/eyes as independent animals without support.
Decide how rounding of the reported aggregate will be handled before new
outputs; no aggregate tolerance is supplied here.

A successful historical replay would establish computational agreement within
those limits. Assessing a biological age effect requires the study design and
clock applicability; claims about recovery, function, safety, lasting change
or human retinal translation need their corresponding biological observations.

## Verification record and failed paths

The test command above is the verification hook. Its expected outcome is
unittest `OK`; the runnable synthetic comparison must return `MATCH` with
scientific gates blocked. A failing software test is a **FAIL** for the
preparation release and must be fixed or the software claim downgraded before
sharing it. The parent packet records the dated execution result separately.

The current historical run is **INCONCLUSIVE / blocked** because the exact
adapter, historical model, method/reference values and original keyed output
fixture have not been admitted. The next hook is receipt and review of that
material. Failure to retrieve it is evidence of an unavailable dependency,
not evidence that the authors' biological finding is false. Preserve any
future `MISMATCH` receipt and investigate keyed discrepancies before changing
an input or tolerance.
