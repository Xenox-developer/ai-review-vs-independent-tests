"""Render only actual held-out task counts. No generated numerical content."""
import json
from pathlib import Path

from .prepare import ROOT


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    scores = json.loads((ROOT/'results/scores.json').read_text())['summary']
    sensitivity = json.loads((ROOT/'results/independent-recalculation.json').read_text())
    conditions = ['initial','review','tests']
    values = [scores[c]['passed'] for c in conditions]
    other = [sensitivity['counts'][c] for c in conditions]
    n = scores['tasks']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':16,
                         'axes.spines.top':False,'axes.spines.right':False})
    fig,ax = plt.subplots(figsize=(11.5,6.5),layout='constrained')
    fig.patch.set_facecolor('#f7f9fc'); ax.set_facecolor('#f7f9fc')
    x=list(range(3));width=.31
    bars = ax.bar([v-width/2 for v in x],values,color='#54729b',width=width,
                  label='Exact class',zorder=3)
    alternate = ax.bar([v+width/2 for v in x],other,color='#459384',width=width,
                       label='Subclass accepted',zorder=3)
    ax.set_xticks(x,['Initial','Review → repair','Tests → repair'])
    ax.set_ylim(0,n+1.1)
    ax.set_yticks(range(0,n+1))
    ax.set_ylabel('Tasks passed')
    ax.set_title('Tasks passing checks',loc='left',pad=65,fontweight='bold',fontsize=22)
    ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),ncol=2,frameon=False)
    ax.grid(axis='y',color='#dbe2ec',zorder=0)
    ax.spines[['left','bottom']].set_color('#c7d1de')
    ax.tick_params(length=0,pad=12)
    for series,numbers in ((bars,values),(alternate,other)):
        for bar,value in zip(series,numbers):
            ax.text(bar.get_x()+bar.get_width()/2,value+.18,f'{value}/{n}',ha='center',va='bottom',fontweight='bold',fontsize=18)
    fig.savefig(ROOT/'results/correctness.png',dpi=180)
    fig.savefig(ROOT/'results/correctness.svg')
    svg=ROOT/'results/correctness.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)


if __name__ == '__main__': main()
