#!/usr/bin/env python3
"""Verify the reviewed packet and decision boundaries, without data downloads."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
from build_decision import build

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE/name).read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    checks=[]
    def check(name,ok):
        checks.append({'name':name,'status':'PASS' if ok else 'FAIL'})
    manifest=read('public-files.json')
    files=manifest['files']
    check('public allowlist has no duplicates',len(files)==len(set(files)))
    check('private root scripts and correspondence excluded',not any(
        n in files for n in ['audit_mail.py','CAMPAIGN.md','writing-brief.yaml','prepare_public.py']))
    hashes=read('artifact-hashes.json')['files']
    check('hash manifest matches explicit allowlist',set(hashes)==set(files)|{'public-files.json'})
    for name,expected in hashes.items():
        path=HERE/name
        safe=not Path(name).is_absolute() and '..' not in Path(name).parts and not path.is_symlink()
        check('safe existing artifact '+name,safe and path.is_file())
        check('artifact SHA-256 '+name,path.is_file() and sha(path)==expected)
    for name in files:
        path=HERE/name
        if path.suffix in {'.md','.json','.csv','.tsv','.jsonl'}:
            text=path.read_text()
            check('private correspondence exclusion '+name,not any(
                marker in text for marker in ('cmail_runtime.db','cody@frg.earth',
                                              'cx004-ryan-reply','cx004-mail-review')))
    decision=read('decision.json')
    check('integrated evidence projection recomputes',build()==decision)
    check('all four biological readouts stay insufficient',set(decision['readouts'])=={
        f'CX004-R0{i}' for i in range(1,5)} and set(decision['readouts'].values())=={'insufficient_signal'})
    check('experiment replacement remains inconclusive',decision['experiment_replacement']=='INCONCLUSIVE')
    for key in ['public_search_universal_exhaustion_claim','unconditional_wetlab_necessity_proven',
                'retinal_efficacy_established','new_independent_clock_replay_completed',
                'new_observed_data_generated','new_wetlab_purchase_or_arrangement','paid_compute_used']:
        check('claim boundary '+key,decision[key] is False)
    human=read('human/recovery-reference-audit.json')
    check('three donors and twelve technical reference rows',human['biological_units']==3
          and human['technical_reference_rows']==12 and len(human['rows'])==12)
    expected=sum(r['reported_reference_srsf1_minus_bfp_years'] for r in human['donor_reference_contrasts'])/3
    check('human reference donor arithmetic',math.isclose(expected,human['equal_donor_mean_reported_difference_years'],abs_tol=1e-12))
    with (HERE/'ocular/results/sample_qc.csv').open(newline='') as stream:
        qc=list(csv.DictReader(stream))
    check('ten distinct mouse animals',len(qc)==len({r['animal_id'] for r in qc})==10)
    check('source and fixed-QC nucleus totals',sum(int(r['n_deposited']) for r in qc)==35907
          and sum(int(r['n_rna_qc']) for r in qc)==34210)
    check('primary mouse units are four and three',sum(r['group']=='APP_OSK' for r in qc)==4
          and sum(r['group']=='APP_GFP' for r in qc)==3)
    freeze=read('ocular/FREEZE.json')
    for name,expected in freeze['sha256'].items():
        check('original ocular frozen byte '+name,sha(HERE/'ocular'/name)==expected)
    correction=read('ocular/provenance-correction.json')
    panels=read('ocular/panels.json')
    check('inherited panel source location corrected without changing frozen bytes',
          correction['sha256']==panels['orthology_sha256']==sha(HERE/'ocular'/correction['resolved_copy'])
          and correction['frozen_file_sha256']==sha(HERE/'ocular/panels.json')
          and not correction['frozen_bytes_changed'] and not correction['outcomes_changed'])
    assignment=read('assignment/results.json')
    receipt=read('assignment/retrieval-2.json')
    source=next(r for r in receipt['sources'] if r['id']=='geo350289-metadata.xlsx')
    check('assignment workbook unchanged by exact fresh hash',source['sha256']==assignment['workbook_sha256']
          ==assignment['prior_workbook_sha256'] and assignment['workbook_unchanged'])
    check('assignment counts are sample records, not replication',assignment['series_sample_records']==769
          and not assignment['outcome_analysis_unlocked'])
    figures=read('figures/SOURCES.json')
    for name,expected in figures['source_sha256'].items():
        check('figure source binding '+name,sha(HERE/name)==expected)
    check('figure generator binding',sha(HERE/'plot_results.py')==figures['generator_sha256'])
    for name in files:
        if Path(name).suffix=='.md':
            for link in re.findall(r'\]\(([^)]+)\)',(HERE/name).read_text()):
                if '://' in link or link.startswith('#'):
                    continue
                target=link.split('#',1)[0]
                if target and not target.startswith('../2026-10-'):
                    check('local link '+name+' -> '+target,(HERE/Path(name).parent/target).exists())
    failures=[r for r in checks if r['status']=='FAIL']
    result={'schema':'cx004-decision-packet-verification/v1','status':'PASS' if not failures else 'FAIL',
            'passed':len(checks)-len(failures),'total':len(checks),'failed':failures,
            'scope':'Reviewed artifact bytes, source bindings, saved arithmetic and explicit evidence boundaries. Not biological validation.',
            'experiment_replacement':'INCONCLUSIVE'}
    if args.write:
        (HERE/'VERIFICATION.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(bool(failures))


if __name__=='__main__':
    main()
