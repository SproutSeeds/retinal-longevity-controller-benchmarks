#!/usr/bin/env python3
"""Run every frozen v2 acceptance packet through the actual executable."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ENGINE = ROOT / 'scripts/controller_rpe_uncertainty_evaluator_v2.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    freeze = json.loads((HERE / 'FREEZE.json').read_text())
    for name, digest in freeze['inputs'].items():
        if sha(HERE / name) != digest:
            raise ValueError('Frozen input changed: ' + name)
    execution = HERE / 'EXECUTION.json'
    if not execution.exists():
        if args.verify:
            raise ValueError('Execution record is missing')
        execution.write_text(render({'started_at_utc': datetime.now(timezone.utc).isoformat(),
            'frozen_at_utc': freeze['frozen_at_utc'], 'schema_sha256': sha(HERE / 'SCHEMA.json'),
            'scope': 'First actual version-2 CLI acceptance run after frozen schema, source bindings and expected cases.'}))
    cases = json.loads((HERE / 'CASES.json').read_text())
    evaluations = []
    unique_observations = {}
    for case in cases['valid_packets']:
        pid = case['packet_id']
        proc = subprocess.run([sys.executable, str(ENGINE), '--packet', str(HERE / 'packets' / (pid + '.json')),
            '--catalog', str(HERE / 'ADMISSION_CATALOG.json')], capture_output=True, text=True, check=True)
        result = json.loads(proc.stdout)
        checks = {'resolution_counts': result['resolution_counts'] == case['resolution_counts'],
                  'function_statuses': [r['status'] for r in result['function_findings']] == case['function_statuses'],
                  'source_scope': result['scope_transfer_blocked'] == case['scope_transfer_blocked'],
                  'RNA_function_join': result['axes']['rna_function_link'] == case['rna_function_link'],
                  'restoration_unestablished': result['restoration_verdict'] == 'unestablished',
                  'no_protocol_authority': result['protocol_recommendation_authorized'] is False,
                  'source_uncertainty_axis': result['axes']['uncertainty'] == ('software_control_only' if pid == 'SOFTWARE_CONTROL' else 'explicit_source_limits_preserved')}
        if pid == 'SOFTWARE_CONTROL':
            checks['software_only_authority'] = result['biological_authority'] == 'none' and set(result['axes'].values()) == {'software_control_only'}
        if not all(checks.values()):
            raise AssertionError((pid, checks))
        evaluations.append({'packet_id': pid, 'status': 'PASS', 'checks': checks, 'evaluation': result})
        if pid not in {'SOFTWARE_CONTROL', 'UNLINKED_RNA_FUNCTION'}:
            for observation in result['observations']:
                if observation['evidence_id'] in unique_observations:
                    raise AssertionError('Duplicate canonical observation')
                unique_observations[observation['evidence_id']] = observation
    comparison = []
    for eid, observation in sorted(unique_observations.items()):
        u = observation['uncertainty']
        interval = u['interval']
        comparison.append({'evidence_id': eid, 'study': observation['study_id'], 'modality': observation['modality'],
            'estimate': format(u['estimate'], '.17g'), 'v1_direction': observation['direction'], 'v2_resolution': u['resolution'],
            'interval_status': interval['status'], 'ci95_low': '' if interval['low'] is None else format(interval['low'], '.17g'),
            'ci95_high': '' if interval['high'] is None else format(interval['high'], '.17g'), 'unit_pattern': u['unit_pattern'],
            'unit_vector_entries': len(u['unit_vector']),
            'normalization_agreement': u['normalization'].get('direction_agreement', 'not_applicable'),
            'omission_stability': u['omissions'].get('direction_and_precision_preserved', 'not_admitted'),
            'dependence': u['source_dependence'], 'RNA_function_join': u['rna_function_join']['status'],
            'status': 'known_outcome_secondary_software_comparison'})
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(comparison[0]), delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerows(comparison)
    result = {'status': 'PASS', 'claim_level': 'Verified', 'interpretation_level': 'Heuristic',
        'valid_packets': len(evaluations), 'unique_source_observations': len(unique_observations),
        'unique_resolution_counts': dict(sorted(Counter(o['uncertainty']['resolution'] for o in unique_observations.values()).items())),
        'engine_sha256': sha(ENGINE), 'schema_sha256': sha(HERE / 'SCHEMA.json'),
        'known_outcome_suite': True, 'frontier_model_evaluation': False, 'held_out_performance_estimate': False,
        'biological_replication': False, 'restoration_verdict': 'unestablished', 'wet_lab_replacement': 'INCONCLUSIVE'}
    outputs = {'EVALUATIONS.json': render({'schema': 'rpe.uncertainty-regression-run/2', 'evaluations': evaluations,
                    'engine_sha256': sha(ENGINE), 'schema_sha256': sha(HERE / 'SCHEMA.json')}),
               'before-after.tsv': stream.getvalue(), 'RESULT.json': render(result)}
    for name, content in outputs.items():
        if args.verify:
            if (HERE / name).read_text() != content:
                raise ValueError('Reproduction mismatch: ' + name)
        else:
            (HERE / name).write_text(content)
    print(f"PASS v2 CLI: {len(evaluations)} frozen packets; {len(unique_observations)} distinct source observations; {result['unique_resolution_counts']}")


if __name__ == '__main__':
    main()
