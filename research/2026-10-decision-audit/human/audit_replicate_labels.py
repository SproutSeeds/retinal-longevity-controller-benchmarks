#!/usr/bin/env python3
"""Preserve source-local replicate numbering separately from exact library keys."""
import argparse
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent


def build():
    refs=json.loads((HERE/'reference-output-audit.json').read_text())['reported_reference_rows']
    meta={r['library']:r for r in json.loads((HERE/'reference-join-manifest.json').read_text())['samples']}
    mismatches=[]
    checked=0
    for r in refs:
        if r['source']!='srsf1-source-fig3.xlsx' or r['sheet']!='3a' or r['join']['status']!='verified_exact_library_and_metadata':
            continue
        v=r['values']; m=meta[v['SampleID']]
        match=re.search(r'\bRep(\d+)\b',m['title'])
        if not match:
            raise ValueError('Missing title replicate for accepted library')
        checked+=1
        rep=int(match.group(1))
        if rep!=v['Replicate']:
            mismatches.append({'library':v['SampleID'],'geo_sample':m['sample_id'],
                'workbook_replicate':v['Replicate'],'geo_title_replicate':rep,
                'construct':v['Gene'],'source_row':r['row'],'source_coordinate':r['coordinates']['Replicate'],
                'exact_library_join_preserved':True})
    return {'schema':'cx004-replicate-numbering-review/v1','stage':'post_analysis_independent_source_review',
            'checked_exact_library_joins':checked,'mismatch_count':len(mismatches),'rows':mismatches,
            'interpretation':'The twelve NTg rows have source-local numbering 1/2 versus 3/4. Exact accession/library keys and the audited biological fields agree. Numbering semantics remain unconfirmed; replicate labels are not used as a cross-source row key.',
            'original_outputs_changed':False}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args()
    result=build()
    target=HERE/'replicate-label-review.json'
    if args.write:
        target.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    elif result!=json.loads(target.read_text()):
        raise SystemExit('FAIL: source-local replicate numbering differs')
    print('PASS:',result['checked_exact_library_joins'],'library joins;',result['mismatch_count'],'replicate-label differences retained')
