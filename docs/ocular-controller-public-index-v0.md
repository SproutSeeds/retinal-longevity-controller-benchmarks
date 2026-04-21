# Retinal Longevity Controller Public Index v0

Date: 2026-04-21

Updated: 2026-04-21

## Purpose

This is the public front door for the currently released retinal and ocular
longevity controller and benchmark surfaces.

It connects the public GitHub package repo, npm packages, Synapse artifact
shelves, one-page public brief, and Zenodo DOI in one place, while keeping the
claim boundary explicit.

The mission context is safety-first lineage-preserving rejuvenation: build
controller infrastructure that can evaluate whether a candidate partial
reprogramming or restoration signal improves age-associated state while
preserving adult identity and rejecting transformation-risk shortcuts.

The retinal lane is the current bounded public wedge. It is not a therapy
claim; it is a disciplined benchmark-and-evidence surface for asking what a
controller should accept, reject, or leave unresolved in eye-relevant longevity
research.

## Public Starting Points

### One-Page Brief

Shortest showable overview:

- [Ocular Longevity Controller One-Page Public Brief v0](ocular-longevity-controller-one-page-v0.md)

Use this when a host, collaborator, funder, or reviewer needs the project in
one fast pass.

### GitHub

Public package and module repo:

- https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks

This repo is the public code/package surface. It is not the full internal
research workspace.

### DOI

Versioned Zenodo DOI:

- https://doi.org/10.5281/zenodo.19633942

Concept DOI for future versions:

- https://doi.org/10.5281/zenodo.19633941

### npm

Main public entry point:

```bash
npm install controller-benchmark
```

Current verified package versions:

- `controller-benchmark@0.1.4`
- `controller-benchmark-data@0.1.5`
- `controller-benchmark-js@0.1.3`
- `controller-benchmark-schemas@0.1.2`

Package roles:

- `controller-benchmark` is the one-install entry point.
- `controller-benchmark-data` carries the public benchmark bundle and readers.
- `controller-benchmark-js` summarizes benchmark bundles and outputs.
- `controller-benchmark-schemas` validates benchmark artifact contracts.

CLI inspection:

```bash
npx controller-benchmark --list-examples
npx controller-benchmark --example cx004
npx controller-benchmark --example hazard-stop
```

The built-in examples are documentation surfaces, not biological proof. They
show how the benchmark preserves contradiction, abstention, and hard safety
blocks in concrete cases.

### Synapse

Public Synapse project:

- `Partial Reprogramming Controller Public Artifacts`
- https://www.synapse.org/Synapse:syn74240566

Published public artifact index:

- `controller-ocular-public-artifact-index-v2.md`
- https://www.synapse.org/Synapse:syn74531916

Public ocular benchmark pack:

- `ocular-benchmark-pack-v0`
- https://www.synapse.org/Synapse:syn74252747

Public ocular world-share pack:

- `ocular-world-share-pack-v0`
- https://www.synapse.org/Synapse:syn74260927

## What Has Been Released

### Ocular benchmark pack v0

The ocular benchmark pack carries the current retina-centered public benchmark
surface. It includes:

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

The ocular world-share pack carries the current retina/RGC-centered public
progress story. It includes:

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

### One-page public brief

The one-page brief exposes the project in a host/funder/reviewer-friendly
shape:

- object
- why it matters
- what exists now
- what the examples show
- near-term research path
- what we need
- explicit non-claims
- clean ask

Role:

- make the project usable in outreach without exposing private planning,
  provider, inbox, or negotiation context

## Current Claim Boundary

The public surfaces support this bounded statement:

The controller project has public, versioned benchmark infrastructure and a
support-only retinal/ocular progress shelf, including a pair-backed adult human
support layer, an exact stable adult subset, and named residual gaps in the
current human-route surface.

The public surfaces do not claim:

- solved retinal or ocular rejuvenation
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

- there is no Hugging Face dataset or model card for the public bundle
- there is no separate public ocular-only GitHub repo
- the main internal `longevity-research` workspace remains private
- there is no wet-lab result or provider-selection result in the public shelf

## Recommended Next Public Hardening

The next public hardening pass should be:

1. keep npm releases aligned with the public README and package docs
2. publish future GitHub releases from this repo, not the private workspace
3. add a Hugging Face dataset card only if a dataset-native mirror becomes useful
4. add a short "How to cite / how to inspect" section to each package README
5. keep the Synapse public index current whenever public shelf contents change
6. keep public language centered on evidence boundaries, not therapy claims

## Citation And Inspection

Cite or inspect the exact public surfaces:

- DOI: https://doi.org/10.5281/zenodo.19633942
- GitHub: https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks
- Synapse public artifact index: https://www.synapse.org/Synapse:syn74531916
- Synapse benchmark pack: https://www.synapse.org/Synapse:syn74252747
- Synapse world-share pack: https://www.synapse.org/Synapse:syn74260927
- npm package entry point: `controller-benchmark`

## Stewardship

Published by SproutSeeds.

Research stewardship: Fractal Research Group, https://frg.earth
