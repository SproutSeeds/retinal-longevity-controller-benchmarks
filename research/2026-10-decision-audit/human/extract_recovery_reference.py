#!/usr/bin/env python3
"""Audit newly identified published 5-on/2-off reference outputs descriptively."""
import argparse
import collections
import csv
import hashlib
import json
import statistics
from pathlib import Path
from extract_reference import rows_from_sheet
from xlsx_cells import read_workbook

HERE = Path(__file__).resolve().parent


def derive(workbook, manifest):
    contract = json.loads((HERE / 'recovery-reference-addendum.json').read_text())
    if hashlib.sha256(workbook.read_bytes()).hexdigest() != contract['source_sha256']:
        raise ValueError('Changed recovery reference workbook')
    binding = json.loads((HERE / 'reference-input-addendum.json').read_text())['join_manifest']
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != binding['sha256']:
        raise ValueError('Changed reference join manifest')
    metadata = json.loads(manifest.read_text())['samples']
    sheet = next(s for s in read_workbook(workbook) if s['sheet'] == '4c')
    rows = rows_from_sheet(sheet, 1)
    grouped = collections.defaultdict(list)
    for row in rows:
        val = row['values']
        row.update(source='srsf1-source-fig4.xlsx', sheet='4c',
                   source_sha256=contract['source_sha256'])
        row['reported_age_difference_residual_years'] = val['AgeDiff'] - (val['Predicted_age'] - val['Line_age'])
        if abs(row['reported_age_difference_residual_years']) > 1e-10:
            raise ValueError('Age difference arithmetic mismatch')
        if 'SampleID' in val:
            raise ValueError('Unexpected new sample identifier; review join rules')
        grouped[(val['Line'], val['Gene'])].append(row)
    mappings = {'M55': 'AG12657', 'M68': 'AG13369', 'M79': 'AG16359'}
    groups = []
    for (line, construct), members in sorted(grouped.items()):
        genotype = 'mTagBFP2' if construct == 'BFP' else construct
        eligible = [m for m in metadata if m['donor_or_line'] == mappings[line]
                    and m['genotype'] == genotype and m['on_days_geo'] == 5
                    and m['off_days_geo'] == 2]
        groups.append({'line': line, 'donor': mappings[line], 'construct': construct,
                       'reference_rows': [r['row'] for r in members],
                       'technical_replicates': [r['values']['Rep'] for r in members],
                       'mean_reported_age_years': statistics.mean(r['values']['Predicted_age'] for r in members),
                       'mean_reported_age_difference_years': statistics.mean(r['values']['AgeDiff'] for r in members),
                       'geo_libraries': sorted(m['library'] for m in eligible),
                       'geo_accessions': sorted(m['sample_id'] for m in eligible),
                       'mapping_status': 'donor_construct_schedule_group_only',
                       'individual_reference_to_library_join': False})
    contrasts = []
    for line in sorted(mappings):
        selection = {g['construct']: g for g in groups if g['line'] == line}
        contrasts.append({'line': line, 'donor': mappings[line],
                          'reported_reference_srsf1_minus_bfp_years':
                          selection['SRSF1']['mean_reported_age_years'] - selection['BFP']['mean_reported_age_years']})
    return {'schema_version': 1, 'claim_level': 'Verified',
            'claim': 'Extraction and arithmetic of published reference outputs only',
            'analysis_status': 'retrospective_descriptive_audit',
            'biological_units': 3, 'technical_reference_rows': len(rows),
            'induction_days': 5, 'off_days': 2,
            'clock_replayed': False, 'new_p_values_computed': False,
            'rows': rows, 'groups': groups, 'donor_reference_contrasts': contrasts,
            'equal_donor_mean_reported_difference_years': statistics.mean(
                r['reported_reference_srsf1_minus_bfp_years'] for r in contrasts)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workbook', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, default=HERE / 'reference-join-manifest.json')
    args = parser.parse_args()
    result = derive(args.workbook, args.manifest)
    (HERE / 'recovery-reference-audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    with (HERE / 'recovery-reference-groups.csv').open('w', newline='') as handle:
        fields = ['line', 'donor', 'construct', 'mean_reported_age_years', 'mean_reported_age_difference_years', 'geo_libraries', 'mapping_status']
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for group in result['groups']:
            writer.writerow({k: '|'.join(group[k]) if isinstance(group[k], list) else group[k] for k in fields})
    print('Published reference rows:', result['technical_reference_rows'])
    print('Independent donor lines:', result['biological_units'])
    print('Mean reported SRSF1 minus BFP:', result['equal_donor_mean_reported_difference_years'])
    for row in result['donor_reference_contrasts']:
        print(row)


if __name__ == '__main__':
    main()
