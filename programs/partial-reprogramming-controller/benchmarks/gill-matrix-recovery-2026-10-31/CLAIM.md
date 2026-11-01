# Gill RNA source recovery

Claim level: **Verified**, bounded to acquisition, original-value preservation and source-label availability.

Two pinned GSE165177 processed RNA matrices contain 35,805 feature rows and 95 expression columns. All 3,401,475 expression values are finite and preserved exactly as source text in a locus-aligned working derivative. Ninety column labels match GEO titles exactly. Five formatting aliases remain provisional and lie outside the frozen analysis roster. All 26 required RNA arms for the 13 frozen contrasts have exact matches.

Repeated gene IDs and blank IDs retain separate genomic-locus rows. The two reordered feature identities are joined explicitly; their source vectors are identical, so the ordering difference has no observed numeric consequence. The package performs no gene-ID collapse, batch correction, clock fitting or functional comparison.

## Verification hook

From this folder, run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 verify.py
python3 recover.py --download --verify
python3 recover.py --write --merge
python3 verify_merged.py
```

Expected: offline artifact/roster checks and 15 rejection/regression tests pass. Full source replay verifies both original SHA-256 hashes and gzip streams. Independent merged verification reports 35,805 rows, 95 columns, 3,401,475 finite source values and zero changed cells. Missing or changed original files make source replay incomplete; they never trigger an automatic substitution. A fresh-cache release check received HTTP 403 from GEO, so current end-to-end reacquisition remains INCONCLUSIVE despite the verified retained original files.

The original input hashes, extracted tables, aligned output and Python checks are deterministic. Live network availability can change. Mutable institutional metadata is a dated discovery record; an indexed file or matching filename alone does not establish its contents.

## Interpretation and remaining requirements

Record: **PASS** for source recovery and software behavior. Record: **INCONCLUSIVE** for the molecular-age/function question, which remains **DEFERRED**. Original Figure 3C per-sample clock outputs, technical-replicate migration measurements and an authoritative function-culture/RNA crosswalk are still required under the unchanged frozen contract.

This known-outcome challenge leaves Phase 483 and prior controller verdicts unchanged. Gill and colleagues retain credit for the original data, experiments, clock and published biological findings. This recovery supplies no efficacy, safety, persistence or clinical result.
