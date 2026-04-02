# Controller Benchmark Modules

Published by SproutSeeds. Research stewardship: Fractal Research Group
(`frg.earth`).

This repository is the public package home for the controller benchmark module
stack.

It holds reusable public infrastructure derived from the controller benchmark
program, with the relationship-specific packet and private reviewer context
kept out of scope.

## Packages

- `controller-benchmark-schemas`
  - schema contracts and validation helpers for condition records, compile
    receipts, shell receipts, and trust-boundary artifacts
- `controller-benchmark-data`
  - the current public-neutral benchmark bundle with lightweight Node readers
- `controller-benchmark-js`
  - thin JavaScript tooling for summarizing, comparing, and snapshotting
    benchmark artifacts
- `controller-benchmark`
  - opinionated umbrella package for the current public controller benchmark
    release surface

## Working Boundary

This repo is for public benchmark infrastructure.

It is not the place for:

- private reviewer packets
- compensation or ownership notes
- live negotiation context
- unpublished relationship-layer material

## Current Status

- public repo home is live
- the first three benchmark packages are published on npm at `0.1.0`
- the umbrella package is being added as the one-install public entry point

## Install Targets

```bash
npm install controller-benchmark-schemas
npm install controller-benchmark-data
npm install controller-benchmark-js
npm install controller-benchmark
```

## Design Principle

The goal is benchmark-first infrastructure:

- explicit contracts
- explicit provenance
- explicit trust boundaries
- reusable public artifacts

The goal is not to overclaim solved biology.
