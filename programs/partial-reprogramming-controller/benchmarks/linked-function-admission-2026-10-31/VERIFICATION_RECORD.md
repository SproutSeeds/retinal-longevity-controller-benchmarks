# Linked-input audit verification

Claim level: Verified for source extraction and deterministic intake replay; Heuristic for acquisition rank and prospective interpretation. Biological restoration and joint-function conclusions remain INCONCLUSIVE.

Run from this folder:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 verify.py
python3 audit_sources.py --verify
```

Expected: portable artifact/intake checks PASS; source metadata extraction PASS against all 27 retained source files. The second hook needs the ignored source cache and Poppler's pdftotext. `python3 acquire.py` restores missing files only if live bytes match their recorded hashes. Changed or unavailable live sources leave full-source verification incomplete.

The source hook checks every retained file's bytes and digest, extracts six GEO RNA rosters and one ENA RNA roster, reproduces the RNA metadata and Gill within-RNA pairing tables, and re-extracts all ten Schiff PDF summaries. The rendered source table on PDF page 7 was inspected directly before finalization. Counts reproduce 177 RNA records, 13 within-RNA contrasts, three Gill donor labels and 26 reported Schiff experiments across ten summarized lines.

The portable hook checks the artifact manifest, original contract digest, candidate ranking replay, source-extraction table consistency and adversarial admission tests. It does not download raw reads, reproduce gene expression estimates, independently validate the papers or supply missing culture/function identities. The seven retained failed acquisition attempts remain visible; full Saini article/supplement coverage is incomplete.

Determinism: retained-source parsers, table extraction and local intake decisions are deterministic under the recorded inputs. Network availability, rendered publisher pages and external scientific validity are separate observations. The known published outcomes were reviewed during selection; this is a known-outcome source audit.

Verification result: PASS for the recorded source extraction and local replay after executing these hooks. Final command outputs and public-release state are recorded in the handoff receipt; external scientific evaluation remains pending.
