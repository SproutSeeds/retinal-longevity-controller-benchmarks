# Claim: Source-bound RPE evidence replay

Level: **Verified**, bounded to software and numerical consumption of released source-result tables. Biological interpretations are **Heuristic**.

The two executable evaluators, immutable acceptance packets and expected outputs live under `programs/partial-reprogramming-controller/` in this repository. `public-package.json` binds all released files. The v2 receipt records 937 source-derived numerical comparisons and 56 actual CLI rejections; the earlier engine has seven exact golden-output comparisons. The v2 suite contains nine acceptance packets and 23 distinct source observations. Test cases, observations and biological units are separate counts.

Verification hook, from the repository root:

```sh
python3 -m pip install jsonschema==4.25.1
python3 research/2026-10-rpe-controller/verify_public.py
python3 research/2026-10-public-data/release_check.py
python3 tools/research-sync/test_sync.py
```

Expected: each command exits zero and reports PASS or a passing unittest result. The numerical tolerance is `2e-10` scaled error. Exact expected JSON output and table reproduction use byte comparisons. The public verification receipt is deterministic under the supported Python environment; its protection-check count reflects only exported files.

Limits: known-outcome secondary analysis; same-agent verification; no independent biological replication, raw-matrix replay in this quick check, held-out performance estimate, clinical advice or restoration certification. The original source freeze is historical and the public excerpt is explicitly labeled as a later export. A passing public CI run binds its tested commit, not later commits.
