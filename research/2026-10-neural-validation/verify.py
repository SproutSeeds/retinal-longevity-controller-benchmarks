#!/usr/bin/env python3
"""Verify release bytes and selected reported claims; standard library only."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE / name).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    checks = []

    def check(name, passed):
        checks.append({'name': name, 'status': 'PASS' if passed else 'FAIL'})

    manifest = load('artifact-hashes.json')
    check('explicit_allowlist_equals_hash_manifest',
          set(load('public-files.json')['files']) == set(manifest['files']) - {'public-files.json'})
    for name, expected in manifest['files'].items():
        path = HERE / name
        check('bytes:' + name, path.is_file() and not path.is_symlink() and sha(path) == expected)
    for name in ['analysis/VERIFICATION.json', 'decomposition/VERIFICATION.json',
                 'decomposition/EXTENSION_VERIFICATION.json', 'human/VERIFICATION.json',
                 'human/percell/VERIFICATION.json', 'human/percell/SAVED_VERIFICATION.json',
                 'bulk/VERIFICATION.json', 'bulk/SAVED_VERIFICATION.json', 'recovery/verification.json']:
        check('historical_verification_pass:' + name, load(name)['status'] == 'PASS')
    bulk = load('bulk/results.json')
    rows = bulk['panel_results']
    for method in ['log2_cpm', 'log2_median_ratio', 'within_library_rank']:
        cycle = next(r for r in rows if r['method'] == method and r['panel'] == 'cycle_panel')
        check('nine_negative_paired_changes:' + method,
              len(cycle['scores']) == 9 and all(r['delta'] < 0 for r in cycle['scores']))
    human = load('human/marker-audit.json')
    contrasts = [r for r in human['contrasts'] if r['method'] in ['log2_cpm', 'log2_median_ratio_cpm_equivalent']
                 and r['panel'] == 'reprogramming_without_OSK_overlap']
    check('four_cd24_dominated_human_contrasts', len(contrasts) == 4 and all(
        .795 < next(g['signed_share'] for g in r['gene_details'] if g['gene'] == 'CD24') < .896
        for r in contrasts))
    percell = load('human/percell/results.json')['sample_variant_results']
    check('complete_22_by_8_grid', len(percell) == 176 and len({r['variant'] for r in percell}) == 22)
    primary = [r for r in percell if r['variant'] == 'primary']
    check('57317_barcodes_two_donors', sum(r['n_retained'] for r in primary) == 57317
          and len({r['donor'] for r in primary}) == 2)
    for donor, n, hits in [('GM00731', 6915, 852), ('GM23815', 12209, 2851)]:
        r = next(r for r in primary if r['donor'] == donor and r['day'] == 7)
        check('day7_codetection:' + donor, r['n_retained'] == n and r['coexpression_at_least_two_count'] == hits)
    cohort1 = load('analysis/cohort1-results.json')
    cohort2 = load('analysis/cohort2-results.json')
    check('independent_animal_counts', cohort1['independent_animals'] == 4 and cohort2['independent_animals'] == 7)
    check('neural_cell_counts', cohort1['cell_count'] == 1194 and cohort2['cell_count'] == 3857)
    check('readouts_still_insufficient', all(set(r['readouts'].values()) == {'insufficient_signal'}
                                         for r in [cohort1, cohort2]))
    cross = load('analysis/cross-cohort-results.json')['comparisons']
    cycle = next(r for r in cross if r['celltype'] == 'Microglia' and r['panel_name'] == 'cycle_panel'
                 and r['support_tier'] == 'primary_support')
    d1 = cycle['cohort1_direction_details']['log2_cpm']
    d2 = cycle['cohort2_direction_details']['log2_cpm']
    check('microglial_mean_agreement_and_omission_disagreement', d1['mean_difference'] < 0
          and d2['mean_difference'] < 0 and min(d1['animal_omission_range']) < 0 < max(d1['animal_omission_range'])
          and max(d2['animal_omission_range']) < 0)
    decomp = load('decomposition/results.json')['results']
    r = next(r for r in decomp if r['panel'] == 'stress_panel' and r['cell_floor'] == 20 and r['scale'] == 10000)['equal_lane_mean']
    check('stress_partition_with_opposing_components', r['composition'] < 0 < r['within_type']
          and abs(r['composition'] + r['within_type'] - r['total']) < 1e-12)
    samples = load('recovery/full-animal-source-map.json')['samples']
    missing = [r for r in samples if not r['observed_in_shared_object']]
    check('seven_omitted_samples_five_unverified_withdrawal_labels', len(missing) == 7
          and sum(r['treatment_author_code'] == '2Dox5' for r in missing) == 5
          and all(r['withdrawal_days_after_final_pulse'] is None for r in missing if r['treatment_author_code'] == '2Dox5'))
    check('spoken_companions_match', (HERE / 'presentation/spoken-notes.txt').read_bytes()
          == (HERE / 'presentation/spoken-notes.md').read_bytes())
    check('private_human_barcode_table_excluded', 'human/percell/primary-cells.tsv.gz' not in manifest['files'])
    return {'status': 'PASS' if all(r['status'] == 'PASS' for r in checks) else 'FAIL',
            'claim_level': 'Verified computation; Heuristic biological interpretation',
            'experiment_replacement': 'INCONCLUSIVE',
            'scope': 'Release integrity, archived verification status and reported numerical summaries. This command does not replay raw biological inputs.',
            'checks': checks, 'check_count': len(checks)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    report = verify()
    if args.write:
        (HERE / 'VERIFICATION.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(report['status'], report['check_count'], 'release and summary checks')
    for check in report['checks']:
        if check['status'] != 'PASS':
            print(check['status'], check['name'])
    if report['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
