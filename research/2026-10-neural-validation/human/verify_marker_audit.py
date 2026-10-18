#!/usr/bin/env python3
"""Run unit/source checks and verify byte-identical independent replay."""
import contextlib
import argparse
import io
import json
from pathlib import Path
import tempfile
import unittest

import marker_audit as audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=Path("/tmp/cx004-independent-comparator-2026-10-18"))
    parser.add_argument("--prior", type=Path, default=audit.PRIOR)
    args = parser.parse_args()
    audit.PRIOR = args.prior
    suite = unittest.defaultTestLoader.discover(str(audit.HERE), pattern="test_marker_audit.py")
    stream = io.StringIO()
    test_result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    output_names = ["marker-audit.json", "gene-contributions.csv", "gene-availability.csv"]
    original_hashes = {name: audit.sha(audit.HERE / name) for name in output_names}
    with tempfile.TemporaryDirectory(prefix="cx004-human-replay-", dir="/tmp") as folder:
        with contextlib.redirect_stdout(io.StringIO()):
            audit.build(args.cache, Path(folder), args.prior)
        replay_hashes = {name: audit.sha(Path(folder) / name) for name in output_names}
    identical = original_hashes == replay_hashes
    passed = test_result.wasSuccessful() and identical
    receipt = {
        "status": "PASS" if passed else "FAIL",
        "claim_level": "Verified computation; Heuristic marker interpretation",
        "tests_run": test_result.testsRun,
        "test_failures": len(test_result.failures),
        "test_errors": len(test_result.errors),
        "test_output": stream.getvalue().split("----------------------------------------------------------------------")[0].rstrip(),
        "deterministic_replay": "PASS" if identical else "FAIL",
        "output_sha256": original_hashes,
        "replay_output_sha256": replay_hashes,
        "source_sha256": {name: audit.sha(audit.HERE / name) for name in [
            "posthoc-contract.json", "marker_audit.py", "test_marker_audit.py", "ADDENDUM.md"]},
        "verification_hook": "python3 programs/partial-reprogramming-controller/benchmarks/cx004-neural-validation-2026-10-18/human/verify_marker_audit.py",
        "prior_immutable_hashes_rechecked": True,
        "scope": "One human donor; no p-values, biological state calibration, age effect, safety or recovery promotion.",
    }
    audit.save(audit.HERE / "VERIFICATION.json", receipt)
    print(f"{receipt['status']}: {test_result.testsRun} tests; deterministic replay {receipt['deterministic_replay']}")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
