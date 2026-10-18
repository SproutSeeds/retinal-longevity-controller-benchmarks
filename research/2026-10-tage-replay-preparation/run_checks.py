#!/usr/bin/env python3
"""Run the actual offline regression suite; optionally record its source hashes."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SOURCES = ["replay.py", "workflow-contract.json", "examples/make_synthetic_demo.py",
           "examples/author-packet-template.json", "tests/test_replay.py", "run_checks.py"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(HERE / "tests"))
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    passed = result.wasSuccessful() and result.testsRun > 0 and not result.skipped
    record = {
        "schema": "cx004.tage_preparation_tests.v1",
        "status": "PASS" if passed else "FAIL",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": "python3 run_checks.py --write" if args.write else "python3 run_checks.py",
        "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
        "source_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in SOURCES},
        "historical_model_executed": False,
        "scope": "Invented fixtures test software behavior; no historical clock or biological model is executed.",
        "test_log": stream.getvalue(),
    }
    if args.write:
        (HERE / "TEST_RESULTS.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(stream.getvalue(), end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
