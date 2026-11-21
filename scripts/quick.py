import sys, time; sys.path.insert(0, 'src')
from pvm.data.synthetic import make_cohort
from pvm.methods import run_methods
t=time.time()
ps = make_cohort(160, 4, seed=0)
res, ex = run_methods(ps, fed_rounds=200, sigmas=(0.5,8.0,32.0,128.0))
print(time.time()-t)
for k,v in res.items():
    print(k, {a:(round(b,3) if isinstance(b,float) else b) for a,b in v.items() if a in ('precision','recall','f1','fa_per_day','delay_min','auroc','auprc','tau','epsilon','rounds_to_converge','loss_gap')})
