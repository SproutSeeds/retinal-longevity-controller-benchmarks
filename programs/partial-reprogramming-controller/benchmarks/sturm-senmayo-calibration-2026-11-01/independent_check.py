#!/usr/bin/env python3
"""Independent numerical/source check. Does not import analyze or its math."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import scipy
from scipy import stats

HERE = Path(__file__).resolve().parent
TOL = 1e-10


def read_table(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream,delimiter="\t"))


def same(actual, expected, context):
    if expected is None:
        if actual is not None:
            raise AssertionError(context + ": expected unavailable")
    elif actual is None or not np.isclose(actual, float(expected), rtol=0, atol=TOL):
        raise AssertionError(context + ": numerical mismatch")


def corr(x,y):
    if np.ptp(x)==0 or np.ptp(y)==0:
        return None
    return float(stats.spearmanr(x,y).statistic)


def partial(x,y,t):
    design=np.column_stack([np.ones(len(t)),np.asarray(t,dtype=float)])
    output=[]
    for values in [x,y]:
        values=np.asarray(values,dtype=float)
        residual=values-design@np.linalg.lstsq(design,values,rcond=None)[0]
        raw=np.sum((values-values.mean())**2)
        if np.sum(residual**2)<=1e-24*max(1,float(raw)):
            return None
        output.append(residual)
    return float(stats.pearsonr(*output).statistic)


def main(sources):
    upstream=HERE.parent/'alternative-function-screen-2026-11-01'
    metadata=json.loads((upstream/'SOURCE_MANIFEST.json').read_text())['files']
    filename='GSE179848_processed_cell_lifespan_RNAseq_data.csv.gz'
    assert hashlib.sha256((sources/filename).read_bytes()).hexdigest()==metadata[filename]['sha256']
    original=read_table(upstream/'eligible-untreated-records.tsv')
    scored=read_table(HERE/'sample-scores.tsv')
    assert len(original)==len(scored)==22
    keyed={row['study_sample_id']:row for row in original}
    assert len(keyed)==22
    for row in scored:
        base=keyed[row['study_sample_id']]
        for key in ['rna_column','gsm','donor','donor_age_years','days_grown_source','passage','function_value_source','function_present','function_units']:
            assert row[key]==base[key],key
    genes=[r['gene_symbol'] for r in read_table(HERE/'senmayo-human.tsv')]
    values={}
    with gzip.open(sources/filename,'rt',newline='') as stream:
        reader=csv.reader(stream);header=next(reader)
        columns=[header.index(row['rna_column']) for row in scored]
        for row in reader:
            if row[0] in genes:
                assert row[0] not in values
                values[row[0]]=[row[index] for index in columns]
    coverage=json.loads((HERE/'GENE_COVERAGE.json').read_text())
    assert set(coverage['included_genes'])==set(values)
    assert coverage['available_genes']==len(values)>=100
    used=[g for g in genes if g in values]
    numerical=np.array([[float(v) for v in values[g]] for g in used])
    assert np.isfinite(numerical).all()
    mean=numerical.mean(axis=0)
    for i,row in enumerate(scored): same(mean[i],row['score'],'source-derived score')
    source_cells=read_table(HERE/'panel-expression-source.tsv')
    assert len(source_cells)==len(used)*22
    assert len({(r['gene_symbol'],r['study_sample_id']) for r in source_cells})==len(source_cells)
    by_id={r['study_sample_id']:i for i,r in enumerate(scored)}
    for row in source_cells:
        assert row['expression_value_source']==values[row['gene_symbol']][by_id[row['study_sample_id']]]
    results=json.loads((HERE/'RESULTS.json').read_text())
    loo=read_table(HERE/'leave-one-out.tsv')
    intervals=read_table(HERE/'adjacent-changes.tsv')
    checked=0
    for donor in ['HC1','HC2']:
        all_rows=sorted((r for r in scored if r['donor']==donor),key=lambda r:float(r['days_grown_source']))
        rows=[r for r in all_rows if r['function_present']=='true']
        arrays=lambda records:[np.array([float(r[k]) for r in records]) for k in ['score','function_value_source','days_grown_source','passage']]
        x,y,t,p=arrays(rows)
        expected=results['donors'][donor]
        checks={'spearman_score_function':corr(x,y),'linear_day_residual_pearson':partial(x,y,t),'linear_passage_residual_pearson':partial(x,y,p),
                'spearman_score_day':corr(x,t),'spearman_function_day':corr(y,t),'spearman_passage_day':corr(p,t)}
        valid=[]
        donor_intervals=[r for r in intervals if r['donor']==donor]
        assert len(donor_intervals)==len(all_rows)-1
        for a,b,actual in zip(all_rows,all_rows[1:],donor_intervals):
            assert (a['study_sample_id'],b['study_sample_id'])==(actual['from_study_sample_id'],actual['to_study_sample_id'])
            dt=float(b['days_grown_source'])-float(a['days_grown_source'])
            dx=(float(b['score'])-float(a['score']))/dt
            same(dt,actual['elapsed_days'],'interval duration');same(dx,actual['score_change_per_day'],'score rate')
            if a['function_present']=='true' and b['function_present']=='true':
                dy=(float(b['function_value_source'])-float(a['function_value_source']))/dt
                assert actual['status']=='included';same(dy,actual['function_change_per_day'],'function rate');valid.append((dx,dy))
            else:
                assert actual['status']=='missing_function_endpoint' and actual['function_change_per_day']=='NA'
        checks['adjacent_rate_spearman']=corr(*map(np.array,zip(*valid))) if len(valid)>=4 else None
        assert expected['included_adjacent_intervals']==len(valid)
        for key,value in checks.items():same(value,expected[key],donor+' '+key);checked+=1
        donor_loo=[r for r in loo if r['donor']==donor]
        assert {r['excluded_study_sample_id'] for r in donor_loo}=={r['study_sample_id'] for r in rows}
        assert len(donor_loo)==len(rows)
        for item in donor_loo:
            kept=[r for r in rows if r['study_sample_id']!=item['excluded_study_sample_id']]
            xx,yy,tt,_=arrays(kept)
            same(corr(xx,yy),None if item['spearman']=='NA' else item['spearman'],'LOO Spearman')
            same(partial(xx,yy,tt),None if item['linear_day_residual_pearson']=='NA' else item['linear_day_residual_pearson'],'LOO time residual')
            checked+=2
    return {'schema':'controller.independent-numerical-check/1','status':'PASS','claim_level':'Verified numerical/source agreement only','expression_strings_compared':len(source_cells),'sample_means_checked':22,'association_coefficients_checked':checked,'absolute_tolerance':TOL,'original_function_strings_preserved':21,'imports_primary_analysis':False,'libraries':{'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__},'scope':'Source strings, exact samples, fixed means, donor statistics, missing-function intervals and every leave-one-out coefficient. No biological validity, causal or intervention validation.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources',type=Path,default=HERE.parents[1]/'.data/alternative-function-screen-2026-11-01')
    parser.add_argument('--emit',type=Path)
    args=parser.parse_args()
    result=main(args.sources)
    text=json.JSONEncoder(indent=2,sort_keys=True).encode(result)+'\n'
    if args.emit:args.emit.write_text(text)
    print(text.strip())
