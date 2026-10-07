"""Plot measured development coverage; never infer missing scores."""
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR','/tmp/jobfit_mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
SUMMARY=ROOT/'evals/results/cp23/pipeline_v11/coverage_summary_v2.json'
HOLD_OPTIONS=ROOT/'evals/results/cp23/pipeline_v11/hold_options_v1.json'
OUTPUT=ROOT/'reports/figures/cp2/fig08_pipeline_v11_coverage_20261004_v3.png'


def main():
    data=json.loads(SUMMARY.read_text())
    prior=json.loads(HOLD_OPTIONS.read_text())
    main=json.loads((SUMMARY.parent/'summary_v1.json').read_text())
    if len(data['pairs'])!=60 or len(prior['cases'])!=60:raise ValueError('Incomplete development coverage')
    labels=['v1 saved','v1.1 main','v1.1 follow-up']
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),sharey=True)
    for ax,policy in zip(axes,('H1','H2')):
        before=[sum(r['cv_id']==cv and r[f'{policy}_status'] in ('final','provisional')
                    for r in prior['cases']) for cv in ('CV1','CV2')]
        cv1=[before[0],main['per_cv']['CV1'][policy],data['per_cv']['CV1'][policy]]
        cv2=[before[1],main['per_cv']['CV2'][policy],data['per_cv']['CV2'][policy]]
        x=range(3)
        ax.bar([i-.2 for i in x],cv1,width=.4,label='CV1',color='#238b45')
        ax.bar([i+.2 for i in x],cv2,width=.4,label='CV2',color='#2171b5')
        for i,(a,b) in enumerate(zip(cv1,cv2)):
            ax.text(i-.2,a+.35,str(a),ha='center',fontsize=9)
            ax.text(i+.2,b+.35,str(b),ha='center',fontsize=9)
        ax.set_ylim(0,33);ax.set_yticks(range(0,31,5))
        ax.set_xticks(list(x),labels,rotation=12)
        ax.set_title(f'{policy}: '+('whole-job hold' if policy=='H1' else 'limited provisional exclusion'))
        ax.axhline(27,color='#bb3e03',linestyle='--',linewidth=1)
    axes[0].set_ylabel('Scored pairs per CV, out of 30')
    axes[1].legend()
    fig.suptitle('Development score coverage on the same 60 pairs')
    fig.text(.03,.01,'H2 on saved v1 outputs is an offline counterfactual. Formal target: 54 of 60 overall; dashed 27/30 per CV is a reference. Missing scores stay missing.',fontsize=8)
    fig.tight_layout(rect=(0,.08,1,.94))
    if OUTPUT.exists():raise ValueError('Versioned figure already exists')
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(OUTPUT,dpi=180,bbox_inches='tight',facecolor='white')
    plt.close(fig)
    print(str(OUTPUT.relative_to(ROOT)))


if __name__=='__main__':main()
