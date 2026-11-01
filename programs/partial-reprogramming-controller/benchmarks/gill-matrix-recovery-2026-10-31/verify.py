#!/usr/bin/env python3
"""Offline package integrity and conservative sample/contrast checks."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def table(name):
    with (HERE / name).open(newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def main():
    manifest = json.loads((HERE / 'ARTIFACT_MANIFEST.json').read_text())
    for name, expected in manifest['files'].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            raise AssertionError('Released artifact differs: ' + name)
    contract = json.loads((HERE / 'MATRIX_CONTRACT.json').read_text())
    for name, expected in contract['frozen_dependencies'].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            raise AssertionError('Original frozen dependency differs: ' + name)
    qc = json.loads((HERE / 'MATRIX_QC.json').read_text())
    source_verification = json.loads((HERE / 'FULL_SOURCE_VERIFICATION.json').read_text())
    assert source_verification['status'] == 'PASS'
    assert source_verification['expression_values_compared'] == qc['finite_numeric_values_preserved'] == 3401475
    assert source_verification['changed_source_cells'] == 0
    assert qc['merged_feature_rows'] == qc['unique_locus_keys'] == 35805
    assert qc['sample_columns'] == 95
    assert qc['new_admitted_function_pairs'] == 0 and qc['joint_comparison'] == 'DEFERRED'
    samples = table('sample-columns.tsv')
    assert len(samples) == len({row['geo_sample_id'] for row in samples}) == len({row['source_label'] for row in samples}) == 95
    assert Counter(row['match_status'] for row in samples) == {'exact_title': 90, 'provisional_format_alias': 5}
    with (HERE.parent / 'linked-function-admission-2026-10-31/rna-samples.tsv').open(newline='') as stream:
        metadata = {row['sample_id']: row for row in csv.DictReader(stream, delimiter='\t') if row['accession'] == 'GSE165177'}
    for row in samples:
        assert row['geo_title'] == metadata[row['geo_sample_id']]['title']
        if row['match_status'] == 'exact_title':
            assert row['source_label'] == row['geo_title']
        else:
            assert contract['provisional_title_aliases'][row['source_label']] == row['geo_title']
            assert row['in_frozen_comparison'] == 'false'
    coverage = table('contrast-coverage.tsv')
    with (HERE.parent / 'gill-migration-comparison-2026-10-31/rna-pairs.tsv').open(newline='') as stream:
        original_pairs = list(csv.DictReader(stream, delimiter='\t'))
    assert len(coverage) == len(original_pairs) == 13
    for row, pair in zip(coverage, original_pairs):
        assert all(row[field] == value for field, value in pair.items())
        assert row['rna_expression_available'] == 'true'
        assert row['joint_comparison'] == 'DEFERRED'
        for field in ['original_clock_values_available', 'migration_values_available', 'function_crosswalk_available']:
            assert row[field] == 'false'
        for arm in ['control', 'treated']:
            match = [sample for sample in samples if sample['geo_sample_id'] == row[arm + '_rna_id']]
            assert len(match) == 1 and match[0]['match_status'] == 'exact_title'
    issues = table('gene-id-issues.tsv')
    repeated = [row for row in issues if row['issue'] == 'repeated_gene_id']
    assert len(issues) == 159 and len(repeated) == 157
    assert len({row['ID'] for row in repeated}) == qc['repeated_nonempty_gene_ids'] == 77
    assert sum(row['issue'] == 'blank_gene_id' for row in issues) == qc['blank_gene_id_rows'] == 2
    reordered = table('reordered-features.tsv')
    assert {row['ID'] for row in reordered} == {'ENSG00000280101', 'ENSG00000280358'}
    assert len(reordered) == qc['reordered_feature_rows'] == 2
    assert qc['numeric_cells_differing_under_a_positional_join'] == 0
    subprocess.run([sys.executable, str(HERE / 'test_recover.py')], check=True)
    print('PASS offline recovery package: %d bound artifacts; 95 source columns; 26 exact frozen RNA arms; 13 contrasts; zero joint function admissions.' % len(manifest['files']))
    print('Original-source replay is separate: python3 recover.py --download --verify; python3 verify_merged.py after --write --merge.')


if __name__ == '__main__':
    main()
