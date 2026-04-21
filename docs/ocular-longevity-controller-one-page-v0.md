# Ocular Longevity Controller One-Page Public Brief v0

Date: 2026-04-20

## The Object

The Ocular Longevity Controller is public benchmark infrastructure for asking what eye-aging and restoration-like claims are allowed to mean.

It is not a therapy claim. It creates an auditable decision layer that separates:

- supported evidence
- support-only context
- blocked claims
- missing required anchors
- contradiction
- review-required states
- abstention

## Why It Matters

Ocular longevity work is becoming possible before it is easy to interpret. Retinal images, OCT, ocular atlases, single-cell data, and donor-tissue programs are producing useful signals, but the field still needs a public way to avoid turning partial evidence into overconfident claims.

This project makes the boundary visible:

> what is known, what is missing, what is contradicted, and what should not be promoted yet.

## What Exists Now

Public repository:

- `https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks`

DOI:

- `https://doi.org/10.5281/zenodo.19633942`

NPM entry point:

```bash
npm install controller-benchmark
npx controller-benchmark --help
npx controller-benchmark --example cx004
npx controller-benchmark --example hazard-stop
```

Current public package family:

- `controller-benchmark`
- `controller-benchmark-data`
- `controller-benchmark-js`
- `controller-benchmark-schemas`

## What The Examples Show

`cx004` shows a contradiction path:

- a baseline can look attractive
- the controller detects a Gill-versus-Olova conflict
- the result escalates to validation instead of pretending the biology is solved

`hazard-stop` shows a hard safety block:

- a tempting route remains blocked because the controller refuses to reopen a tumor-hazard family

These examples are not biological proof. They are public, inspectable examples of how the controller should behave when evidence is incomplete, risky, or contradictory.

## Near-Term Research Path

The strongest next funding shape is an NEI R21 secondary-data project:

> build and evaluate an abstention-aware controller for ocular aging and restoration-claim adjudication using existing human vision-related data.

The R21 path is explicitly secondary-data only:

- no new human data collection
- no new image grading
- no wet-lab assay
- no clinical trial
- no patient advice
- no therapy-readiness claim

## What We Need

Useful help now:

- an eligible host or collaborator for an NEI R21 secondary-data route
- ocular atlas or vision-data experts who can sanity-check the data path
- independent reviewers who can challenge the claim boundaries
- funders who want public-domain ocular longevity infrastructure
- providers who can quote the smallest missing biology tranche, not vague discovery work

## What This Is Not

This is not:

- medical advice
- clinical decision support
- a therapy recommendation
- proof of ocular rejuvenation
- a claim that public data closes the human validation gap

## The Clean Ask

If you are a host, collaborator, funder, or reviewer:

> Can you help route, review, or support a secondary-data-only ocular controller project whose main output is a public evidence-boundary layer, not a treatment claim?

Contact:

- `cody@frg.earth`
- `https://frg.earth`
