# controller-benchmark-data

Published by SproutSeeds. Research stewardship: Fractal Research Group ([frg.earth](https://frg.earth)).

Versioned benchmark bundle and lightweight readers for the controller
phase-stratified benchmark.

## Install

```bash
npm install controller-benchmark-data
```

For local development inside this repo:

```bash
cd packages/controller-benchmark-data
npm test
npm pack --dry-run
```

## What This Is

`controller-benchmark-data` packages the current live public benchmark bundle as
versioned data with small Node readers.

It currently ships:

- the accession-pinned study corpus
- the negative-family registry
- the live compiled condition records
- the compiler coverage and trust receipt
- the benchmark shell receipt
- the baseline and controller output tables
- the study-specific compiler rule packs that produced the live bundle

The point is not to turn one research thread into npm theater.

The point is:

- preserve one exact benchmark bundle
- make it easy to inspect from Node tooling
- keep the bundle versioned and attributable
- let downstream tools use the same artifact set without re-deriving it from
  prose memory

## What This Is Not

`controller-benchmark-data` is not:

- the controller compiler
- the benchmark runner
- a generic ETL framework
- a matrix extraction toolkit
- a claim that the bundle is final or universally authoritative

It is a versioned benchmark bundle with lightweight readers.

## Package Positioning

The clean split is:

- `controller-benchmark-schemas`
  - stable contracts and validators
- `controller-benchmark-data`
  - one current benchmark bundle and thin readers

That means the schema package can travel widely, while this package can carry
one exact benchmark state honestly.

## Quick Start

```js
import {
  BUNDLE_ID,
  BUNDLE_MANIFEST,
  listCompilerRules,
  readBenchmarkShellReceipt,
  readConditionRecords,
  readStudyCorpusRows,
} from "controller-benchmark-data";

console.log(BUNDLE_ID);
console.log(BUNDLE_MANIFEST.condition_count);
console.log(listCompilerRules());
console.log(readStudyCorpusRows().length);
console.log(readConditionRecords().length);
console.log(readBenchmarkShellReceipt().summary.controller_output_counts);
```

## API Surface

- `BUNDLE_ID`
- `BUNDLE_MANIFEST`
- `listArtifacts()`
- `listCompilerRules()`
- `getArtifactPath(name)`
- `getArtifactUrl(name)`
- `readArtifactRaw(name)`
- `readStudyCorpusRaw()`
- `readStudyCorpusRows()`
- `readNegativeFamilyRegistry()`
- `readConditionFixture()`
- `readConditionRecords()`
- `readCompileReceipt()`
- `readCoverageTrustReceipt()`
- `readAgeOnlyBaselineOutputRaw()`
- `readAgeOnlyBaselineOutputRows()`
- `readControllerOutputRaw()`
- `readControllerOutputRows()`
- `readBenchmarkShellReceipt()`
- `readCompilerRule(name)`
- `loadLatestBundle()`

## Current Boundary

This package distributes a public-neutral benchmark bundle derived from the
controller canon.

The public package should not leak reviewer-specific naming, private packet
context, or relationship-layer labels into the release surface.
