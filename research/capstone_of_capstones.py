#!/usr/bin/python3
# =============================================================================
# capstone_of_capstones.py — does stacking CAPSTONES on capstones help, or diminish?
#
# Housekeeping question from the family: each capstone is a META-allocator over the SAME family keepers, differing
# only by rule (breakthrough=risk-parity, brilliant=min-var, bossy=levered, believer=1/N, bemused=random) or by
# ingredient set (brigade=keepers+near-keepers, boundless=kitchen-sink) or objective (bastion=insurance overlay).
# So the honest test: if you allocate a "capstone of capstones," do you get further improvement — or, because
# they are all built from the same ingredients, are they so correlated that stacking adds nothing (diminishing
# returns immediately)? This directly checks the intuition. Contrast with the cross-asset keeper book, where
# combining UNCORRELATED sleeves DID beat the best sleeve — the lesson is about correlation, not layering.
#
# The five allocation-rule capstones share the exact 6-keeper KM (exact reconstruction); brigade/boundless/bastion
# are reconstructed on the shared harness with their documented ingredient/overlay theses (labeled).
# =============================================================================
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _breakthrough_common import panel, rets, riskadj, stats

SPINE=["SPY","IEF","GLD","DBC","DBA"]; TREND=["SPY","IEF","GLD","DBC"]; TAIL=["GLD","TLT"]
GULF="KSA"; GROWTH="QQQ"; PE=["BX","KKR","APO","CG","ARES","BAM"]
NEAR=["USMV","VNQ","EEM"]; SINK=NEAR+["HYG","TIP","UUP","XLE","XLK","XLF","LQD"]
ALL=sorted(set(SPINE+TREND+TAIL+[GULF,GROWTH]+PE+SINK+["SPY"]))
VW,REB,COST,WARM=60,21,5/1e4,252

def _invvol(R,T,syms):
    M=np.vstack([R[s] for s in syms]); out=np.zeros(T); w=np.ones(len(syms))/len(syms); wp=w.copy()
    for t in range(VW,T):
        if (t-VW)%REB==0:
            v=np.array([M[i,t-VW:t].std() for i in range(len(syms))]); inv=np.divide(1.0,v,out=np.zeros_like(v),where=v>0)
            w=inv/inv.sum() if inv.sum()>0 else np.ones(len(syms))/len(syms)
        out[t]=float(w@M[:,t])-(np.abs(w-wp).sum()*COST if (t-VW)%REB==0 else 0); wp=w if (t-VW)%REB==0 else wp
    return out
def _trend(R,T,syms):
    lv={s:np.cumprod(1+R[s]) for s in syms}; out=np.zeros(T); w=np.zeros(len(syms)); wp=w.copy()
    for t in range(WARM,T):
        if (t-WARM)%REB==0:
            sig=np.array([1.0 if (lv[s][t]/lv[s][t-231]-1)>0 else 0.0 for s in syms]); w=sig/max(sig.sum(),1)
        out[t]=float(sum(w[i]*R[syms[i]][t] for i in range(len(syms))))-(np.abs(w-wp).sum()*COST if (t-WARM)%REB==0 else 0); wp=w if (t-WARM)%REB==0 else wp
    return out

P,dates=panel(ALL); R={s:rets(P[s]) for s in P}; T=len(R["SPY"])
KEEP={"spine":_invvol(R,T,SPINE),"trend":_trend(R,T,TREND),"tail":_invvol(R,T,TAIL),
      "gulf":R[GULF],"growth":R[GROWTH],"PE":np.mean(np.vstack([R[s] for s in PE]),axis=0)}
KM=np.vstack(list(KEEP.values())); spy=R["SPY"]

def run_alloc(M, wfn, start=WARM):
    k,Tn=M.shape; out=np.zeros(Tn); w=np.ones(k)/k; wp=w.copy()
    for t in range(start,Tn):
        if (t-start)%REB==0:
            w=wfn(M[:,t-VW:t]); s=np.abs(w).sum(); w=w/s if s>0 else np.ones(k)/k
        out[t]=float(w@M[:,t])-(np.abs(w-wp).sum()*COST if (t-start)%REB==0 else 0); wp=w if (t-start)%REB==0 else wp
    return out[start:]
def w_rp(win): v=win.std(axis=1); return np.divide(1.0,v,out=np.zeros_like(v),where=v>0)
def w_minvar(win):
    C=np.cov(win); C=C+np.eye(len(C))*1e-6
    try: w=np.linalg.solve(C,np.ones(len(C)))
    except np.linalg.LinAlgError: w=np.ones(len(C))
    return np.clip(w,0,None)
def w_ones(win): return np.ones(win.shape[0])
np.random.seed(42)
def w_rand(win): return np.random.random(win.shape[0])

# extended-ingredient KMs for the ingredient-set capstones (reconstructed on the shared harness)
KM_brigade=np.vstack(list(KEEP.values())+[R[s] for s in NEAR])
KM_boundless=np.vstack(list(KEEP.values())+[R[s] for s in SINK])
bear=_trend(R,T,["SPY"]);  # long-SPY-trend; insurance = SHORT it when trend<=0 (risk-off)
bastion_overlay=np.where(bear[WARM:]==0.0, -1.0*spy[WARM:], 0.0)  # short SPY only when SPY trend is off

bt   = run_alloc(KM, w_rp)                       # breakthrough (risk parity) — the wired winner
bril = run_alloc(KM, w_minvar)                   # brilliant (min-variance optimizer)
boss = 1.5*bt                                     # bossy (levered conviction = 1.5x breakthrough)
belv = run_alloc(KM, w_ones)                      # believer (1/N buy-hold)
bem  = np.mean([run_alloc(KM, w_rand) for _ in range(200)], axis=0)   # bemused (random null, avg of 200)
brig = run_alloc(KM_brigade, w_rp)               # brigade (keepers + near-keepers)
bnd  = run_alloc(KM_boundless, w_ones)            # boundless (kitchen-sink, equal-weight = dilutive)
bas  = 0.85*bt + 0.15*bastion_overlay            # bastion (insurance overlay)
CAP={"breakthrough":bt,"brilliant":bril,"bossy":boss,"believer":belv,"bemused":bem,"brigade":brig,"boundless":bnd,"bastion":bas}
order=["breakthrough","brilliant","brigade","bastion","bossy","believer","boundless","bemused"]  # by standalone quality

print("="*96,"\nCAPSTONE OF CAPSTONES — does stacking meta-allocators help, or is it redundant?  (family keepers)\n"+"="*96)
print(f"  {'capstone':<14}{'Sharpe':>8}{'CAGR':>8}{'maxDD':>8}   built from")
built={"breakthrough":"6 keepers, risk-parity","brilliant":"6 keepers, min-var","bossy":"6 keepers, 1.5x levered",
       "believer":"6 keepers, 1/N","bemused":"6 keepers, random","brigade":"6 keepers + 3 near-keepers",
       "boundless":"6 keepers + 7 extras, equal-wt","bastion":"breakthrough + bear insurance"}
for c in order:
    m=riskadj(CAP[c],spy[WARM:]); st=stats(CAP[c])
    print(f"  {c:<14}{m['sh']:>+8.2f}{st['cagr']*100:>+7.1f}%{st['dd']*100:>+7.0f}%   {built[c]}")

# pairwise correlations among capstones
M=np.vstack([CAP[c] for c in order]); C=np.corrcoef(M)
iu=np.triu_indices(len(order),1); print(f"\n  pairwise capstone correlations: mean {C[iu].mean():+.2f}, min {C[iu].min():+.2f}, max {C[iu].max():+.2f}  (want LOW for diversification)")

print(f"\n  CAPSTONE OF CAPSTONES — add capstones one at a time (equal-weight the streams), watch the Sharpe:")
print(f"  {'stacked set':<44}{'Sharpe':>8}{'ΔSharpe':>9}")
prev=None
for i in range(1,len(order)+1):
    sub=order[:i]; combo=np.mean([CAP[c] for c in sub],axis=0); sh=riskadj(combo,spy[WARM:])['sh']
    d=f"{sh-prev:+.3f}" if prev is not None else "  —"; prev=sh
    print(f"  {'+'.join(sub) if i<=3 else sub[-1]+f'  (+{i} total)':<44}"[:44]+f"{sh:>8.2f}{d:>9}")
best=max(riskadj(CAP[c],spy[WARM:])['sh'] for c in order)
allc=np.mean([CAP[c] for c in order],axis=0); rp_meta_sh=riskadj(allc,spy[WARM:])['sh']
print(f"\n  best SINGLE capstone Sharpe {best:+.2f}  vs  all-8 capstone-of-capstones {rp_meta_sh:+.2f}  ->  net {rp_meta_sh-best:+.2f}")
print("\n  READ (the diminishing-returns intuition, verified — and it's worse than diminishing):")
print("  • CONFIRMED, and STRONGER: stacking capstones doesn't plateau, it goes NEGATIVE. Best single capstone")
print("    +1.20 (bastion) vs all-8 capstone-of-capstones +1.12 -> net -0.08. The very first addition already adds")
print("    nothing (breakthrough+brilliant, dSharpe -0.009). You don't gain by layering; you DILUTE your best one.")
print("  • WHY: the capstones are +0.92 correlated (min +0.74, bossy~breakthrough +1.00) — they are all allocations")
print("    of the SAME six keepers, just re-weighted. There is no new information to diversify, so combining them")
print("    only averages your best capstone DOWN toward the mean while adding a layer of turnover/cost. A capstone")
print("    of capstones is redundant BY CONSTRUCTION. The edge was never the allocation layer — it's the keepers")
print("    (bemused's law: allocation skill is small; the keepers are the edge).")
print("  • THE CONTRAST that makes it a rule: the cross-asset keeper book combined UNCORRELATED sleeves (corr ~0)")
print("    and BEAT its best sleeve (+0.83 > +0.72); this stacks CORRELATED allocators (corr +0.92) and LOSES to")
print("    its best (+1.12 < +1.20). Same 'combine' operation, opposite outcome — correlation is the whole story.")
print("    DIVERSIFY ACROSS UNCORRELATED INGREDIENTS; NEVER ACROSS CORRELATED ALLOCATORS OF THE SAME INGREDIENTS.")
print("  • PRACTICAL (for the wiring housekeeping): do NOT run capstones as a stack. Pick ONE by OBJECTIVE —")
print("    breakthrough (balanced risk-parity), bastion (defense, best Sharpe + smallest DD), bossy (aggression,")
print("    +16% CAGR at -25% DD). They are ALTERNATIVES, not additions — which is exactly why only one is wired.")
