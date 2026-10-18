#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["numpy==2.5.4", "scipy==1.18.1", "h5py==3.16.0"]
# ///
"""Run synthetic tests without opening any observed expression matrix."""
import io
import unittest

import percell_audit as audit


def main():
    suite = unittest.defaultTestLoader.discover(str(audit.HERE), pattern="test_percell_audit.py")
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    receipt = {"status": "PASS" if result.wasSuccessful() else "FAIL", "tests_run": result.testsRun,
               "failures": len(result.failures), "errors": len(result.errors),
               "evidence_class": "synthetic_implementation_tests_only", "observed_matrices_opened": False,
               "test_output": stream.getvalue().split("----------------------------------------------------------------------")[0].rstrip(),
               "source_sha256": {name: audit.sha(audit.HERE / name) for name in [
                   "percell_audit.py", "test_percell_audit.py", "percell-contract-proposal.json"]}}
    audit.save(audit.HERE / "PERCELL_TESTS.json", receipt)
    print(f"{receipt['status']}: {result.testsRun} synthetic tests; observed matrices not opened")
    if not result.wasSuccessful():
        print(stream.getvalue())
        raise SystemExit(1)


if __name__ == "__main__":
    main()
