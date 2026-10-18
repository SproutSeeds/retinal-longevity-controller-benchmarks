#!/usr/bin/env python3
"""Admit GEO donor pairs and count-column aliases without reading count rows."""
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
CACHE = Path('/tmp/cx004-neural-validation-2026-10-18')
OLD = Path('/tmp/cx004-independent-comparator-2026-10-18')
ANALYSIS = HERE.parent / 'analysis'
COMMIT = '011586aea2e8612c794e57d2a260fa1a29d417a0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    (HERE / name).write_text(json.JSONEncoder(indent=2, sort_keys=True, allow_nan=False).encode(data) + '\n')


def parse_identifier(name):
    m = re.fullmatch(r'([A-H](?:[1-9]|1[0-2]))_(\d+)_(A|D)(0?6|18|48)h_(Dox|untr)_chim', name)
    if not m:
        raise ValueError('Unrecognized sample identifier: ' + name)
    return {'well': m[1], 'donor_id': m[2], 'timepoint': f'{m[3]}{int(m[4]):02d}h',
            'treatment': m[5]}


def parse_samples(text):
    rows = []
    for chunk in text.split('^SAMPLE = ')[1:]:
        accession = chunk.splitlines()[0]
        fields = defaultdict(list)
        for line in chunk.splitlines()[1:]:
            if ' = ' in line:
                key, value = line.split(' = ', 1)
                fields[key].append(value)

        def one(key):
            if len(fields[key]) != 1:
                raise ValueError('Ambiguous or missing GEO field: ' + key)
            return fields[key][0]

        characteristics = [x.split(': ', 1) for x in fields['!Sample_characteristics_ch1']]
        if len({k for k, _ in characteristics}) != len(characteristics):
            raise ValueError('Duplicate characteristic')
        attrs = dict(characteristics)
        if one('!Sample_geo_accession') != accession or not re.fullmatch(r'GSM\d+', accession):
            raise ValueError('GEO accession conflict')
        if attrs['Sex'] not in {'F', 'M'}:
            raise ValueError('Missing or unadmitted donor sex')
        title = one('!Sample_title')
        description = one('!Sample_description')
        parsed = parse_identifier(description)
        t = re.fullmatch(r'(A|D)(06|18|48)h_(Dox|untr)_(old|young)_rep([1-5])', title)
        if not t or (parsed['timepoint'], parsed['treatment']) != (t[1] + t[2] + 'h', t[3]):
            raise ValueError('Title and description conflict')
        if (attrs['time'], attrs['treatment'], attrs['age']) != (parsed['timepoint'], parsed['treatment'], t[4]):
            raise ValueError('Characteristics conflict')
        if one('!Sample_organism_ch1') != 'Mus musculus' or attrs['genotype'] != 'iOSKM':
            raise ValueError('Unadmitted species or genotype')
        if attrs['media'] != ('NSC media' if parsed['timepoint'].startswith('A') else 'differentiation media'):
            raise ValueError('Time and media conflict')
        rows.append({'geo_accession': accession, 'title': title, 'description': description,
            **parsed, 'age_group': attrs['age'], 'sex': attrs['Sex'], 'media': attrs['media'],
            'species': 'Mus musculus', 'genotype': attrs['genotype'], 'source_cell_type': attrs['cell type'],
            'replicate_label': int(t[5]), 'source_url': 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=' + accession})
    return rows


def join_header(rows, header):
    if header[:2] != ['Geneid', 'Length'] or len(set(header)) != len(header):
        raise ValueError('Ambiguous count header')
    lookup = {tuple(parse_identifier(col).items()): col for col in header[2:]}
    if len(lookup) != len(header) - 2:
        raise ValueError('Count alias collision')
    used = []
    for row in rows:
        key = tuple(parse_identifier(row['description']).items())
        if key not in lookup:
            raise ValueError('GEO sample absent from count header')
        row['count_column'] = lookup[key]
        used.append(lookup[key])
    if len(used) != len(set(used)) or set(used) != set(header[2:]):
        raise ValueError('Count columns do not join one-to-one to GEO')
    return rows


def donor_pairs(rows):
    donors = defaultdict(list)
    for row in rows:
        donors[row['donor_id']].append(row)
    pairs = []
    for donor, records in sorted(donors.items(), key=lambda x: int(x[0])):
        for key in ['age_group', 'sex', 'species', 'genotype', 'replicate_label']:
            if len({r[key] for r in records}) != 1:
                raise ValueError('Donor metadata conflict: ' + key)
        a18 = [r for r in records if r['timepoint'] == 'A18h']
        if len(a18) != 2 or {r['treatment'] for r in a18} != {'Dox', 'untr'}:
            raise ValueError('Incomplete or duplicate A18h pair')
        pair = {'donor_id': donor, 'age_group': records[0]['age_group'], 'sex': records[0]['sex'],
                'media': 'NSC media', 'timepoint': 'A18h', 'species': 'Mus musculus',
                'genotype': 'iOSKM', 'libraries_across_all_times': len(records)}
        for row in a18:
            arm = 'treated' if row['treatment'] == 'Dox' else 'control'
            pair[arm + '_geo_accession'] = row['geo_accession']
            pair[arm + '_count_column'] = row['count_column']
            pair[arm + '_well'] = row['well']
        pairs.append(pair)
    return pairs


def main():
    sources = []
    prior_manifest = json.loads((HERE.parent.parent / 'cx004-independent-comparator-2026-10-18/input-files.json').read_text())
    for name in ['GSE245385-series.txt', 'GSE245385-samples.txt']:
        source = next(r for r in prior_manifest['sources'] if r['id'] == name)
        path = OLD / name
        assert sha(path) == source['expected_sha256']
        sources.append({'id': name, 'url': source['url'], 'sha256': sha(path), 'bytes': path.stat().st_size, 'cache_path': str(path)})
    rows = parse_samples((OLD / 'GSE245385-samples.txt').read_text())
    header = next(csv.reader(io.StringIO((CACHE / 'GSE245385_countTable.header.csv').read_text())))
    rows = join_header(rows, header)
    pairs = donor_pairs(rows)
    assert len(rows) == len({r['geo_accession'] for r in rows}) == 65 and len(pairs) == 9
    assert {r['donor_id'] for r in pairs if r['age_group'] == 'old'} == {'940', '946', '966', '967'}
    assert {r['donor_id'] for r in pairs if r['age_group'] == 'young'} == {'1892', '1893', '1894', '1914', '1926'}
    assert next(r for r in rows if r['well'] == 'H8')['count_column'] == 'H8_966_D6h_Dox_chim'
    code = (CACHE / 'bulk-DESeq2_analysis_chimeric_clean.R').read_text()
    assert '"Well","MouseID","Timepoint","Treatment",NA' in code
    assert "names(counts)[names(counts) == 'H8_966_D6h_untr_chim'] <- 'H8_966_D6h_Dox_chim'" in code
    pattern = r'coldata\$Age <- plyr::mapvalues\(coldata\$MouseID,\s+from=c\((.*?)\),\s+to=c\((.*?)\)\)'
    m = re.search(pattern, code, re.S)
    assert m
    keys, values = [re.findall(r'"([^"]+)"', s) for s in m.groups()]
    age_map = dict(zip(keys, values))
    assert len(age_map) == 9 and all(age_map[r['donor_id']] == r['age_group'] for r in rows)
    for name in ['bulk-DESeq2_analysis_chimeric_clean.R', 'bulk-DESeq2_DEG_plots_clean.R']:
        path = CACHE / name
        tree = json.loads((OLD / 'svz-code-tree.json').read_text())
        blob = next(r for r in tree['tree'] if r['path'] == 'bulkRNAseq/' + name.removeprefix('bulk-'))
        data = path.read_bytes()
        assert len(data) == blob['size']
        assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == blob['sha']
        sources.append({'id': name, 'url': 'https://raw.githubusercontent.com/gitlucyxu/SVZreprogramming/' + COMMIT + '/bulkRNAseq/' + name.removeprefix('bulk-'),
                        'sha256': sha(path), 'bytes': path.stat().st_size, 'cache_path': str(path), 'git_blob_validated': True})
    receipt = json.loads((CACHE / 'GSE245385_countTable.header.receipt.json').read_text())
    assert sha(CACHE / 'GSE245385_countTable.header.csv') == receipt['header_sha256']
    sources.append({'id': 'GSE245385_countTable.header.csv', 'url': receipt['source_url'],
                    'sha256': receipt['header_sha256'], 'bytes': receipt['header_bytes'],
                    'cache_path': str(CACHE / 'GSE245385_countTable.header.csv'), 'partial_header_only': True})
    sources.append({'id': 'PMC12036604.html', 'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12036604/',
                    'sha256': sha(CACHE / 'PMC12036604.html'), 'cache_path': str(CACHE / 'PMC12036604.html'),
                    'bytes': (CACHE / 'PMC12036604.html').stat().st_size})
    orthology = json.loads((ANALYSIS / 'orthology.json').read_text())
    panels = {}
    for name, humans in orthology['panels'].items():
        panels[name] = {'source_human_genes': humans, 'genes': []}
        for human in humans:
            row = orthology['mapping'][human]
            panels[name]['genes'].append({'human_symbol': human, 'status': row['status'],
                'mouse_symbol': row.get('mouse_symbol'),
                'mouse_ensembl_gene': row['selected']['mouse_ensembl_gene'] if row['status'] == 'mapped' else None})
    save('panels.json', {'orthology_source': '../analysis/orthology.json', 'orthology_sha256': sha(ANALYSIS / 'orthology.json'),
                        'panels': panels, 'feature_match': 'Use the frozen selected mouse Ensembl ID, with only an optional numeric Ensembl version suffix removed; require uniqueness.',
                        'replacement_genes_allowed': False})
    save('sample-metadata.json', {'claim_level': 'Verified', 'samples': rows,
        'group_counts': [{'age_group': k[0], 'timepoint': k[1], 'treatment': k[2], 'libraries': v}
                         for k,v in sorted(Counter((r['age_group'],r['timepoint'],r['treatment']) for r in rows).items())]})
    save('admission.json', {'claim_level': 'Verified', 'decision': 'admit_acute_A18h_donor_paired_comparator',
        'expression_rows_inspected': 0, 'expression_outcomes_computed': False, 'pairs': pairs,
        'samples': len(rows), 'donors': len(pairs), 'primary_libraries': 18,
        'primary_timepoint': 'A18h', 'withdrawal_observations': 0,
        'age_months': {'young': [3,4], 'old': [25,25]},
        'donor_source': 'GEO Sample_description MouseID, cross-checked against pinned author code lines 183-186; each culture is from one mouse (paper Fig. 7a).',
        'well_source': 'Author code explicitly names the first token Well; do not infer batch or lane from it.',
        'technical_lanes': 'All libraries pooled and sequenced across three lanes; lane is not an independent donor.',
        'sequencer_metadata_discrepancy': 'GEO instrument field says NovaSeq 6000; detailed GEO extraction protocol and paper specify NovaSeq X Plus. Does not change donor pairing.',
        'header_alias_rule': 'A6h/D6h in count columns correspond exactly to A06h/D06h in GEO; no other alias or silent treatment correction.',
        'H8': {'deposited_header_and_geo': '966 D06h Dox', 'author_code_documents_prior_run_mislabel': True,
               'used_for_primary': False},
        'timing': {'A06h_A18h_A48h': '6/18/48 hours of ongoing induction in NSC medium.',
            'D06h_D18h_D48h': '6/18/48 hours in differentiation medium after 18 hours of induction; doxycycline continues, totaling 24/36/66 hours.',
            'withdrawal_verified': False, 'continued_induction_verified': True,
            'source_url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12036604/#F7',
            'methods_url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12036604/#S40'},
        'excluded_from_primary': {'A06h_A48h': 'Only old Dox libraries; no time-matched untreated controls. A48h also used lower plating density.',
            'D06h_D18h_D48h': 'Old treatment pairs exist, but continued-induction differentiation cannot answer withdrawal and lacks young treated arms.',
            'all_time_pooling': 'Repeated cultures from the same nine donors; 65 libraries are not 65 independent replicates.'},
        'confounding': ['Doxycycline and OSKM are bundled; no genotype-negative Dox control in this series.',
            'Age is observational; four old and five young donors have slightly different sex composition. Pairing does not randomize age.',
            'Bulk scores combine transcription and any cell-mixture differences; no per-cell state or rare-state calibration.',
            'Custom reference adds rtTA/P2A/T2A/E2A features; it does not by itself separate endogenous and transgenic OSKM reads.'],
        'sources': sources, 'readouts': {f'CX004-R0{i}': 'insufficient_signal' for i in range(1,5)}})
    save('header-exposure.json', receipt)
    save('source-manifest.json', {'sources': sources, 'published_result_exposure': True,
        'exposure': 'Paper Fig. 7 findings, methods and author-code comments containing prior DEG counts were read. No local bulk expression rows or newly computed outcomes were inspected.',
        'raw_count_file_expected_bytes': int(receipt['http_head']['Content-Length']),
        'full_count_file_hash_available_before_download': False})
    print('PASS bulk metadata: 65 library columns; 9 donors; 9 complete A18h pairs; no withdrawal endpoint')


if __name__ == '__main__':
    main()
