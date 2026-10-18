#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1"]
# ///
"""Independent raw-table arithmetic and exact-test verification.

This verifier does not import the analysis implementation. SciPy supplies
independent tied ranks and binomial-test values. Git proof belongs to the
separate execution receipt; this verifier checks archived artifact hashes.
"""
import argparse
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from scipy.stats import binomtest, rankdata

HERE = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--cache',type=Path,default=Path('/tmp/cx004-neural-validation-2026-10-18'))
    p.add_argument('--result-dir',type=Path,default=HERE)
    p.add_argument('--output',type=Path,default=HERE)
    args=p.parse_args()
    checks=[]

    def check(name, condition):
        checks.append({'check':name,'status':'PASS' if bool(condition) else 'FAIL'})

    def close(a,b):
        return np.allclose(np.asarray(a,dtype=float),np.asarray(b,dtype=float),atol=1e-10,rtol=1e-10)

    frozen=read_json(HERE/'FREEZE.json')
    for name,key in [('contract.json','contract_sha256'),('admission.json','admission_sha256'),
                     ('panels.json','panels_sha256'),('analyze.py','analysis_sha256')]:
        check('frozen_hash:'+name,digest(HERE/name)==frozen[key])
    contract=read_json(HERE/'contract.json')
    admission=read_json(HERE/'admission.json')
    panels=read_json(HERE/'panels.json')['panels']
    result=read_json(args.result_dir/'results.json')
    execution=read_json(args.result_dir/'execution-receipt.json')
    source=read_json(args.result_dir/'count-source-receipt.json')
    path=args.cache/'GSE245385_countTable.csv.gz'
    check('raw_source_bytes',path.stat().st_size==2745316 and digest(path)==source['sha256']==result['source']['sha256'])
    with gzip.open(path,'rb') as f:
        check('frozen_header',hashlib.sha256(f.readline()).hexdigest()==contract['input']['header_sha256'])
    raw=pd.read_csv(path)
    check('all_library_metadata_join',set(raw.columns[2:])=={r['count_column'] for r in read_json(HERE/'sample-metadata.json')['samples']})
    genes=raw['Geneid'].str.replace(r'^(ENSMUSG\d{11})\.\d+$',r'\1',regex=True).tolist()
    check('unique_features_and_raw_integrity',len(genes)==len(set(genes))==31057 and
          np.isfinite(raw.iloc[:,1:].to_numpy(dtype=float)).all() and (raw['Length']>0).all() and
          (raw.iloc[:,2:].to_numpy()>=0).all() and (raw.iloc[:,2:].to_numpy()%1==0).all())
    check('complete_feature_audit',result['feature_audit']['original_feature_ids']==raw['Geneid'].tolist()
          and result['feature_audit']['non_ensembl_features']==['M2rtTAADDGENE20342FULL','P2A','T2A','E2A'])
    pairs=admission['pairs']
    columns=[pair[arm+'_count_column'] for pair in pairs for arm in ['control','treated']]
    check('exact_18_primary_columns',result['primary_columns_in_pair_order']==columns and len(set(columns))==18)
    x=raw[columns].to_numpy(dtype=float)
    totals=x.sum(axis=0)
    check('complete_QC',all(row['count_column']==c and row['raw_library_total']==int(x[:,i].sum())
        and row['detected_features']==int((x[:,i]>0).sum()) and row['passes_500_detected_features']
        for i,(c,row) in enumerate(zip(columns,result['library_qc']))) and len(result['library_qc'])==18)
    values={'log2_cpm':np.log1p(x*(1e6/totals))/math.log(2),
            'within_library_rank':(rankdata(x,axis=0,method='average')-1)/(len(x)-1)}
    all_positive=x[(x>0).all(axis=1)]
    ratios=all_positive/np.exp(np.log(all_positive).mean(axis=1))[:,None]
    factors=np.median(ratios,axis=0)
    factors=factors/np.exp(np.mean(np.log(factors)))
    depths=factors*np.exp(np.mean(np.log(totals)))
    values['log2_median_ratio']=np.log1p(x*(1e6/depths))/math.log(2)
    check('median_ratio_fit',len(all_positive)==result['normalization']['all_positive_genes'] and
          close(factors,result['normalization']['median_ratio_size_factors']) and
          close(depths,result['normalization']['median_ratio_effective_depths']))
    old=np.array([p['age_group']=='old' for p in pairs])
    index={g:i for i,g in enumerate(genes)}
    contributions=pd.read_csv(args.result_dir/'gene-contributions.csv',dtype={'donor_id':str})
    p_families={}
    check('all_12_comparisons_present',len(result['panel_results'])==12 and
          {(r['method'],r['panel']) for r in result['panel_results']}==set(itertools.product(values,panels)))
    for row in result['panel_results']:
        label=row['method']+':'+row['panel']
        panel=panels[row['panel']]
        present=[g for g in panel['genes'] if g['status']=='mapped' and g['mouse_ensembl_gene'] in index]
        check('coverage:'+label,row['coverage']['present_genes']==len(present) and row['coverage']['failures']==[])
        gene_values=values[row['method']][[index[g['mouse_ensembl_gene']] for g in present],:]
        gene_deltas=gene_values[:,1::2]-gene_values[:,::2]
        scores=gene_values.mean(axis=0)
        delta=scores[1::2]-scores[::2]
        age=float(delta[old].mean()-delta[~old].mean())
        check('scores_and_pairing:'+label,
              [r['donor_id'] for r in row['scores']]==[p['donor_id'] for p in pairs] and
              close([r['control'] for r in row['scores']],scores[::2]) and
              close([r['treated'] for r in row['scores']],scores[1::2]) and
              close([r['delta'] for r in row['scores']],delta) and
              close([row['old_mean_delta'],row['young_mean_delta'],row['overall_mean_delta']],
                    [delta[old].mean(),delta[~old].mean(),delta.mean()]))
        total=float(delta.sum())
        null=[abs(float(delta[list(ix)].sum())/4-(total-float(delta[list(ix)].sum()))/5)
              for ix in itertools.combinations(range(9),4)]
        numerator=sum(v>=abs(age)-1e-12*max(1,abs(age)) for v in null)
        check('exact_age_test:'+label,close(row['age_test']['signed_effect'],age) and
              row['age_test']['numerator']==numerator and row['age_test']['denominator']==126 and
              close(row['age_test']['p'],numerator/126) and
              close(sorted(row['age_test']['null_absolute_statistics']),sorted(null)))
        positives=int((delta>1e-12).sum());negatives=int((delta < -1e-12).sum());n=positives+negatives
        sign_p=binomtest(positives,n,p=0.5,alternative='two-sided').pvalue if n else 1.0
        check('independent_binomial:'+label,row['overall_sign_test']['positive']==positives and
              row['overall_sign_test']['negative']==negatives and row['overall_sign_test']['zero']==9-n and
              close(row['overall_sign_test']['p'],sign_p))
        for name,pvalue in [('age_test',numerator/126),('overall_sign_test',sign_p)]:
            p_families.setdefault((row['method'],name),[]).append((row,pvalue))
        target_contributions=(gene_deltas[:,old].mean(axis=1)-gene_deltas[:,~old].mean(axis=1))/len(present)
        check('per_gene_reconstruction:'+label,close([g['age_difference_contribution'] for g in row['gene_contributions']],target_contributions)
              and close(sum(target_contributions),age))
        selected=contributions[(contributions['method']==row['method'])&(contributions['panel']==row['panel'])]
        matched=len(selected)==len(present)*9
        for gi,g in enumerate(present):
            for di,pair in enumerate(pairs):
                rr=selected[(selected['mouse_ensembl_gene']==g['mouse_ensembl_gene'])&(selected['donor_id']==pair['donor_id'])]
                if len(rr)!=1:
                    matched=False
                else:
                    rr=rr.iloc[0]
                    matched &= rr['age_group']==pair['age_group'] and close(
                        [rr['control_value'],rr['treated_value'],rr['delta'],rr['age_difference_contribution']],
                        [gene_values[gi,2*di],gene_values[gi,2*di+1],gene_deltas[gi,di],target_contributions[gi]])
        check('gene_CSV_values:'+label,matched)
        valid_omissions=len(row['gene_omissions'])==len(present)
        for gi,omission in enumerate(row['gene_omissions']):
            omitted=(gene_deltas.sum(axis=0)-gene_deltas[gi])/(len(present)-1)
            valid_omissions &= omission['omitted_mouse_gene']==present[gi]['mouse_symbol'] and close(omission['donor_deltas'],omitted)
            valid_omissions &= close(omission['age_difference'],omitted[old].mean()-omitted[~old].mean())
        check('all_gene_omissions:'+label,valid_omissions)
        if row['method']=='log2_cpm':
            valid=len(row['donor_omissions'])==9
            for di,omission in enumerate(row['donor_omissions']):
                keep=np.arange(9)!=di
                valid &= omission['omitted_donor']==pairs[di]['donor_id'] and omission['old_n']==int(old[keep].sum())
                valid &= close(omission['age_difference'],delta[keep & old].mean()-delta[keep & ~old].mean())
            check('all_primary_donor_omissions:'+label,valid)
    for (method,test),family in p_families.items():
        ordered=sorted(family,key=lambda z:z[1])
        for rank,(row,_) in enumerate(ordered):
            expected=min(1,max((4-j)*ordered[j][1] for j in range(rank+1)))
            check('Holm:'+method+':'+test+':'+row['panel'],close(row[test+'_holm_p'],expected) and row[test+'_family']['size']==4)
    check('result_and_gene_file_receipt_hashes',digest(args.result_dir/'results.json')==execution['results_sha256']
          and digest(args.result_dir/'gene-contributions.csv')==execution['gene_contributions_sha256'])
    check('readouts_unchanged',set(result['readouts'].values())=={'insufficient_signal'})
    record={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL', 'claim_level':'Verified',
        'scope':'Archived hashes and independently reconstructed raw-table arithmetic; biological interpretation remains heuristic.',
        'passed':sum(c['status']=='PASS' for c in checks),'total':len(checks),'checks':checks,
        'generated_at_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':digest(path),
        'analyze_execution_mode':execution['freeze_validation'],
        'historical_git_proof_reexecuted_by_this_verifier':False,
        'verification_code_sha256':digest(Path(__file__)),
        'independent_libraries':'pandas raw reader; scipy.stats.rankdata and scipy.stats.binomtest; no analyze.py imports'}
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'VERIFICATION.json').write_text(json.JSONEncoder(indent=2,sort_keys=True).encode(record)+'\n')
    print(record['status'],str(record['passed'])+'/'+str(record['total']),'independent bulk checks')
    if record['status']!='PASS':
        print([c for c in checks if c['status']=='FAIL'])
        raise SystemExit(1)


if __name__=='__main__':
    main()
