# controller-benchmark-schemas

Published by SproutSeeds. Research stewardship: Fractal Research Group ([frg.earth](https://frg.earth)).

Schemas and validators for benchmark condition records, compiler receipts, and
trust-boundary artifacts.

## Install

```bash
npm install controller-benchmark-schemas
```

For local development inside this repo:

```bash
cd packages/controller-benchmark-schemas
npm test
npm pack --dry-run
```

## What This Is

`controller-benchmark-schemas` is a small infrastructure package for projects
that want stable, machine-readable contracts around benchmark artifacts.

It currently ships schemas and validation helpers for:

- benchmark condition records
- condition-record compile receipts
- benchmark shell receipts
- compiler coverage and trust receipts

These contracts were developed inside the partial reprogramming controller
program, but the package itself is not retinal-, ocular-, or cell-type-specific.

The reusable layer is:

- one benchmarked condition
- one compile step
- one evaluation run
- one explicit trust boundary

That pattern can travel beyond a single biological domain, including beyond the
current ocular benchmark lane that helped discover it.

## What This Is Not

`controller-benchmark-schemas` is not:

- a tissue-specific ontology
- a matrix parser
- a model training package
- a wet-lab protocol library
- a claim that the underlying biology is solved

It is a contract layer for benchmark artifacts.

## Included Schemas

- `condition-record`
- `condition-record-compile-receipt`
- `benchmark-shell-receipt`
- `compiler-coverage-trust-receipt`

## Quick Start

```js
import {
  CONDITION_RECORD_SCHEMA,
  getSchema,
  validateConditionRecord,
} from "controller-benchmark-schemas";

const record = {
  condition_id: "VITA_CTRL_003",
  study_family_id: "gill_2022",
  accession_bundle: "GSE165180",
  phase_layer: "maturation_phase_bulk_plus_abstention",
  primary_evidence_class: "observed_temporal",
  supporting_evidence_classes: ["bulk_proxy_support"],
  age_signal_score: 0.83,
  age_signal_status: "strong_positive",
  identity_pressure_level: "low",
  identity_status: "bounded_support",
  risk_pressure_level: "low",
  risk_status: "bounded_support",
  active_negative_family_ids: [],
  negative_family_roles: [],
  negative_family_tiers: [],
  condition_summary:
    "Gill successful maturation branch with real later-phase timing and relatively favorable proxy identity profile.",
  source_trace: {
    source_kind: "study_specific_rule",
    derived_from: [
      "/abs/compiler-rules/gill_2022-v0.json",
      "/abs/controller-benchmark-study-corpus-v0.csv",
    ],
    notes: ["Compiled from a study-specific rule pack."],
  },
  provenance: {
    reviewer: "Codex",
    reviewed_on: "2026-04-02",
    status: "draft",
    benchmark_links: [],
  },
};

console.log(validateConditionRecord(record));
console.log(CONDITION_RECORD_SCHEMA.$id);
console.log(getSchema("benchmarkShellReceipt").title);
```

Expected result:

```js
{ valid: true, errors: [] }
```

## Package Positioning

The strongest use case is not:

"Turn a research program into npm branding."

The strongest use case is:

"Make benchmark artifacts explicit enough that multiple tools can validate,
inspect, and reuse them without relying on prose memory."

## API Surface

### Schema exports

- `CONDITION_RECORD_SCHEMA`
- `CONDITION_RECORD_COMPILE_RECEIPT_SCHEMA`
- `BENCHMARK_SHELL_RECEIPT_SCHEMA`
- `COMPILER_COVERAGE_TRUST_RECEIPT_SCHEMA`
- `getSchema(name)`
- `listSchemas()`

### Validation exports

- `validateConditionRecord(value)`
- `validateConditionRecordCompileReceipt(value)`
- `validateBenchmarkShellReceipt(value)`
- `validateCompilerCoverageTrustReceipt(value)`

## Current Boundary

This package intentionally validates structure and constrained vocabulary.

It does not perform generic JSON Schema evaluation, and it does not infer
biological correctness. That is the right first step for a package whose job is
to stabilize artifact contracts.
