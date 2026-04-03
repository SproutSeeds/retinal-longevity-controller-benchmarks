# controller-benchmark

Published by SproutSeeds. Research stewardship: Fractal Research Group ([frg.earth](https://frg.earth)).

Opinionated umbrella package for the current public controller benchmark release.

## Install

```bash
npm install controller-benchmark
```

For local development inside this repo:

```bash
cd packages/controller-benchmark
npm install --no-package-lock
npm test
npm pack --dry-run
```

## What This Is

`controller-benchmark` is the one-install happy path for the current public
controller benchmark surface.

It composes:

- `controller-benchmark-schemas`
  - contract and validation layer
- `controller-benchmark-data`
  - current released benchmark bundle
- `controller-benchmark-js`
  - thin JavaScript interpretation and summarization helpers

The point is to make the current public benchmark release easy to load,
validate, and inspect without forcing users to learn the full internal package
split on day one.

## What This Is Not

`controller-benchmark` is not:

- the Python compiler
- the benchmark runner
- a model-training runtime
- a controller-serving stack
- a claim that the underlying biology is settled

It is the public release surface for the current benchmark bundle and its
shareable JS/runtime helpers.

## Quick Start

```js
import {
  RELEASE_METADATA,
  buildCurrentBenchmarkSnapshot,
  loadCurrentBenchmark,
  validateCurrentBenchmark,
} from "controller-benchmark";

console.log(RELEASE_METADATA.bundle_id);

const benchmark = loadCurrentBenchmark();
const validation = validateCurrentBenchmark(benchmark);
const snapshot = buildCurrentBenchmarkSnapshot(benchmark);

console.log(validation.valid);
console.log(snapshot.shell.fail_closed);
```

## Tiny Browser Demo

A static browser demo is included here:

- [/Volumes/Code_2TB/code/longevity-research/packages/controller-benchmark/examples/browser-demo/index.html](/Volumes/Code_2TB/code/longevity-research/packages/controller-benchmark/examples/browser-demo/index.html)

Refresh the demo data:

```bash
node packages/controller-benchmark/examples/browser-demo/build-demo-data.mjs
```

Serve it locally:

```bash
cd packages/controller-benchmark/examples/browser-demo
python3 -m http.server 8000
```

## API Surface

### Umbrella helpers

- `RELEASE_METADATA`
- `loadCurrentBenchmark()`
- `validateCurrentBenchmark(bundle?)`
- `buildCurrentBenchmarkSnapshot(bundle?)`
- `loadValidatedCurrentBenchmark()`

### Curated re-exports

- schema validators and schema constants from `controller-benchmark-schemas`
- bundle readers and bundle metadata from `controller-benchmark-data`
- summarization and snapshot helpers from `controller-benchmark-js`

## Design Boundary

This package is intentionally opinionated around one current public release.

The lower-level packages remain the more stable foundation:

- `controller-benchmark-schemas`
- `controller-benchmark-data`
- `controller-benchmark-js`

That keeps the architecture clean while giving most users a much simpler entry
point.
