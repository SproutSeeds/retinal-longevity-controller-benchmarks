# Verification record

Date: 2026-10-18. Claim level: **Verified** for source integrity, identifier checks, extraction and arithmetic. Biological experiment replacement: **INCONCLUSIVE**.

| Hook | Result | Scope |
| --- | --- | --- |
| Portable `verify.py` | **PASS 24/24** | Saved-source hashes/bindings, all reference rows, exact joins, group membership and arithmetic |
| Source-cache `verify.py` | **PASS 25/25** | Same checks plus all 48 retrieved source-byte hashes |
| `test_reference.py` | **PASS 16 tests** | Synthetic missing/duplicate/conflicting identity and workbook-parsing cases |
| `replay.py` | **PASS 10/10 byte-identical outputs** | Full extraction and audit rebuild from cached public sources |

## Portable public check

From the decision-audit packet root:

```sh
python3 human/verify.py
python3 -m unittest discover -s human -p 'test_*.py'
```

Expected outputs: `PASS 24/24` and `Ran 16 tests ... OK`. Python standard library only. No network, author model, original downloaded XLSX, paid service or private correspondence is required. The packet-level `FREEZES.jsonl` and all human JSON files referenced by `verify.py` must be included in the public allowlist. `verification.json` records the portable result.

These checks ensure the saved artifact's internal integrity and arithmetic. They do not independently reconstruct source values from a workbook absent from the package. Use the source-cache hook for byte authentication, and the full replay to re-extract values from the pinned public workbooks.

## Source acquisition and replay

`source-plan-1.json` through `source-plan-4.json` preserve the requested URLs. `fetch_sources.py` retrieves bounded public files and writes byte receipts. Preserve the committed `retrieval-*.json` receipts and place fresh receipts in temporary storage when testing downloads; changed source hashes require review. The branch-`master` STAMPScreen 404 is preserved, with a later successful `main` lookup.

The completed run used the first three source plans in one source cache and the fourth in a separate cache. From the public packet root, fetch fresh sources without changing the committed receipts:

```sh
python3 human/fetch_sources.py human/source-plan-1.json --cache /tmp/cx004-human-sources --receipt /tmp/cx004-human-fetch-1.json
python3 human/fetch_sources.py human/source-plan-2.json --cache /tmp/cx004-human-sources --receipt /tmp/cx004-human-fetch-2.json
python3 human/fetch_sources.py human/source-plan-3.json --cache /tmp/cx004-human-sources --receipt /tmp/cx004-human-fetch-3.json
python3 human/fetch_sources.py human/source-plan-4.json --cache /tmp/cx004-human-extra --receipt /tmp/cx004-human-fetch-4.json
python3 human/verify.py --cache /tmp/cx004-human-sources --extra /tmp/cx004-human-extra
```

Expected: `PASS 25/25`. The receipt is [verification-full.json](verification-full.json).

```sh
python3 human/replay.py \
  --cache /tmp/cx004-human-sources \
  --extra /tmp/cx004-human-extra \
  --raw-counts /tmp/GSE325735_human_raw_counts.txt.gz
```

The raw-count input is the public [GSE325735 human matrix](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE325nnn/GSE325735/suppl/GSE325735_human_raw_counts.txt.gz), which was already cached from the preceding analysis. Save that source at the specified temporary path or pass its actual location. Review file size and available storage before fetching. Expected: `PASS 10 / 10 byte-identical outputs`. [replay-receipt.json](replay-receipt.json) lists every before/after hash. Fresh environments can pass different cache locations. `replay.py` reruns extraction and rewrites the ten deterministic derived artifacts, then requires their hashes to remain identical; no contract or historical receipt is rewritten. Updated live metadata may require a separately reviewed source revision rather than an exact historical replay.

## Correction history and limitations

The original contract and three XLSX hashes were frozen before the initial numerical inspection. Its join manifest binding was incomplete: the 72-row raw recovery manifest did not contain the normalized full-study metadata required by the extractor. The explicit post-inspection addendum binds that input. Literal NTg matching and count-column presence were repaired and tested. Fig. 4c was discovered later and is an explicit retrospective extension. No amendment is represented as predating inspection.

The 1,027 initial rows and 12 additional rows are published-reference occurrences. Technical replicates, repeated source outputs and cells are not counted as independent donors. The recovered withdrawal comparison uses three equally weighted donor means. Individual recovery reference rows remain unassigned to individual RNA libraries. No clock was applied, no new inferential p-value was computed, and no biological safety or retinal function claim follows from these checks.
