# Scope of the verified result

**Status:** Verified computation / Heuristic biological interpretation. **Verification record:** [VERIFICATION.json](VERIFICATION.json). **Experiment replacement:** INCONCLUSIVE. **CX004-R01 through R04:** `insufficient_signal`.

The verified claim is that the released, pinned observations produce the reported donor, gene and depth sensitivities under the stated contracts. The most consistent acute response is the decrease in the cell-cycle score in all nine paired mouse neural donors across all three scoring methods and every single-gene omission. The narrower human interpretation is supported by gene-contribution arithmetic and per-barcode recounting. Source reconciliation identifies already-sequenced samples whose missing assignments prevent a verified withdrawal analysis.

Canonical evidence comprises [bulk/results.json](bulk/results.json), [bulk/cycle-robustness.json](bulk/cycle-robustness.json), [analysis/cross-cohort-results.json](analysis/cross-cohort-results.json), [human/marker-audit.json](human/marker-audit.json), [human/percell/results.json](human/percell/results.json), [decomposition/extension-results.json](decomposition/extension-results.json) and [recovery/full-animal-source-map.json](recovery/full-animal-source-map.json). The README and methods are summaries of these artifacts.

Verification hook, from the packet root:

```sh
python3 verify.py
python3 run_checks.py
```

Expected result: PASS, with every subprocess returning zero. The first command verifies release hashes and selected scientific summaries. The second repeats saved-output arithmetic and synthetic adversaries in an isolated temporary copy; it requires `uv` and pinned Python dependencies, but no biological download. Historical full observed-input replays are recorded separately and can be repeated with [REPRODUCTION.md](REPRODUCTION.md). A passing software check does not independently validate experimental design or biological benefit.

Frozen contracts and receipts retain the order of decisions: the main neural panels and decomposition preceded neural expression outcomes; cohort 1 followed cohort 2; bulk and per-cell contracts preceded their new runs; human concentration and decomposition extensions are post hoc. Exact label permutations require exchangeability, and age was not randomized. Repeated cells, genes, libraries or synthetic samples do not increase donor replication.

These results do not establish lasting human or ocular rejuvenation, calibrated safety, a causal age effect, same-cell recovery, a treatment recommendation or biological novelty. Such claims remain Conjecture or untested. The [next-input decisions](NEXT_STEPS.md) specify what could change that status. The controller's existing phase and both historical research canons remain unchanged.
