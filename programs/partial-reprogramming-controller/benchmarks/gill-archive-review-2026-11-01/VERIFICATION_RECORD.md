# Gill archive review verification

Claim level: **Verified** for retained-file identity and the bounded intake disposition.

Record date: November 1, 2026. Verification status: **PASS**. Biological comparison: **INCONCLUSIVE / DEFERRED**.

Executed hooks, from the repository root:

```sh
python3 programs/partial-reprogramming-controller/benchmarks/gill-archive-review-2026-11-01/verify.py
python3 programs/partial-reprogramming-controller/benchmarks/gill-archive-review-2026-11-01/verify.py --sources programs/partial-reprogramming-controller/.data/gill-source-recovery-2026-11-01
```

The offline hook verifies seven released artifacts, four protected dependencies and the six original frozen input files. The full replay additionally checks four complete source files by byte count, SHA-256 and MD5, with 21 ZIP-member occurrences and both CRC traversals. Three Cambridge source files also agree with freshly retrieved repository metadata. The publisher's accepted-manuscript ZIP has no independently supplied repository checksum; its identity is bound to the retained HTTPS acquisition and SHA-256.

A missing-source-directory probe returns INCONCLUSIVE with exit 2. A separate probe changes one byte while retaining the original source filename and length; it returns FAIL with exit 1. Original source files are unchanged by both probes. Repeated full replay output is byte-identical.

The thesis has 186 PDF pages and zero embedded files. PDF pages 111, 113 and 158 were rendered and visually inspected against extracted text. Article Figure 3 and its first supplement were also visually inspected. Spreadsheet structures and the transparent-reporting document were inspected as inert OOXML. These checks support the source review; the verifier cannot independently establish scientific meaning, investigator intent or global data absence.

The original 13-contrast freeze and prior readiness are byte-preserved. No migration value or predicted sample age was digitized, imputed or computed. No joint pair is admitted, and no historical clock identity is established. Retained source files are required for full replay; the public offline hook reports `full_source_replay: NOT_RUN` explicitly.

The controller publication posture gate and `git diff --check` pass for the scoped release. Public export contains eight files in this dated packet, including its manifest. Original source archives, the full thesis and correspondence are excluded.

Determinism: hashes, inventories and byte-preservation checks are deterministic for the pinned files. Live endpoints and metadata may change. The observed successful download resolves the earlier HTTP 500 path for these exact objects on this date; it does not promise continued availability.
