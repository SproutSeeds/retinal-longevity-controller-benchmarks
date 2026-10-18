#!/usr/bin/env python3
"""Verify the frozen admission, recovery joins, hashes and source boundaries."""
import csv
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).parent
CACHE = Path('/tmp/cx004-neural-validation-2026-10-18')
FROZEN_ADMISSION_SHA256 = '9dc8818d059d68f3991b3aa569e504e603cee1234e5e58f4bcb3ebf6c9eb3148'


def load(name):
    return json.loads((HERE / name).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(cache, prior_cache, artifacts_only=False, output=HERE / 'verification.json'):
    checks = []

    def check(name, value):
        checks.append({'check': name, 'status': 'PASS' if value else 'FAIL'})

    admission = load('cohort1-admission.json')
    check('frozen_admission_bytes_unchanged', sha(HERE / 'cohort1-admission.json') == FROZEN_ADMISSION_SHA256)
    meta = list(csv.DictReader(io.StringIO((HERE / 'cohort1-cell-metadata.tsv').read_text()), delimiter='\t'))
    check('observed_cells_and_unique_barcodes', len(meta) == len({r['cell_barcode'] for r in meta}) == 1194)
    check('observed_animals_match_admission', {r['hash.ID'] for r in meta} == {r['hash_id'] for r in admission['animals']})
    check('observed_treatment_is_immediate_only', {r['Treatment'] for r in meta} == {'untr', '2Dox0'})
    check('observed_per_animal_celltypes_match', all(
        {ct: sum(r['hash.ID'] == a['hash_id'] and r['Celltype'] == ct for r in meta)
         for ct in a['celltype_counts']} == a['celltype_counts'] for a in admission['animals']))
    check('count_integrity_receipt_all_passed', all(load('cohort1-metadata.json')['checks'].values()))
    mappings = load('full-animal-source-map.json')['samples']
    check('18_wholebody_animals_unique', len(mappings) == len({r['hash_id'] for r in mappings}) == 18)
    check('11_included_7_excluded', sum(r['observed_in_shared_object'] for r in mappings) == 11)
    check('5_code_2Dox5_all_unobserved', len([r for r in mappings if r['treatment_author_code'] == '2Dox5']) == 5
          and all(not r['observed_in_shared_object'] and r['withdrawal_days_after_final_pulse'] is None
                  for r in mappings if r['treatment_author_code'] == '2Dox5'))
    check('excluded_publisher_sex_stays_missing', all(r['sex_publisher'] is None for r in mappings if not r['observed_in_shared_object']))
    check('cohort1_four_male_single_lane', all(r['sex_publisher'] == 'M' and r['tenx_lane'] == 1
          for r in mappings if r['cohort'] == 1 and r['observed_in_shared_object']))
    check('cohort2_shared_lanes_sex_matched', all(
        {r['sex_publisher'] for r in mappings if r['cohort'] == 2 and r['tenx_lane'] == lane
         and r['observed_in_shared_object']} == {sex} for lane, sex in [(1, 'F'), (2, 'M')]))
    check('three_explicit_bl6_aliases', {(r['animal_label_author_code'], r['animal_label_publisher'])
          for r in mappings if r['animal_label_author_code'] != r['animal_label_publisher']}
          == {('BL61', 'B1'), ('BL62', 'B2'), ('BL63', 'B3')})
    table = load('supplementary-table1-cells.json')
    check('only_metadata_worksheet_inspected', table['worksheet_xml_read'] == ['xl/worksheets/sheet1.xml']
          and table['other_worksheet_xml_read'] is False)
    sample_rows = load('publisher-sample-metadata.json')['samples']
    check('publisher_has_35_sample_rows', len(sample_rows) == 35)
    check('continuous_treatment_lanes_disjoint',
          {r['tenx_lane'] for r in sample_rows[18:] if r['condition'] == 'old+OSKM (SVZ)'} == {'3', '6'}
          and {r['tenx_lane'] for r in sample_rows[18:] if r['condition'] in {'old', 'young'}} == {'1', '2', '4', '5'})
    raw = load('raw-availability.json')
    check('four_geo_gex_only_headers', len(raw['geo_matrices']) == 4
          and all(r['feature_types'] == ['Gene Expression'] for r in raw['geo_matrices']))
    c1 = raw['geo_matrices'][0]
    check('cohort1_raw_join_counts', (c1['barcodes'], c1['included_object_barcodes_match_raw'],
          c1['additional_raw_barcodes_without_recovered_animal_assignment']) == (10842, 1194, 9648))
    check('feature_alignment_difference_preserved', c1['features'] == 31054 and c1['shared_object_rna_features'] == 31057)
    check('seven_runs_21_original_gex_files', len(raw['ena_run_metadata']) == 7
          and len(raw['original_fastq_inventory']) == 21
          and all(r['filename'].startswith('GEX') for r in raw['original_fastq_inventory']))
    check('fastq_content_uninspected', not raw['fastq_content_inspected'] and not raw['full_raw_download_executed'])
    check('cohort1_fastq_cost_bound', raw['ena_fastq_bytes_by_geo_library']['GSM7022367'] == 44207239760)
    sources = load('source-admission.json')
    versions = sources['zenodo_version_comparison']
    check('both_wholebody_files_unchanged_between_versions',
          all(r['unchanged'] for r in versions if 'ciOSKM' not in r['file']))
    check('corrupted_continuous_file_replaced', any(not r['unchanged'] and r['v2_bytes'] == 753766915
          for r in versions if 'ciOSKM' in r['file']))
    access = load('sources/cambridge-rpe1-embargo.json')
    check('rpe1_thesis_embargo_date_verified', access['status'] == 'embargo' and access['embargoDate'] == '2027-04-07')
    check('all_readouts_unchanged_insufficient', set(sources['readouts'].values()) == {'insufficient_signal'})
    manifest = load('source-manifest.json')
    unchecked_raw = []
    for source in manifest['sources']:
        if artifacts_only and 'snapshot' not in source:
            unchecked_raw.append(source['id'])
            continue
        path = (HERE / source['snapshot'] if 'snapshot' in source
                else (prior_cache if source.get('previously_pinned') else cache) / source['id'])
        check('source_bytes:' + source['id'], path.is_file() and path.stat().st_size == source['bytes'] and sha(path) == source['sha256'])
        if 'repository_checksum' in source:
            check('repository_md5:' + source['id'], path.is_file() and 'md5:' + hashlib.md5(path.read_bytes()).hexdigest() == source['repository_checksum'])
    check('download_budget_below_1GB', manifest['downloaded_cache_bytes'] < 1000000000)
    result = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v', 'test_recovery.py'], cwd=HERE, text=True, capture_output=True)
    check('nine_adversarial_barcode_tests_pass', result.returncode == 0 and 'Ran 9 tests' in result.stderr)
    record = {'claim_level': 'Verified', 'status': 'PASS' if all(r['status'] == 'PASS' for r in checks) else 'FAIL',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'passed': sum(r['status'] == 'PASS' for r in checks),
        'total': len(checks), 'checks': checks, 'test_output': result.stderr,
        'hook': 'PYTHONDONTWRITEBYTECODE=1 python3 verify_recovery.py',
        'determinism': 'Checks are deterministic for pinned local inputs; verification timestamp varies.',
        'frozen_cohort1_admission_sha256': FROZEN_ADMISSION_SHA256,
        'mode': 'derived_artifact_audit' if artifacts_only else 'full_source_and_artifact_audit',
        'raw_sources_not_rechecked': unchecked_raw,
        'scope': 'Metadata, hashes, source availability and barcode joins only; no expression outcome verification.'}
    output.write_text(json.JSONEncoder(indent=2, sort_keys=True).encode(record) + '\n')
    print(f"{record['status']} recovery verification {record['passed']}/{record['total']}")
    if record['status'] != 'PASS':
        print([r for r in checks if r['status'] != 'PASS'])
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, default=CACHE)
    parser.add_argument('--prior-cache', type=Path, default=Path('/tmp/cx004-independent-comparator-2026-10-18'))
    parser.add_argument('--artifacts-only', action='store_true')
    parser.add_argument('--output', type=Path, default=HERE / 'verification.json')
    args = parser.parse_args()
    main(args.cache, args.prior_cache, args.artifacts_only, args.output)
