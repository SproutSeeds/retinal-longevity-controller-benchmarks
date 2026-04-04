# Changelog

## 0.1.2 - 2026-04-04

- add a summary helper for the frozen `CX-004` resolution-review gate
- extend the merged benchmark snapshot with a `resolution_review_gate` layer
- keep the demo-facing JS summary surface aligned with the expanded public
  bundle

## 0.1.1 - 2026-04-03

- add summary helpers for the public `CX-004` validation handoff object
- extend the merged benchmark snapshot with a `validation_handoff` layer
- keep JS summaries aligned with the newer contradiction and passive
  recommendation public bundle surfaces

## 0.1.0 - 2026-04-02

- scaffold `controller-benchmark-js`
- add read-only benchmark summarization and comparison helpers
- keep the package thin and bundle-agnostic so it composes with the data and
  schema layers
- add a repo-local three-package demo that validates and summarizes the public
  benchmark stack end to end
