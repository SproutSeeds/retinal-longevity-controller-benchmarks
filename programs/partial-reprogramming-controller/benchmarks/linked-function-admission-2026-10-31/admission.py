#!/usr/bin/env python3
"""Replay the bounded dataset intake decisions; no outcome or efficacy scoring."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def evaluate(candidate, contract):
    missing = [name for name in contract['required_evidence']
               if candidate.get('evidence', {}).get(name) != 'verified']
    reasons = ['evidence_unresolved:' + name for name in missing]
    if candidate.get('link_level') not in contract['allowed_link_levels']:
        reasons.append('no_admissible_unit_link')
    authority = candidate.get('unit_crosswalk_authority') or {}
    if not (authority.get('url') and authority.get('locator') and len(authority.get('sha256', '')) == 64):
        reasons.append('crosswalk_authority_missing')
    links = candidate.get('unit_crosswalk', [])
    if not links:
        reasons.append('crosswalk_rows_missing')
    rna_ids, function_ids, donors = set(), set(), set()
    for link in links:
        rna, function = link.get('rna', {}), link.get('function', {})
        if not rna.get('sample_id') or not function.get('observation_id'):
            reasons.append('assay_ids_missing')
        if rna.get('sample_id') in rna_ids or function.get('observation_id') in function_ids:
            reasons.append('assay_observation_reused')
        rna_ids.add(rna.get('sample_id'))
        function_ids.add(function.get('observation_id'))
        for field in contract['required_comparison_fields']:
            if not str(rna.get(field) or '').strip() or not str(function.get(field) or '').strip():
                reasons.append('context_missing:' + field)
            elif rna[field] != function[field]:
                reasons.append('context_mismatch:' + field)
        if function.get('measurement_kind') != 'direct_function':
            reasons.append('function_is_not_a_direct_measurement')
        if rna.get('donor_id'):
            donors.add(rna['donor_id'])
    system = candidate.get('system')
    if system not in contract['system_scope']:
        reasons.append('unknown_system_scope')
    if candidate.get('same_cell_continuity_claim', False):
        reasons.append('destructive_assay_cannot_supply_same_cell_continuity')
    reasons = sorted(set(reasons))
    admitted = not reasons
    scope = ('joint_adult_primary' if system == 'adult_primary'
             else 'joint_adult_origin_descendant_only' if system == 'adult_primary_reprogrammed_descendants'
             else 'joint_support_only') if admitted else 'deferred_joint_analysis'
    return {'candidate_id': candidate['candidate_id'], 'decision': scope,
            'joint_analysis_admitted': admitted,
            'adult_primary_admitted': admitted and system == 'adult_primary',
            'linked_observations': len(links) if admitted else 0,
            'independent_donors': len(donors) if admitted else 0,
            'reasons': reasons}


def derive():
    contract = json.loads((HERE / 'ADMISSION_CONTRACT.json').read_text())
    binding = json.loads((HERE / 'CONTRACT_BINDING.json').read_text())
    if hashlib.sha256((HERE / 'ADMISSION_CONTRACT.json').read_bytes()).hexdigest() != binding['contract_sha256']:
        raise ValueError('Frozen admission contract changed')
    candidates = json.loads((HERE / 'CANDIDATES.json').read_text())['candidates']
    if len(candidates) != 8 or len({row['candidate_id'] for row in candidates}) != 8:
        raise ValueError('The bounded eight-candidate roster changed')
    ranked = sorted(candidates, key=lambda row: (row['scope_priority'], row['source_access_priority'],
                                                row['crosswalk_recovery_priority'], row['candidate_id']))
    results = [evaluate(row, contract) for row in ranked]
    table = []
    for rank, (row, result) in enumerate(zip(ranked, results), 1):
        table.append({'acquisition_rank': rank, 'candidate_id': row['candidate_id'], 'study': row['study'],
                      'accession': row['accession'], 'system': row['system'], 'rna_records': row['rna_records'],
                      'function_endpoint': row['function_endpoint'], 'link_level': row['link_level'],
                      'joint_analysis_admitted': result['joint_analysis_admitted'],
                      'decision': result['decision'], 'missing_evidence': ' | '.join(row['missing_evidence']),
                      'next_action': row['next_action']})
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=list(table[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(table)
    record = {'schema': 'linked-function.admission-result/1', 'candidate_count': len(results),
              'joint_admissions': sum(row['joint_analysis_admitted'] for row in results),
              'adult_primary_admissions': sum(row['adult_primary_admitted'] for row in results),
              'ranking_level': 'Heuristic', 'gate_replay_level': 'Verified_after_verification_hook',
              'ranking_status': 'provisional_internal_rank_pending_human_priority_review',
              'results': results}
    return {'ADMISSION_RESULTS.json': json.dumps(record, indent=2, sort_keys=True) + '\n',
            'dataset-shortlist.csv': output.getvalue()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    outputs = derive()
    for name, content in outputs.items():
        path = HERE / name
        if args.verify:
            if not path.is_file() or path.read_text() != content:
                raise ValueError('Admission output changed: ' + name)
        else:
            path.write_text(content)
    print('PASS admission replay: eight reviewed candidates; ranking is heuristic; original biological findings retain source authorship.')


if __name__ == '__main__':
    main()
