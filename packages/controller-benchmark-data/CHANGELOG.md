# Changelog

## 0.1.2 - 2026-04-03

- retire the legacy external-review benchmark namespace from the shipped bundle,
  receipts, and public-neutral benchmark artifacts
- align generated script paths and shell receipt naming with the neutral
  `controller-benchmark` namespace
- make the bundle manifest self-report the current `controller-benchmark-data`
  package version instead of a stale hardcoded value

## 0.1.1 - 2026-04-03

- add the public `CX-004` validation handoff and receipt to the released
  benchmark bundle
- expose readers for the `CX-004` validation handoff surfaces
- keep the contradiction ledger, passive recommendation scaffold, and public
  browser snapshot aligned with the newer benchmark tranche

## 0.1.0 - 2026-04-02

- scaffold `controller-benchmark-data`
- package the live public-neutral phase-stratified controller benchmark bundle
- add lightweight Node readers for bundle artifacts and compiler rule packs
