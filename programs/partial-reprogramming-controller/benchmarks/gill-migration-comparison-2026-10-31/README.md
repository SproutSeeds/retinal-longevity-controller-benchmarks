# Gill RNA age and migration function

Title: Gill RNA age and migration function

**Verified, software and roster scope:** the frozen roster contains 13 final-outgrowth RNA contrasts. The empty observed intake returns **DEFERRED**, with zero functional observations, zero molecular-age values and zero computed effects. The contract specifies the comparison to run when source-compatible measurements arrive.

This is a **known-outcome** challenge: [Gill et al.](https://elifesciences.org/articles/71624) already describe variable migration responses and their relationship to molecular measures. Original investigators retain credit for the experiments, clock and biological findings. Our contribution is the frozen analysis contract and its executable checks. This local freeze precedes new numerical intake; external registration and blinded validation are separate milestones.

## Comparison and experimental units

Use existing per-RNA-sample outputs of the investigators' Figure 3C custom transcriptomic clock and original technical-replicate migration speeds. An authoritative culture/RNA mapping must agree on donor, treatment, exposure, withdrawal and collection context. Matched sibling cultures require explicit source authority. RNA is a destructive assay, so the comparison has parent/sibling-culture scope.

| Reprogramming duration | RNA contrasts | Donor labels represented |
|---|---:|---:|
| 10 days | 3 | 3 |
| 13 days | 4 | 2 |
| 15 days | 2 | 1 |
| 17 days | 4 | 3 |

These are ceilings from RNA metadata; functional coverage is currently zero. Reprogramming duration does not measure withdrawal persistence. The fibroblast lineage includes temporary identity transition and selected outgrowth; adult-primary ocular evidence remains separate.

Technical speeds are averaged within culture. Pair-level treated-minus-control effects retain donor, duration and experiment. Experiments are averaged within donor/duration, then donors receive equal weight within that duration. Durations remain separate. Donor ranges and leave-one-donor-out summaries describe sensitivity; single-donor strata cannot supply that sensitivity. Directional flags use zero as their arithmetic boundary and supply no statistical equivalence or significance claim.

Finite signed wound-edge slopes are retained, including negative movement when supported by the source; unfavorable results are eligible under the same rules.

## Reproduce the current checkpoint

Python 3.10 or newer and its standard library are sufficient:

```sh
python3 verify.py
python3 intake.py --verify-readiness
```

Run these commands in this directory. `verify.py` checks the artifact and freeze digests, replays the empty observed intake, confirms roster coverage, and runs synthetic software controls. Those controls never enter observed scientific results.

## Prepare future source-reviewed inputs

Copy the three `*.template.tsv` files to a private intake directory as `crosswalk.tsv`, `migration.tsv` and `molecular_age.tsv`. Copy `evidence.template.json` there as `evidence.json`. Templates contain headers and pending review fields, with no invented measurements. Keep received files and correspondence outside the public export allowlist.

For each evidence source, supply `source_id`, `role` (`crosswalk`, `migration` or `molecular_age`), original HTTPS `url`, exact `locator`, a packet-relative retained-file `path`, and its `sha256`. Migration sources additionally declare `granularity: technical_replicate_speed`. Source files must resolve inside that intake directory. Retain original files alongside curated TSVs; source and curated-input digests have different purposes.

Complete the evidence review with `status: verified`, `reviewer`, `reviewed_at` and `basis`; explicitly confirm research-analysis permission. The review must check the mapping, values, original replicate unit, exclusions and completeness. The software checks these declarations and file integrity; scientific source review establishes whether they are true. Redistribution permission is a separate field and must be reviewed before any public release of new data.

Every frozen pair needs complete inputs or a source-backed entry in `excluded_pairs`, keyed by its `pair_id` with `reason` and a crosswalk-role `source_id`. Unsupported joins, reused observations/cultures, incompatible contexts or units, missing values and clock substitutions defer calculation. A different replicate design requires an explicit contract amendment.

```sh
python3 intake.py --input-dir /path/to/private-intake --output /path/to/new-result.json
```

Output creation refuses to overwrite an existing file. Review the decision and coverage before interpreting effects. Signed effects describe these cultures only. No new clinical, safety, rejuvenation or persistence conclusion follows. Wet-lab replacement remains **INCONCLUSIVE** and **Phase 483** still awaits a genuine supervised external packet exchange.

See [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md), [ANALYSIS_CONTRACT.json](ANALYSIS_CONTRACT.json), [FREEZE.json](FREEZE.json), [READINESS.json](READINESS.json) and [VERIFICATION_RECORD.md](VERIFICATION_RECORD.md).
