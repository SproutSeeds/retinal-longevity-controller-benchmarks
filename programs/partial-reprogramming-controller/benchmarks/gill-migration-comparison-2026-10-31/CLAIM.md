# Claim: frozen Gill comparison and reproducible intake

Level: **Verified**, bounded to software behavior and RNA-roster accounting after the verification hook passes. Analysis choices are **Heuristic**. Biological comparison: **INCONCLUSIVE**, awaiting source-compatible inputs.

Canonical evidence: `intake.py`, `test_intake.py`, `rna-pairs.tsv`, `READINESS.json` and `ARTIFACT_MANIFEST.json`. Process documents and the plan are not biological evidence.

Verification hook: `python3 verify.py` from this directory. Expected: frozen metadata and artifact digests match; 13 contrasts have duration-specific donor counts 3/2/1/3; empty observed intake is DEFERRED; synthetic arithmetic and rejection controls pass. Standard-library execution is deterministic and performs no network requests. Original source context is bound to the preceding source audit; this replay does not reacquire the original paper or independently validate its experiments.

No new RNA effects, functional effects, clock reproduction, restoration, safety or ocular conclusions are supplied. Phase 483 and prior controller verdicts remain unchanged. Original investigators retain experimental credit.
