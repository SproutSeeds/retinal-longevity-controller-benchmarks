# Cell-cycle responses and the missing recovery measurement

[Presentation PDF](retinal-validation-results.pdf) · [editable PowerPoint](retinal-validation-results.pptx) · [spoken notes](spoken-notes.txt)

The six slides summarize the paired mouse neural result, animal sensitivity across tissue cohorts, human marker concentration, human co-detection/depth sensitivity, conditional composition and the next existing-data target. Source links are in speaker notes and [slide-sources.json](slide-sources.json). The PDF preserves the inspected layout; the PowerPoint retains three native charts with embedded data workbooks and two editable tables.

Figures are computed from the released results. The chart values are rounded to eight decimal places for native workbook compatibility; unrounded analysis values remain in the result JSON files. The plain-text and Markdown spoken companions contain identical narration. They are presentation language, not additional evidence.

`build.mjs` uses the installed `@oai/artifact-tool` presentation runtime and the presentation skill's finalizer. It expects absolute `SKILL_DIR`, `DECK_WORKSPACE`, `DATA_DIR`, `RUNTIME_PYTHON` and `RUNTIME_NODE_MODULES` environment values, with the runtime module directory resolvable by Node. Use a fresh build workspace for each revision. The public numerical analysis and figure reproduction do not require this runtime.
