#!/usr/bin/env python3
"""Offline verification from released source strings; original downloads separate."""
import math
from pathlib import Path
import subprocess
import sys

import analyze as a

HERE=Path(__file__).resolve().parent


def compare(actual,expected,where='result'):
    if isinstance(expected,dict):
        if not isinstance(actual,dict) or set(actual)!=set(expected):
            raise AssertionError(where+': keys differ')
        for key in expected:compare(actual[key],expected[key],where+'.'+key)
    elif isinstance(expected,list):
        if len(actual)!=len(expected):raise AssertionError(where+': length differs')
        for i,(x,y) in enumerate(zip(actual,expected)):compare(x,y,where+'.'+str(i))
    elif isinstance(expected,float):
        if actual is None or not math.isclose(actual,expected,rel_tol=0,abs_tol=1e-10):
            raise AssertionError(where+': numeric value differs')
    elif actual!=expected:
        raise AssertionError(where+': value differs')


def main():
    manifest=a.read_json(HERE/'ARTIFACT_MANIFEST.json')
    for name,expected in manifest['files'].items():
        if Path(name).name!=name or a.sha(HERE/name)!=expected:
            raise AssertionError('Artifact hash differs: '+name)
    a.check_freeze()
    genes=[r['gene_symbol'] for r in a.table(HERE/'senmayo-human.tsv')]
    assert len(genes)==len(set(genes))==125
    expression=a.table(HERE/'panel-expression-source.tsv')
    assert len(expression)==2750
    cells={(r['gene_symbol'],r['study_sample_id']):r for r in expression}
    assert len(cells)==2750
    eligible=a.table(a.UPSTREAM/'eligible-untreated-records.tsv')
    paired=a.table(a.UPSTREAM/'matched-records.tsv')
    a.validate_records(eligible,paired)
    scored=a.table(HERE/'sample-scores.tsv')
    by_id={r['study_sample_id']:r for r in scored}
    assert len(scored)==len(by_id)==22
    for row in eligible:
        actual=by_id[row['study_sample_id']]
        for key in ['rna_column','gsm','donor','donor_age_years','days_grown_source','passage','function_value_source','function_present','function_units']:
            assert row[key]==actual[key],key
        strings=[cells[(g,row['study_sample_id'])] for g in genes]
        assert all(cell['rna_column']==row['rna_column'] for cell in strings)
        values=[float(cell['expression_value_source']) for cell in strings]
        a.finite(values)
        mean=math.fsum(values)/125
        compare(float(actual['score']),mean,'sample mean')
        row.update(score=mean,days=float(row['days_grown_source']),passage_number=float(row['passage']),
                   function=float(row['function_value_source']) if row['function_present']=='true' else None)
    stats,intervals,loo=a.summarize(eligible)
    result=a.read_json(HERE/'RESULTS.json')
    compare(stats,result['donors'])
    assert result['rejuvenation_intervention'] is False and result['population_inference_performed'] is False and result['Gill_joint_admissions']==0
    assert result['available_reference_genes']==125 and result['readout_claim_level']=='Heuristic'
    interval_fields=['donor','from_study_sample_id','to_study_sample_id','elapsed_days','score_change_per_day','function_change_per_day','status']
    loo_fields=['donor','excluded_study_sample_id','n','spearman','linear_day_residual_pearson']
    for name,rows,fields in [('adjacent-changes.tsv',intervals,interval_fields),('leave-one-out.tsv',loo,loo_fields)]:
        actual=a.table(HERE/name)
        expected=list(__import__('csv').DictReader(a.table_text(rows,fields).splitlines(),delimiter='\t'))
        assert len(actual)==len(expected)
        for x,y in zip(actual,expected):
            for key in fields:
                if key in {'elapsed_days','score_change_per_day','function_change_per_day','spearman','linear_day_residual_pearson'} and y[key]!='NA':
                    compare(float(x[key]),float(y[key]),name+' '+key)
                else:
                    compare(x[key],y[key],name+' '+key)
    independent=a.read_json(HERE/'INDEPENDENT_CHECK.json')
    assert independent['status']=='PASS' and independent['imports_primary_analysis'] is False
    assert independent['expression_strings_compared']==2750 and independent['association_coefficients_checked']==56
    coverage=a.read_json(HERE/'GENE_COVERAGE.json')
    assert coverage['status']=='PASS' and coverage['included_genes']==genes and coverage['absent_genes']==[]
    test=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(HERE),'-p','test_analyze.py'],capture_output=True,text=True)
    if test.returncode:raise AssertionError(test.stdout+test.stderr)
    print(test.stderr.strip())
    print('PASS offline calibration: 125 genes; 22 RNA records; 21 paired observations; two donors; all frozen sensitivities; no population or intervention inference.')


if __name__=='__main__':
    main()
