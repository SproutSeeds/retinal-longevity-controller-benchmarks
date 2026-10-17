#!/usr/bin/env python3
"""Offline numerical/provenance checks; PASS is computational, not biological."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent

def read(name):return json.loads((HERE/name).read_text())

def verify():
 checks=[]
 def check(name,value):checks.append({'name':name,'status':'PASS' if value else 'FAIL'})
 contract=hashlib.sha256((HERE/'analysis-contract.json').read_bytes()).hexdigest()
 g=read('paired-guide-results.json');m=read('donor-model-results.json');o=read('ocular-sensitivity-results.json');s=read('clustered-sampling-results.json');l=read('liver-withdrawal-results.json')
 for name,obj in [('guides',g),('donor',m),('ocular',o),('synthetic',s),('liver',l)]:
  check(name+'_contract_bound',obj['contract_sha256']==contract)
  check(name+'_claim_bounded',obj['claim_level']=='Heuristic')
 for v in g['variants']:
  prefix=f"guide_{v['minimum_target_UMI']}_{v['require_pair']}"
  sizes=v['cell_group_sizes'];check(prefix+'_all_cells_accounted',sum(sizes.values())==g['cells']==36514)
  check(prefix+'_incomplete_pairs_excluded',not set(v['structure']['target_groups_missing_a_pair']) & set(sizes))
  check(prefix+'_effects_count',len(v['effects'])==v['tested_perturbations'])
  check(prefix+'_controls_and_cell_floor',all(r['cells']>=20 and r['NT_cells']>=20 for r in v['effects']))
  check(prefix+'_finite_correlations',all(math.isfinite(r['pearson_r']) and -1<=r['pearson_r']<=1 for r in v['effects']))
  check(prefix+'_published_priorities_all_retained',len(v['priority_hits'])==4)
  change=v['assignment_changes'];check(prefix+'_assignment_reconciliation',change['new_assigned']==change['previous_assigned']+change['newly_assigned']-change['no_longer_assigned'])
 check('paired_primary_count',g['variants'][0]['assignment_changes']['new_assigned']==10183)
 lookup={r['library']:r['donor'] for r in m['samples']}
 check('donor_units_3_not_12',len(set(lookup.values()))==3 and len(lookup)==12)
 for name,v in m['variants'].items():
  seen=[]
  for f in v['folds']:
   tr,te=set(f['train_libraries']),set(f['test_libraries']);seen.extend(te)
   check(name+'_'+f['held_donor']+'_no_donor_leak',not tr&te and {lookup[x] for x in te}=={f['held_donor']} and f['held_donor'] not in {lookup[x] for x in tr})
  check(name+'_each_library_tested_once',sorted(seen)==sorted(lookup))
  null=v['balanced_label_control'];check(name+'_216_balanced_controls',len(null['scores'])==null['enumerated']==216)
  check(name+'_negative_control_mean',abs(sum(null['scores'])/216-.5)<1e-10)
  check(name+'_three_fold_average',abs(v['mean_donor_AUROC']-sum(f['AUROC'] for f in v['folds'])/3)<1e-12)
 check('RPE_six_frozen_sensitivities',len(o['sensitivities'])==6)
 check('RPE_every_library_omitted_once',len(o['leave_one_library_out'])==sum(len(v) for v in o['groups'].values())==18)
 check('RPE_discordant_signal_retained',all(r['age_vs_OSK_vector']['pearson_r']>0 for r in o['sensitivities']))
 check('synthetic_separate_authority',s['evidence_class']=='synthetic_only')
 check('36_clustered_scenarios',len(s['scenarios'])==36)
 check('MonteCarlo_integration_agrees',all(c['within_5SE_plus_1e-4'] for c in s['checks']))
 check('quadrature_converges',all(abs(c['quadrature']-c['quadrature_512'])<1e-5 for c in s['checks']))
 check('fixed_total_cells',all(r['donors']*r['cells_per_donor']==1200 for r in s['scenarios']))
 check('independent_closed_form',all(abs(r['probability_at_least_one_detected']-(1-(1-r['prevalence']*.8)**1200))<1e-10 for r in s['scenarios'] if r['latent_donor_ICC']==0))
 check('false_positive_formula',all(abs(r['probability_at_least_one_false_flag']-(1-r['specificity']**r['cells']))<1e-10 for r in s['false_positive_scenarios']))
 check('liver_observed_count_accounted',l['total_measured_cells']==sum(r['deposited_cells'] for r in l['libraries']))
 check('liver_nonempty_measured',all(r['nonempty_cells']==r['deposited_cells'] for r in l['libraries']))
 resolution=read('source-resolution.json')
 check('all_readouts_stay_open',len(resolution['readout_verdicts'])==4 and set(resolution['readout_verdicts'].values())=={'insufficient_signal'})
 check('no_global_absence_claim','not exhaustive' in resolution['search_scope'])
 files=['analyze.py','analysis-contract.json','panels.json','input-files.json','sample-metadata.json','source-resolution.json','paired-guide-results.json','donor-model-results.json','ocular-sensitivity-results.json','clustered-sampling-results.json','liver-withdrawal-results.json','liver-contract.json']
 result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','claim_level':'Verified','scope':'Computational provenance, arithmetic and separation checks only. Biological replacement remains INCONCLUSIVE.',
  'checks':checks,'passed':sum(c['status']=='PASS' for c in checks),'total':len(checks),
  'artifact_hashes':{f:hashlib.sha256((HERE/f).read_bytes()).hexdigest() for f in files}}
 return result

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
 result=verify()
 if not args.write:
  expected=read('VERIFICATION.json')['artifact_hashes']
  changed=[name for name,value in result['artifact_hashes'].items() if expected.get(name)!=value]
  if changed:
   print('FAIL: artifact hashes differ from the recorded verification:',', '.join(changed))
   print('Review changes, rerun analyses as appropriate, then use --write for a new receipt.')
   raise SystemExit(1)
 if args.write:(HERE/'VERIFICATION.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(result['status'],str(result['passed'])+'/'+str(result['total']))
 for check in result['checks']:
  if check['status']!='PASS':print(check)
 raise SystemExit(0 if result['status']=='PASS' else 1)
