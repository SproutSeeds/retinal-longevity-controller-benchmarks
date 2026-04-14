# Retinal Longevity Controller Benchmarks

Published by SproutSeeds. Research stewardship: Fractal Research Group
([frg.earth](https://frg.earth)).

This repository is the public artifact and package surface for a safety-first
retinal longevity controller: a benchmarked research system for evaluating
lineage-preserving partial-reprogramming and restoration signals without
overclaiming therapy or solved biology.

The work starts in the retina because the eye gives the project a bounded,
high-value place to test whether a longevity signal preserves adult retinal
cell identity, avoids transformation-risk shortcuts, and remains honest under
explicit decision gates.

The npm package names remain `controller-benchmark-*` because this repo also
publishes reusable benchmark infrastructure, while the public repository name
now centers the retinal and ocular longevity controller evaluation story.

## Start Here

For the current public front door across GitHub, npm, and Synapse, start here:

- [Retinal Longevity Controller Public Index v0](docs/ocular-controller-public-index-v0.md)

That index ties together:

- this public GitHub package repo
- the published npm benchmark modules
- the public Synapse ocular benchmark pack
- the public Synapse ocular world-share pack
- the exact public claim boundaries

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
- the benchmark package stack is published on npm
- `controller-benchmark` is the one-install public entry point
- the current public bundle surface includes:
  - contradiction-ledger artifacts
  - passive recommendation scaffold artifacts
  - the `CX-004` validation handoff for the live Gill-versus-Olova pair
- public Synapse ocular shelves are live for:
  - `ocular-benchmark-pack-v0`
  - `ocular-world-share-pack-v0`

Current verified npm versions:

- `controller-benchmark@0.1.2`
- `controller-benchmark-data@0.1.4`
- `controller-benchmark-js@0.1.2`
- `controller-benchmark-schemas@0.1.1`

## Install Targets

```bash
npm install controller-benchmark-schemas
npm install controller-benchmark-data
npm install controller-benchmark-js
npm install controller-benchmark
```

## Tiny Browser Demo

A static browser demo lives under:

- `packages/controller-benchmark/examples/browser-demo`

Refresh the demo data from the current public benchmark bundle:

```bash
node packages/controller-benchmark/examples/browser-demo/build-demo-data.mjs
```

Then serve the directory locally:

```bash
cd packages/controller-benchmark/examples/browser-demo
python3 -m http.server 8000
```

## Design Principle

The goal is benchmark-first infrastructure:

- explicit contracts
- explicit provenance
- explicit trust boundaries
- reusable public artifacts

The goal is not to overclaim solved biology.
