# Composition can oppose a within-type marker difference

**Exact algebra; Heuristic biological interpretation.** In the cohort-2 stress panel, the composition and within-type terms have opposite signs. At the primary 20-cell support floor and CP10k scale, the equal-lane total is −0.004811, partitioned into −0.017309 composition and +0.012498 within type. These are differences in mean per-cell log-expression scores.

Primary common support includes Microglia and Oligodendrocyte. It retains 58.8–68.1% of each primary animal's recovered cells. The 10-cell sensitivity admits five named types, retains 87.1–89.1%, and also has opposed stress components. Both denominators are conditional on that declared support. This arithmetic illustrates how an aggregate marker summary can conceal an opposing component. It does not identify a causal effect, unbiased tissue abundance or improvement in stress physiology.

The calculation is distinct from the pseudobulk analysis. All four panels, two support floors and two expression scales are in [results.json](results.json). It retains every lane, type mean, fraction and direct-cell-average check. [The contract](contract.json) was committed before neural outcomes.

```sh
uv run decomposition/decompose.py --cache /path/to/raw-cache --replay-frozen-hashes
uv run decomposition/verify_decomposition.py
uv run decomposition/reproduce.py --cache /path/to/raw-cache
```

Run from the packet root. The verifier checks 284 identities/provenance conditions and 10 synthetic adversarial cases. The observed output replays byte-identically on the pinned environment. Original experiment and data: [Xu et al., Nature Aging 2024](https://doi.org/10.1038/s43587-024-00594-3).
