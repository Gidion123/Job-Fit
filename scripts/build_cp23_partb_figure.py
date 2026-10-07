"""Plot saved Part B coverage only; no inference and no quality claim."""
from collections import Counter
import json
from pathlib import Path
import os

os.environ.setdefault('MPLCONFIGDIR', '/tmp/jobfit_mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT/'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
RECEIPT = ROOT/'evals/results/cp23/end_to_end_dev/cp23_partb_completion_20261004_v2.json'
OUTPUT = ROOT/'reports/figures/cp2/fig07_partb_coverage_20261004_v1.png'


def main():
    receipt=json.loads(RECEIPT.read_text())
    rows=[json.loads(p.read_text()) for p in RUN.glob('match_*.json')]
    if len(rows)!=receipt['pairs_saved_final'] or receipt['scope']!='development_only':
        raise ValueError('Part B receipt or scope changed')
    names=['Final score','On hold','No score','No score object']
    keys=['final','on_hold','no_score','no_score_object']
    colors=['#238b45','#fdae61','#756bb1','#9e9e9e']
    fig,ax=plt.subplots(figsize=(8.5,4.8))
    for i,cv in enumerate(('CV1','CV2')):
        counts=Counter(r['score']['status'] if r.get('score') else 'no_score_object'
                       for r in rows if r['cv_id']==cv)
        left=0
        for label,key,color in zip(names,keys,colors):
            n=counts[key]
            ax.barh(i,n,left=left,color=color,label=label if i==0 else None)
            if n: ax.text(left+n/2,i,str(n),ha='center',va='center',color='black',fontsize=9)
            left+=n
        if left!=30: raise ValueError('Expected thirty saved pairs per CV')
    ax.set_yticks([0,1],['CV1','CV2']);ax.invert_yaxis()
    ax.set_xlim(0,30);ax.set_xlabel('Saved CV/JD pairs');ax.set_title('Part B output coverage')
    ax.legend(ncol=4,loc='upper center',bbox_to_anchor=(.5,-.13),fontsize=8)
    fig.text(.04,.01,'Development: Hybrid Qwen top30 per synthetic CV, DeepSeek Flash, K=30; 60 saved pairs. Holds are not zero scores.',fontsize=8)
    fig.tight_layout(rect=(0,.08,1,1))
    if OUTPUT.exists(): raise ValueError('Versioned figure already exists')
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(OUTPUT,dpi=180,bbox_inches='tight',facecolor='white')
    plt.close(fig)
    print(str(OUTPUT.relative_to(ROOT)))


if __name__=='__main__': main()
