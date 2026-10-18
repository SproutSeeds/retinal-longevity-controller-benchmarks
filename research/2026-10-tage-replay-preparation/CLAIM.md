# Claim: historical-clock preparation

Claim level: **Verified, software scope only**, within the recorded checks.

Scope: the independently written input validator, frozen comparison plan and sample-keyed numerical comparator can be checked using synthetic cases. A passing software check establishes its named behavior. It does not establish the origin of supplied artifacts, execute a historical tAge model, reproduce a biological result, or close a human recovery readout.

Scientific state: historical model execution is pending; no competing GSTA4 age estimate exists. All four CX004 human readouts remain insufficient_signal. Experiment replacement remains INCONCLUSIVE.

Verification hook: from this packet directory, run `python3 run_checks.py` and `python3 verify.py`. The commands and examples in WORKFLOW.md exercise the same public interface. Expected outcome: the software verification passes, synthetic examples remain marked synthetic, and the historical execution gate remains blocked. Determinism: validation and synthetic comparisons use fixed fixtures and no model fitting, randomness, network or biological download. Temporary paths and recorded timestamps vary without changing the assertions.

Verification records: [VERIFICATION.json](VERIFICATION.json) and [TEST_RESULTS.json](TEST_RESULTS.json) bind the checked code and test outcomes. These records attest software preparation only.

Original credit: Lu and colleagues own the experimental work and reported predictions; clock developers own their models. This packet owns only its new validation code, documentation and review.
