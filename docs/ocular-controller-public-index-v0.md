# Ocular Controller Public Index v0

Date: 2026-04-11

## Purpose

This is the public front door for the currently released ocular/controller
benchmark surfaces.

It connects the public GitHub package repo, npm packages, and Synapse artifact
shelves in one place, while keeping the claim boundary explicit.

## Public Starting Points

### GitHub

Public package and module repo:

- https://github.com/SproutSeeds/controller-benchmark-modules

This repo is the public code/package surface. It is not the full internal
research workspace.

### npm

Main public entry point:

```bash
npm install controller-benchmark
```

Current verified package versions:

- `controller-benchmark@0.1.2`
- `controller-benchmark-data@0.1.4`
- `controller-benchmark-js@0.1.2`
- `controller-benchmark-schemas@0.1.1`

Package roles:

- `controller-benchmark` is the one-install entry point.
- `controller-benchmark-data` carries the public benchmark bundle and readers.
- `controller-benchmark-js` summarizes benchmark bundles and outputs.
- `controller-benchmark-schemas` validates benchmark artifact contracts.

### Synapse

Public Synapse project:

- `Partial Reprogramming Controller Public Artifacts`
- https://www.synapse.org/Synapse:syn74240566

Public ocular benchmark pack:

- `ocular-benchmark-pack-v0`
- https://www.synapse.org/Synapse:syn74252747

Public ocular world-share pack:

- `ocular-world-share-pack-v0`
- https://www.synapse.org/Synapse:syn74260927

## What Has Been Released

### Ocular benchmark pack v0

The benchmark pack includes:

- an ocular benchmark contract
- an ocular scoring-kernel note
- a starter pack
- a starter-pack manifest
- a surface-preparation note
- a launch-prerequisites note

Role:

- define a reproducible benchmark-facing contract and starter surface
- preserve the exact public boundary for later baseline and launch-readiness
  work

### Ocular world-share pack v0

The world-share pack includes:

- a public progress brief
- a public claim-boundary note
- a human-authority story-arc note
- a stable adult-subset note and compact CSV
- a `GSE236027` residual-gap note and compact CSV
- a `GSE148077` holdout-alignment note and compact CSV

Role:

- share the current bounded, support-only human-informed ocular progress story
- show the exact residual gaps rather than blur them into solved biology

### Public benchmark modules

The npm/GitHub package stack currently exposes:

- schema contracts
- benchmark bundle readers
- JavaScript summary helpers
- the public `CX-004` validation handoff surface
- contradiction-ledger and passive-recommendation scaffold artifacts

Role:

- make the benchmark artifacts easier to validate, inspect, and reuse
- keep provenance and trust boundaries machine-readable

## Current Claim Boundary

The public surfaces support this bounded statement:

The controller project has public, versioned benchmark infrastructure and a
support-only ocular progress shelf, including a pair-backed adult human support
layer, an exact stable adult subset, and named residual gaps in the current
human-route surface.

The public surfaces do not claim:

- solved ocular rejuvenation
- human intervention truth
- adult human kernel re-entry
- therapy readiness
- Kaggle or competition launch readiness
- a wet-lab result from the current provider outreach lane
- a provider choice or spend decision

## What Is Not Public Here

The broader internal research workspace is not public.

Not included here:

- provider emails or quotes
- confidential disclosure agreement material
- private reviewer packets
- live negotiation context
- controlled or non-redistributable datasets
- unpublished relationship-layer material
- raw wet-lab data from the current acquisition lane

## What Does Not Exist Yet

As of this index:

- there is no Zenodo DOI for the ocular/controller public shelf
- there is no Hugging Face dataset or model card for the public bundle
- there is no separate public ocular-only GitHub repo
- the main internal `longevity-research` workspace remains private

## Recommended Next Public Hardening

The next public hardening pass should be:

1. create an immutable Zenodo record for the public shelf or package release
2. add a Hugging Face dataset card only if we want a dataset-native mirror
3. publish a public GitHub release from this repo, not the private workspace
4. keep npm releases aligned with the public README and package docs
5. add a short "How to cite / how to inspect" section after the DOI exists

## Citation Until DOI

Until a DOI exists, cite the exact public surfaces:

- GitHub: https://github.com/SproutSeeds/controller-benchmark-modules
- Synapse benchmark pack: https://www.synapse.org/Synapse:syn74252747
- Synapse world-share pack: https://www.synapse.org/Synapse:syn74260927
- npm package entry point: `controller-benchmark`

## Stewardship

Published by SproutSeeds.

Research stewardship: Fractal Research Group, https://frg.earth
