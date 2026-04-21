# Retinal Longevity Controller Benchmarks

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19633942.svg)](https://doi.org/10.5281/zenodo.19633942)

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

If you need the shortest showable overview, start here:

- [Ocular Longevity Controller One-Page Public Brief v0](docs/ocular-longevity-controller-one-page-v0.md)

For the current public front door across GitHub, npm, Synapse, and citation
metadata, continue here:

- [Retinal Longevity Controller Public Index v0](docs/ocular-controller-public-index-v0.md)

Together, those pages tie together:

- this public GitHub package repo
- the published npm benchmark modules
- the DOI-backed Zenodo release
- the published Synapse public artifact index
- the public Synapse ocular benchmark pack
- the public Synapse ocular world-share pack
- the Zenodo DOI
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
- one-page public brief is live
- the benchmark package stack is published on npm
- `controller-benchmark` is the one-install public entry point
- the current public bundle surface includes:
  - contradiction-ledger artifacts
  - passive recommendation scaffold artifacts
  - the `CX-004` validation handoff for the live Gill-versus-Olova pair
- public Synapse ocular shelves are live for:
  - `controller-ocular-public-artifact-index-v2.md`
  - `ocular-benchmark-pack-v0`
  - `ocular-world-share-pack-v0`
- Zenodo archival DOI is live

Current verified npm versions:

- `controller-benchmark@0.1.4`
- `controller-benchmark-data@0.1.5`
- `controller-benchmark-js@0.1.3`
- `controller-benchmark-schemas@0.1.2`

## CLI Walkthroughs

The umbrella package now includes a small command-line entry point for concrete
benchmark walkthroughs:

```bash
npx controller-benchmark --help
npx controller-benchmark --list-examples
npx controller-benchmark --example cx004
npx controller-benchmark --example hazard-stop
```

Use `cx004` to inspect the Gill-versus-Olova contradiction path. Use
`hazard-stop` to inspect a hard preserve-block case where the controller refuses
to reopen a tumor-hazard family.

## Citation And Archival Metadata

Versioned Zenodo DOI:

- `10.5281/zenodo.19633942`

Concept DOI for future versions:

- `10.5281/zenodo.19633941`

Synapse public artifact index:

- https://www.synapse.org/Synapse:syn74531916

Citation metadata is available in `CITATION.cff`. Zenodo metadata is available
in `.zenodo.json`.

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
