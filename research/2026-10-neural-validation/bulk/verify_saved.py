#!/usr/bin/env python3
"""Standard-library CI verification of saved outputs; no raw acquisition."""
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
COUNT_SHA256='8a057b616cc6807534650b83d40bbbae8dc50bdfdb5a47ce02dd93e8dc5d76be'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,default=HERE)
    args=p.parse_args()
    checks=[]
    def check(name,value): checks.append({'check':name,'status':'PASS' if value else 'FAIL'})
    def load(name): return json.loads((HERE/name).read_text())
    def close(a,b): return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)
    freeze=load('FREEZE.json')
    for name,key in [('contract.json','contract_sha256'),('admission.json','admission_sha256'),
                     ('panels.json','panels_sha256'),('analyze.py','analysis_sha256')]:
        check('frozen_artifact:'+name,sha(HERE/name)==freeze[key])
    result,receipt,source=load('results.json'),load('execution-receipt.json'),load('count-source-receipt.json')
    pairs=load('admission.json')['pairs'];metadata=load('sample-metadata.json')['samples']
    check('saved_output_bytes',sha(HERE/'results.json')==receipt['results_sha256'] and sha(HERE/'gene-contributions.csv')==receipt['gene_contributions_sha256'])
    check('source_hash_binding',source['sha256']==result['source']['sha256']==receipt['source_sha256']==COUNT_SHA256)
    check('frozen_result_binding',result['freeze']==freeze and result['contract_sha256']==freeze['contract_sha256'])
    check('metadata_units',len(metadata)==65 and len(pairs)==9 and sum(p['age_group']=='old' for p in pairs)==4)
    columns=[p[k+'_count_column'] for p in pairs for k in ['control','treated']]
    check('complete_18_library_QC',result['primary_columns_in_pair_order']==columns and len(result['library_qc'])==18
          and all(q['passes_500_detected_features'] and q['detected_features']>=500 for q in result['library_qc']))
    names=set(load('contract.json')['panels']['family']);methods={'log2_cpm','log2_median_ratio','within_library_rank'}
    rows=result['panel_results']
    check('complete_12_comparisons',len(rows)==12 and {(r['method'],r['panel']) for r in rows}==set(itertools.product(methods,names)))
    genes=list(csv.DictReader((HERE/'gene-contributions.csv').open()))
    families={}
    for row in rows:
        name=row['method']+':'+row['panel']
        check('complete_pair_values:'+name,len(row['scores'])==9 and [r['donor_id'] for r in row['scores']]==[p['donor_id'] for p in pairs]
              and all(r['age_group']==p['age_group'] and r['sex']==p['sex'] for r,p in zip(row['scores'],pairs)))
        delta=[r['treated']-r['control'] for r in row['scores']]
        old=[d for d,p in zip(delta,pairs) if p['age_group']=='old'];young=[d for d,p in zip(delta,pairs) if p['age_group']=='young']
        effect=math.fsum(old)/4-math.fsum(young)/5
        check('means:'+name,all(close(d,r['delta']) for d,r in zip(delta,row['scores'])) and
              close(math.fsum(old)/4,row['old_mean_delta']) and close(math.fsum(young)/5,row['young_mean_delta']) and
              close(math.fsum(delta)/9,row['overall_mean_delta']) and close(effect,row['age_test']['signed_effect']))
        null=[]
        for old_ix in itertools.combinations(range(9),4):
            a=math.fsum(delta[i] for i in old_ix)/4
            b=math.fsum(delta[i] for i in range(9) if i not in old_ix)/5
            null.append(abs(a-b))
        numerator=sum(s>=abs(effect)-1e-12*max(1,abs(effect)) for s in null)
        check('age_enumeration:'+name,row['age_test']['numerator']==numerator and row['age_test']['denominator']==126
              and close(row['age_test']['p'],numerator/126) and len(row['age_test']['null_absolute_statistics'])==126
              and all(close(a,b) for a,b in zip(sorted(null),sorted(row['age_test']['null_absolute_statistics']))))
        positive=sum(d>1e-12 for d in delta);negative=sum(d < -1e-12 for d in delta);n=positive+negative
        sign_num=min(2**n,2*sum(math.comb(n,k) for k in range(min(positive,negative)+1)))
        check('sign_enumeration:'+name,row['overall_sign_test']['numerator']==sign_num and
              row['overall_sign_test']['denominator']==2**n and row['overall_sign_test']['positive']==positive and
              row['overall_sign_test']['negative']==negative and close(row['overall_sign_test']['p'],sign_num/2**n))
        for test,pvalue in [('age_test',numerator/126),('overall_sign_test',sign_num/2**n)]:
            families.setdefault((row['method'],test),[]).append((row,pvalue))
        selected=[g for g in genes if g['method']==row['method'] and g['panel']==row['panel']]
        ng=row['coverage']['present_genes']
        ok=len(selected)==ng*9
        for donor,score in zip(pairs,row['scores']):
            gg=[g for g in selected if g['donor_id']==donor['donor_id']]
            ok &= len(gg)==ng and all(close(float(g['treated_value'])-float(g['control_value']),float(g['delta'])) for g in gg)
            ok &= close(math.fsum(float(g['control_value']) for g in gg)/ng,score['control'])
            ok &= close(math.fsum(float(g['treated_value']) for g in gg)/ng,score['treated'])
        ok &= close(math.fsum(g['age_difference_contribution'] for g in row['gene_contributions']),effect)
        check('saved_gene_reconstruction:'+name,ok)
    for (method,test),family in families.items():
        ordered=sorted(family,key=lambda z:z[1])
        for rank,(row,_) in enumerate(ordered):
            adjusted=min(1,max((4-i)*ordered[i][1] for i in range(rank+1)))
            check('Holm:'+method+':'+test+':'+row['panel'],close(row[test+'_holm_p'],adjusted) and row[test+'_family']['size']==4)
    check('CX004_scope_preserved',set(result['readouts'].values())=={'insufficient_signal'})
    summary=load('cycle-robustness.json')
    check('cycle_summary_result_binding',summary['source_results_sha256']==sha(HERE/'results.json'))
    response_rows=list(csv.DictReader((HERE/'paired-responses.csv').open()))
    response_map={(r['method'],r['panel'],r['donor_id']):r for r in response_rows}
    pairs_by_id={p['donor_id']:p for p in pairs}
    exact_pairs=len(response_rows)==len(response_map)==108
    for row in rows:
        for score in row['scores']:
            record=response_map.get((row['method'],row['panel'],score['donor_id']))
            if record is None:
                exact_pairs=False
            else:
                donor=pairs_by_id[score['donor_id']]
                exact_pairs &= all(record[k]==donor[k] for k in ['control_well','treated_well','control_geo_accession','treated_geo_accession'])
                exact_pairs &= all(close(float(record[k]),score[k]) for k in ['control','treated','delta'])
    check('108_exact_paired_rows_with_wells',exact_pairs)
    for item in summary['methods']:
        row=next(r for r in rows if r['panel']=='cycle_panel' and r['method']==item['method'])
        means=[math.fsum(o['donor_deltas'])/9 for o in row['gene_omissions']]
        good=item['all_nine_responses_negative']==all(s['delta']<0 for s in row['scores'])
        good &= item['gene_omission_any_donor_loses_negative_direction']==any(d>=0 for o in row['gene_omissions'] for d in o['donor_deltas'])
        good &= all(close(a,b) for a,b in zip(item['gene_omission_overall_mean_range'],[min(means),max(means)]))
        for i,omission in enumerate(item['donor_omissions']):
            kept=[s for j,s in enumerate(row['scores']) if i!=j]
            older=[s['delta'] for s in kept if s['age_group']=='old'];younger=[s['delta'] for s in kept if s['age_group']=='young']
            good &= omission['omitted_donor']==row['scores'][i]['donor_id']
            good &= close(omission['overall_mean'],math.fsum(s['delta'] for s in kept)/8)
            good &= close(omission['age_difference'],math.fsum(older)/len(older)-math.fsum(younger)/len(younger))
        for contribution in item['overall_gene_contributions']:
            gg=[g for g in genes if g['panel']=='cycle_panel' and g['method']==item['method'] and g['mouse_symbol']==contribution['mouse_symbol']]
            value=math.fsum(float(g['delta']) for g in gg)/(9*20)
            good &= close(contribution['overall_mean_contribution'],value)
        check('cycle_robustness_summary:'+item['method'],good)
    record={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL',
        'claim_level':'Verified','scope':'Saved-output consistency and hash binding only; no raw source replay or historical git proof in this command.',
        'raw_acquisition_performed':False,'passed':sum(c['status']=='PASS' for c in checks),'total':len(checks),
        'checks':checks,'source_sha256':COUNT_SHA256,'verification_code_sha256':sha(Path(__file__)),
        'generated_at_utc':datetime.now(timezone.utc).isoformat()}
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'SAVED_VERIFICATION.json').write_text(json.JSONEncoder(indent=2,sort_keys=True).encode(record)+'\n')
    print(record['status'],str(record['passed'])+'/'+str(record['total']),'saved bulk checks; no raw acquisition')
    if record['status']!='PASS': raise SystemExit(1)


if __name__=='__main__': main()
