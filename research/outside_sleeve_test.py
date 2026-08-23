#!/usr/bin/python3
# =============================================================================
# outside_sleeve_test.py — would a sleeve OUTSIDE the capstone universe help the mega-capstones?
#
# capstone_of_capstones showed stacking capstones is net-negative — they are +0.92 correlated (same keepers).
# The law's other half: a sleeve OUTSIDE the keeper universe, if genuinely UNCORRELATED, should help where
# another capstone cannot. Test it — add candidate satellites to the two best mega-capstones (breakthrough =
# balanced, bastion = defense), at a 30% risk budget, and measure correlation + Sharpe/drawdown lift:
#   MF-trend     time-series momentum, LONG/SHORT across a broad asset set (managed futures / crisis alpha)
#   FX-carry     equity-vol-gated G10 carry (our cross-asset keeper — NOT in the capstone keepers)
#   factor-MN    market-neutral defensive factor (long QUAL/USMV/VLUE/MOAT − short SPY)
#   bear-ins     short SPY when risk-off (tail insurance; negative return, negative corr)
#   [CONTROL] another capstone (brilliant) — should NOT help (corr high), by the law.
# =============================================================================
import os, sys, json, urllib.request
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _breakthrough_common import rets, riskadj, stats

H={"APCA-API-KEY-ID":os.environ["ALPACA_KEY_ID"],"APCA-API-SECRET-KEY":os.environ["ALPACA_SECRET_KEY"]}
def bars(s,adj="all"):
    u=(f"https://data.alpaca.markets/v2/stocks/bars?symbols={s}&timeframe=1Day&start=2016-01-01&end=2026-08-01"
       f"&adjustment={adj}&feed=sip&limit=10000"); d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40))
    return {b["t"][:10]:b["c"] for b in d.get("bars",{}).get(s,[])}

SPINE=["SPY","IEF","GLD","DBC","DBA"]; TREND=["SPY","IEF","GLD","DBC"]; TAIL=["GLD","TLT"]
PE=["BX","KKR","APO","CG","ARES","BAM"]; DEFN=["QUAL","USMV","VLUE","MOAT"]
MF=["SPY","IEF","GLD","DBC","TLT","UUP","EEM","HYG","VNQ"]; FX=["FXA","FXB","FXC","FXE","FXF","FXY"]
ALL=sorted(set(SPINE+TREND+TAIL+PE+DEFN+MF+FX+["KSA","QQQ"]))
TR={s:bars(s) for s in ALL}; PRfx={s:bars(s,"split") for s in FX}
dates=sorted(set.intersection(*[set(TR[s]) for s in ALL], *[set(PRfx[s]) for s in FX]))
P={s:np.array([TR[s][d] for d in dates],float) for s in ALL}
pf={s:np.array([PRfx[s][d] for d in dates],float) for s in FX}
R={s:P[s][1:]/P[s][:-1]-1 for s in ALL}; rpf={s:pf[s][1:]/pf[s][:-1]-1 for s in FX}
T=len(R["SPY"]); WARM=252; VW=60; REB=21; sqrt=np.sqrt
def lag(g): g=np.asarray(g,float); o=np.zeros_like(g); o[1:]=g[:-1]; return o

# --- capstone streams (breakthrough, bastion, brilliant) on the shared keeper harness ------------------
def _invvol(syms):
    M=np.vstack([R[s] for s in syms]); out=np.zeros(T); w=np.ones(len(syms))/len(syms)
    for t in range(VW,T):
        if (t-VW)%REB==0:
            v=np.array([M[i,t-VW:t].std() for i in range(len(syms))]); inv=np.divide(1.0,v,out=np.zeros_like(v),where=v>0)
            w=inv/inv.sum() if inv.sum()>0 else np.ones(len(syms))/len(syms)
        out[t]=float(w@M[:,t])
    return out
def _trend(syms):
    lv={s:np.cumprod(1+R[s]) for s in syms}; out=np.zeros(T); w=np.zeros(len(syms))
    for t in range(WARM,T):
        if (t-WARM)%REB==0:
            sig=np.array([1.0 if (lv[s][t]/lv[s][t-231]-1)>0 else 0.0 for s in syms]); w=sig/max(sig.sum(),1)
        out[t]=float(sum(w[i]*R[syms[i]][t] for i in range(len(syms))))
    return out
KEEP={"spine":_invvol(SPINE),"trend":_trend(TREND),"tail":_invvol(TAIL),"gulf":R["KSA"],"growth":R["QQQ"],
      "PE":np.mean(np.vstack([R[s] for s in PE]),axis=0)}
KM=np.vstack(list(KEEP.values()))
def run_alloc(M,wfn):
    k,Tn=M.shape; out=np.zeros(Tn); w=np.ones(k)/k
    for t in range(WARM,Tn):
        if (t-WARM)%REB==0: w=wfn(M[:,t-VW:t]); s=np.abs(w).sum(); w=w/s if s>0 else np.ones(k)/k
        out[t]=float(w@M[:,t])
    return out[WARM:]
def w_rp(win): v=win.std(axis=1); return np.divide(1.0,v,out=np.zeros_like(v),where=v>0)
def w_mv(win):
    C=np.cov(win)+1e-6*np.eye(win.shape[0])
    try: w=np.linalg.solve(C,np.ones(win.shape[0]))
    except np.linalg.LinAlgError: w=np.ones(win.shape[0])
    return np.clip(w,0,None)
bt=run_alloc(KM,w_rp)
bear_trend=_trend(["SPY"]); bastion_overlay=np.where(bear_trend[WARM:]==0.0,-1.0*R["SPY"][WARM:],0.0)
bas=0.85*bt+0.15*bastion_overlay
bril=run_alloc(KM,w_mv)

# --- OUTSIDE sleeves (aligned to [WARM:]) -------------------------------------------------------------
def mf_trend():
    lv={s:np.cumprod(1+R[s]) for s in MF}; out=np.zeros(T); w=np.zeros(len(MF))
    for t in range(WARM,T):
        if (t-WARM)%REB==0:
            sig=np.array([1.0 if (lv[s][t]/lv[s][t-231]-1)>0 else -1.0 for s in MF]); w=sig/len(MF)  # long/SHORT
        out[t]=float(sum(w[i]*R[MF[i]][t] for i in range(len(MF))))
    return out[WARM:]
def factor_mn(): return (np.mean(np.vstack([R[s] for s in DEFN]),axis=0)-R["SPY"])[WARM:]           # long defensive - short SPY
def bear_ins(): return bastion_overlay                                                                # short SPY when risk-off
def fx_carry():
    yld={s:np.array([np.clip(R[s]-rpf[s],0,None)[max(0,i-252):i].sum() for i in range(len(R[s]))]) for s in FX}
    carry=np.zeros(T)
    for t in range(252,T-REB,REB):
        rank=sorted(FX,key=lambda s:yld[s][t]); lo,sh=rank[-2:],rank[:2]
        for d in range(t,min(t+REB,T)): carry[d]=0.5*sum(R[s][d] for s in lo)-0.5*sum(R[s][d] for s in sh)
    spx=R["SPY"]-R["IEF"]*0  # equity excess proxy = SPY ret
    rv=lambda x,w:np.array([x[max(0,i-w):i].std() for i in range(len(x))])
    gate=lag((rv(R["SPY"],21)<=rv(R["SPY"],252)).astype(float))
    return (gate*carry)[WARM:]

OUT={"MF-trend":mf_trend(),"FX-carry":fx_carry(),"factor-MN":factor_mn(),"bear-ins":bear_ins(),"[capstone]brilliant":bril[:]-0}
def ann_vol(x): return x.std()*sqrt(252)

def combine(cap, sleeve, risk_budget=0.30):
    vc,vs=ann_vol(cap),ann_vol(sleeve)
    a = risk_budget*vc/vs if vs>0 else 0.0                 # scale sleeve to ~30% of the capstone's vol
    return cap + a*sleeve

print("="*98,"\nOUTSIDE-SLEEVE TEST — does a sleeve OUTSIDE the capstones help the mega-capstones?  (30% risk budget)\n"+"="*98)
for capnm,cap in [("breakthrough",bt),("bastion",bas)]:
    base=riskadj(cap,R["SPY"][WARM:]); bstat=stats(cap)
    print(f"\n  === {capnm}  (alone: Sharpe {base['sh']:+.2f}, maxDD {bstat['dd']*100:+.0f}%) ===")
    print(f"  {'add sleeve':<22}{'corr':>7}{'sleeve Sh':>11}{'combo Sh':>10}{'ΔSharpe':>9}{'combo DD':>10}")
    rows=[]
    for nm,sl in OUT.items():
        c=np.corrcoef(cap,sl)[0,1]; combo=combine(cap,sl); m=riskadj(combo,R["SPY"][WARM:]); md=stats(combo)
        rows.append((nm,c,riskadj(sl,R["SPY"][WARM:])['sh'],m['sh'],m['sh']-base['sh'],md['dd']))
    for nm,c,ssh,csh,d,dd in sorted(rows,key=lambda x:-x[4]):
        print(f"  {nm:<22}{c:>+7.2f}{ssh:>+11.2f}{csh:>+10.2f}{d:>+9.3f}{dd*100:>+9.0f}%")
print("\n  READ (the law's other half — verified, and refined):")
print("  • YES, an OUTSIDE sleeve can help where another capstone cannot — the clear winner is MF-TREND (managed-")
print("    futures long/short): corr just +0.24, standalone Sharpe +0.58, best ΔSharpe +0.045 (breakthrough) /")
print("    +0.022 (bastion), and NO drawdown cost (-17% -> -17%). Classic crisis-alpha trend is the mega-capstones'")
print("    natural complement. FX-carry helps too but modestly (+0.011): uncorrelated (+0.17) yet thin-return (+0.39).")
print("  • THE CONTROL CONFIRMS capstone_of_capstones: adding another capstone (brilliant, corr +0.91) gives a")
print("    trivial +0.011 AND WORSENS drawdown (-17% -> -23%). A correlated addition doesn't diversify — it just")
print("    piles on the same risk. Outside-and-uncorrelated beats inside-and-correlated, exactly as the law predicts.")
print("  • THE REFINEMENT — low correlation is necessary but NOT sufficient. bear-ins (corr -0.32) and factor-MN")
print("    (-0.26) have the LOWEST correlations yet HURT Sharpe (-0.024, -0.075) because their standalone returns are")
print("    NEGATIVE. They are INSURANCE — you buy a little drawdown protection and PAY for it in Sharpe — not")
print("    enhancers. A satellite lifts Sharpe only when it is BOTH uncorrelated AND positive-return.")
print("  VERDICT: the full diversification law — a sleeve helps a mega-capstone iff it brings NEW, UNCORRELATED,")
print("  POSITIVE return. Another capstone fails it (correlated); a tail hedge fails it (negative return); a")
print("  managed-futures TREND satellite passes it (uncorrelated + positive + crisis-alpha) and is the best outside")
print("  complement. Practical: pair a mega-capstone with a trend satellite, not with another capstone or a hedge")
print("  (unless you specifically want tail protection at a Sharpe cost — which bastion already bakes in).")
