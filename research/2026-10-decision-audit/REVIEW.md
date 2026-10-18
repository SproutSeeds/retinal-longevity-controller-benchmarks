# Independent review and corrections

**Review scope — Verified:** agents assigned to separate lanes reviewed the other lanes' artifacts, source records and biological-unit decisions. This is internal independent implementation/source review, not external peer review. The coordinator integrated the findings and retained the original experimental authorship.

| Review | Evidence | Disposition |
|---|---|---|
| Mouse arithmetic and inference | A separate standard-library calculation reproduced the seven-animal cycle contrast, 13/35 label result and gene/animal omission ranges; the saved verifier passed 877 checks. | No numerical or biological-unit error found. Batch/exchangeability limits, multiplicity and near-zero omission retained. |
| Mouse source and marker scope | Primary paper corroborated sex, paired RNA/ATAC animals, two batches and the author QC count. Fixed bins retain ambiguous/unassigned cells and per-animal support. | The 393-nucleus pipeline discrepancy and heuristic marker identities remain explicit. |
| Human source extraction | Reviewer independently checked 1,039 workbook row occurrences and 5,247 extracted fields against original XLSX sources. | The 1,027 initial occurrences and 12 recovery rows remain separate; no independent-donor count inflation. |
| Human joins and short recovery arithmetic | All 66 accepted validation joins and 12 recovery group memberships matched original GEO key/biological fields; the three donor differences reproduce −10.700069 model-years. | Exact library joins and group-only recovery matches remain distinct; no clock replay claimed. |
| Source-local replicate labels | Twelve NTg validation rows use workbook 1/2 versus GEO 3/4 numbering. | Added a reproducible post-analysis numbering audit and report note. Keys/values unchanged; numbering semantics remain unconfirmed. |
| Xu withdrawal evidence | Thesis figures, narrative and publisher reporting-summary image reviewed independently. | Five-day design and reported return to old baseline supported; named-animal linkage remains heuristic. |
| Minimum missing mouse input | Original integration wording required original LMO counts even if authoritative assignments existed. | Corrected the alternatives: a complete validated assignment table can suffice. Reviewer rechecked PASS. |
| Inherited panel provenance | Frozen panel file contained a relative path from the previous packet. Its declared source hash matched that prior artifact. | Added a byte-identical source copy and [location correction](ocular/PROVENANCE_CORRECTION.md), preserving all five frozen files. Reviewer rechecked PASS. |
| Public reproduction instructions | Human source replay examples contained private-checkout prefixes. | Rewrote examples relative to this public packet with temporary caches; historical receipts remain unchanged. |
| Figures | Coordinator visually inspected both generated PNGs matching the PDF layouts. | Labels, sample units, unsupported marker bin and reference-output limits are visible. |

No blocking arithmetic or biological-unit finding remains from these reviews. The unresolved source labels, timings, QC mismatch, original clock dependencies and target biological readouts remain explicit limitations. Passing the reviews does not promote experiment replacement beyond INCONCLUSIVE.
