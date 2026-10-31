#!/usr/bin/env python3
"""Source-bound, descriptive Gill intake. No clock training or biological certification."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen():
    binding = json.loads((HERE / 'FREEZE.json').read_text())
    for name, expected in binding['files'].items():
        if sha(HERE / name) != expected:
            raise ValueError('Frozen input changed: ' + name)
    contract = json.loads((HERE / 'ANALYSIS_CONTRACT.json').read_text())
    with (HERE / 'rna-pairs.tsv').open(newline='') as stream:
        pairs = list(csv.DictReader(stream, delimiter='\t'))
    return contract, pairs


def load_packet(path, templates=False):
    contract, _ = frozen()
    suffix = '.template' if templates else ''
    tables = {}
    hashes = {}
    for name, columns in contract['table_columns'].items():
        file = path / (name + suffix + '.tsv')
        with file.open(newline='') as stream:
            reader = csv.DictReader(stream, delimiter='\t')
            if reader.fieldnames != columns:
                raise ValueError('Unexpected TSV columns: ' + name)
            tables[name] = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in tables[name]):
            raise ValueError('Malformed TSV row: ' + name)
        hashes[file.name] = sha(file)
    file = path / ('evidence' + suffix + '.json')
    hashes[file.name] = sha(file)
    return {**tables, 'evidence': json.loads(file.read_text()), 'base': path, 'input_sha256': hashes}


def evaluate(bundle, allow_synthetic=False):
    contract, pairs = frozen()
    issues = []
    evidence = bundle['evidence']
    synthetic = evidence.get('fixture_kind') == 'synthetic_control'
    if evidence.get('fixture_kind') not in ('observed', 'synthetic_control'):
        issues.append('unknown_fixture_kind')
    if synthetic and not allow_synthetic:
        issues.append('synthetic_not_observed_evidence')
    if evidence.get('schema') != 'gill.migration-input/1':
        issues.append('wrong_input_schema')
    review = evidence.get('review', {})
    if review.get('status') != 'verified' or any(not str(review.get(k, '')).strip() for k in ('reviewer', 'reviewed_at', 'basis')):
        issues.append('source_and_coverage_review_pending')
    if evidence.get('analysis_permitted') is not True:
        issues.append('analysis_permission_unresolved')
    sources = {}
    base = Path(bundle['base']).resolve()
    for source in evidence.get('sources', []):
        sid = source.get('source_id')
        if not sid or sid in sources:
            issues.append('missing_or_duplicate_source_id')
        sources[sid] = source
        if any(not str(source.get(k, '')).strip() for k in contract['evidence_review']['source_fields']):
            issues.append('source_provenance_incomplete')
        if source.get('role') not in contract['evidence_review']['roles']:
            issues.append('unknown_source_role')
        if not str(source.get('url', '')).startswith('https://'):
            issues.append('source_url_missing')
        path = (base / str(source.get('path', ''))).resolve()
        if not path.is_relative_to(base) or not path.is_file():
            issues.append('source_path_invalid')
        elif sha(path) != source.get('sha256'):
            issues.append('source_hash_mismatch')
        if source.get('role') == 'migration' and source.get('granularity') != 'technical_replicate_speed':
            issues.append('migration_granularity_not_admitted')

    def authority(row, role):
        if sources.get(row.get('source_id'), {}).get('role') != role:
            issues.append('row_authority_missing:' + role)

    expected = {}
    for pair in pairs:
        for arm, condition in [('control', 'negative_control'), ('treated', 'transiently_reprogrammed')]:
            expected[pair[arm + '_rna_id']] = {k: pair[k] for k in ('donor_label', 'reprogramming_days', 'experiment')}
            expected[pair[arm + '_rna_id']]['condition'] = condition
    crosswalk, cultures = {}, {}
    for row in bundle['crosswalk']:
        authority(row, 'crosswalk')
        if any(not str(row.get(k, '')).strip() for k in contract['table_columns']['crosswalk']):
            issues.append('crosswalk_field_missing')
        rid, cid = row.get('rna_id'), row.get('function_culture_id')
        if rid not in expected:
            issues.append('unknown_rna_id')
        elif any(row.get(k) != value for k, value in expected[rid].items()):
            issues.append('crosswalk_frozen_context_mismatch')
        if rid in crosswalk or cid in cultures:
            issues.append('rna_or_culture_reused')
        if row.get('link_level') not in contract['unit_policy']['allowed_links']:
            issues.append('link_level_not_admitted')
        if row.get('link_level') == 'same_parent_culture_aliquots' and row.get('rna_parent_culture_id') != cid:
            issues.append('same_parent_id_mismatch')
        crosswalk[rid], cultures[cid] = row, row
    observations, observation_ids = defaultdict(list), set()
    for row in bundle['migration']:
        authority(row, 'migration')
        if any(not str(row.get(k, '')).strip() for k in contract['table_columns']['migration']):
            issues.append('migration_field_missing')
        oid, cid = row.get('observation_id'), row.get('function_culture_id')
        if not oid or oid in observation_ids:
            issues.append('observation_reused_or_missing')
        observation_ids.add(oid)
        if cid not in cultures:
            issues.append('unmapped_function_culture')
        elif any(row.get(k) != cultures[cid].get(k) for k in contract['unit_policy']['context_fields']):
            issues.append('rna_function_context_mismatch')
        if row.get('speed_units') != contract['primary_function']['units']:
            issues.append('migration_units_incompatible')
        try:
            value = float(row.get('speed', ''))
            if not math.isfinite(value):
                raise ValueError()
            observations[cid].append(value)
        except (ValueError, TypeError):
            issues.append('migration_value_invalid')
    ages = {}
    for row in bundle['molecular_age']:
        authority(row, 'molecular_age')
        rid = row.get('rna_id')
        if rid not in expected or rid in ages:
            issues.append('molecular_rna_unknown_or_reused')
        if row.get('clock_id') != contract['primary_molecular']['clock_id']:
            issues.append('molecular_clock_mismatch')
        try:
            value = float(row.get('age_years', ''))
            if not math.isfinite(value):
                raise ValueError()
            ages[rid] = value
        except (ValueError, TypeError):
            issues.append('molecular_value_invalid')
    excluded = evidence.get('excluded_pairs', {})
    if set(excluded) - {p['pair_id'] for p in pairs}:
        issues.append('unknown_excluded_pair')
    coverage, eligible = [], []
    for pair in pairs:
        pid = pair['pair_id']
        ids = [pair['control_rna_id'], pair['treated_rna_id']]
        complete = all(rid in crosswalk and rid in ages and observations.get(crosswalk[rid]['function_culture_id']) for rid in ids)
        if pid in excluded:
            reason = excluded[pid]
            authority(reason, 'crosswalk')
            if not str(reason.get('reason', '')).strip() or complete:
                issues.append('exclusion_unjustified_or_complete_pair_excluded')
            status = 'source_excluded'
        elif complete:
            status = 'complete'
            eligible.append(pair)
            if any(crosswalk[ids[0]][k] != crosswalk[ids[1]][k] for k in ('withdrawal_context', 'collection_context')):
                issues.append('control_treated_collection_mismatch')
        else:
            status = 'missing_required_inputs'
            issues.append('pair_coverage_unresolved:' + pid)
        coverage.append({'pair_id': pid, 'status': status, 'reason': excluded.get(pid, {}).get('reason', '')})
    if not eligible:
        issues.append('no_complete_pairs')
    result = {'schema': 'gill.migration-readiness/1', 'claim_level': 'Verified',
              'verification_scope': 'software_and_roster_only',
              'decision': 'DEFERRED' if issues else 'READY_FOR_DESCRIPTIVE_COMPARISON',
              'input_kind': 'synthetic_control' if synthetic else 'observed',
              'biological_validation': False, 'system': contract['system'],
              'frozen_pair_count': len(pairs), 'rna_donor_labels_in_frozen_roster': 3,
              'migration_observations_received': len(bundle['migration']),
              'molecular_values_received': len(bundle['molecular_age']),
              'input_sha256': bundle.get('input_sha256', {}),
              'issues': sorted(set(issues)), 'coverage': coverage,
              'pair_effects': [], 'donor_effects': [], 'duration_summaries': []}
    if issues:
        return result
    groups = defaultdict(list)
    for pair in eligible:
        control, treated = pair['control_rna_id'], pair['treated_rna_id']
        cv, tv = [observations[crosswalk[rid]['function_culture_id']] for rid in (control, treated)]
        age_delta = ages[treated] - ages[control]
        speed_delta = mean(tv) - mean(cv)
        if not math.isfinite(age_delta) or not math.isfinite(speed_delta):
            raise ValueError('Non-finite computed difference; calculation stopped')
        row = {**pair, 'delta_age_years': age_delta, 'delta_speed_um_per_hour': speed_delta,
               'control_technical_observations': len(cv), 'treated_technical_observations': len(tv),
               'molecular_lower': age_delta < 0, 'migration_higher': speed_delta > 0}
        result['pair_effects'].append(row)
        groups[(pair['reprogramming_days'], pair['donor_label'])].append(row)
    for (duration, donor), rows in sorted(groups.items()):
        result['donor_effects'].append({'reprogramming_days': duration, 'donor_label': donor,
                                       'pair_count': len(rows), 'delta_age_years': mean(r['delta_age_years'] for r in rows),
                                       'delta_speed_um_per_hour': mean(r['delta_speed_um_per_hour'] for r in rows)})
    for duration in contract['durations_days']:
        rows = [r for r in result['donor_effects'] if int(r['reprogramming_days']) == duration]
        if not rows:
            continue
        summary = {'reprogramming_days': duration, 'independent_donor_count': len(rows), 'leave_one_donor_out': []}
        for field in ('delta_age_years', 'delta_speed_um_per_hour'):
            values = [r[field] for r in rows]
            summary['mean_' + field] = mean(values)
            summary['range_' + field] = [min(values), max(values)]
        for row in rows if len(rows) >= 2 else []:
            others = [r for r in rows if r['donor_label'] != row['donor_label']]
            summary['leave_one_donor_out'].append({'excluded_donor': row['donor_label'], 'remaining_donor_count': len(others),
                                                  **{field: mean(r[field] for r in others) for field in ('delta_age_years', 'delta_speed_um_per_hour')}})
        result['duration_summaries'].append(summary)
    return result


def render(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-readiness', action='store_true')
    args = parser.parse_args()
    result = evaluate(load_packet(args.input_dir or HERE, templates=args.input_dir is None))
    output = render(result)
    if args.verify_readiness:
        if args.input_dir or args.output:
            parser.error('--verify-readiness only checks the committed empty observed intake')
        if (HERE / 'READINESS.json').read_text() != output:
            raise ValueError('Observed readiness replay changed')
        print('PASS: frozen observed intake is DEFERRED; no functional effects computed.')
    elif args.output:
        with args.output.open('x') as stream:
            stream.write(output)
    else:
        print(output, end='')


if __name__ == '__main__':
    main()
