#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Verify exact replay of the conditional decomposition from raw RNA."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
from decompose import sha, save_json

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='cx004-decomposition-', dir='/tmp') as tmp:
        out = Path(tmp) / 'results.json'
        subprocess.run([sys.executable, str(HERE / 'decompose.py'), '--cache', str(args.cache),
                        '--output', str(out), '--replay-frozen-hashes'], check=True)
        original, replay = sha(HERE / 'results.json'), sha(out)
    same = original == replay
    save_json(HERE / 'REPRODUCTION.json', {
        'status': 'PASS' if same else 'FAIL', 'result_sha256': original,
        'replay_sha256': replay, 'exact_bytes_equal': same,
        'code_sha256': sha(HERE / 'decompose.py'), 'replay_code_sha256': sha(Path(__file__)),
        'scope': 'Same raw source, frozen definitions, pinned execution environment. Exact replay validates arithmetic, not a biological mechanism.'})
    print('PASS: byte-identical decomposition' if same else 'FAIL: replay differs')
    if not same:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
