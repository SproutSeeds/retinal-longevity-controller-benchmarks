#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Replay both admitted cohorts in temporary storage and compare exact bytes."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

from neural_analysis import save_json, sha

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cohort2-cache', type=Path, required=True)
    parser.add_argument('--cohort1-cache', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, default=Path('/tmp'))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='cx004-neural-replay-', dir=args.scratch) as directory:
        replay = Path(directory)
        subprocess.run([sys.executable, str(HERE / 'neural_analysis.py'),
                        '--cache', str(args.cohort2_cache), '--contract', str(HERE / 'contract.json'),
                        '--freeze-receipt', str(HERE.parent / 'FREEZE.json'),
                        '--output', str(replay / 'cohort2-results.json'), '--replay-frozen-hashes'], check=True)
        subprocess.run([sys.executable, str(HERE / 'cohort1_analysis.py'),
                        '--cache', str(args.cohort1_cache), '--output', str(replay / 'cohort1-results.json'),
                        '--cohort2-results', str(replay / 'cohort2-results.json'), '--replay-frozen-hashes'], check=True)
        names = ['cohort2-results.json', 'cohort1-results.json', 'cross-cohort-results.json',
                 'animal-celltype-qc.tsv', 'composition.tsv', 'cohort1-animal-celltype-qc.tsv', 'cohort1-composition.tsv']
        comparisons = [{'file': name, 'reference_sha256': sha(HERE / name), 'replay_sha256': sha(replay / name),
                        'exact_bytes_equal': (HERE / name).read_bytes() == (replay / name).read_bytes()}
                       for name in names]
    result = {'status': 'PASS' if all(r['exact_bytes_equal'] for r in comparisons) else 'FAIL',
              'claim_level': 'Verified' if all(r['exact_bytes_equal'] for r in comparisons) else 'Heuristic',
              'comparisons': comparisons,
              'mode': 'archived_hash_replay', 'historical_git_proof_rerun': False,
              'scope': 'Pinned software and exact same input snapshots on this execution environment. Seven derived artifacts replay byte-identically; execution-mode receipts are excluded because they correctly distinguish historical git checking from portable hash replay.',
              'code_sha256': {name: sha(HERE / name) for name in ['neural_analysis.py', 'cohort1_analysis.py', 'reproduce.py']}}
    save_json(HERE / 'REPRODUCTION.json', result)
    print(result['status'], sum(r['exact_bytes_equal'] for r in comparisons), '/', len(comparisons), 'artifacts byte-identical')
    if result['status'] != 'PASS':
        sys.exit(1)


if __name__ == '__main__':
    main()
