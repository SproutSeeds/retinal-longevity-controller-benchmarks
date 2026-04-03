# controller-benchmark-js

Published by SproutSeeds. Research stewardship: Fractal Research Group ([frg.earth](https://frg.earth)).

Thin JavaScript tooling for summarizing and interpreting controller benchmark
bundles.

## Install

```bash
npm install controller-benchmark-js
```

For local development inside this repo:

```bash
cd packages/controller-benchmark-js
npm test
npm pack --dry-run
```

Repo-local end-to-end stack demo:

```bash
node packages/controller-benchmark-js/examples/local-stack-demo.js
```

## What This Is

`controller-benchmark-js` is the thin read-only tooling layer that sits on
top of benchmark artifacts.

It is designed to:

- summarize benchmark bundles in JavaScript
- compare baseline and controller outputs
- surface fail-closed behavior clearly
- group and index condition records for downstream tools
- stay small enough to reuse in dashboards, review tools, and packet UIs

This package composes naturally with:

- `controller-benchmark-schemas`
  - structure and contract validation
- `controller-benchmark-data`
  - versioned benchmark bundle and readers

## What This Is Not

`controller-benchmark-js` is not:

- the Python compiler
- the benchmark runner
- a model-training package
- a controller-serving runtime
- a replacement for biological judgment

It is a thin interpretation and summarization layer.

## Quick Start

```js
import {
  buildBenchmarkSnapshot,
  compareOutputs,
  summarizeCoverageTrust,
  summarizeShellReceipt,
} from "controller-benchmark-js";

import {
  loadLatestBundle,
  readAgeOnlyBaselineOutputRows,
  readControllerOutputRows,
} from "controller-benchmark-data";

const bundle = loadLatestBundle();
const ageOnlyRows = readAgeOnlyBaselineOutputRows();
const controllerRows = readControllerOutputRows();

console.log(summarizeCoverageTrust(bundle.coverageTrustReceipt));
console.log(summarizeShellReceipt(bundle.benchmarkShellReceipt));
console.log(compareOutputs(ageOnlyRows, controllerRows));
console.log(
  buildBenchmarkSnapshot({
    conditionRecords: bundle.conditionRecords,
    coverageTrustReceipt: bundle.coverageTrustReceipt,
    benchmarkShellReceipt: bundle.benchmarkShellReceipt,
    ageOnlyRows,
    controllerRows,
  }),
);
```

## API Surface

- `BASELINE_OUTPUTS`
- `CONTROLLER_OUTPUTS`
- `countBy(items, selector)`
- `indexConditionRecords(records)`
- `groupConditionRecordsByPhase(records)`
- `groupConditionRecordsByStudyFamily(records)`
- `listNegativePressureConditions(records)`
- `compareOutputs(ageOnlyRows, controllerRows)`
- `summarizeCoverageTrust(coverageTrustReceipt)`
- `summarizeShellReceipt(benchmarkShellReceipt)`
- `buildBenchmarkSnapshot(input)`

## Repo-Local Stack Demo

The repo-local demo script composes all three benchmark packages together:

- `controller-benchmark-schemas`
  - validate the live contract surfaces
- `controller-benchmark-data`
  - load the current benchmark bundle
- `controller-benchmark-js`
  - summarize coverage, shell behavior, output transitions, and the merged
    snapshot

Run:

```bash
node packages/controller-benchmark-js/examples/local-stack-demo.js
```

This prints one JSON report showing:

- whether the live condition records and receipts validate
- how the trust boundary is distributed
- how age-only and controller outputs differ
- one merged benchmark snapshot for downstream tools

## Design Boundary

This package intentionally works over plain JavaScript objects and rows.

That keeps it easy to compose with multiple artifact sources while avoiding a
premature rewrite of the compiler or the evaluator into Node.
