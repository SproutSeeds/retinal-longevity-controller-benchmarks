# Expression and neural-data update

Four-slide addendum to the October 17 retinal public-data presentation, dated October 18, 2026 UTC. The PDF is the shareable render; the PowerPoint contains editable text, two native tables and one native chart with an embedded value workbook. `spoken-notes.txt` and `spoken-notes.md` contain identical narration. Sources are in the PowerPoint speaker notes and `slide-sources.json`.

The human result is a one-donor expression comparison. Neural work is metadata/count admission; neural expression contrasts remain pending. Sampling results are synthetic. All four late human readouts remain insufficient_signal, with experiment replacement INCONCLUSIVE.

Rebuild with `build.mjs`, Artifact Tool 2.8.59 and the corresponding presentation validation helpers. Set absolute `SKILL_DIR`, `DECK_WORKSPACE`, `DATA_DIR`, `RUNTIME_NODE_MODULES`, `RUNTIME_BIN_DIR` and `RUNTIME_PYTHON`. Link the installed runtime's node_modules in a private build directory, copy this builder there, and run it with that runtime's Node executable. `DATA_DIR` is this research folder's parent of `presentation/`. Use a fresh output directory for each revision. The builder requires the installed runtime rather than installing substitutes.

The authored font is Liberation Sans. PDF conversion used LibreOffice with an explicit font configuration pointing to the runtime's installed font directory. Every PDF page was rendered and visually inspected; all PDF fonts are embedded. Structural/import checks, native-table/chart checks, narration equality and file hashes are in `QA.json`. Desktop PowerPoint editing was not exercised. Charts embed displayed values rounded to three decimals, while scientific JSON retains full precision.
