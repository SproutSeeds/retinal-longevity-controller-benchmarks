#!/usr/bin/env python3
"""Run portable saved-output checks in a temporary copy; no biological downloads."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    if shutil.which('uv') is None:
        parser.error('Install uv first; scientific script dependencies are pinned in each script')
    manifest = json.loads((HERE / 'public-files.json').read_text())
    contract = json.loads((HERE / 'human/posthoc-contract.json').read_text())
    candidates = [HERE.parent / '2026-10-independent-comparator',
                  HERE.parent / 'cx004-independent-comparator-2026-10-18']
    prior = next((p for p in candidates if all((p / n).is_file() for n in contract['prior_sha256'])), None)
    if prior is None:
        parser.error('Keep the preceding independent-comparator packet beside this packet')
    commands = [
        ['uv', 'run', '--script', 'analysis/verify_analysis.py'],
        ['uv', 'run', '--script', 'decomposition/verify_decomposition.py'],
        ['uv', 'run', '--script', 'decomposition/verify_extension.py', '--replay-frozen-hashes'],
        [sys.executable, 'recovery/verify_recovery.py', '--artifacts-only'],
        [sys.executable, 'human/test_marker_audit.py'],
        ['uv', 'run', '--script', 'human/verify_percell.py'],
        [sys.executable, 'human/verify_saved_percell.py'],
        [sys.executable, 'bulk/verify_saved.py'],
        ['uv', 'run', '--python', '3.12', '--with', 'numpy==2.5.4', 'python', 'bulk/test_bulk.py'],
    ]
    rows = []
    with tempfile.TemporaryDirectory(prefix='cx004-public-checks-') as temporary:
        root = Path(temporary)
        packet = root / '2026-10-neural-validation'
        for name in manifest['files']:
            rel = Path(name)
            if rel.is_absolute() or '..' in rel.parts:
                raise ValueError('Unsafe allowlist entry')
            source = HERE / rel
            if source.is_symlink():
                raise ValueError('Public files must not be symlinks')
            target = packet / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        old = root / '2026-10-independent-comparator'
        old.mkdir()
        for name in contract['prior_sha256']:
            shutil.copy2(prior / name, old / name)
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        for command in commands:
            result = subprocess.run(command, cwd=packet, env=environment, text=True,
                                    capture_output=True, timeout=600)
            row = {'command': ['python3' if x == sys.executable else x for x in command],
                   'exit_code': result.returncode, 'status': 'PASS' if result.returncode == 0 else 'FAIL',
                   'stdout': result.stdout.strip(), 'stderr': result.stderr.strip()}
            rows.append(row)
            print(row['status'], ' '.join(row['command']), flush=True)
            if result.returncode:
                print(result.stdout, result.stderr)
                break
    report = {'status': 'PASS' if len(rows) == len(commands) and all(r['exit_code'] == 0 for r in rows) else 'FAIL',
              'scope': 'Saved-output arithmetic and synthetic behavior only; no raw biological input replay.',
              'biological_downloads': False, 'published_files_modified': False, 'checks': rows}
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(report['status'], len(rows), 'portable check commands')
    if report['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
