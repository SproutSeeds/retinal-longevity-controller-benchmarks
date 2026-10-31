#!/usr/bin/env python3
"""Offline artifact and intake replay, separate from original-source checking."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from admission import derive

HERE = Path(__file__).resolve().parent


def rows(name):
    with (HERE / name).open(newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def main():
    manifest = json.loads((HERE / 'ARTIFACT_MANIFEST.json').read_text())
    for name, expected in manifest['files'].items():
        path = HERE / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Bound artifact differs: ' + name)
    for name, expected in derive().items():
        if (HERE / name).read_text() != expected:
            raise ValueError('Intake replay differs: ' + name)
    facts = json.loads((HERE / 'SOURCE_FACTS.json').read_text())
    samples = rows('rna-samples.tsv')
    if dict(Counter(row['accession'] for row in samples)) != facts['rna_sample_counts']:
        raise ValueError('RNA roster counts differ')
    if len(samples) != facts['rna_sample_records_total'] or len({(r['accession'], r['sample_id']) for r in samples}) != len(samples):
        raise ValueError('Duplicate or missing RNA metadata records')
    by_id = {row['sample_id']: row for row in samples if row['accession'] == 'GSE165177'}
    pairs = rows('gill-rna-pairs.tsv')
    for pair in pairs:
        suffix = pair['reprogramming_days'] + 'days_exp' + pair['experiment']
        if by_id[pair['control_rna_id']]['title'] != pair['donor_label'] + '_negative_control_' + suffix:
            raise ValueError('Control source title differs')
        if by_id[pair['treated_rna_id']]['title'] != pair['donor_label'] + '_transiently_reprogrammed_' + suffix:
            raise ValueError('Treated source title differs')
        if pair['function_unit_id'] or pair['joint_function_admitted'] != 'False':
            raise ValueError('Within-RNA metadata was promoted into a functional join')
    if len(pairs) != facts['gill_within_rna_contrasts'] or sorted({row['donor_label'] for row in pairs}) != facts['gill_donor_labels']:
        raise ValueError('RNA contrast/donor scope differs')
    functional = rows('schiff-function-line-summaries.tsv')
    if len(functional) != facts['schiff_function_summary_lines']:
        raise ValueError('Function summary cardinality differs')
    if sum(int(row['reported_experiments']) for row in functional) != facts['schiff_reported_experiment_sum']:
        raise ValueError('Reported experiment total differs')
    if any(row['rna_donor_label'] or row['joint_function_admitted'] != 'False' for row in functional):
        raise ValueError('An unsupported RPE assay crosswalk was introduced')
    result = json.loads((HERE / 'ADMISSION_RESULTS.json').read_text())
    if result['candidate_count'] != 8 or result['joint_admissions'] != 0 or result['adult_primary_admissions'] != 0:
        raise ValueError('Reviewed bounded-admission checkpoint changed')
    process = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(HERE),
                              '-p', 'test_*.py', '-v'], capture_output=True, text=True)
    if process.returncode:
        raise RuntimeError(process.stdout + process.stderr)
    print(process.stderr.strip())
    print('PASS offline replay: %d bound artifacts; %d RNA metadata records; %d within-RNA contrasts; eight reviewed candidates; zero joint admissions.' %
          (len(manifest['files']), len(samples), len(pairs)))
    print('Original-source verification is separate: python audit_sources.py --verify (requires retained public inputs and pdftotext).')


if __name__ == '__main__':
    main()
