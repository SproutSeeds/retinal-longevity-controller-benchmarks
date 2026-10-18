# Inherited panel source location

Independent review found that the frozen `panels.json` retained the relative pointer `../analysis/orthology.json` from the preceding packet. That literal path does not resolve inside this new packet. The inherited gene lists and declared source SHA-256 are unchanged and correct.

The source is the [earlier public orthology artifact](https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks/blob/566621cdfe5a87d56b94d3baf2cafb7bb2b6030c/research/2026-10-neural-validation/analysis/orthology.json). A byte-identical copy is provided here as [inherited-orthology.json](inherited-orthology.json), bound by [provenance-correction.json](provenance-correction.json).

This correction supplies the missing provenance location after analysis. It changes neither the frozen panels, mapping, computation nor outcomes. The original frozen bytes remain preserved. The packet verifier checks the copied source against the original declared hash.
