#!/usr/bin/env python3
"""Offline integrity, roster and executable counterexample verification."""
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import sys
from intake import HERE, frozen, sha


def main():
    manifest = json.loads((HERE / 'ARTIFACT_MANIFEST.json').read_text())
    for name, expected in manifest['files'].items():
        if sha(HERE / name) != expected:
            raise ValueError('Artifact differs: ' + name)
    contract, pairs = frozen()
    donors, counts = defaultdict(set), defaultdict(int)
    for pair in pairs:
        day = int(pair['reprogramming_days'])
        donors[day].add(pair['donor_label'])
        counts[day] += 1
    assert len(pairs) == 13 and len({p['pair_id'] for p in pairs}) == 13
    assert {day: len(labels) for day, labels in donors.items()} == {10: 3, 13: 2, 15: 1, 17: 3}
    assert dict(counts) == {10: 3, 13: 4, 15: 2, 17: 4}
    assert contract['system'] == 'adult_primary_reprogrammed_descendants'
    for command in ([sys.executable, '-B', str(HERE / 'intake.py'), '--verify-readiness'],
                    [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(HERE), '-p', 'test_*.py', '-v']):
        process = subprocess.run(command, capture_output=True, text=True)
        if process.returncode:
            raise RuntimeError(process.stdout + process.stderr)
        print((process.stdout + process.stderr).strip())
    print('PASS: %d bound artifacts; 13 frozen RNA contrasts; empty observed intake; synthetic controls only.' % len(manifest['files']))


if __name__ == '__main__':
    main()
