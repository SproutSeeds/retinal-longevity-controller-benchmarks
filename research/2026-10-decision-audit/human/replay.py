#!/usr/bin/env python3
"""Re-extract all numerical outputs and require byte-identical files."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUTS = ['reference-output-audit.json', 'recovery-reference-audit.json',
           'recovery-reference-groups.csv', 'validation-reference-joins.csv',
           'SOURCES.json', 'complete-workbook-inventory.json', 'search-ledger.json',
           'chronology-audit.json', 'clock-readiness.json', 'raw-counts-structure.json']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--extra', type=Path, required=True)
    parser.add_argument('--raw-counts', type=Path, required=True)
    parser.add_argument('--write', type=Path)
    args = parser.parse_args()
    before = {f: hashlib.sha256((HERE / f).read_bytes()).hexdigest() for f in OUTPUTS}
    commands = [
        [sys.executable, str(HERE / 'extract_reference.py'), '--cache', str(args.cache), '--manifest', str(HERE / 'reference-join-manifest.json')],
        [sys.executable, str(HERE / 'extract_recovery_reference.py'), '--workbook', str(args.cache / 'srsf1-source-fig4.xlsx')],
        [sys.executable, str(HERE / 'build_audit.py'), '--cache', str(args.cache), '--extra', str(args.extra), '--raw-counts', str(args.raw_counts)],
    ]
    for command in commands:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
    after = {f: hashlib.sha256((HERE / f).read_bytes()).hexdigest() for f in OUTPUTS}
    result = {'schema_version': 1, 'status': 'PASS' if before == after else 'FAIL',
              'scope': 'Byte-identical replay of ten derived source-audit and reference-arithmetic files',
              'outputs': [{'path': f, 'before': before[f], 'after': after[f], 'identical': before[f] == after[f]} for f in OUTPUTS]}
    if args.write:
        args.write.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'], sum(x['identical'] for x in result['outputs']), '/', len(OUTPUTS), 'byte-identical outputs')
    raise SystemExit(0 if result['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
