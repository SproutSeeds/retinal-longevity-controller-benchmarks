# Independent calculation and interpretation checks

Separate implementation and review lanes checked the neural, human and source-recovery work. Two maximum-effort Claude Opus 5.5 reviews examined design and interpretation; three GPT-6 Astra maximum-effort lanes implemented and cross-reviewed bounded analyses. Model output was treated as proposed reasoning. Numerical claims were accepted only after checking source artifacts and independent calculations.

The human lane independently recounted 57,317 barcodes and reviewed the paired neural bulk results with 1,791 numerical comparisons and 48 exact/Holm comparisons. A second bulk verifier re-read raw counts using a separate pandas/SciPy implementation and passed 127 checks. Neural analyses and the decomposition extension were replayed from pinned raw inputs, with byte-identical outputs. Public saved-output checks and synthetic adversaries can be rerun independently through `run_checks.py`.

The review changed interpretation in material ways. The human bulk panel is reported as CD24-dominated. The paired mouse overlap-excluded age contrast is reported as Nanog-dependent. Rank and depth sensitivities remain adjacent to primary results. Exact composition partitions retain alternative reference conventions and conditional support denominators.

Several review suggestions were rejected after verification. NANOG and SALL4 were not universally zero in the human matrix. Author labels called `Well` did not establish preparation plate or processing order. Within-library ranks were not assumed immune to compositional change. The four-test Holm family was retained, and later ordered p-values were evaluated against their correct sequential thresholds. A marker rule was not promoted to calibrated rare-state prevalence. These corrections are represented in the tests and detailed result reports.

Independent computational agreement establishes arithmetic and implementation consistency. It does not turn same-study cohorts into independent studies or establish efficacy, biological novelty or clinical safety. The source authors retain credit for their experiments.
