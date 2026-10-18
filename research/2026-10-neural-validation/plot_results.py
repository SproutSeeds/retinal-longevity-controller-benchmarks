#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["matplotlib==3.11.2", "numpy==2.5.4"]
# ///
"""Standalone scientific figures derived only from archived observed results."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / 'figures'
C = {'ink':'#142E3A', 'teal':'#087F83', 'amber':'#9B5D22', 'gray':'#647783'}
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11, 'axes.spines.top':False,
                     'axes.spines.right':False, 'pdf.fonttype':42, 'axes.labelcolor':C['ink']})


def read(name):
    return json.loads((HERE / name).read_text())


def save(fig, name):
    fig.savefig(OUT / (name + '.png'), dpi=180, bbox_inches='tight')
    fig.savefig(OUT / (name + '.pdf'), bbox_inches='tight',
                metadata={'CreationDate':None, 'ModDate':None, 'Creator':'plot_results.py'})
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    cross = read('analysis/cross-cohort-results.json')
    row = next(x for x in cross['comparisons'] if x['celltype']=='Microglia'
               and x['panel_name']=='cycle_panel' and x['support_tier']=='primary_support')
    fig, ax = plt.subplots(figsize=(9, 4.5))
    fig.subplots_adjust(bottom=.27)
    for y, key, color in [(1,'cohort2',C['teal']), (0,'cohort1',C['amber'])]:
        d = row[key + '_direction_details']['log2_cpm']
        lo, hi = d['animal_omission_range']
        ax.plot([lo,hi],[y,y],color=color,lw=4,alpha=.55)
        ax.scatter([d['mean_difference']],[y],s=100,color=color,zorder=4)
        ax.text(d['mean_difference'],y+.14,f"Full mean {d['mean_difference']:+.3f}",ha='center',color=color)
        ax.text((lo+hi)/2,y-.2,f"Omission range {lo:+.3f} to {hi:+.3f}",ha='center',fontsize=10)
    ax.axvline(0,color=C['gray'],lw=1,ls='--')
    ax.set_yticks([0,1],['Cohort 1\n2 treated, 2 controls','Cohort 2\n2 treated, 2 controls'])
    ax.set_ylim(-.5,1.5)
    ax.set_xlabel('Treated − control mean log2(1 + CPM) panel score')
    ax.set_title('Microglial cell-cycle means agree; individual animals limit consistency',pad=18)
    fig.text(.14,.03,'Lines show leave-one-animal ranges, not confidence intervals. Same study, different cohorts.\nSource: Xu et al., Nature Aging 2024, GSE224438. Gene and lane sensitivities remain in the full results.',fontsize=9)
    save(fig,'neural-animal-sensitivity')

    human = read('human/marker-audit.json')
    rows = [x for construct in ['OSK','O4YRSK'] for method in ['log2_cpm','log2_median_ratio_cpm_equivalent']
            for x in human['contrasts'] if x['construct']==construct and x['method']==method
            and x['panel']=='reprogramming_without_OSK_overlap']
    fig, ax = plt.subplots(figsize=(9,5.0))
    fig.subplots_adjust(bottom=.25)
    for y,row in enumerate(rows):
        cd = next(x for x in row['gene_details'] if x['gene']=='CD24')
        part = cd['additive_contribution']
        ax.barh(y,part,color=C['teal'])
        ax.barh(y,row['mean_difference']-part,left=part,color='#CBD5DA')
        ax.text(part/2,y,f"CD24 {cd['signed_share']:.1%}",ha='center',va='center',color='white',fontsize=10)
    ax.set_yticks(range(4),['OSK / CPM','OSK / median ratio','O4YRSK / CPM','O4YRSK / median ratio'])
    ax.invert_yaxis()
    ax.set_xlabel('Additive contribution to treated − control seven-gene panel difference')
    ax.set_title('CD24 contributes most of this selected human bulk marker difference',pad=18)
    fig.text(.14,.03,'Teal: CD24. Gray: signed sum of the other six fixed genes. One donor, eight libraries.\nSource: Lu et al., Cell 2025, GSE297233. Counts do not establish a calibrated cell state.',fontsize=9)
    save(fig,'human-marker-concentration')

    bulk = read('bulk/results.json')
    fig, axes = plt.subplots(1,3,figsize=(12,4),sharey=True)
    methods = [('log2_cpm','CPM'),('log2_median_ratio','Median ratio'),('within_library_rank','Within-library rank')]
    for ax,(method,label) in zip(axes,methods):
        row = next(x for x in bulk['panel_results'] if x['method']==method and x['panel']=='cycle_panel')
        for y,s in enumerate(row['scores']):
            ax.scatter(s['delta'],y,color=C['amber'] if s['age_group']=='old' else C['teal'],s=42)
        ax.axvline(0,color=C['gray'],lw=1,ls='--')
        ax.set_title(label)
        ax.set_xlabel('Paired score difference')
    axes[0].set_yticks(range(9),[s['donor_id']+' ('+s['age_group']+')' for s in row['scores']])
    axes[0].invert_yaxis()
    fig.suptitle('The acute neural cell-cycle panel decreases in every paired donor',y=1.05,fontsize=14)
    fig.text(.11,-.06,'Each dot is one donor’s 18-hour Dox/OSKM minus untreated culture. Axes use different score units.\nSource: Xu et al., Nature Aging 2024, GSE245385. Direction agreement does not establish rejuvenation or a causal age effect.',fontsize=9)
    fig.tight_layout()
    save(fig,'bulk-paired-cycle')
    inputs = ['analysis/cross-cohort-results.json','human/marker-audit.json','bulk/results.json']
    receipt={'source_sha256':{p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in inputs},
             'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'figures':[p.name for p in sorted(OUT.iterdir()) if p.suffix in {'.png','.pdf'}],
             'scope':'Descriptive figures from observed outputs. Omission ranges are not confidence intervals.'}
    (OUT/'SOURCES.json').write_text(json.JSONEncoder(indent=2,sort_keys=True).encode(receipt)+'\n')


if __name__=='__main__':
    main()
