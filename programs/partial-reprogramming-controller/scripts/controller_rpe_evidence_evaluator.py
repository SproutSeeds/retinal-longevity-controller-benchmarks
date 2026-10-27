#!/usr/bin/env python3
"""Evaluate admitted RPE evidence on separate axes; no restoration certification.

The reviewed catalog, not the requesting packet, supplies assay scope and source
bindings. This deterministic extension does not replace the RGC kernel or test
frontier-model reasoning. A source hash authenticates local bytes, not biology.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

CONTROLLER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CONTROLLER_ROOT.parents[1]
DEFAULT_CATALOG = CONTROLLER_ROOT / 'benchmarks/rpe-controller-function-bridge-2026-10-26/ADMISSION_CATALOG.json'
PACKET_KEYS = {'packet_id', 'evidence_ids', 'requested_scope', 'evidence_kind'}


def source_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('source_outside_root_or_missing')
    return path


def finite_number(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('nonfinite_measurement')
    return number


def extract(binding: dict, root: Path) -> dict:
    path = source_path(root, binding['path'])
    if hashlib.sha256(path.read_bytes()).hexdigest() != binding['sha256']:
        raise ValueError('source_hash_mismatch')
    with path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    selected = [row for row in rows if all(row.get(k) == v for k, v in binding['selector'].items())]
    if len(selected) != binding['expected_rows'] or not selected:
        raise ValueError('source_selector_cardinality_mismatch')
    if binding['calculation'] == 'paired_difference':
        values = [finite_number(row[binding['value_b']]) - finite_number(row[binding['value_a']]) for row in selected]
        n = len(values)
    elif binding['calculation'] == 'reported_estimate':
        values = [finite_number(row[binding['value_field']]) for row in selected]
        n = int(selected[0][binding['n_field']])
        if any(int(row[binding['n_field']]) != n for row in selected):
            raise ValueError('mixed_biological_unit_counts')
    elif binding['calculation'] == 'reported_cohort_estimates':
        values = [finite_number(selected[0][field]) for field in binding['value_fields']]
        n = binding['independent_units']
    else:
        raise ValueError('unknown_calculation')
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError('invalid_biological_unit_count')
    positive = sum(v > 0 for v in values)
    negative = sum(v < 0 for v in values)
    direction = 'mixed' if positive and negative else 'increased' if positive else 'decreased' if negative else 'unchanged'
    return {
        'evidence_id': binding['evidence_id'], 'study_id': binding['study_id'],
        'system': binding['system'], 'biological_unit': binding['biological_unit'],
        'independent_units': n, 'assay_id': binding['assay_id'],
        'modality': binding['modality'], 'comparison': binding['comparison'],
        'values': values,
        'mean': None if binding['calculation'] == 'reported_cohort_estimates' else mean(values),
        'summary_type': 'separate_cohort_estimates' if binding['calculation'] == 'reported_cohort_estimates' else binding['calculation'],
        'direction': direction,
        'positive_values': positive, 'negative_values': negative,
        'source_path': binding['path'], 'source_sha256': binding['sha256'],
        'scope_note': binding['scope_note'],
    }


def evaluate_packet(packet: dict, catalog: dict, root: Path = REPO_ROOT) -> dict:
    if set(packet) - PACKET_KEYS:
        raise ValueError('unrecognized_packet_fields')
    if not isinstance(packet.get('packet_id'), str) or not packet['packet_id']:
        raise ValueError('missing_packet_id')
    ids = packet.get('evidence_ids')
    if not isinstance(ids, list) or not ids or any(not isinstance(x, str) for x in ids):
        raise ValueError('missing_or_invalid_evidence_ids')
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate_evidence_ids')
    if packet.get('evidence_kind') not in {'observed', 'synthetic_software_control'}:
        raise ValueError('invalid_evidence_kind')
    if packet.get('requested_scope') not in {'source_system', 'adult_primary_human_ocular'}:
        raise ValueError('invalid_requested_scope')
    if catalog.get('schema') != 'rpe.admission-catalog/1':
        raise ValueError('unknown_admission_catalog')
    bindings = {row['evidence_id']: row for row in catalog['evidence']}
    if len(bindings) != len(catalog['evidence']):
        raise ValueError('ambiguous_catalog_ids')
    if any(eid not in bindings for eid in ids):
        raise ValueError('unadmitted_evidence')
    observations = [extract(bindings[eid], root) for eid in ids]
    synthetic = packet['evidence_kind'] == 'synthetic_software_control'
    molecular = [o for o in observations if o['modality'] == 'RNA']
    functions = [o for o in observations if o['modality'] == 'function']
    function_findings = []
    for obs in functions:
        status = {'increased': 'increased_in_source_assay', 'decreased': 'decreased_in_source_assay',
                  'mixed': 'heterogeneous_in_source_assay', 'unchanged': 'unchanged_in_source_assay'}[obs['direction']]
        function_findings.append({'evidence_id': obs['evidence_id'], 'status': status,
                                  'assay_id': obs['assay_id'], 'independent_units': obs['independent_units'],
                                  'study_id': obs['study_id'], 'system': obs['system'], 'comparison': obs['comparison'],
                                  'biological_unit': obs['biological_unit']})
    transfer_blocked = packet['requested_scope'] == 'adult_primary_human_ocular' and any(
        o['system'] != 'adult_primary_human_RPE' for o in observations)
    supplied_links = catalog.get('reviewed_cross_assay_links', [])
    linked = [link for link in supplied_links if set(link['evidence_ids']).issubset(ids)]
    if linked:
        raise ValueError('cross_assay_link_evaluation_requires_versioned_extension')
    axes = {
        'molecular_observation': 'observed_association_or_response' if molecular else 'not_supplied',
        'function': 'source_assay_observed' if functions else 'not_measured_in_packet',
        'rna_function_link': 'unverified' if molecular and functions else 'not_supplied',
        'withdrawal_persistence': 'not_established_for_adult_human_ocular_restoration',
        'age_restoration': 'not_established',
        'undesirable_states': 'not_assessed_by_these_panels',
        'same_cell_continuity': 'not_established',
    }
    if synthetic:
        axes = {key: 'software_control_only' for key in axes}
        function_findings = []
    reasons = ['calibrated_age_restoration_endpoint_absent', 'compatible_function_after_verified_withdrawal_absent',
               'rare_adverse_state_and_lineage_authority_absent']
    if transfer_blocked:
        reasons.append('source_system_cannot_be_transferred_to_requested_adult_primary_human_scope')
    if molecular and functions:
        reasons.append('condition_or_local_ordinal_labels_do_not_establish_cross_assay_pairing')
    return {
        'schema': 'rpe.evidence-evaluation/1', 'packet_id': packet['packet_id'],
        'engine': 'deterministic_reviewed_evidence_v1',
        'claim_level': 'Verified', 'interpretation_level': 'Heuristic',
        'observations': observations, 'axes': axes, 'function_findings': function_findings,
        'scope_transfer_blocked': transfer_blocked,
        'biological_authority': 'none' if synthetic else 'reviewed_source_scope_only',
        'restoration_verdict': 'unestablished', 'protocol_recommendation_authorized': False,
        'reasons': reasons,
        'certification_scope': 'Local RPE evidence interpretation; no RGC-kernel or clinical certification.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = evaluate_packet(json.loads(args.packet.read_text()), json.loads(args.catalog.read_text()))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f'RPE evidence rejected: {exc}\n')
    rendered = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
