# RNA and measured function across eight human-cell studies

This reproducible input audit ranks eight existing human-cell studies for a molecular/function comparison. It recovers 177 RNA metadata records, 13 source-labeled within-RNA comparisons in the Gill transient-reprogramming subseries, and ten published RPE functional-line summaries. Full joint RNA/function admission remains deferred for all eight candidates.

The [report](REPORT.md) explains the evidence and next decision. [dataset-shortlist.csv](dataset-shortlist.csv) is the ranked table; [CANDIDATES.json](CANDIDATES.json) preserves each source, scope, missing input and priority rationale. Acquisition rank is Heuristic and measures which evidence to recover next. It is never an efficacy or safety score.

From this folder, run the portable checks with Python 3.12 or later:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 verify.py
```

This verifies artifact hashes, frozen-contract replay, metadata-table consistency and the admission counterexamples. It uses the released source extractions and internal source review, and makes no network requests. The acquisition rank is provisional pending human priority review. It does not independently establish the biological truth of the source papers.

For the original source-byte and extraction checks, install Poppler's `pdftotext`, then run:

```sh
python3 acquire.py
python3 audit_sources.py --verify
```

The restore step downloads only the 27 source records/documents bound in SOURCE_MANIFEST.json into the ignored controller `.data/linked-function-admission-2026-10-31/` cache. No sequencing reads are downloaded. It reuses matching bytes, preserves the seven historical failed attempts, and rejects changed live responses instead of replacing the frozen evidence. Mutable web pages can prevent exact historical source restoration; report that as incomplete source verification. The offline replay remains a separate, narrower check.

CONTRACT_BINDING.json is a public derivative of the original pre-acquisition contract freeze. It retains the contract hash, freeze time and known-outcome selection status; private operating-plan bytes are outside this public binding. Original investigators retain credit for experiments, interventions and published findings. Article license information and unresolved data-reuse scope are explicit in the source/candidate records.
