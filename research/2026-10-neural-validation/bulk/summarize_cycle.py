#!/usr/bin/env python3
"""Summarize fixed saved outputs; added donor summaries are explicitly post hoc."""
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

HERE=Path(__file__).resolve().parent


def main():
    result=json.loads((HERE/'results.json').read_text())
    pairs=json.loads((HERE/'admission.json').read_text())['pairs']
    pair_map={p['donor_id']:p for p in pairs}
    with (HERE/'paired-responses.csv').open('w',newline='') as stream:
        fields=['method','panel','donor_id','age_group','sex','control_well','treated_well',
                'control_geo_accession','treated_geo_accession','control','treated','delta']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in result['panel_results']:
            for score in row['scores']:
                donor=pair_map[score['donor_id']]
                writer.writerow({'method':row['method'],'panel':row['panel'],**score,
                    **{k:donor[k] for k in fields if k in donor and k not in score}})
    genes=list(csv.DictReader((HERE/'gene-contributions.csv').open()))
    summaries=[]
    for row in result['panel_results']:
        if row['panel']!='cycle_panel': continue
        scores=row['scores'];deltas=[s['delta'] for s in scores]
        overall=[]
        for info in row['coverage']['present']:
            contributions=[float(g['delta'])/20 for g in genes if g['method']==row['method']
                           and g['panel']=='cycle_panel' and g['mouse_symbol']==info['mouse_symbol']]
            value=mean(contributions)
            overall.append({'mouse_symbol':info['mouse_symbol'],'overall_mean_contribution':value,
                            'fraction_of_signed_overall_mean':value/row['overall_mean_delta']})
        assert math.isclose(sum(g['overall_mean_contribution'] for g in overall),row['overall_mean_delta'],abs_tol=1e-10)
        donor_omissions=[]
        for i,score in enumerate(scores):
            keep=[s for j,s in enumerate(scores) if j!=i]
            donor_omissions.append({'omitted_donor':score['donor_id'],
                'overall_mean':mean(s['delta'] for s in keep),
                'age_difference':mean(s['delta'] for s in keep if s['age_group']=='old')-
                                 mean(s['delta'] for s in keep if s['age_group']=='young')})
        summaries.append({'method':row['method'],'overall_mean':row['overall_mean_delta'],
            'all_nine_responses_negative':all(d<0 for d in deltas),
            'gene_omission_any_donor_loses_negative_direction':any(d>=0 for o in row['gene_omissions'] for d in o['donor_deltas']),
            'gene_omission_overall_mean_range':[min(mean(o['donor_deltas']) for o in row['gene_omissions']),max(mean(o['donor_deltas']) for o in row['gene_omissions'])],
            'gene_omission_age_difference_range':[min(o['age_difference'] for o in row['gene_omissions']),max(o['age_difference'] for o in row['gene_omissions'])],
            'donor_omission_any_overall_mean_loses_negative_direction':any(o['overall_mean']>=0 for o in donor_omissions),
            'donor_omission_any_age_difference_loses_positive_direction':any(o['age_difference']<=0 for o in donor_omissions),
            'donor_omissions':donor_omissions,
            'overall_gene_contributions':sorted(overall,key=lambda r:abs(r['overall_mean_contribution']),reverse=True),
            'age_gene_contributions':sorted(row['gene_contributions'],key=lambda r:abs(r['age_difference_contribution']),reverse=True)})
    output={'claim_level':'Verified','scope':'Arithmetic summary of frozen marker scores; no mechanism or efficacy inference.',
        'source_results_sha256':hashlib.sha256((HERE/'results.json').read_bytes()).hexdigest(),
        'predeclared':'Single-gene omissions under all methods and CPM donor-omission age differences were in the frozen contract.',
        'posthoc':'After viewing the results, root requested overall-mean donor omissions and MR/rank donor-omission age summaries. These are derived from fixed saved scores with normalization held fixed; no raw refit or added hypothesis test.',
        'methods':summaries}
    (HERE/'cycle-robustness.json').write_text(json.JSONEncoder(indent=2,sort_keys=True).encode(output)+'\n')
    print('PASS saved cycle summary; 108 paired-response rows with exact well labels')


if __name__=='__main__': main()
