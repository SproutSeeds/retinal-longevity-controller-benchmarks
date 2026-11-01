#!/usr/bin/env python3
"""Make the standalone scientific figure from released source-bound scores."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent


def residual(v,t):
    design=np.column_stack([np.ones(len(t)),t])
    return v-design@np.linalg.lstsq(design,v,rcond=None)[0]


def main():
    with (HERE/'sample-scores.tsv').open(newline='') as f:
        rows=list(csv.DictReader(f,delimiter='\t'))
    results=json.loads((HERE/'RESULTS.json').read_text())
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(2,4,figsize=(15.3,7.7),layout='constrained')
    colors={'HC1':'#235e91','HC2':'#a94f2d'}
    for i,donor in enumerate(['HC1','HC2']):
        series=sorted([r for r in rows if r['donor']==donor],key=lambda r:float(r['days_grown_source']))
        t=np.array([float(r['days_grown_source']) for r in series])
        x=np.array([float(r['score']) for r in series])
        y=np.array([float(r['function_value_source']) if r['function_present']=='true' else np.nan for r in series])
        valid=np.isfinite(y)
        summary=results['donors'][donor]
        axes[i,0].plot(t,x,'o-',color=colors[donor],lw=1.1,ms=5)
        if not valid.all():
            axes[i,0].scatter(t[~valid],x[~valid],s=105,facecolors='none',edgecolors='#111111',zorder=5)
            axes[i,0].annotate('RNA only',xy=(t[~valid][0],x[~valid][0]),xytext=(8,-19),textcoords='offset points',fontsize=9)
        axes[i,1].plot(t,y,'o-',color=colors[donor],lw=1.1,ms=5)
        scatter=axes[i,2].scatter(x[valid],y[valid],c=t[valid],cmap='viridis',vmin=0,vmax=205,s=45,edgecolors='white',linewidths=.4)
        axes[i,2].set_title('Raw association: ρ = %.3f'%summary['spearman_score_function'],fontsize=11)
        rx,ry=residual(x[valid],t[valid]),residual(y[valid],t[valid])
        axes[i,3].scatter(rx,ry,c=t[valid],cmap='viridis',vmin=0,vmax=205,s=45,edgecolors='white',linewidths=.4)
        axes[i,3].axhline(0,color='#bbbbbb',lw=.7);axes[i,3].axvline(0,color='#bbbbbb',lw=.7)
        axes[i,3].set_title('Linear time residuals: r = %.3f'%summary['linear_day_residual_pearson'],fontsize=11)
        axes[i,0].set_ylabel(donor+' · '+str(summary['paired_records'])+' paired records\nPanel mean (source log2 VST)')
        axes[i,1].set_ylabel('Spare capacity\n(pmol O₂/min/20,000 cells)')
        axes[i,2].set_ylabel('Spare capacity')
        axes[i,3].set_ylabel('Spare-capacity residual')
        axes[i,0].set_xlabel('Days in culture');axes[i,1].set_xlabel('Days in culture')
        axes[i,2].set_xlabel('Panel mean (source log2 VST)');axes[i,3].set_xlabel('Panel-expression residual')
        for ax in axes[i]:
            ax.grid(alpha=.15);ax.set_axisbelow(True)
    axes[0,0].set_title('125-gene panel expression',fontsize=11)
    axes[0,1].set_title('Measured respiratory capacity',fontsize=11)
    axes[1,0].set_title('125-gene panel expression',fontsize=11)
    axes[1,1].set_title('Measured respiratory capacity',fontsize=11)
    fig.colorbar(scatter,ax=axes[:,2:].ravel().tolist(),label='Days in culture',shrink=.78,pad=.02)
    fig.suptitle('RNA panel expression and respiration diverge across two donor culture series',fontsize=15)
    fig.supxlabel('Sturm et al. (2022) source cultures · Saul et al. (2022) human SenMayo genes\nHeuristic panel mean; two 18-year-old donors; descriptive observations of untreated culture aging.',fontsize=10)
    fig.savefig(HERE/'calibration.png',dpi=180,metadata={'Software':'Matplotlib; source-bound frozen analysis'})
    fig.savefig(HERE/'calibration.pdf',metadata={'Title':'RNA panel expression and respiration in two donor culture series','Author':'Longevity Research','Subject':'Frozen descriptive reanalysis of Sturm et al. data with Saul et al. panel','CreationDate':None,'ModDate':None})
    plt.close(fig)
    print('Saved calibration.png and calibration.pdf from the released score table.')


if __name__=='__main__':
    main()
