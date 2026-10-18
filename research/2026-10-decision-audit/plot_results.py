#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["matplotlib==3.11.2", "numpy==2.5.4"]
# ///
"""Descriptive figures from archived results; no new fit or inferential test."""
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / 'figures'
INK, TEAL, AMBER, GRAY = '#142E3A', '#087F83', '#A26526', '#647783'
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10,
    'axes.spines.top':False, 'axes.spines.right':False, 'pdf.fonttype':42,
    'axes.labelcolor':INK, 'text.color':INK})


def rows(name):
    with (HERE / name).open(newline='') as stream:
        return list(csv.DictReader(stream))


def save(fig, name):
    fig.savefig(OUT / (name + '.png'), dpi=180, bbox_inches='tight')
    fig.savefig(OUT / (name + '.pdf'), bbox_inches='tight',
                metadata={'CreationDate':None, 'ModDate':None, 'Creator':'plot_results.py'})
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    scores = [r for r in rows('ocular/results/animal_scores.csv')
              if r['panel']=='cycle_panel' and r['method']=='CPM']
    bins = [r for r in rows('ocular/results/marker_bin_contrasts.csv')
            if r['panel']=='cycle_panel' and r['minimum_cells_each_animal']=='50']
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.8), gridspec_kw={'width_ratios':[1,1.6]})
    fig.subplots_adjust(bottom=.27, top=.80, wspace=.65)
    groups = [('APP_GFP','GFP\n3 animals',GRAY), ('APP_OSK','OSK\n4 animals',TEAL)]
    for x,(group,label,color) in enumerate(groups):
        vals = [float(r['score']) for r in scores if r['group']==group]
        axes[0].scatter(x + np.linspace(-.08,.08,len(vals)), vals, s=52, color=color)
        axes[0].plot([x-.20,x+.20],[np.mean(vals)]*2,color=color,lw=2)
    axes[0].set_xticks([0,1],[g[1] for g in groups])
    axes[0].set_ylabel('Mean log2(1 + CPM) of cell-cycle genes')
    axes[0].set_title('A  Each point is one animal',loc='left',fontsize=11,pad=15)
    axes[0].text(.5, -.30, 'OSK − GFP = −0.124\nPermutation p = 13/35; Holm p = 1.0',
                 transform=axes[0].transAxes, ha='center', fontsize=9)
    order = ['excitatory_marker_bin','inhibitory_marker_bin','microglial_marker_bin',
             'oligodendrocyte_marker_bin','precursor_marker_bin','astrocyte_marker_bin',
             'ambiguous','unassigned']
    labels = ['Excitatory','Inhibitory','Microglial','Oligodendrocyte','Precursor',
              'Astrocyte','Ambiguous','Unassigned']
    for threshold, offset, color, symbol in [(1,-.12,TEAL,'o'), (2,.12,AMBER,'s')]:
        for y,name in enumerate(order):
            r = next(r for r in bins if r['bin']==name and int(r['threshold_umi'])==threshold)
            if r['status']=='available':
                axes[1].scatter(float(r['delta']),y+offset,s=40,color=color,marker=symbol,
                                label=f'≥{threshold} UMI / marker' if y==0 else None)
            elif threshold==1:
                axes[1].text(-.94,y,'insufficient cells',va='center',fontsize=8,color=GRAY)
    axes[1].axvline(0,color=GRAY,lw=1,ls='--')
    axes[1].set_yticks(range(len(order)),labels)
    axes[1].invert_yaxis()
    axes[1].set_xlabel('OSK − GFP cell-cycle panel difference')
    axes[1].set_title('B  Heuristic marker groups',loc='left',fontsize=11,pad=15)
    axes[1].legend(frameon=False,fontsize=8,loc='upper left',bbox_to_anchor=(0,1.0))
    fig.suptitle('Cell-cycle differences vary across marker groups in an independent mouse study',
                 x=.10, ha='left', y=.97, fontsize=14)
    fig.text(.10,.035,'GSE276656: seven female APP/PS1 mice in the treatment contrast. Three wild-type animals are context only.\n'
             'Marker groups require two expressed markers and ≥50 nuclei in every animal; they are not validated cell types.\n'
             'Points and bars show observed scores/means, not uncertainty intervals. Missing batch labels limit interpretation.', fontsize=9)
    save(fig,'mouse-cycle-comparison')

    human = json.loads((HERE/'human/recovery-reference-audit.json').read_text())
    fig, ax = plt.subplots(figsize=(9,4.8))
    fig.subplots_adjust(bottom=.29, top=.81, left=.21)
    for y,row in enumerate(human['donor_reference_contrasts']):
        value=row['reported_reference_srsf1_minus_bfp_years']
        ax.plot([0,value],[y,y],lw=2,color=TEAL,alpha=.55)
        ax.scatter(value,y,color=TEAL,s=60)
        ax.text(value-.3,y-.14,f'{value:.2f}',ha='right',fontsize=9)
    ax.axvline(0,color=GRAY,lw=1,ls='--')
    ax.set_yticks(range(3),[r['line']+' / '+r['donor'] for r in human['donor_reference_contrasts']])
    ax.set_xlim(-18,1)
    ax.set_ylim(-.5,2.5)
    ax.invert_yaxis()
    ax.set_xlabel('Published SRSF1 − BFP predicted-age difference (model-years)')
    ax.set_title('Published clock outputs after five days on and two days off',pad=20,fontsize=13)
    fig.text(.10,.035,'Three donor lines, two technical observations per construct and donor (12 reference rows).\n'
             'Equal-donor mean: −10.70 model-years. These are publisher reference outputs, not an independent clock replay\n'
             'or years of life restored. Source: Plesa et al., Nature Aging 2026, Source Data Fig. 4c.',fontsize=9)
    save(fig,'human-short-withdrawal-reference')
    inputs=['ocular/results/animal_scores.csv','ocular/results/marker_bin_contrasts.csv',
            'human/recovery-reference-audit.json']
    receipt={'source_sha256':{p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in inputs},
             'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'figures':[p.name for p in sorted(OUT.iterdir()) if p.suffix in {'.pdf','.png'}],
             'scope':'Descriptive displays only; no new biological observations, model fit or statistical test.'}
    (OUT/'SOURCES.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    main()
