#!/usr/bin/env python3
"""Verify public bytes and actual evaluator behavior; no biological downloads."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTROLLER = ROOT / 'programs/partial-reprogramming-controller'


def execute(arguments):
    result = subprocess.run([sys.executable, *map(str, arguments)], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def main():
    manifest = json.loads((HERE / 'public-package.json').read_text())
    for name, expected in manifest['files'].items():
        path = ROOT / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise AssertionError('Public file differs: ' + name)
    v2 = CONTROLLER / 'benchmarks/rpe-uncertainty-controller-v2-2026-10-26'
    print(execute([v2 / 'verify.py', '--verify']).strip())
    bridge = CONTROLLER / 'benchmarks/rpe-controller-function-bridge-2026-10-26'
    records = json.loads((bridge / 'EVALUATIONS.json').read_text())['evaluations']
    for record in records:
        actual = json.loads(execute([CONTROLLER / 'scripts/controller_rpe_evidence_evaluator.py',
                                    '--packet', bridge / 'packets' / (record['packet_id'] + '.json'),
                                    '--catalog', bridge / 'ADMISSION_CATALOG.json']))
        if actual != record['evaluation']:
            raise AssertionError('Earlier CLI output changed: ' + record['packet_id'])
    linked = CONTROLLER / 'benchmarks/linked-function-admission-2026-10-31'
    print(execute([linked / 'verify.py']).strip())
    gill = CONTROLLER / 'benchmarks/gill-migration-comparison-2026-10-31'
    print(execute([gill / 'verify.py']).strip())
    recovered = CONTROLLER / 'benchmarks/gill-matrix-recovery-2026-10-31'
    print(execute([recovered / 'verify.py']).strip())
    archives = CONTROLLER / 'benchmarks/gill-archive-review-2026-11-01'
    print(execute([archives / 'verify.py']).strip())
    alternative = CONTROLLER / 'benchmarks/alternative-function-screen-2026-11-01'
    print(execute([alternative / 'verify.py']).strip())
    calibration = CONTROLLER / 'benchmarks/sturm-senmayo-calibration-2026-11-01'
    print(execute([calibration / 'verify.py']).strip())
    assignment_recheck = CONTROLLER / 'benchmarks/gse350289-assignment-recheck-2026-11-01'
    print(execute([assignment_recheck / 'verify.py']).strip())
    download_recovery = CONTROLLER / 'benchmarks/gse350289-download-recovery-2026-11-01'
    print(execute([download_recovery / 'verify.py']).strip())
    print('PASS public replay: %d released files; 9 v2 packets; %d earlier packets; no raw-data or model download.' % (len(manifest['files']), len(records)))


if __name__ == '__main__':
    main()
