#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["numpy==2.5.4", "pandas==3.0.6", "scipy==1.18.1", "h5py==3.16.0", "scikit-learn==1.9.1", "openpyxl==3.1.5", "matplotlib==3.11.2"]
# ///
"""Source-native diagnostics under analysis-contract.json; no biological promotion."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import re

import h5py
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.special import roots_jacobi
from scipy.stats import spearmanr

HERE=Path(__file__).resolve().parent
CFG=json.loads((HERE/'analysis-contract.json').read_text())
PANELS=json.loads((HERE/'panels.json').read_text())

def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def save(name,obj):
 (HERE/name).write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n')

def receipt():
 return {'claim_level':'Heuristic','contract_sha256':digest(HERE/'analysis-contract.json'),'evidence_class':'derived_observed'}

def checked(cache,name):
 rows=json.loads((HERE/'input-files.json').read_text())['files']
 row=next(r for r in rows if r['id']==name)
 path=cache/name
 if not path.exists() or digest(path)!=row['sha256']:raise ValueError('Missing or changed source: '+name)
 return path

def h5column(group,key):
 obj=group[key]
 if isinstance(obj,h5py.Group):
  cat=obj['categories'][:];cat=np.array([v.decode() if isinstance(v,bytes) else v for v in cat],dtype=object)
  return np.array([cat[i] if i>=0 else None for i in obj['codes'][:]],dtype=object)
 v=obj[:]
 if '__categories' in group and key in group['__categories']:
  cat=group['__categories'][key][:];cat=[x.decode() if isinstance(x,bytes) else x for x in cat]
  return np.array([cat[i] if i>=0 else None for i in v],dtype=object)
 if v.dtype.kind in 'SO':return np.array([x.decode() if isinstance(x,bytes) else x for x in v],dtype=object)
 return v

def bulk(cache,acc):
 row=json.loads((HERE/'bulk-inputs.json').read_text())[acc]
 p=checked(cache,row['matrix_file'])
 raw=pd.read_csv(p,sep='\t' if p.name.endswith('txt.gz') else ',',index_col=0).drop(columns=['Gene type'],errors='ignore')
 if raw.columns.has_duplicates or raw.isna().any().any() or (raw.values<0).any() or not np.isfinite(raw.values).all():raise ValueError('Invalid count matrix')
 totals=raw.sum(axis=0)
 if (totals<=0).any() or (raw.values%1!=0).any():raise ValueError('Expected positive integer-count libraries')
 keep=~(raw.index.isna()|raw.index.duplicated(False))
 cpm=raw.loc[keep].div(totals,axis=1)*1e6
 return raw,cpm,np.log2(1+cpm),totals

def group_guides(guides,names,machinery,minimum=5,dominance=.8,require_pair=True):
 """Target sums include both guide channels. All channels enter denominator."""
 guides=np.asarray(guides)
 if guides.ndim!=2 or guides.shape[1]!=len(names) or len(machinery)!=len(guides):raise ValueError('Guide dimensions')
 if not np.isfinite(guides).all() or (guides<0).any() or (guides%1!=0).any():raise ValueError('Guide UMI counts')
 groups={}
 for i,name in enumerate(names):
  if re.fullmatch(r'NT_\d+',name):key='NT'
  elif re.fullmatch(r'.+_(CRA|CRI)[12]',name):key=name[:-1]
  else:raise ValueError('Unknown guide channel '+name)
  groups.setdefault(key,[]).append(i)
 keys=sorted(groups)
 grouped=np.column_stack([guides[:,groups[k]].sum(axis=1) for k in keys])
 detected=np.column_stack([(guides[:,groups[k]]>0).sum(axis=1) for k in keys])
 total=guides.sum(axis=1);top=grouped.argmax(axis=1);best=grouped[np.arange(len(top)),top]
 frac=np.divide(best,total,out=np.zeros(len(best),float),where=total>0)
 labels=np.full(len(top),'unassigned',dtype=object)
 candidate=(best>=minimum)&(frac>=dominance)
 for i in np.flatnonzero(candidate):
  k=keys[top[i]]
  if machinery[i] not in ['CRA','CRI']:continue
  if k!='NT' and (not k.endswith('_'+machinery[i]) or len(groups[k])!=2):continue
  if require_pair and detected[i,top[i]]<2:continue
  labels[i]=machinery[i]+'_NT' if k=='NT' else k
 return labels,{'guide_groups':len(keys),'target_groups_missing_a_pair':[k for k in keys if k!='NT' and len(groups[k])!=2],
                'NT_channels':len(groups.get('NT',[]))}

def old_guides(guides,names,machinery):
 total=guides.sum(1);top=guides.argmax(1);best=guides[np.arange(len(top)),top]
 fraction=np.divide(best,total,out=np.zeros(len(top),float),where=total>0)
 labels=np.full(len(top),'unassigned',dtype=object)
 for i in np.flatnonzero((best>=5)&(fraction>=.8)):
  name=names[top[i]]
  if name.startswith('NT_') and machinery[i] in ['CRA','CRI']:labels[i]=machinery[i]+'_NT'
  elif name[:-1].endswith('_'+machinery[i]):labels[i]=name[:-1]
 return labels

def aggregate(counts,labels):
 groups,idx=np.unique(labels,return_inverse=True)
 assignment=csr_matrix((np.ones(len(idx)),(idx,np.arange(len(idx)))),shape=(len(groups),len(idx)))
 pb=(assignment@counts).toarray();sizes=np.bincount(idx)
 if not np.allclose(pb.sum(axis=0),np.asarray(counts.sum(axis=0)).ravel()):raise ValueError('Aggregation does not conserve counts')
 return groups,pb,sizes

def perturbation(cache):
 path=checked(cache,'exp3_merged_not_normalized.h5ad')
 with h5py.File(path,'r') as f:
  names=sorted(k for k in f['obs'] if re.fullmatch(r'.+_(CRA|CRI)[12]|NT_\d+',k))
  guides=np.column_stack([h5column(f['obs'],k) for k in names])
  a,b=h5column(f['obs'],'CRA'),h5column(f['obs'],'CRI')
  if ((a==1)&(b==1)).any():raise ValueError('Conflicting machinery')
  machinery=np.where(a==1,'CRA',np.where(b==1,'CRI','WT'))
  samples=h5column(f['obs'],'SampleName');barcodes=h5column(f['obs'],'_index');genes=h5column(f['var'],'_index')
  x=f['X'];counts=csr_matrix((x['data'][:],x['indices'][:],x['indptr'][:]),shape=tuple(x.attrs['shape']))
 if len(set(barcodes))!=len(barcodes) or len(set(genes))!=len(genes):raise ValueError('Duplicate identifiers')
 if not np.isfinite(counts.data).all() or (counts.data<0).any() or (counts.data%1!=0).any():raise ValueError('Invalid RNA counts')
 old=old_guides(guides,names,machinery)
 result=receipt()|{'source_sha256':digest(path),'cells':len(samples),'guide_columns':len(names),
  'methods_source':'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12799168/supplementaryFiles',
  'methods_locator':'SI Appendix, page 3, Single-cell RNA sequencing and Perturb-seq',
  'authority':'Dual-guide design is author documented. Exact author demultiplexing remains unspecified; all assignments here are reconstructed.',
  'variants':[]}
 priority=['E2F3_CRA','EZH2_CRA','STAT3_CRI','ZFX_CRI']
 for minimum,dominance,pair in [(5,.8,True),(3,.7,True),(10,.9,True),(5,.8,False)]:
  labels,structure=group_guides(guides,names,machinery,minimum,dominance,pair)
  admitted=labels!='unassigned';old_admitted=old!='unassigned'
  change={'new_assigned':int(admitted.sum()),'previous_assigned':int(old_admitted.sum()),
   'newly_assigned':int((admitted&~old_admitted).sum()),'no_longer_assigned':int((~admitted&old_admitted).sum()),
   'different_target_among_both':int((admitted&old_admitted&(labels!=old)).sum())}
  labels[machinery=='WT']=['WT_'+str(s) for s in samples[machinery=='WT']]
  groups,pb,sizes=aggregate(counts,labels)
  cpm=pb/pb.sum(1,keepdims=True)*1e6;log=np.log2(1+cpm);index={g:i for i,g in enumerate(groups)}
  early,late=index['WT_PD14'],index['WT_PD32'];axis=log[late]-log[early]
  eligible=(cpm[early]>=1)&(cpm[late]>=1);no_cycle=eligible&~np.isin(genes,PANELS['cycle_panel'])
  effects=[]
  for g in groups:
   if not g.endswith(('_CRA','_CRI')) or sizes[index[g]]<20:continue
   target,mode=g.rsplit('_',1);nt=index.get(mode+'_NT')
   if nt is None or sizes[nt]<20:continue
   delta=log[index[g]]-log[nt];positions=np.flatnonzero(genes==target)
   target_effect=float(delta[positions[0]]) if len(positions) else None
   effects.append({'perturbation':g,'cells':int(sizes[index[g]]),'NT_cells':int(sizes[nt]),
    'pearson_r':float(np.corrcoef(axis[eligible],delta[eligible])[0,1]),
    'r_excluding_cycle_panel':float(np.corrcoef(axis[no_cycle],delta[no_cycle])[0,1]),
    'target_log2CPM_difference':target_effect,
    'target_direction_consistent':bool(target_effect>0 if mode=='CRA' else target_effect<0) if target_effect is not None else None})
  item={'minimum_target_UMI':minimum,'target_dominance':dominance,'require_pair':pair,'structure':structure,
        'assignment_changes':change,'cell_group_sizes':{str(g):int(n) for g,n in zip(groups,sizes)},
        'tested_perturbations':len(effects),'effects':sorted(effects,key=lambda r:r['perturbation']),
        'priority_hits':[next((r for r in effects if r['perturbation']==g),{'perturbation':g,'status':'below threshold or absent'}) for g in priority]}
  result['variants'].append(item)
  print('paired guides',minimum,dominance,pair,change,'eligible',len(effects),flush=True)
  if minimum==5 and pair:
   pd.DataFrame({'barcode':barcodes,'machinery':machinery,'sample':samples,'previous':old,'reconstructed_pair_group':labels}).to_csv(HERE/'guide-call-comparison.tsv.gz',sep='\t',index=False,compression={'method':'gzip','mtime':0})
 save('paired-guide-results.json',result)

def corr(x,y):return {'pearson_r':float(np.corrcoef(x,y)[0,1]),'spearman_r':float(spearmanr(x,y).statistic)}

def ocular(cache):
 raw,cpm,log,totals=bulk(cache,'GSE304038')
 log.index=log.index.astype(str).str.upper();cpm.index=log.index
 keep=~log.index.duplicated(False);log=log.loc[keep];cpm=cpm.loc[keep]
 cols=list(log.columns)
 groups={'young':[c for c in cols if c.startswith('Young-')], 'old':[c for c in cols if c.startswith('Old-rep')],
         'vector':[c for c in cols if c.startswith('Old-Control-')], 'OSK':[c for c in cols if c.startswith('Old-OSK-')]}
 if set(sum(groups.values(),[]))!=set(cols) or min(map(len,groups.values()))<2:raise ValueError('RPE group admission')
 def contrasts(gr):
  means={k:log[v].mean(axis=1) for k,v in gr.items()}
  return means['old']-means['young'],means['OSK']-means['vector'],means['vector']-means['old']
 age,effect,vector=contrasts(groups)
 result=receipt()|{'groups':groups,'units':'gene-wise log2(CPM+1) contrasts; no biological replicate p-values','sensitivities':[],
  'coupling_warning':'age=(old-young), vector_shift=(vector-old) share old with opposite signs; their correlation is algebraically coupled, not independent evidence of a batch effect.',
  'source_sha256':digest(checked(cache,json.loads((HERE/'bulk-inputs.json').read_text())['GSE304038']['matrix_file']))}
 for threshold in [1,5,10]:
  eligible=(cpm[groups['old']].mean(axis=1)>=threshold)&(cpm[groups['young']].mean(axis=1)>=threshold)
  for excluded in [[],PANELS['cycle_panel']+PANELS['reprogramming_state']]:
   mask=eligible&~log.index.isin(excluded)
   result['sensitivities'].append({'baseline_CPM_threshold':threshold,'exclude_fixed_cycle_and_reprogramming_panels':bool(excluded),'genes':int(mask.sum()),
    'age_vs_OSK_vector':corr(age[mask],effect[mask]),'age_vs_vector_old_algebraically_coupled':corr(age[mask],vector[mask])})
 eligible=(cpm[groups['old']].mean(axis=1)>=1)&(cpm[groups['young']].mean(axis=1)>=1)
 loo=[]
 for group,columns in groups.items():
  for column in columns:
   new={g:list(v) for g,v in groups.items()};new[group].remove(column)
   a,e,_=contrasts(new);loo.append({'omitted':column,'group':group,**corr(a[eligible],e[eligible])})
 result['leave_one_library_out']=loo
 # Independent group centroids are descriptive; no residualization claims.
 from sklearn.decomposition import PCA
 x=log.loc[eligible].T.to_numpy();pca=PCA(n_components=2,svd_solver='full');scores=pca.fit_transform(x)
 result['PCA']={'variance_ratio':pca.explained_variance_ratio_.tolist(),'scores':[{'sample':col,'PC1':float(a),'PC2':float(b)} for col,(a,b) in zip(log.columns,scores)]}
 result['library_totals']={k:float(v) for k,v in totals.items()}
 save('ocular-sensitivity-results.json',result)
 print('RPE sensitivities',[(r['baseline_CPM_threshold'],r['age_vs_OSK_vector']['pearson_r']) for r in result['sensitivities']],flush=True)

def human(cache):
 from sklearn.pipeline import make_pipeline
 from sklearn.preprocessing import StandardScaler
 from sklearn.linear_model import LogisticRegression
 from sklearn.metrics import roc_auc_score,balanced_accuracy_score
 raw,cpm,log,totals=bulk(cache,'GSE325735')
 mappath=checked(cache,'43587_2026_1234_MOESM15_ESM.xlsx')
 mapping=pd.read_excel(mappath,sheet_name='3e')[['ENSG_clean','Symbol']].dropna().drop_duplicates()
 badids=mapping.loc[mapping.ENSG_clean.duplicated(False),'ENSG_clean'];badsym=mapping.loc[mapping.Symbol.duplicated(False),'Symbol']
 mapping=mapping[~mapping.ENSG_clean.isin(badids)&~mapping.Symbol.isin(badsym)]
 lookup=dict(zip(mapping.ENSG_clean,mapping.Symbol));log.index=[lookup.get(str(g).split('.')[0],str(g)) for g in log.index]
 if log.index.has_duplicates:raise ValueError('Ambiguous gene symbols')
 meta=pd.DataFrame(json.loads((HERE/'sample-metadata.json').read_text())['samples'])
 rows=meta[(meta.accession=='GSE325735')&(meta.on_days_geo==5)&(meta.off_days_geo==2)&~meta.construct_conflict&meta.genotype.isin(['SRSF1','mTagBFP2'])].sort_values('matrix_column')
 names=rows.matrix_column.tolist();donors=rows.donor_or_line.to_numpy();y=(rows.genotype=='SRSF1').to_numpy().astype(int)
 if len(set(donors))!=3:raise ValueError('Expected 3 donors')
 for d in sorted(set(donors)):
  sub=rows[rows.donor_or_line==d]
  if set(sub.genotype)!= {'SRSF1','mTagBFP2'} or sub.experimental_batch_from_description.nunique(dropna=False)!=1 or sub.sequencing_batch.nunique()!=1:raise ValueError('Unmatched donor controls')
 panelnames=sorted(set(sum([PANELS[k] for k in ['fibroblast_identity','reprogramming_state','cycle_panel','stress_panel']],[])))
 features=[g for g in panelnames if g in log.index]
 x=log.loc[features,names].T.to_numpy();noncycle=[i for i,g in enumerate(features) if g not in PANELS['cycle_panel']]
 nuisance=np.column_stack([np.log1p(totals[names]),np.log1p((raw[names]>0).sum(axis=0))])
 variants={'expression':(x,features),'expression_without_cycle':(x[:,noncycle],[features[i] for i in noncycle]),'depth_only':(nuisance,['log_library_size','log_detected_genes'])}
 result=receipt()|{'task':'SRSF1 versus BFP treatment recognition, 5d on/2d off','donors':sorted(set(donors)),'libraries':len(names),
  'authority':'Within-study leave-one-donor-out diagnostic. Three donors are not a powered independent study validation. Treatment recognition does not measure benefit or safety.',
  'batch_limit':'All 12 libraries share sequencing batch LIB092645. Experimental batch is unrecorded for all 12; common missingness does not establish common experimental batch.',
  'samples':[{'library':n,'donor':str(d),'SRSF1':int(v)} for n,d,v in zip(names,donors,y)],'variants':{}}
 def fit_fold(xx,labels,held):
  train=donors!=held;test=~train
  model=make_pipeline(StandardScaler(),LogisticRegression(C=1,class_weight='balanced',max_iter=2000,random_state=CFG['seed']))
  model.fit(xx[train],labels[train]);pred=model.predict_proba(xx[test])[:,1]
  return train,test,model,pred
 for variant,(xx,fnames) in variants.items():
  out=np.zeros(len(y));folds=[]
  for d in sorted(set(donors)):
   train,test,model,pred=fit_fold(xx,y,d);out[test]=pred;scaler,est=model[0],model[1]
   folds.append({'held_donor':str(d),'train_libraries':np.array(names)[train].tolist(),'test_libraries':np.array(names)[test].tolist(),
    'AUROC':float(roc_auc_score(y[test],pred)),'balanced_accuracy':float(balanced_accuracy_score(y[test],pred>=.5)),
    'coefficients':est.coef_[0].tolist(),'intercept':float(est.intercept_[0]),'scaler_mean':scaler.mean_.tolist(),'scaler_scale':scaler.scale_.tolist()})
  result['variants'][variant]={'features':fnames,'folds':folds,'pooled_library_AUROC':float(roc_auc_score(y,out)),
   'mean_donor_AUROC':float(np.mean([f['AUROC'] for f in folds])),'out_of_donor_probabilities':out.tolist()}
 # Exact balanced within-donor relabelings give an algorithmic negative control.
 ds=sorted(set(donors));indices=[np.flatnonzero(donors==d) for d in ds]
 if all(len(ix)==4 and y[ix].sum()==2 for ix in indices):
  assignments=[list(itertools.combinations(ix,2)) for ix in indices]
  for variant,(xx,_) in variants.items():
   null=[]
   for combo in itertools.product(*assignments):
    labels=np.zeros(len(y),int);labels[list(sum((list(c) for c in combo),[]))]=1
    fold_aucs=[]
    for d in ds:
     _,test,_,pred=fit_fold(xx,labels,d);fold_aucs.append(roc_auc_score(labels[test],pred))
    null.append(float(np.mean(fold_aucs)))
   observed=result['variants'][variant]['mean_donor_AUROC']
   result['variants'][variant]['balanced_label_control']={'enumerated':len(null),'mean':float(np.mean(null)),
    'fraction_at_least_observed':float(np.mean(np.array(null)>=observed-1e-12)),
    'interpretation':'Technical-label exchangeability diagnostic, not a donor-level biological efficacy p-value.','scores':null}
 else:result['permutation_hold']='Design was not exactly three donors with two libraries per arm.'
 save('donor-model-results.json',result)
 print('Donor diagnostic',[(v,r['mean_donor_AUROC']) for v,r in result['variants'].items()],flush=True)

def detection(prevalence,sensitivity,donors,cells_per_donor,rho,quadrature=256):
 if not (0<prevalence<1 and 0<sensitivity<=1 and 0<=rho<1 and donors>=1 and cells_per_donor>=1):raise ValueError('Invalid sampling parameters')
 if rho==0:return float(-np.expm1(donors*cells_per_donor*np.log1p(-prevalence*sensitivity)))
 concentration=1/rho-1;a=prevalence*concentration;b=(1-prevalence)*concentration
 nodes,weights=roots_jacobi(quadrature,b-1,a-1)
 q=(nodes+1)/2;weights=weights/weights.sum()
 zero=float(np.dot(weights,np.exp(cells_per_donor*np.log1p(-sensitivity*q))))
 return float(1-zero**donors)

def synthetic():
 result=receipt()|{'evidence_class':'synthetic_only','assumptions':CFG['synthetic'],'scenarios':[],'false_positive_scenarios':[]}
 for p,rho,d in itertools.product([.001,.01,.05],[0,.01,.05,.1],[1,3,6]):
  n=1200//d
  result['scenarios'].append({'prevalence':p,'latent_donor_ICC':rho,'donors':d,'cells_per_donor':n,'sensitivity':.8,
                            'probability_at_least_one_detected':detection(p,.8,d,n,rho)})
 for n,specificity in itertools.product([373,1200],[.99,.999,.9999]):
  result['false_positive_scenarios'].append({'cells':n,'specificity':specificity,'true_prevalence':0,'probability_at_least_one_false_flag':float(-np.expm1(n*np.log(specificity)))})
 rng=np.random.default_rng(CFG['seed']);checks=[]
 for p,rho,d in [(.01,.05,1),(.01,.05,6),(.001,.1,3),(.05,.01,3)]:
  n=1200//d;c=1/rho-1;q=rng.beta(p*c,(1-p)*c,size=(100000,d))
  prob=1-np.prod((1-.8*q)**n,axis=1);estimate=float(prob.mean());se=float(prob.std(ddof=1)/np.sqrt(len(prob)))
  exact=detection(p,.8,d,n,rho);double=detection(p,.8,d,n,rho,512)
  checks.append({'prevalence':p,'rho':rho,'donors':d,'quadrature':exact,'quadrature_512':double,'MonteCarlo':estimate,'MonteCarlo_SE':se,
                 'within_5SE_plus_1e-4':abs(estimate-exact)<5*se+1e-4})
 result['checks']=checks;save('clustered-sampling-results.json',result)
 print('Synthetic scenarios',len(result['scenarios']),'checks',all(c['within_5SE_plus_1e-4'] for c in checks),flush=True)

def liver(cache):
 from scipy.sparse import csc_matrix
 config=json.loads((HERE/'liver-contract.json').read_text())
 sources=json.loads((HERE/'source-manifest.json').read_text())['files']
 result=receipt()|{'source':'GSE144600','evidence_class':'derived_observed','liver_contract_sha256':digest(HERE/'liver-contract.json'),
  'authority':'Observed mouse liver snapshot after one day on and one day off. Whole-library mixtures; no independent-donor or human/ocular inference.','libraries':[]}
 for name,condition in [('liver-minus.h5','minusDox'),('liver-plus.h5','plusDox_1day_on_1day_off')]:
  path=cache/name;source=next(r for r in sources if r['name']==name)
  if digest(path)!=source['sha256']:raise ValueError('Changed liver matrix')
  with h5py.File(path,'r') as f:
   group=f['matrix'] if 'matrix' in f else f['mm10']
   x=csc_matrix((group['data'][:],group['indices'][:],group['indptr'][:]),shape=tuple(group['shape'][:])).T.tocsr()
   genes=group['gene_names'][:] if 'gene_names' in group else group['features']['name'][:]
   genes=np.array([v.decode() if isinstance(v,bytes) else str(v) for v in genes])
   barcodes=[v.decode() if isinstance(v,bytes) else str(v) for v in group['barcodes'][:]]
  if len(set(barcodes))!=len(barcodes) or (x.data<0).any() or (x.data%1!=0).any() or not np.isfinite(x.data).all():raise ValueError('Invalid liver counts')
  totals=np.asarray(x.sum(1)).ravel();keep=totals>0
  mitochondrial=np.array([g.lower().startswith('mt-') for g in genes])
  mt_counts=np.asarray(x[:,mitochondrial].sum(1)).ravel()
  mt_fraction=np.divide(mt_counts,totals,out=np.zeros(len(totals),float),where=totals>0)
  source_qc=(totals>=2000)&(mt_fraction<=.45)
  scores={'barcode':[condition+':'+b for b,k in zip(barcodes,keep) if k],'total_counts':totals[keep]}
  summary={}
  for panel,markers in config['panels'].items():
   selected=[g for g in markers if np.sum(genes==g)==1];ix=[int(np.flatnonzero(genes==g)[0]) for g in selected]
   values=np.log2(1+x[keep][:,ix].toarray()/totals[keep,None]*1e4)
   score=values.mean(1);scores[panel]=score
   summary[panel]={'genes':selected,'missing_or_ambiguous':sorted(set(markers)-set(selected)),
    'median_log2CP10K':float(np.median(score)),'fraction_any_marker_detected':float(np.mean((values>0).any(1)))}
  result['libraries'].append({'condition':condition,'file':name,'source_url':source['url'],'source_sha256':source['sha256'],
   'deposited_cells':x.shape[0],'nonempty_cells':int(keep.sum()),'gene_rows':x.shape[1],'total_UMIs':int(x.sum()),'panels':summary,
   'posthoc_source_QC_sensitivity':{'cells':int(source_qc.sum()),'mitochondrial_gene_rows':int(mitochondrial.sum()),
    'rule':'At least 2000 deposited counts and at most 45% mitochondrial counts, mt- prefix.',
    'authority':'Post hoc source-method sensitivity, not the frozen primary. Paper says reads; this uses deposited UMI counts. Cell-set equivalence is unverified.'}})
  pd.DataFrame(scores).to_csv(HERE/(condition+'-cell-panels.tsv.gz'),sep='\t',index=False,compression={'method':'gzip','mtime':0})
 result['total_measured_cells']=sum(r['deposited_cells'] for r in result['libraries']);save('liver-withdrawal-results.json',result)
 print('Liver comparator observed cells',result['total_measured_cells'],flush=True)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('task',choices=['perturbation','ocular','human','synthetic','liver','all']);parser.add_argument('--cache',type=Path,default=HERE/'.cache')
 args=parser.parse_args()
 for name,func in [('perturbation',perturbation),('ocular',ocular),('human',human),('synthetic',lambda _:synthetic())]:
  if args.task in [name,'all']:func(args.cache)
 if args.task=='liver':liver(args.cache)

if __name__=='__main__':main()
