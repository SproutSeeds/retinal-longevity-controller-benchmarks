#!/usr/bin/env python3
"""Verify the released preparation packet; does not execute a biological model."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    checks = []

    def check(name, ok):
        checks.append({'name': name, 'status': 'PASS' if ok else 'FAIL'})

    manifest = json.loads((HERE / 'artifact-hashes.json').read_text())
    allowlist = json.loads((HERE / 'public-files.json').read_text())['files']
    check('reviewed file list matches hash manifest',
          set(manifest['files']) == set(allowlist) | {'public-files.json'})
    for name, expected in manifest['files'].items():
        relative = Path(name)
        safe = not relative.is_absolute() and '..' not in relative.parts
        path = HERE / relative
        check('safe regular artifact:' + name, safe and path.is_file() and not path.is_symlink())
        if safe and path.is_file() and not path.is_symlink():
            check('sha256:' + name, hashlib.sha256(path.read_bytes()).hexdigest() == expected)
    state = json.loads((HERE / 'status.json').read_text())
    check('historical model unexecuted', state['historical_model_executed'] is False)
    check('historical replication remains pending', state['historical_replication'] == 'PENDING_INPUTS_AND_ADAPTER')
    check('no competing GSTA4 estimate', state['competing_gsta4_age_estimate'] is None)
    check('four human readouts remain open', len(state['human_readouts']) == 4 and
          set(state['human_readouts'].values()) == {'insufficient_signal'})
    check('experiment replacement inconclusive', state['experiment_replacement'] == 'INCONCLUSIVE')
    tests = json.loads((HERE / 'TEST_RESULTS.json').read_text())
    check('recorded tests passed', tests['status'] == 'PASS' and tests['tests_run'] > 0
          and tests['failures'] == 0 and tests['errors'] == 0 and tests['skipped'] == 0)
    check('recorded tests are software only', tests['historical_model_executed'] is False)
    required_test_sources = {'replay.py', 'workflow-contract.json', 'examples/make_synthetic_demo.py',
                             'examples/author-packet-template.json', 'tests/test_replay.py', 'run_checks.py'}
    check('test record covers exact source set', set(tests['source_sha256']) == required_test_sources)
    for name in sorted(required_test_sources):
        check('tested source sha256:' + name,
              tests['source_sha256'].get(name) == hashlib.sha256((HERE / name).read_bytes()).hexdigest())
    result = {'status': 'PASS' if all(x['status'] == 'PASS' for x in checks) else 'FAIL',
              'scope': 'Release integrity and software-preparation bookkeeping only. No historical model execution or biological replication.',
              'passed': sum(x['status'] == 'PASS' for x in checks), 'total': len(checks), 'checks': checks}
    if args.write:
        (HERE / 'VERIFICATION.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'], f"{result['passed']}/{result['total']}")
    for item in checks:
        if item['status'] == 'FAIL':
            print(item['name'])
    raise SystemExit(result['status'] != 'PASS')


if __name__ == '__main__':
    main()
