#!/usr/bin/env python3
"""Build bounded source/availability receipts without reading expression outcomes."""
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import argparse
import re
import shutil
import urllib.parse
import xml.etree.ElementTree as ET
from build_admission import code_map

HERE = Path(__file__).parent
CACHE = Path('/tmp/cx004-neural-validation-2026-10-18')
OLD = Path('/tmp/cx004-independent-comparator-2026-10-18')
PRIOR = HERE.parent.parent / 'cx004-independent-comparator-2026-10-18'
if not PRIOR.is_dir():
    PRIOR = HERE.parent.parent / '2026-10-independent-comparator'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    (HERE / name).write_text(json.JSONEncoder(indent=2, sort_keys=True).encode(data) + '\n')


def join_cohort1_barcodes(raw_barcodes, object_barcodes, library):
    """Join this one library only after validating its uniform GEM suffix.

    A lane prefix or a different GEM suffix can distinguish otherwise identical
    sequences. Reject those inputs rather than erasing biological provenance.
    """
    if library != 'GSM7022367':
        raise ValueError('Barcode transform is admitted only for GSM7022367')
    if not raw_barcodes or not object_barcodes:
        raise ValueError('Both barcode collections must be nonempty')
    if any(re.fullmatch(r'[ACGT]{16}-1', b) is None for b in raw_barcodes):
        raise ValueError('Raw barcodes must have exactly 16 bases and uniform -1 suffix')
    if any(re.fullmatch(r'[ACGT]{16}', b) is None for b in object_barcodes):
        raise ValueError('Object barcodes must have exactly 16 bases and no suffix')
    raw_set = {b[:-2] for b in raw_barcodes}
    object_set = set(object_barcodes)
    if len(raw_set) != len(raw_barcodes) or len(object_set) != len(object_barcodes):
        raise ValueError('Barcode identifiers must be unique before and after transform')
    if not object_set <= raw_set:
        raise ValueError('Some object cells have no raw barcode match')
    return {
        'included_object_barcodes_match_raw': len(object_set),
        'additional_raw_barcodes_without_recovered_animal_assignment': len(raw_set - object_set),
        'barcode_transform': 'Remove the validated uniform -1 suffix from GSM7022367 only.',
        'raw_pattern': '[ACGT]{16}-1', 'object_pattern': '[ACGT]{16}',
        'unique_before_and_after_transform': True,
    }


def main():
    table = json.loads((HERE / 'supplementary-table1-cells.json').read_text())
    cells = {x['coordinate']: x['value'] for x in table['cells']}
    columns = ['experiment', 'sample_code', 'animal_label', 'strain', 'sex', 'condition',
               'experimental_batch', 'chemistry', 'multiplex_oligo', 'tenx_lane']
    table_rows = []
    for r in range(5, 40):
        row = {name: cells.get(chr(65 + j) + str(r)) for j, name in enumerate(columns)}
        row['source_range'] = f'SuppTable1!A{r}:J{r}'
        row['included_in_study'] = row['experiment'] != '(other samples run and sequenced, but not included in this study)'
        table_rows.append(row)
    save('publisher-sample-metadata.json', {'source_url': table['source_url'],
        'source_sha256': table['source_sha256'], 'table': 'SuppTable1', 'samples': table_rows})

    prior_admission = json.loads((PRIOR / 'neural-admission.json').read_text())
    cohort1 = json.loads((HERE / 'cohort1-admission.json').read_text())
    code1 = (OLD / 'svz-iOSKM_cohort1-seurat_part2.R').read_text()
    code2 = (OLD / 'svz-iOSKM_cohort2-iOSKM2_seurat_part2.R').read_text()
    maps = {1: code_map(code1, 'treatment')[0], 2: code_map(code2, 'treatment')[0]}
    ages = code_map(code2, 'age_genotype')[0]
    present = {1: {x['hash_id'] for x in cohort1['animals']},
               2: {x['hash_id'] for x in prior_admission['animals']}}
    mappings = []
    for cohort, mapping in maps.items():
        for key, treatment in mapping.items():
            bits = key.split('-')
            sample_code, animal, oligo = bits[0], bits[1], bits[-1]
            matches = [r for r in table_rows if r['experimental_batch'] == str(cohort)
                       and r['sample_code'] == sample_code and r['multiplex_oligo'] == oligo]
            # Whole-body rows precede the SVZ-targeted rows and are selected explicitly.
            matches = [r for r in matches if int(re.search(r'!A(\d+):', r['source_range'])[1]) <= 22]
            assert len(matches) == 1, (cohort, key, matches)
            row = matches[0]
            expected_aliases = {'BL61': 'B1', 'BL62': 'B2', 'BL63': 'B3'}
            assert row['animal_label'] == expected_aliases.get(animal, animal)
            assert row['included_in_study'] == (key in present[cohort])
            mappings.append({'cohort': cohort, 'hash_id': key, 'animal_label_author_code': animal,
                'animal_label_publisher': row['animal_label'], 'sample_code': sample_code,
                'multiplex_oligo': oligo, 'treatment_author_code': treatment,
                'age_genotype_author_code': ages[key] if cohort == 2 else None,
                'cohort1_age_label_author_code': 'old' if cohort == 1 else None,
                'cohort1_age_label_locator': 'iOSKM_cohort1/seurat_part2.R lines 215-218' if cohort == 1 else None,
                'genotype_publisher': row['strain'],
                'sex_publisher': row['sex'], 'tenx_lane': int(row['tenx_lane']),
                'source_range': row['source_range'], 'observed_in_shared_object': key in present[cohort],
                'source_confirms_run_and_sequenced': True,
                'withdrawal_days_after_final_pulse': 0 if treatment == '2Dox0' and key in present[cohort] else None,
                'timing_limit': '2Dox5 is the author treatment label; the exact omitted-sample endpoint is not independently documented in Table 1.' if treatment == '2Dox5' else None})
    save('full-animal-source-map.json', {'claim_level': 'Verified',
        'source_sha256': table['source_sha256'], 'source_url': table['source_url'],
        'author_code_commit': cohort1['author_code_commit'],
        'author_code_sources': [{'file': name, 'sha256': sha(OLD / name),
            'url': 'https://raw.githubusercontent.com/gitlucyxu/SVZreprogramming/' + cohort1['author_code_commit'] + '/' + suffix}
            for name, suffix in [('svz-iOSKM_cohort1-seurat_part2.R', 'iOSKM_cohort1/seurat_part2.R'),
                                 ('svz-iOSKM_cohort2-iOSKM2_seurat_part2.R', 'iOSKM_cohort2/iOSKM2_seurat_part2.R')]],
        'samples': mappings, 'notes': ['Source table confirms sequencing, not public recoverability of barcode-to-animal assignments.',
        'Missing strain, sex and condition entries for excluded rows stay null; author-code labels are recorded separately.']})
    save('supplement-corroboration.json', {'claim_level': 'Verified',
        'frozen_admission_sha256': sha(HERE / 'cohort1-admission.json'),
        'frozen_admission_modified': False,
        'source_url': table['source_url'], 'source_sha256': table['source_sha256'],
        'cohort1_included_rows': ['SuppTable1!A5:J8'],
        'cohort1_included_sexes': ['M', 'M', 'M', 'M'],
        'cohort1_tenx_lane': 1, 'cohort1_chemistry': 'v3.0',
        'cohort1_lane_alias': {'cohort1_single_multiplexed_lane': 1},
        'cohort2_shared_lane_sexes': {'1': 'F', '2': 'M'},
        'cohort2_shared_lane_rows': ['SuppTable1!A11:J14'],
        'excluded_rows_confirmed_sequenced': ['SuppTable1!A9:J10', 'SuppTable1!A18:J22'],
        'sample_aliases': {'BL61': 'B1', 'BL62': 'B2', 'BL63': 'B3'},
        'exposure': {'expression_outcomes_calculated': False, 'worksheet_xml_read': table['worksheet_xml_read'],
            'other_worksheet_xml_read': False,
            'author_code_metadata_comments_seen': True,
            'limit': 'Author comments about historical cell counts are source claims, not independently recovered excluded cells.'}})

    raw = []
    for gsm, part, cohort, lane in [('GSM7022367','1',1,1), ('GSM7022368','2-1',2,1),
                                  ('GSM7022369','2-2',2,2), ('GSM7022370','2-3',2,3)]:
        f = CACHE / f'{gsm}_{part}_features.tsv.gz'
        b = CACHE / f'{gsm}_{part}_barcodes.tsv.gz'
        features = [r.split('\t') for r in gzip.open(f, 'rt').read().splitlines()]
        barcodes = gzip.open(b, 'rt').read().splitlines()
        assert len(set(barcodes)) == len(barcodes)
        row = {'geo_library': gsm, 'cohort': cohort, 'tenx_lane': lane,
               'barcodes': len(barcodes), 'features': len(features),
               'feature_types': sorted({r[2] for r in features}),
               'barcode_sha256': sha(b), 'feature_sha256': sha(f),
               'full_cell_to_animal_assignment_deposited_in_matrix_triplet': False,
               'matrix_downloaded': False}
        if cohort == 1:
            observed = list(csv.DictReader(io.StringIO((HERE / 'cohort1-cell-metadata.tsv').read_text()), delimiter='\t'))
            included = [r['cell_barcode'] for r in observed]
            row.update(join_cohort1_barcodes(barcodes, included, gsm))
            row['shared_object_rna_features'] = 31057
            row['feature_alignment_required'] = True
        raw.append(row)
    run_rows = list(csv.DictReader(io.StringIO((CACHE / 'ena-SRP420832.tsv').read_text()), delimiter='\t'))
    wholebody = [x for x in run_rows if x['library_name'] in {r['geo_library'] for r in raw}]
    originals = {}
    sra = ET.fromstring((CACHE / 'ncbi-wholebody-runs.xml').read_bytes())
    for run in sra.findall('.//RUN_SET/RUN'):
        accession = run.attrib['accession']
        for f in run.findall('.//SRAFile'):
            if f.attrib.get('supertype') != 'Original':
                continue
            key = (accession, f.attrib['filename'])
            v = {k: f.attrib[k] for k in ['filename','size','md5']}
            v['run_accession'] = accession
            v['size'] = int(v['size'])
            if key in originals:
                assert originals[key] == v
            originals[key] = v
    assert len(originals) == 21 and len(wholebody) == 7
    assert all(x['filename'].startswith('GEX') for x in originals.values())
    sizes = {gsm: sum(sum(int(n) for n in r['fastq_bytes'].split(';')) for r in wholebody if r['library_name'] == gsm)
             for gsm in [r['geo_library'] for r in raw]}
    save('raw-availability.json', {'claim_level': 'Verified', 'geo_matrices': raw,
        'ena_run_metadata': wholebody, 'original_fastq_inventory': sorted(originals.values(), key=lambda x:(x['run_accession'],x['filename'])),
        'ena_fastq_bytes_by_geo_library': sizes, 'ena_wholebody_total_bytes': sum(sizes.values()),
        'separate_lmo_or_undetermined_original_fastq_listed': False,
        'fastq_content_inspected': False, 'full_raw_download_executed': False,
        'missing_input': 'Full per-cell LMO count matrix or barcode-to-animal assignment for excluded animals, with demultiplexing/QC provenance.',
        'scope_limit': 'Catalog metadata and feature/barcode headers do not prove whether any barcode reads are embedded within GEX FASTQs.',
        'technical_replicate_rule': 'Cohort2 GEX libraries each have L003/L004 sequencing runs; these are not extra animals or extra 10x lanes.'})

    latest = json.loads((CACHE / 'zenodo-12613762.json').read_text())
    old = json.loads((OLD / 'svz-zenodo.json').read_text())
    version_comparison = []
    for current in latest['files']:
        previous = next(x for x in old['files'] if x['key'] == current['key'])
        version_comparison.append({'file': current['key'], 'v1_bytes': previous['size'],
            'v2_bytes': current['size'], 'v1_checksum': previous['checksum'], 'v2_checksum': current['checksum'],
            'unchanged': (previous['size'],previous['checksum']) == (current['size'],current['checksum'])})
    save('source-admission.json', {'claim_level': 'Verified', 'expression_analysis_executed': False,
        'cohort1': {'decision': cohort1['decision'], 'artifact': 'cohort1-admission.json'},
        'withdrawal': {'decision': 'blocked_on_public_full_hash_assignment', 'sequencing_confirmed': True,
            'observations_in_shared_objects': 0, 'animal_source_map': 'full-animal-source-map.json',
            'raw_inventory': 'raw-availability.json'},
        'zenodo_version_comparison': version_comparison,
        'cioskm': {'decision': 'deferred_nonreplication_comparator', 'v1_corrupted': True,
            'v2_size_bytes': 753766915, 'v2_checksum': 'md5:f327804d131b645312f7b6f4d32a64a7',
            'source_url': 'https://zenodo.org/records/12613762',
            'reasons': ['Continuous SVZ-targeted one-week induction differs from whole-body pulsed induction.',
                        'Controls and treated animals occupy disjoint 10x lanes in both batches.',
                        'No withdrawal endpoint.', 'No value for the current frozen cross-cohort direction comparator.'],
            'download_executed': False},
        'new_public_human_retinal_withdrawal': {'decision': 'no_new_eligible_dataset_identified_in_bounded_search',
            'recent_index_query': 'FIRST_PDATE:[2026-10-16 TO 2026-10-18] AND TITLE_ABS:("partial reprogramming" OR "transient reprogramming" OR "epigenetic rejuvenation")',
            'recent_index_hits': 0, 'exhaustive_absence_claim': False,
            'candidate': {'title': 'Cellular Identity Dynamics in Reprogramming, Oncogenic Stress, and Ageing',
                'author': 'Yongmin Kwon', 'doi': '10.17863/CAM.129172',
                'source_url': 'https://www.repository.cam.ac.uk/items/d696e1f1-d49a-4edb-878b-22133a7b15cd',
                'submitted_date': '2025-10-31', 'repository_accessioned_date': '2026-04-07',
                'embargo_until': '2027-04-07', 'status': 'public_abstract_only_not_admitted',
                'model': 'Human RPE1 cells with inducible OKS and induction/withdrawal single-cell profiling described in abstract.',
                'limits': ['Primary adult donor identity, withdrawal duration, counts and sample map unavailable.',
                           'Not newly published since the prior audit; newly surfaced by this focused search.',
                           'No access request or outreach sent.']}},
        'readouts': {f'CX004-R0{i}': 'insufficient_signal' for i in range(1,5)}})

    primary_sources = {
        'zenodo-12613762.json': 'https://zenodo.org/api/records/12613762',
        'ena-SRP420832.tsv': 'https://www.ebi.ac.uk/ena/portal/api/filereport?accession=SRP420832&result=read_run&fields=run_accession,experiment_accession,library_name,library_strategy,read_count,base_count,fastq_bytes,fastq_ftp,fastq_md5,submitted_ftp,submitted_bytes&format=tsv',
        'ncbi-wholebody-runs.xml': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=sra&id=SRR23332081,SRR23332082,SRR23332083,SRR23332085,SRR23332086,SRR23332087,SRR23332088&rettype=full&retmode=xml',
        'cambridge-rpe1-item.json': 'https://api.repository.cam.ac.uk/server/api/core/items/d696e1f1-d49a-4edb-878b-22133a7b15cd',
        'cambridge-rpe1-embargo.json': 'https://api.repository.cam.ac.uk/server/api/core/items/d696e1f1-d49a-4edb-878b-22133a7b15cd/accessStatus',
        'europepmc-since-prior-audit.json': 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + urllib.parse.urlencode({'query': 'FIRST_PDATE:[2026-10-16 TO 2026-10-18] AND TITLE_ABS:("partial reprogramming" OR "transient reprogramming" OR "epigenetic rejuvenation")', 'format':'json','pageSize':100,'resultType':'core'})}
    (HERE / 'sources').mkdir(exist_ok=True)
    manifest = []
    for name,url in primary_sources.items():
        path = CACHE / name
        shutil.copyfile(path,HERE / 'sources' / name)
        manifest.append({'id': name, 'url': url, 'sha256': sha(path), 'bytes': path.stat().st_size,
                         'snapshot': 'sources/' + name})
    for row in raw:
        gsm = row['geo_library']
        for path in sorted(CACHE.glob(gsm + '*')):
            url = f'https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM7022nnn/{gsm}/suppl/'
            if not path.name.endswith('index.html'):
                url += path.name
            manifest.append({'id': path.name, 'url': url, 'sha256': sha(path), 'bytes':path.stat().st_size,
                             'cache_path': str(path)})
    manifest.extend([{'id': 'svz_iOSKM_cohort1_toshare.rds', 'url': cohort1['source_url'],
        'sha256': cohort1['source_sha256'], 'bytes': 94079882, 'repository_checksum':cohort1['zenodo_checksum']},
        {'id':'43587_2024_594_MOESM2_ESM.xlsx','url':table['source_url'],'sha256':table['source_sha256'],
         'bytes':table['source_size_bytes'],'repository_checksum':'md5:'+table['source_md5']},
        {'id':'PMC12036604.html','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC12036604/',
         'sha256':sha(CACHE/'PMC12036604.html'),'bytes':(CACHE/'PMC12036604.html').stat().st_size,
         'cache_only':True}])
    pinned = json.loads((PRIOR / 'input-files.json').read_text())['sources']
    for name in ['svz-zenodo.json', 'svz-iOSKM_cohort1-seurat_part1.R', 'svz-iOSKM_cohort1-seurat_part2.R',
                 'svz-iOSKM_cohort2-iOSKM2_seurat_part1.R', 'svz-iOSKM_cohort2-iOSKM2_seurat_part2.R']:
        prior_source = next(x for x in pinned if x['id'] == name)
        path = OLD / name
        assert sha(path) == prior_source['expected_sha256']
        manifest.append({'id': name, 'url': prior_source['url'], 'sha256': sha(path),
                         'bytes':path.stat().st_size, 'cache_path':str(path), 'previously_pinned':True})
    save('source-manifest.json', {'retrieved_date':'2026-10-18','sources':manifest,
        'data_download_budget_bytes':1000000000,
        'downloaded_cache_bytes':sum(p.stat().st_size for p in CACHE.iterdir() if p.is_file()),
        'raw_inputs_location':str(CACHE),
        'prior_pinned_source_manifest':'https://github.com/SproutSeeds/retinal-longevity-controller-benchmarks/blob/main/research/2026-10-independent-comparator/input-files.json'})
    print('PASS recovery: 35 publisher sample rows; 18 whole-body sample joins; 4 GEO libraries; 7 whole-body runs; 21 original FASTQs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, default=CACHE)
    parser.add_argument('--prior-cache', type=Path, default=OLD)
    parser.add_argument('--prior', type=Path, default=PRIOR)
    args = parser.parse_args()
    CACHE, OLD, PRIOR = args.cache, args.prior_cache, args.prior
    main()
