#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["rdata==1.1.0", "numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Same-study cross-cohort comparator, using separately frozen admission."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from neural_analysis import (COMMON_LIMITS, RawData, aggregate, composition, evaluate_contrast, load_raw_rds,
                             panel_coverage, qc_and_profiles, save_json, sha, verify_committed_file)

HERE = Path(__file__).resolve().parent


def attach_cohort1_admission(metadata, admission):
    required = ['hash.ID', 'orig.ident', 'Treatment', 'Celltype', 'LMO2_classification.global']
    if any(field not in metadata for field in required) or metadata[required].isna().any().any():
        raise ValueError('Cohort1 metadata fields missing')
    if set(metadata['LMO2_classification.global']) != {'Singlet'}:
        raise ValueError('Cohort1 contains non-singlet assignments')
    animals = admission['animals']
    mapping = {row['hash_id']: row for row in animals}
    if len(mapping) != len(animals) or len({a['animal_label'] for a in animals}) != len(animals):
        raise ValueError('Cohort1 animal mapping is ambiguous')
    if set(metadata['hash.ID']) != set(mapping):
        raise ValueError('Cohort1 animal mapping is not complete')
    for sample, group in metadata.groupby('hash.ID', observed=True, sort=True):
        row = mapping[sample]
        if set(group['orig.ident']) != {row['orig_ident']} or set(group['Treatment']) != {row['treatment']}:
            raise ValueError('Cohort1 source metadata conflicts with admission')
        actual_types = {str(k): int(v) for k, v in group['Celltype'].value_counts().items() if v > 0}
        if len(group) != row['cells'] or actual_types != row['celltype_counts']:
            raise ValueError('Cohort1 source cell counts or annotations changed')
    result = metadata.copy()
    for output, field in [('animal_id', 'animal_label'), ('lane', 'lane'),
                          ('treatment', 'treatment'), ('age_group', 'age_group'),
                          ('genotype', 'genotype'), ('sex', 'sex'), ('geo_library', 'geo_library')]:
        result[output] = [mapping[s][field] for s in result['hash.ID']]
    result['celltype'] = result['Celltype'].astype(str)
    return result


def load_cohort1(cache, admission):
    raw = load_raw_rds(Path(cache) / 'svz_iOSKM_cohort1_toshare.rds', admission['source_sha256'])
    raw.metadata = attach_cohort1_admission(raw.metadata, admission)
    return raw


def require_cohort1_freeze(receipt_path, contract_path, parent_contract_path, orthology_path,
                          admission_path, replay_frozen_hashes=False):
    receipt = json.loads(Path(receipt_path).read_text())
    if receipt.get('expression_execution_authorized') is not True:
        raise ValueError('Cohort1 expression execution is not authorized')
    paths = {'contract_sha256': contract_path, 'parent_contract_sha256': parent_contract_path,
             'orthology_sha256': orthology_path, 'admission_sha256': admission_path}
    for key, path in paths.items():
        if sha(path) != receipt[key]:
            raise ValueError('Cohort1 frozen input changed: ' + key)
        if not replay_frozen_hashes:
            verify_committed_file(path, receipt['commit'])
    return receipt


def direction_details(result):
    details = {}
    for method, row in result['methods'].items():
        sign = np.sign(row['mean_difference'])
        omission_values = [o['methods'][method]['mean_difference'] for o in result['single_animal_omissions']
                           if method in o['methods']]
        details[method] = {
            'mean_difference': row['mean_difference'],
            'all_pairwise_differences_share_mean_sign': bool(sign != 0 and all(
                np.sign(x['difference']) == sign for x in row['all_treated_control_differences'])),
            'all_gene_omissions_share_mean_sign': bool(sign != 0 and all(
                np.sign(x) == sign for x in row['single_gene_omission_differences'].values())),
            'all_animal_omissions_available': len(omission_values) == len(result['animals']),
            'all_animal_omissions_share_mean_sign': bool(sign != 0 and len(omission_values) == len(result['animals'])
                                                       and all(np.sign(x) == sign for x in omission_values)),
            'animal_omission_range': [min(omission_values), max(omission_values)] if omission_values else None,
        }
    return details


def run_cohort1(raw, parent_contract, contract, orthology):
    named = parent_contract['cell_types']['named']
    pb = aggregate(raw, named + parent_contract['cell_types']['unresolved'])
    panels = panel_coverage(orthology, raw.genes, parent_contract['thresholds'])
    treated, controls = contract['treated_animals'], contract['control_animals']
    if set(pb.animals) != set(treated + controls):
        raise ValueError('Cohort1 frozen contrast does not cover its four animal identities')
    results = []
    for tier, cells_key, genes_key in [
            ('primary_support', 'primary_min_cells_per_animal_type', 'primary_min_detected_genes_per_animal_type'),
            ('lower_cell_sensitivity', 'sensitivity_min_cells_per_animal_type', 'sensitivity_min_detected_genes_per_animal_type')]:
        for celltype in named:
            for panel_name, panel in panels.items():
                result = evaluate_contrast(pb, celltype, panel, treated, controls, [], parent_contract['thresholds'],
                                           parent_contract['thresholds'][cells_key], parent_contract['thresholds'][genes_key],
                                           'cohort1_single_library_comparator', tier)
                results.append({'panel_name': panel_name, 'comparison': result,
                                'direction_details': direction_details(result)})
    qc, profiles = qc_and_profiles(pb, parent_contract, panels)
    return {'claim_level': 'Verified', 'evidence_class': 'observed_same_study_cross_cohort_comparator',
            'contract_id': contract['id'], 'input_sha256': raw.source_sha256,
            'gene_count': len(raw.genes), 'cell_count': raw.counts.shape[1],
            'independent_animals': len(pb.animals), 'independent_libraries': 1,
            'animal_celltype_qc': qc, 'animal_panel_profiles': profiles,
            'panel_coverage': {name: {k: v for k, v in panel.items() if k != 'indices'} for name, panel in panels.items()},
            'composition': composition(pb, named, [], treated, controls),
            'contrasts': results,
            'scope_limits': COMMON_LIMITS + [
                'Author sample labels encode DOB20180508 for both treated animals and DOB20180501 for both controls. Date of birth differs with condition; litter membership is unconfirmed and is not inferred.',
                'All four animals share one multiplexed library. Cohort1 differs from cohort2 in age range, sex composition, chemistry and annotation collapses; same-direction means are weaker than animal-level consistency.'
            ],
            'readouts': {f'CX004-R0{i}': 'insufficient_signal' for i in range(1, 5)},
            'inference': contract['admission']}


def cross_cohort_comparison(cohort1, cohort2, floor):
    one = {(r['comparison']['support_tier'], r['comparison']['celltype'], r['panel_name']): r for r in cohort1['contrasts']}
    two = {(r['primary']['support_tier'], r['primary']['celltype'], r['panel_name']): r for r in cohort2['contrasts']}
    if set(one) != set(two):
        raise ValueError('Cross-cohort predefined contrast grids differ')
    rows = []
    for key in sorted(one):
        r1, r2 = one[key]['comparison'], two[key]['primary']
        row = {'support_tier': key[0], 'celltype': key[1], 'panel_name': key[2],
               'cohort1_status': r1['status'], 'cohort2_status': r2['status'],
               'status': 'available' if r1['status'] == r2['status'] == 'available' else 'unavailable',
               'cohort1_support_failures': r1['support_failures'], 'cohort2_support_failures': r2['support_failures'],
               'cohort1_direction_details': one[key]['direction_details'],
               'cohort2_direction_details': direction_details(r2), 'methods': {}}
        if row['status'] == 'available':
            for method in ['log2_cpm', 'log2_median_ratio_cpm_equivalent']:
                if method not in r1['methods'] or method not in r2['methods']:
                    row['methods'][method] = {'status': 'normalization_unavailable'}
                    continue
                a, b = r1['methods'][method]['mean_difference'], r2['methods'][method]['mean_difference']
                row['methods'][method] = {'status': 'available', 'cohort1_mean_difference': a,
                                          'cohort2_mean_difference': b,
                                          'same_nonzero_direction': bool(np.sign(a) == np.sign(b) and a != 0 and b != 0),
                                          'both_pass_fixed_floor': bool(abs(a) >= floor and abs(b) >= floor)}
            row['same_direction_and_floor_both_normalizations'] = all(
                m.get('status') == 'available' and m['same_nonzero_direction'] and m['both_pass_fixed_floor']
                for m in row['methods'].values())
        rows.append(row)
    return {'claim_level': 'Verified', 'evidence_class': 'descriptive_cross_cohort_direction_comparison',
            'comparisons': rows, 'descriptive_floor': floor,
            'authority': 'Same-study cross-cohort direction robustness with different age, sex, sequencing chemistry and cluster collapses. Mean direction is reported separately from animal consistency; no exact replication or independent-study claim.',
            'scope_limits': COMMON_LIMITS + ['Cohort1 birth-date tokens differ by condition; this does not establish litter membership.'],
            'readouts': {f'CX004-R0{i}': 'insufficient_signal' for i in range(1, 5)}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--freeze-receipt', type=Path, default=HERE.parent / 'COHORT1_FREEZE.json')
    parser.add_argument('--contract', type=Path, default=HERE / 'cohort1-contract.json')
    parser.add_argument('--parent-contract', type=Path, default=HERE / 'contract.json')
    parser.add_argument('--orthology', type=Path, default=HERE / 'orthology.json')
    parser.add_argument('--admission', type=Path, default=HERE.parent / 'recovery/cohort1-admission.json')
    parser.add_argument('--cohort2-results', type=Path, default=HERE / 'cohort2-results.json')
    parser.add_argument('--output', type=Path, default=HERE / 'cohort1-results.json')
    parser.add_argument('--replay-frozen-hashes', action='store_true',
                        help='Portable replay: verify archived hashes; historical git proof is not rerun.')
    args = parser.parse_args()
    receipt = require_cohort1_freeze(args.freeze_receipt, args.contract, args.parent_contract,
                                      args.orthology, args.admission, args.replay_frozen_hashes)
    contract = json.loads(args.contract.read_text())
    parent_contract = json.loads(args.parent_contract.read_text())
    orthology = json.loads(args.orthology.read_text())
    admission = json.loads(args.admission.read_text())
    raw = load_cohort1(args.cache, admission)
    result = run_cohort1(raw, parent_contract, contract, orthology)
    result['freeze'] = receipt
    result['analysis_code_sha256'] = sha(Path(__file__))
    result['shared_analysis_code_sha256'] = sha(HERE / 'neural_analysis.py')
    save_json(args.output, result)
    pd.DataFrame(result['animal_celltype_qc']).to_csv(args.output.parent / 'cohort1-animal-celltype-qc.tsv', sep='\t', index=False, na_rep='NA')
    pd.DataFrame(result['composition']['rows']).to_csv(args.output.parent / 'cohort1-composition.tsv', sep='\t', index=False, na_rep='NA')
    cohort2 = json.loads(args.cohort2_results.read_text())
    if set(admission['animals'][i]['animal_label'] for i in range(len(admission['animals']))) & {
            row['animal_id'] for row in cohort2['animal_celltype_qc']}:
        raise ValueError('Cohorts share an admitted animal identity')
    comparison = cross_cohort_comparison(result, cohort2, parent_contract['effect_descriptors']['descriptive_floor'])
    comparison['cohort1_result_sha256'] = sha(args.output)
    comparison['cohort2_result_sha256'] = sha(args.cohort2_results)
    save_json(args.output.parent / 'cross-cohort-results.json', comparison)
    save_json(args.output.parent / 'cohort1-execution-verification.json', {
        'mode': 'archived_hash_replay' if args.replay_frozen_hashes else 'committed_freeze_verified',
        'historical_git_proof_rerun': not args.replay_frozen_hashes,
        'scope': 'Exact frozen hashes checked in both modes. Portable replay does not reestablish historical commit chronology.',
        'result_sha256': sha(args.output), 'contract_sha256': sha(args.contract),
        'parent_contract_sha256': sha(args.parent_contract), 'admission_sha256': sha(args.admission),
        'orthology_sha256': sha(args.orthology)})
    available = sum(r['comparison']['status'] == 'available' for r in result['contrasts'])
    print('Cohort1 complete;', len(result['contrasts']), 'predefined type/panel/tier rows;', available, 'available; all failures retained')


if __name__ == '__main__':
    main()
