#!/usr/bin/env python3
"""Build bounded source inventories, readiness findings, and readable reference tables."""
import argparse
import collections
import csv
import gzip
import hashlib
import json
import re
from pathlib import Path
from xlsx_cells import read_workbook

HERE = Path(__file__).resolve().parent


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--extra', type=Path, required=True)
    parser.add_argument('--raw-counts', type=Path, required=True)
    args = parser.parse_args()
    with gzip.open(args.raw_counts, 'rt') as handle:
        header = handle.readline().rstrip('\n').split('\t')
    write('raw-counts-structure.json', {'source_url': 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE325nnn/GSE325735/suppl/GSE325735_human_raw_counts.txt.gz',
                                      'sha256': hashlib.sha256(args.raw_counts.read_bytes()).hexdigest(),
                                      'bytes': args.raw_counts.stat().st_size,
                                      'columns': header, 'column_count': len(header),
                                      'unique_library_columns': len(set(header[1:])),
                                      'contains_length_column': 'Length' in header})
    sources = []
    for number in range(1, 5):
        receipt = json.loads((HERE / f'retrieval-{number}.json').read_text())
        for row in receipt['sources']:
            sources.append(dict(row, retrieval_receipt=f'retrieval-{number}.json'))
    def path_for(row):
        return (args.extra if row['retrieval_receipt'] == 'retrieval-4.json' else args.cache) / row['id']
    for row in sources:
        if row['status'] == 'retrieved':
            path = path_for(row)
            if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
                raise ValueError('Changed source: ' + row['id'])
    write('SOURCES.json', {'schema_version': 1, 'date': '2026-10-18',
                          'scope': 'Named publisher supplements, current author code, GEO and Europe PMC discovery queries. A bounded retrieval audit, not global search exhaustion.',
                          'sources': sources})
    inventory = []
    for row in sources:
        if row['status'] != 'retrieved' or not row['id'].endswith('.xlsx'):
            continue
        for sheet in read_workbook(path_for(row)):
            strings = [c for c in sheet['cells'] if isinstance(c['value'], str)]
            matches = [dict(c) for c in strings if re.search(r'withdraw|wash.?off|wash.?out|\bOFF\b|recovery|d-ON', c['value'], re.I)]
            headers = [dict(c) for c in sheet['cells'] if re.fullmatch(r'[A-Z]+1', c['cell'])]
            inventory.append({'source': row['id'], 'source_sha256': row['sha256'], 'sheet': sheet['sheet'],
                              'dimension': sheet['dimension'], 'formula_cells': sum(c['formula'] is not None for c in sheet['cells']),
                              'nonempty_cells': sum(c['value'] is not None for c in sheet['cells']),
                              'row1': headers, 'withdrawal_word_matches': matches})
    write('complete-workbook-inventory.json', {'scope': 'All six main-figure source workbooks and nine supplementary workbooks; semantic schedule linkage still requires figure captions.', 'sheets': inventory})
    broad = []
    queries = []
    for source_id in ['epmc-human-transient.json', 'epmc-human-withdrawal.json', 'geo-human-recovery.json']:
        source = next(r for r in sources if r['id'] == source_id)
        obj = json.loads(path_for(source).read_text())
        if source_id.startswith('epmc'):
            records = obj['resultList']['result']
            queries.append({'source': source_id, 'query': source['query'], 'reported_hits': obj['hitCount'], 'retrieved_records': len(records), 'complete_result_page': len(records) == obj['hitCount']})
            for r in records:
                broad.append({'query_source': source_id, 'id': r['id'], 'source': r.get('source'), 'pmcid': r.get('pmcid'), 'doi': r.get('doi'), 'title': r.get('title'), 'first_publication_date': r.get('firstPublicationDate')})
        else:
            records = obj['esearchresult']['idlist']
            queries.append({'source': source_id, 'query': source['query'], 'reported_hits': int(obj['esearchresult']['count']), 'retrieved_records': len(records), 'complete_result_page': len(records) == int(obj['esearchresult']['count'])})
    geo = []
    for n in range(1, 4):
        j = json.loads((args.cache / f'geo-summary-{n}.json').read_text())['result']
        for uid in j['uids']:
            r = j[uid]
            geo.append({'uid': uid, 'accession': r.get('accession'), 'title': r.get('title'), 'gdstype': r.get('gdstype'), 'taxon': r.get('taxon'), 'sample_count': r.get('n_samples'),
                        'title_screen_match': bool(re.search(r'rejuven|transient reprogram|partial reprogram|age.*revers|SRSF1', r.get('title', ''), re.I))})
    write('search-ledger.json', {'schema_version': 1, 'queries': queries,
                               'screen_rule': 'Title/abstract-led relevance screen followed by named primary-source audits. All retrieval hits remain available here; keyword matches are triage, not proof of relevance or exhaustive exclusion.',
                               'literature_records': broad, 'geo_records': geo})
    metadata = json.loads((HERE / 'reference-join-manifest.json').read_text())['samples']
    off = [r for r in metadata if r['off_days_geo'] is not None]
    schedule = collections.Counter(r['treatment'].split(', ')[-1] for r in off)
    timing = {'schema_version': 1, 'claim_level': 'Verified', 'status': 'partly_resolved',
              'human_factor_off_libraries': len(off), 'donor_lines': sorted(set(r['donor_or_line'] for r in off)),
              'construct_counts': dict(collections.Counter(r['genotype'] for r in off)),
              'geo_schedule_counts': dict(sorted(schedule.items())),
              'source_geo_example': {'url': 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM9612108', 'field': 'Sample_characteristics_ch1 treatment', 'value': 'Dox_1000ng/mL, 1d-ON/8d-OFF'},
              'publisher_short_induction_schedule': {'figure': 'Extended Data Fig. 5d', 'url': 'https://www.nature.com/articles/s43587-026-01234-8/figures/11', 'induction_days': [1, 2, 3], 'days_after_withdrawal': [6, 12]},
              'short_schedule_disposition': 'Unresolved. GEO explicitly labels OFF durations. Treating 8/16 as total elapsed time cannot uniformly yield 6/12 after induction lengths 1,2,3. Preserve labels and obtain a sample-level chronology map.',
              'agreed_schedule': {'induction_days': 5, 'off_days': 2, 'libraries': 12, 'donor_lines': 3, 'source_figure': 'Fig. 4c and Extended Data Fig. 5e', 'library_ids': sorted(r['library'] for r in off if r['on_days_geo'] == 5 and r['off_days_geo'] == 2)},
              'correction': 'Prior metadata synopsis called the withdrawal caption Extended Data Fig. 6d. The current publisher labels it Extended Data Fig. 5d; the earlier evidence bytes are preserved.'}
    write('chronology-audit.json', timing)
    findings = [
        {'input': 'Published reference predictions', 'status': 'partly_recovered', 'detail': '1027 row occurrences in original audited sources; 66 exact Fig. 3a library joins. An additional 12 Fig. 4c withdrawal-reference rows map at donor/construct/schedule-group level.'},
        {'input': 'Gene length vector gl', 'status': 'missing_exact_input', 'source_file': 'ProcessFibroblastData.R', 'source_lines': [85, 90], 'detail': 'Derived from Geneid and Length in all_data_featurecounts(1).txt. Deposited human counts have Geneid and 807 count columns, with no Length column.'},
        {'input': 'Frozen gene filter', 'status': 'missing_exact_input', 'source_file': 'GetGenesForRemoval.R', 'source_lines': [27, 33], 'detail': 'The script queries unversioned live Ensembl and writes genes_to_filter.txt. The exact generated list is absent from the inspected repository tree.'},
        {'input': 'Normalization gene universe', 'status': 'missing_exact_input', 'source_file': 'TrainClock.R', 'source_lines': [81, 93], 'detail': 'Filtering precedes TPM, then natural log(x+1). Script writes GenesForTPMNorm.rds before a mean-expression filter. The exact saved training object is absent from the inspected tree.'},
        {'input': 'Applied correction path and training state', 'status': 'requires_author_clarification', 'source_file': 'ApplyNewData.R', 'source_lines': [14, 24], 'detail': 'fsva is called using training objects, then the corrected output is replaced with uncorrected samples_new_apply. Clarify the intended published path rather than silently repairing it.'},
        {'input': 'Library preparation encoding and complete paired reference set', 'status': 'partly_recovered', 'detail': 'Published coefficients and library adjustments were recovered previously. Validation rows now supply reference outputs; exact per-library inputs and encoding must match the intended pipeline before replay.'},
        {'input': 'Short-induction withdrawal timing and reference rows', 'status': 'requires_author_clarification', 'detail': 'The 1–3-day induction cohort retains 8/16 OFF labels in GEO versus 6/12 after withdrawal in the caption. Its uniquely keyed per-library published predictions were not identified in the inspected workbooks.'},
    ]
    write('clock-readiness.json', {'schema_version': 1, 'claim_level': 'Verified', 'repository': 'https://github.com/saschajung/Clock', 'commit': '7ae5f38b7ea74f76cb13076b64350d5930bb152f',
                                  'current_repository_paths': [r['path'] for r in json.loads((args.cache / 'clock-tree.json').read_text())['tree']],
                                  'forks_returned': len(json.loads((args.cache / 'clock-forks.json').read_text())), 'issues_returned': len(json.loads((args.cache / 'clock-issues.json').read_text())),
                                  'model_executed': False, 'clock_replay_status': 'blocked_on_exact_preprocessing_and_reference_mapping', 'findings': findings})
    refs = json.loads((HERE / 'reference-output-audit.json').read_text())['reported_reference_rows']
    selected = [r for r in refs if r['source'] == 'srsf1-source-fig3.xlsx' and r['sheet'] == '3a']
    with (HERE / 'validation-reference-joins.csv').open('w', newline='') as handle:
        fields = ['source_row', 'SampleID', 'Line', 'Gene', 'Passage', 'Dox', 'Predicted_age', 'AgeDiff', 'join_status', 'geo_accession']
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for r in selected:
            val = {k: r['values'][k] for k in fields if k in r['values']}
            val.update(source_row=r['row'], join_status=r['join']['status'], geo_accession=r['join'].get('sample_id'))
            writer.writerow(val)
    print('Retrieved sources:', sum(r['status'] == 'retrieved' for r in sources), '/', len(sources))
    print('Workbook sheets:', len(inventory))
    print('Discovery queries:', queries)


if __name__ == '__main__':
    main()
