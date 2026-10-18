# Dependencies that remain open

1. **GEO all-record queries exceeded the 20 MB per-file cap.** No oversized response was retained. Sample-only requests successfully retrieved the three required sample manifests. The original failures remain in `retrieval-1.json`; the successful requests are in `retrieval-2.json`.
2. **Searching only the Clock repository missed available numerical parameters.** Supplementary Table 1 supplies 295 terms. This corrects the earlier overly broad missing-weights description. The preprocessing/reference-output gap remains.
3. **The full public Clock history contains scripts but no fitted-model objects.** All 27 reachable commits and 21 distinct paths were inspected. Authors may hold the reference objects outside this repository; their absence here is not a global absence claim.
4. **Running the available clock application script would require unavailable objects and an interpretation choice.** Its frozen-SVA result is subsequently overwritten. We did not execute or silently repair it. Request exact intended preprocessing and a small input/output reference.
5. **Modern ocular clocks do not identify the historical model automatically.** The audited model deposits postdate the 2025 preprint. Source-use restrictions and historical equivalence remain unresolved. No pickle deserialization or model execution occurred.
6. **Fresh GSE350289 workbook retrieval did not recover cell assignment keys.** Two sheets remain empty and populated sheets provide age values without the required joined identities. Await a corrected export; do not infer conditions from row order or expression.
7. **Timing labels disagree across source surfaces.** The 6/12-day caption and 8/16-day GEO OFF labels remain separate. Actual sample dates or author clarification are required.

These limitations preserve the existing `insufficient_signal` decisions. They do not establish that a new wet-lab experiment is inevitable.
