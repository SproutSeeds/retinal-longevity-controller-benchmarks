#!/usr/bin/env python3
"""Extract source metadata and within-RNA pairs without inventing assay joins."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
CONTROLLER = HERE.parents[1]
GEO_FILES = ['GSE126633', 'GSE165177', 'GSE132828', 'GSE297557', 'GSE90889', 'GSE159435']
PAIR_PATTERN = re.compile(r'(O[123])_(negative_control|failed_to_transiently_reprogram|transiently_reprogrammed)_(10|13|15|17)days_exp([12])\Z')


def encode(value):
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n'


def soft_samples(data, accession):
    rows = []
    for block in data.split('^SAMPLE = ')[1:]:
        lines = block.splitlines()
        fields = {}
        for line in lines[1:]:
            if line.startswith('^'):
                break
            if ' = ' in line:
                name, value = line.split(' = ', 1)
                fields.setdefault(name, []).append(value)
        if fields.get('!Sample_library_strategy') != ['RNA-Seq']:
            raise ValueError('Non-RNA sample in RNA source: ' + lines[0])
        rows.append({'accession': accession, 'sample_id': lines[0],
                     'title': fields['!Sample_title'][0],
                     'library_strategy': 'RNA-Seq',
                     'source': '; '.join(fields.get('!Sample_source_name_ch1', [])),
                     'characteristics': fields.get('!Sample_characteristics_ch1', [])})
    if not rows or len({row['sample_id'] for row in rows}) != len(rows):
        raise ValueError('Empty or duplicate sample roster: ' + accession)
    return rows


def gill_pairs(rows):
    grouped = {}
    for row in rows:
        match = PAIR_PATTERN.fullmatch(row['title'])
        if not match:
            continue
        donor, condition, duration, experiment = match.groups()
        group = grouped.setdefault((donor, int(duration), int(experiment)), {})
        if condition in group:
            raise ValueError('Duplicate RNA donor/duration/experiment/condition')
        group[condition] = row
    pairs = []
    for (donor, duration, experiment), group in sorted(grouped.items()):
        if not {'negative_control', 'transiently_reprogrammed'} <= set(group):
            continue
        control, treated = group['negative_control'], group['transiently_reprogrammed']
        ages = [{v.split(': ', 1)[1] for v in row['characteristics']
                 if v.startswith('donor age (years): ')} for row in [control, treated]]
        if len(ages[0]) != 1 or ages[0] != ages[1]:
            raise ValueError('Missing or incompatible RNA donor-age metadata')
        pairs.append({'donor_label': donor, 'donor_age_years': next(iter(ages[0])),
                      'reprogramming_days': duration, 'experiment': experiment,
                      'control_rna_id': control['sample_id'], 'treated_rna_id': treated['sample_id'],
                      'link_scope': 'within_RNA_metadata_only',
                      'function_unit_id': '', 'joint_function_admitted': False})
    return pairs


def tsv(rows, fields):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=fields, delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def derive():
    manifest = json.loads((HERE / 'SOURCE_MANIFEST.json').read_text())
    sources = {row['file']: row for row in manifest['sources']}
    blobs = {}
    for filename, row in sources.items():
        if row['status'] != 'downloaded':
            continue
        data = (CONTROLLER / row['path']).read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Source bytes differ: ' + filename)
        blobs[filename] = data
    samples = []
    counts = {}
    for accession in GEO_FILES:
        rows = soft_samples(gzip.decompress(blobs[accession + '.soft.gz']).decode(), accession)
        counts[accession] = len(rows)
        samples.extend(rows)
    ena = list(csv.DictReader(io.StringIO(blobs['PRJNA598923-ena.tsv'].decode()), delimiter='\t'))
    for row in ena:
        if row['library_strategy'] != 'RNA-Seq' or row['scientific_name'] != 'Homo sapiens':
            raise ValueError('Unexpected ENA assay or organism')
        samples.append({'accession': 'PRJNA598923', 'sample_id': row['run_accession'],
                        'title': row['experiment_title'], 'library_strategy': row['library_strategy'],
                        'source': row['sample_accession'], 'characteristics': []})
    counts['PRJNA598923'] = len(ena)
    alternate = list(csv.DictReader(io.StringIO(blobs['PRJNA589823-ena.tsv'].decode()), delimiter='\t'))
    pairs = gill_pairs([row for row in samples if row['accession'] == 'GSE165177'])
    # Inspect the source PDF table with pdftotext; its rendered page 7 was also
    # reviewed. Extract only reported per-line summaries, never fake raw wells.
    pdf = CONTROLLER / sources['Schiff2019-supplement-full.pdf']['path']
    process = subprocess.run(['pdftotext', '-layout', str(pdf), '-'], text=True, capture_output=True, check=True)
    page = process.stdout.split('\f')[6]
    table = []
    for line in page.splitlines():
        match = re.fullmatch(r'\s*([A-J])\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s*', line)
        if match:
            label, repeats, mean, cv = match.groups()
            table.append({'source_page': 7, 'source_table': 'Supplementary Table 1',
                          'function_line_label': label, 'reported_experiments': int(repeats),
                          'reported_mean_mass_count': mean, 'reported_cv_percent': cv,
                          'rna_donor_label': '', 'joint_function_admitted': False})
    if ''.join(row['function_line_label'] for row in table) != 'ABCDEFGHIJ':
        raise ValueError('Schiff PDF table extraction changed')
    licenses = {}
    for filename, data in blobs.items():
        if not filename.endswith('.xml'):
            continue
        root = ET.fromstring(data)
        license_text = ' '.join(' '.join(node.itertext()) for node in root.findall('.//license'))
        licenses[filename] = 'CC_BY_4.0_article' if 'creativecommons.org/licenses/by/4.0' in license_text else 'review_required'
    design = Counter()
    for row in samples:
        if row['accession'] != 'GSE165177':
            continue
        title = row['title']
        group = ('iPSC_reference' if title.startswith('iPSC_') else 'intermediate' if 'intermediate' in title
                 else 'starting_fibroblast' if title.endswith('_Fib') else 'final_outgrowth')
        design[group] += 1
    facts = {'schema': 'linked-function.source-facts/1', 'rna_sample_counts': counts,
             'rna_sample_records_total': len(samples), 'gill_design_counts': dict(design),
             'gill_within_rna_contrasts': len(pairs),
             'gill_donor_labels': sorted({row['donor_label'] for row in pairs}),
             'gill_experiments': sorted({row['experiment'] for row in pairs}),
             'gill_reprogramming_durations_days': sorted({row['reprogramming_days'] for row in pairs}),
             'schiff_function_summary_lines': len(table),
             'schiff_reported_experiment_sum': sum(row['reported_experiments'] for row in table),
             'schiff_joined_rna_function_units': 0,
             'alternate_sarkar_accession_read_runs_returned': len(alternate),
             'article_licenses': licenses,
             'source_downloads': len(blobs),
             'preserved_source_failures': sum(row['status'] != 'downloaded' for row in manifest['sources']),
             'scope': 'Metadata extraction and candidate admission; no expression effects or joint correlations.'}
    for row in samples:
        row['characteristics'] = json.dumps(row['characteristics'], ensure_ascii=False)
    return {'SOURCE_FACTS.json': encode(facts),
            'rna-samples.tsv': tsv(samples, ['accession', 'sample_id', 'title', 'library_strategy', 'source', 'characteristics']),
            'gill-rna-pairs.tsv': tsv(pairs, ['donor_label', 'donor_age_years', 'reprogramming_days', 'experiment',
                                           'control_rna_id', 'treated_rna_id', 'link_scope', 'function_unit_id', 'joint_function_admitted']),
            'schiff-function-line-summaries.tsv': tsv(table, ['source_page', 'source_table', 'function_line_label',
                                                            'reported_experiments', 'reported_mean_mass_count',
                                                            'reported_cv_percent', 'rna_donor_label', 'joint_function_admitted'])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    outputs = derive()
    for name, content in outputs.items():
        path = HERE / name
        if args.verify:
            if not path.is_file() or path.read_text() != content:
                raise ValueError('Source-derived artifact differs: ' + name)
        else:
            path.write_text(content)
    print('PASS source metadata: six GEO RNA rosters, one ENA RNA roster, Gill within-RNA labels and Schiff PDF summaries; no functional crosswalk inferred.')


if __name__ == '__main__':
    main()
