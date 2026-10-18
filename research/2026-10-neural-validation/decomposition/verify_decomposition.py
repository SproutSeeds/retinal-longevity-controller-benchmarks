#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Recheck observed decomposition arithmetic independently of its generator."""
import json
from pathlib import Path
import unittest
import numpy as np
from decompose import sha, save_json

HERE = Path(__file__).resolve().parent


def main():
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern='test_decomposition.py')
    tests = unittest.TextTestRunner(verbosity=1).run(suite)
    result = json.loads((HERE / 'results.json').read_text())
    checks = []
    def check(name, value):
        checks.append({'name': name, 'status': 'PASS' if bool(value) else 'FAIL'})
    check('frozen_contract_hash', sha(HERE / 'contract.json') == result['contract_sha256'])
    check('generator_hash', sha(HERE / 'decompose.py') == result['code_sha256'])
    check('shared_loader_hash', sha(HERE.parent / 'analysis/neural_analysis.py') == result['analysis_loader_sha256'])
    check('all_predefined_rows_present', len(result['results']) == 16)
    for support in result['support']:
        for animal, row in support['denominators'].items():
            key = f"support:{support['cell_floor']}:{animal}"
            check(key + ':counts', sum(row['counts_by_retained_type'].values()) == row['retained_cells'])
            check(key + ':excluded', row['retained_cells'] + row['excluded_cells'] == row['all_recovered_cells'])
            check(key + ':fraction', abs(row['retained_fraction'] - row['retained_cells'] / row['all_recovered_cells']) < 1e-12)
    for row in result['results']:
        key = f"{row['cell_floor']}:{row['panel']}:{row.get('scale')}"
        if row['status'] != 'available':
            check(key + ':explicit_failure', bool(row.get('reason')))
            continue
        check(key + ':two_lanes', len(row['lane_contrasts']) == 2)
        for lane in row['lane_contrasts']:
            p, q = np.array(lane['fractions_treated']), np.array(lane['fractions_control'])
            a, b = np.array(lane['means_treated']), np.array(lane['means_control'])
            k = key + ':' + lane['lane']
            check(k + ':unit_fractions', abs(p.sum()-1) < 1e-12 and abs(q.sum()-1) < 1e-12)
            check(k + ':total', abs(float(p @ a - q @ b) - lane['total']) < 1e-10)
            check(k + ':composition', abs(float(((p-q)*(a+b)/2).sum())-lane['composition']) < 1e-10)
            check(k + ':within', abs(float(((p+q)*(a-b)/2).sum())-lane['within_type']) < 1e-10)
            check(k + ':direct', abs(lane['total']-lane['direct_cell_average_difference']) < 1e-10)
            check(k + ':sum', abs(lane['total']-lane['composition']-lane['within_type']) < 1e-10)
        for field in ['total', 'composition', 'within_type']:
            check(key + ':mean:' + field,
                  abs(np.mean([x[field] for x in row['lane_contrasts']])-row['equal_lane_mean'][field]) < 1e-12)
    passed = tests.wasSuccessful() and all(x['status'] == 'PASS' for x in checks)
    save_json(HERE / 'VERIFICATION.json', {'status': 'PASS' if passed else 'FAIL', 'checks': checks,
        'check_count': len(checks), 'synthetic_tests': tests.testsRun,
        'result_sha256': sha(HERE / 'results.json'),
        'scope': 'Exact arithmetic, fixed denominators and synthetic software fixtures; no causal or biological validation.'})
    print('PASS' if passed else 'FAIL', len(checks), 'checks;', tests.testsRun, 'synthetic tests')
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
