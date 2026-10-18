#!/usr/bin/env python3
"""Recover public parameters and sample metadata without executing author code."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from xml.etree import ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
PAPER = 'https://www.nature.com/articles/s43587-026-01234-8'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def save(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n')


def column_index(address):
    letters = re.match(r'[A-Z]+', address).group()
    index = 0
    for letter in letters:
        index = 26 * index + ord(letter) - 64
    return index - 1


def workbook(path):
    """Read cached scalar cell values, retaining sparse column positions."""
    with ZipFile(path) as archive:
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [''.join(t.itertext()) for t in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        rels = {x.attrib['Id']: x.attrib['Target'] for x in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        result = {}
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).find('s:sheets', NS):
            rid = sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            target = rels[rid]
            target = target.lstrip('/') if target.startswith('/') else 'xl/' + target
            rows = []
            for row in ET.fromstring(archive.read(target)).findall('s:sheetData/s:row', NS):
                values = []
                for cell in row:
                    index = column_index(cell.attrib['r'])
                    values.extend([''] * (index + 1 - len(values)))
                    value = cell.findtext('s:v', '', NS)
                    if cell.find('s:f', NS) is not None:
                        raise ValueError('Formula cells require a separately verified calculation')
                    if cell.attrib.get('t') == 's':
                        value = shared[int(value)]
                    elif cell.attrib.get('t') == 'inlineStr':
                        value = ''.join(cell.find('s:is', NS).itertext())
                    values[index] = value
                if any(v != '' for v in values):
                    rows.append(values)
            result[sheet.attrib['name']] = rows
        return result


def extract_parameters(rows):
    header_index = next(i for i, row in enumerate(rows) if row[:3] == ['Ensembl ID', 'Gene symbol', 'Coefficient'])
    records = []
    seen = set()
    for row in rows[header_index + 1:]:
        if not row or not row[0]:
            continue
        name = row[0]
        if name in seen:
            raise ValueError('Duplicate model term: ' + name)
        if not (re.fullmatch(r'ENSG\d+', name) or name in {'Intercept', 'LibType.Total', 'LibType.mRNA'}):
            raise ValueError('Unexpected model term: ' + name)
        raw, standardized = float(row[2]), float(row[3])
        if not all(math.isfinite(v) for v in (raw, standardized)):
            raise ValueError('Non-finite coefficient')
        seen.add(name)
        records.append({'term': name, 'symbol': row[1], 'coefficient': raw, 'standardized_coefficient': standardized})
    if not {'Intercept', 'LibType.Total', 'LibType.mRNA'} <= seen:
        raise ValueError('Missing intercept or library terms')
    return records


def samples(path):
    result = []
    current = None
    for line in path.read_text().splitlines():
        if line.startswith('^SAMPLE = '):
            current = {'gsm': line.split(' = ', 1)[1], 'characteristics': {}}
            result.append(current)
        elif line.startswith('^'):
            current = None
        elif current is not None and line.startswith('!Sample_') and ' = ' in line:
            key, value = line.split(' = ', 1)
            if key == '!Sample_characteristics_ch1':
                k, sep, v = value.partition(': ')
                if sep:
                    current['characteristics'][k] = v
            elif key in {'!Sample_title', '!Sample_description', '!Sample_organism_ch1', '!Sample_growth_protocol_ch1', '!Sample_treatment_protocol_ch1', '!Sample_data_processing'}:
                current.setdefault(key[8:], []).append(value)
    return result


def require_exact_mapping(matrix_keys, assignments):
    """Validate explicit library/barcode keys; never infer from row order."""
    keys = set(matrix_keys)
    if len(keys) != len(matrix_keys):
        raise ValueError('Duplicate matrix library/barcode key')
    seen = set()
    for row in assignments:
        required = ('library_id', 'cell_barcode', 'perturbation', 'donor_or_pool_id')
        if any(not str(row.get(k, '')).strip() for k in required):
            raise ValueError('Missing explicit identity field')
        key = (row['library_id'], row['cell_barcode'])
        if key in seen:
            raise ValueError('Duplicate assignment key')
        if key not in keys:
            raise ValueError('Unknown matrix key')
        seen.add(key)
    if seen != keys:
        raise ValueError('Incomplete assignment coverage')
    return {'keys': len(keys), 'status': 'PASS', 'biological_independence_verified': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--counts', type=Path, required=True)
    parser.add_argument('--clock-git', type=Path)
    args = parser.parse_args()
    cache = args.cache
    receipts = [json.loads(p.read_text()) for p in sorted(HERE.glob('retrieval-[0-9].json'))]
    hashes = {r['id']: r['sha256'] for receipt in receipts for r in receipt['sources'] if r['status'] == 'retrieved'}
    for name, wanted in hashes.items():
        if digest(cache / name) != wanted:
            raise ValueError('Source hash changed: ' + name)
    expected_counts = '8f1d726665a18a0f92285d790014077953be1e0733c93efc92939a1c4090046d'
    if digest(args.counts) != expected_counts:
        raise ValueError('Unexpected human counts revision')
    records = extract_parameters(workbook(cache / 'srsf1-coefficients.xlsx')['Sheet1'])
    genes = {r['term'] for r in records if r['term'].startswith('ENSG')}
    count_ids = Counter()
    with gzip.open(args.counts, 'rt') as stream:
        header = stream.readline().strip().split('\t')
        for line in stream:
            count_ids[line.split('\t', 1)[0].split('.')[0]] += 1
    model = {'source': PAPER + '#MOESM4', 'source_sha256': hashes['srsf1-coefficients.xlsx'],
             'source_sheet': 'Sheet1', 'source_header_row': 6, 'claim_level': 'Verified',
             'scope': 'Numeric parameter extraction only. No fitted-model equivalence or biological-age prediction validated.',
             'terms': records, 'gene_terms': len(genes), 'total_terms': len(records),
             'matrix_coverage': {'count_file_sha256': expected_counts, 'libraries': len(header) - 1,
                                 'gene_terms_present': len(genes & count_ids.keys()),
                                 'missing_genes': sorted(genes - count_ids.keys()),
                                 'duplicated_model_gene_ids': sorted(g for g in genes if count_ids[g] > 1)},
             'exact_replay_status': 'BLOCKED',
             'remaining_dependencies': ['Exact gl gene-length vector and normalization gene universe / genes_to_filter.txt',
                                        'Training/calibration objects and intended frozen-SVA application behavior',
                                        'Reference input and predicted outputs to validate numerical equivalence',
                                        'Sample-level clock library encoding and experimental batches']}
    save('srsf1-clock-parameters.json', model)
    h = json.loads((cache / 'clock-commits.json').read_text())
    history = {'repository': 'https://github.com/saschajung/Clock', 'head': h[0]['sha'],
               'commit_count': len(h), 'commit_ids': [r['sha'] for r in h],
               'branches': json.loads((cache / 'clock-branches.json').read_text()),
               'tags': json.loads((cache / 'clock-tags.json').read_text()),
               'releases': json.loads((cache / 'clock-releases.json').read_text()),
               'current_paths': [r['path'] for r in json.loads((cache / 'clock-tree-current.json').read_text())['tree']]}
    if args.clock_git:
        def git(*words):
            return subprocess.check_output(['git', '--git-dir', str(args.clock_git), *words], text=True).strip()
        if git('rev-parse', 'HEAD') != history['head']:
            raise ValueError('History HEAD mismatch')
        commits = git('rev-list', '--all').splitlines()
        if set(commits) != set(history['commit_ids']):
            raise ValueError('Incomplete history inventory')
        history['all_historical_paths'] = sorted(set(git('log', '--all', '--pretty=format:', '--name-only').split()) )
        history['history_inventory_status'] = 'Verified'
    else:
        previous = json.loads((HERE / 'clock-dependency-audit.json').read_text())
        history['all_historical_paths'] = previous['all_historical_paths']
        history['history_inventory_status'] = previous['history_inventory_status']
        print('Retaining the previously verified pinned git-history inventory; not fetching git history in this run')
    apply_text = (cache / 'clock-current-apply.R').read_text()
    correction_line = 'samples_new_apply_corrected <- samples_new_apply'
    history['fsva_output_overwritten_in_apply_script'] = correction_line in apply_text
    history['apply_script_sha256'] = hashes['clock-current-apply.R']
    history['interpretation'] = 'Clarify intended preprocessing with authors; a repository script may be exploratory. Do not silently repair or treat it as proof of a published-result error.'
    save('clock-dependency-audit.json', history)
    all_samples = samples(cache / 'gse325735-samples.txt')
    all_off = [s for s in all_samples if '-OFF' in s['characteristics'].get('treatment', '')]
    recovery = [s for s in all_off if s.get('organism_ch1') == ['Homo sapiens']]
    for sample in recovery:
        names = [v.removeprefix('Library name: ') for v in sample.get('description', []) if v.startswith('Library name: ')]
        if len(names) != 1 or names[0] not in header[1:]:
            raise ValueError('Recovery sample does not map uniquely to deposited counts')
        sample['matrix_column'] = names[0]
    if len({s['matrix_column'] for s in recovery}) != len(recovery):
        raise ValueError('Duplicate recovery library')
    schedules = Counter(s['characteristics']['treatment'].split(', ')[-1] for s in recovery)
    save('srsf1-recovery-samples.json', {'claim_level': 'Verified', 'source_sha256': hashes['gse325735-samples.txt'],
         'geo_sample_count': len(all_samples), 'recovery_library_count': len(recovery), 'schedule_counts': dict(schedules),
         'all_species_off_library_count': len(all_off), 'excluded_nonhuman_off_libraries': len(all_off) - len(recovery),
         'human_construct_counts': dict(Counter(s['characteristics']['genotype'] for s in recovery)),
         'independent_human_donor_lines': len({s['characteristics']['cell line'] for s in recovery}),
         'previous_60_library_scope': '30 SRSF1 and 30 matched BFP libraries. Twelve OSKM libraries are additional comparisons, not new donors.',
         'samples': recovery, 'caption_chronology': 'Extended Data Figure 6d describes 6 and 12 days after withdrawal for brief 1-3 day inductions.',
         'chronology_status': 'UNRESOLVED: preserve GEO 8/16-day OFF labels and caption 6/12-day labels separately.',
         'batch_scope': 'GEO batch fields label sequencing/library batches; independent experimental batches are not established.'})
    wb = workbook(cache / 'geo350289-metadata.xlsx')
    sheets = {name: {'nonempty_rows': len(rows), 'first_nonempty_rows': rows[:3],
                     'max_nonempty_columns': max((max((i + 1 for i, v in enumerate(r) if v != ''), default=0) for r in rows), default=0)} for name, rows in wb.items()}
    save('geo350289-mapping-audit.json', {'claim_level': 'Verified', 'source_sha256': hashes['geo350289-metadata.xlsx'],
         'sheets': sheets, 'status': 'mapping_blocked', 'required_key': ['library_id', 'cell_barcode'],
         'required_mapping_fields': ['hash_identity', 'perturbation', 'donor_or_pool_id', 'sample_id', 'batch_id', 'assignment_qc'],
         'decision': 'No gene-expression matrix download; the inspected workbook does not provide exact cell-to-perturbation assignments.'})
    root = ET.fromstring((cache / 'ocular-source-current.xml').read_bytes())
    paragraphs = [' '.join(p.itertext()) for p in root.findall('.//p')]
    selected = {}
    for label, needle in [('OSK_clock', 'paradoxically increases tAge'), ('GSTA4_clock', '8.5 months'), ('clock_method', 'Bayesian Ridge')]:
        matches = [(i, t) for i, t in enumerate(paragraphs) if needle in t]
        if not matches:
            raise ValueError('Missing ocular source statement: ' + label)
        selected[label] = [{'paragraph_index': i, 'text_sha256': hashlib.sha256(t.encode()).hexdigest()} for i, t in matches]
    ocular = {'source': 'https://doi.org/10.1101/2025.08.30.673239', 'source_sha256': hashes['ocular-source-current.xml'],
              'source_anchors': selected, 'claim_level': 'Heuristic', 'evidence_role': 'Author-reported findings; not independently reproduced here.',
              'OSK': 'Authors report increased overall tAge alongside improvement in some functional endpoints; prolonged exposure raised toxicity concerns.',
              'GSTA4': 'Authors report an 8.5-month lower transcriptomic age after eight weeks of GSTA4 overexpression in old mouse RPE.',
              'interpretation': 'Keep intervention, endpoint and duration separate. Our broad correlation does not replay the fitted clock.',
              'cohorts': {acc: samples(cache / filename) for acc, filename in [('GSE304038', 'gse304038-samples.txt'), ('GSE304043', 'gse304043-samples.txt')]}}
    save('ocular-source-clarification.json', ocular)
    archive_rows = []
    for name in ['tage-model-record.json', 'tage-current-model-record.json']:
        record = json.loads((cache / name).read_text())
        files = record['files']
        archive_rows.append({'doi': record['doi'], 'created': record['created'], 'updated': record['updated'],
                             'files': [{'name': f['key'], 'bytes': f['size'], 'checksum': f['checksum']} for f in files],
                             'model_files_downloaded': False})
    save('ocular-clock-artifacts.json', {'claim_level': 'Verified', 'archives': archive_rows,
         'historical_equivalence': 'UNRESOLVED: these deposits postdate the 2025 ocular preprint; availability does not identify the exact historical model.',
         'license_source': 'https://github.com/Gladyshev-Lab/tAge/blob/d048ba6016a7e5a114f45195e0b11071e2b8c424/LICENSE',
         'license_note': 'The source repository specifies non-commercial, non-revenue-generating academic use. No model execution or redistribution in this package.'})
    print('Recovered', len(genes), 'gene terms and', len(records) - len(genes), 'non-gene terms; coverage', model['matrix_coverage']['gene_terms_present'])
    print('Recovery libraries', len(recovery), 'schedules', dict(schedules))
    print('Workbook sheets', {k: v['nonempty_rows'] for k, v in sheets.items()})


if __name__ == '__main__':
    main()
