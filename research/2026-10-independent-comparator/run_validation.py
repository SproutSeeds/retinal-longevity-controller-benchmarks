#!/usr/bin/env python3
"""Capture failure-case tests and rerun all three result generators on pinned inputs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name, value): (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main(cache):
    result = subprocess.run(['uv', 'run', 'test_analysis.py'], cwd=HERE, capture_output=True, text=True)
    output = result.stdout + result.stderr
    count = re.search(r'Ran (\d+) tests', output)
    write('TESTS.json', {'status': 'PASS' if result.returncode == 0 else 'FAIL', 'exit_code': result.returncode,
                        'tests': int(count[1]) if count else 0, 'command': 'uv run test_analysis.py',
                        'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'output': output})
    print(output)
    if result.returncode: raise SystemExit(result.returncode)
    names = ['human-results.json', 'synthetic-results.json', 'neural-admission.json']
    before = {name: sha(HERE / name) for name in names}
    for args in [['analyze.py', 'human'], ['analyze.py', 'synthetic'], ['inspect_neural.py']]:
        cmd = ['uv', 'run', *args]
        if args != ['analyze.py', 'synthetic']: cmd += ['--cache', str(cache)]
        subprocess.run(cmd, cwd=HERE, check=True)
    files = [{'name': name, 'before_sha256': before[name], 'after_sha256': sha(HERE / name)} for name in names]
    passed = all(r['before_sha256'] == r['after_sha256'] for r in files)
    write('REPRODUCTION.json', {'status': 'PASS' if passed else 'FAIL', 'files': files,
                               'checked_at_utc': datetime.now(timezone.utc).isoformat(),
                               'scope': 'Byte-identical result JSON from frozen source cache and pinned software; visual exports excluded.',
                               'generator_sha256': {name: sha(HERE / name) for name in ['analyze.py', 'inspect_neural.py']}})
    if not passed: raise SystemExit('Result replay changed')
    print('Result replay: PASS (three identical JSON files)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--cache', required=True, type=Path)
    main(parser.parse_args().cache.resolve())
