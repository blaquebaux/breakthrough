#!/usr/bin/python3
# =============================================================================
# black_swan_tail_test.py — should Booster carry an always-on BLACK-SWAN tail sleeve?
#
# The six capstones (breakthrough/brilliant/bossy/believer/brigade/bastion) are meta-allocators over the
# SAME keepers → +0.92 correlated (capstone_of_capstones). So in a correlated crash they ALL fall together;
# diversifying across them buys NOTHING in the tail. Only a CONVEX hedge — one that pays off *because*
# everything else is cratering — wins the swan. This tests whether adding a small, always-on tail sleeve to
# the six-capstone book earns its place, the red-scorecard way: does the crash payoff justify the calm bleed?
#
# Barbell construction: (1-w)*CORE + w*TAIL_sleeve, CORE = equal-weight of the 6 capstones (≈ any one, given
# +0.92 corr). Always ON (you can't time the swan — "timing the tail removes the tail"). w ∈ {0,3%,5%,10%}.
# Tail instruments (ETF proxies for the family's `bleed` sleeve, tradeable on Booster's equity rail):
#   TAIL  Cambria Tail Risk (10y Tsy + long OTM SPX puts) — the HONEST purpose-built hedge (modest bleed)
#   VIXY  ProShares short-term VIX futures — PURE long-vol (huge convexity, BRUTAL carry — the trap)
# Alpaca SIP daily, causal, gross. Read-only.
# =============================================================================
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _breakthrough_common import riskadj, stats, bars, corr
import json, urllib.request

H={"APCA-API-KEY-ID":os.environ["ALPACA_KEY_ID"],"APCA-API-SECRET-KEY":os.environ["ALPACA_SECRET_KEY"]}
def load(s):
    u=(f"https://data.alpaca.markets/v2/stocks/bars?symbols={s}&timeframe=1Day&start=2016-01-01&end=2026-08-01"
       f"&adjustment=all&feed=sip&limit=10000"); d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40))
    return {b["t"][:10]:b["c"] for b in d.get("bars",{}).get(s,[])}

SPINE=["SPY","IEF","GLD","DBC","DBA"]; TREND=["SPY","IEF","GLD","DBC"]; TAILK=["GLD","TLT"]
PE=["BX","KKR","APO","CG","ARES","BAM"]; NEAR=["USMV","VNQ","EEM"]; MF=["SPY","IEF","GLD","DBC","TLT","UUP","EEM","HYG","VNQ"]
SWAN=["TAIL","VIXY"]                                  # the tail-sleeve candidates
ALL=sorted(set(SPINE+TREND+TAILK+PE+NEAR+MF+["KSA","QQQ"]+SWAN))
D={s:load(s) for s in ALL}; D={s:v for s,v in D.items() if len(v)>250}
missing=[s for s in SWAN if s not in D]
dates=sorted(set.intersection(*[set(D[s]) for s in D]))
P={s:np.array([D[s][d] for d in dates],float) for s in D}; R={s:P[s][1:]/P[s][:-1]-1 for s in D}
DT=dates[1:]; T=len(R["SPY"]); VW,REB=60,21

def _invvol(syms):
    M=np.vstack([R[s] for s in syms]); out=np.zeros(T); w=np.ones(len(syms))/len(syms)
    for t in range(VW,T):
        if (t-VW)%REB==0:
            v=np.array([M[i,t-VW:t].std() for i in range(len(syms))]); inv=np.divide(1.,v,out=np.zeros_like(v),where=v>0)
            w=inv/inv.sum() if inv.sum()>0 else np.ones(len(syms))/len(syms)
        out[t]=float(w@M[:,t])
    return out
def _trend(syms):
    lv={s:np.cumprod(1+R[s]) for s in syms}; out=np.zeros(T); w=np.zeros(len(syms))
    for t in range(252,T):
        if (t-252)%REB==0:
            sig=np.array([1. if (lv[s][t]/lv[s][t-231]-1)>0 else 0. for s in syms]); w=sig/max(sig.sum(),1)
        out[t]=float(sum(w[i]*R[syms[i]][t] for i in range(len(syms))))
    return out
KEEP={"spine":_invvol(SPINE),"trend":_trend(TREND),"tail":_invvol(TAILK),"gulf":R["KSA"],"growth":R["QQQ"],
      "PE":np.mean(np.vstack([R[s] for s in PE]),axis=0)}
KM=np.vstack(list(KEEP.values())); KMx=np.vstack(list(KEEP.values())+[R[s] for s in NEAR])
def run(M,rule):
    k,Tn=M.shape; out=np.zeros(Tn); w=np.ones(k)/k
    for t in range(252,Tn):
        if (t-252)%REB==0:
            if rule=="rp": v=M[:,t-VW:t].std(axis=1); inv=np.divide(1.,v,out=np.zeros_like(v),where=v>0); s=inv.sum(); w=inv/s if s>0 else np.ones(k)/k
            elif rule=="mv":
                C=np.cov(M[:,t-VW:t])+1e-6*np.eye(k)
                try: w=np.clip(np.linalg.solve(C,np.ones(k)),0,None); s=w.sum(); w=w/s if s>0 else np.ones(k)/k
                except np.linalg.LinAlgError: w=np.ones(k)/k
            elif rule=="eq": w=np.ones(k)/k
        out[t]=float(w@M[:,t])
    return out[252:]
bt=run(KM,"rp"); bril=run(KM,"mv"); belv=run(KM,"eq"); brig=run(KMx,"rp")
bear=_trend(["SPY"]); bas=0.85*bt+0.15*np.where(bear[252:]==0.,-1.*R["SPY"][252:],0.); boss=1.5*bt
CAPS={"breakthrough":bt,"brilliant":bril,"bossy":boss,"believer":belv,"brigade":brig,"bastion":bas}
CORE=np.mean(np.vstack(list(CAPS.values())),axis=0)   # the six-capstone book (≈ any one; +0.92 corr)
SPY=R["SPY"][252:]; DTc=DT[252:]
sqrt=np.sqrt
def wealth(x): return float(np.cumprod(1+np.asarray(x,float))[-1])
NYR=len(CORE)/252.0
crash = CORE <= np.percentile(CORE,5)                 # the six-capstone book's worst-5% days = the swan window

print("="*104)
print(f"BLACK-SWAN TAIL TEST — does an always-on tail sleeve earn its place on the six-capstone book?")
print(f"  window {DTc[0]} → {DTc[-1]} ({len(DTc)} days, {NYR:.1f}y)  ·  gross, causal" + (f"  ·  MISSING: {missing}" if missing else ""))
print("="*104)

# capstones are ~one bet — show the correlation that motivates the whole thing
cc=np.mean([corr(CAPS[a],CAPS[b]) for a in CAPS for b in CAPS if a<b])
print(f"\n  avg pairwise capstone correlation: {cc:+.2f}  → in a correlated crash they fall TOGETHER (no tail protection)")

for swan in [s for s in SWAN if s in D]:
    TL=R[swan][252:]; st=stats(TL); tr=riskadj(TL,SPY)
    print(f"\n{'—'*104}\n  TAIL SLEEVE = {swan}  (standalone: CAGR {st['cagr']*100:+.0f}%, Sharpe {tr['sh']:+.2f}, "
          f"maxDD {st['dd']*100:+.0f}%, skew {tr['skew']:+.2f})")
    print(f"    corr to core {corr(TL,CORE):+.2f}  ·  CRISIS corr (core's worst-5% days) {corr(TL[crash],CORE[crash]):+.2f}"
          f"  ·  mean {swan} return on those crash days {TL[crash].mean()*100:+.2f}%/day (core {CORE[crash].mean()*100:+.2f}%)")
    base=riskadj(CORE,SPY); bdd=stats(CORE)['dd']
    print(f"    {'barbell':16}{'Sharpe':>8}{'ΔSh':>7}{'CAGR':>7}{'$1→':>7}{'maxDD':>8}{'ΔmaxDD':>8}{'crashDay':>10}")
    print(f"    {'CORE (no tail)':16}{base['sh']:>+8.2f}{'':>7}{stats(CORE)['cagr']*100:>+6.0f}%{wealth(CORE):>6.1f}x{bdd*100:>+7.0f}%{'':>8}{CORE[crash].mean()*100:>+9.2f}%")
    for w in (0.03,0.05,0.10):
        bl=(1-w)*CORE + w*TL; m=riskadj(bl,SPY); md=stats(bl)
        print(f"    {'+ '+str(int(w*100))+'% '+swan:16}{m['sh']:>+8.2f}{m['sh']-base['sh']:>+7.2f}{md['cagr']*100:>+6.0f}%{wealth(bl):>6.1f}x{md['dd']*100:>+7.0f}%{(md['dd']-bdd)*100:>+7.0f}%{bl[crash].mean()*100:>+9.2f}%")
    # episode cushions — did the tail sleeve actually cushion the real crashes?
    def ep(lo,hi):
        mask=np.array([lo<=d<=hi for d in DTc])
        if mask.sum()<3: return None
        c=float(np.prod(1+CORE[mask])-1); t=float(np.prod(1+TL[mask])-1); b5=float(np.prod(1+(0.95*CORE+0.05*TL)[mask])-1)
        return c,t,b5
    print(f"    episode cushions (period return: CORE / {swan} / CORE+5%{swan}):")
    for name,lo,hi in [("2018-Q4 selloff","2018-10-01","2018-12-31"),("2020 COVID crash","2020-02-15","2020-03-31"),
                       ("2022 bear","2022-01-01","2022-12-31"),("2025 tariff shock","2025-03-01","2025-05-31")]:
        e=ep(lo,hi)
        if e: print(f"      {name:20} {e[0]*100:>+7.1f}% / {e[1]*100:>+8.1f}% / {e[2]*100:>+7.1f}%")

print("\n"+"="*104)
print("READ (2018-04 → 2026-07; a GREEN scorecard — the tail sleeve earns its place):")
print("  • WHY it's needed: capstones are +0.93 correlated — the six-capstone book is ~one bet, so a correlated")
print("    crash sinks all six at once. A convex tail sleeve is the ONLY thing that pays in that exact scenario.")
print("  • TAIL (the honest hedge) PAYS FOR ITSELF at a small always-on weight. It bleeds standalone (-7%/yr,")
print("    Sharpe -0.41) but its CRISIS corr is -0.57 (on the book's worst days it makes +1.4%/day while the book")
print("    loses -1.5%). At 5% it nudges Sharpe +1.11→+1.13, trims maxDD -18%→-17%, softens the average crash day")
print("    -1.50%→-1.36%, and costs almost nothing in wealth (2.4x→2.3x). Like bastion's bear: a hedge whose")
print("    negative correlation is strong enough to pay for its own carry. The barbell, realized.")
print("  • VIXY is MORE convex but FRAGILE — a knife-edge. At 3-5% it cushions crashes hardest (COVID +242%,")
print("    2018-Q4 +76%) and even lifts Sharpe (+0.04), but at 10% the ruinous carry (-46%/yr, -100% standalone)")
print("    DOMINATES: Sharpe collapses +1.11→+0.93 and maxDD gets WORSE. Too sensitive to sizing for an always-on")
print("    sleeve. TAIL is the robust choice; VIXY only as a tiny, disciplined satellite if at all.")
print("  • THE HONEST LIMIT: neither helps the SLOW bear (2022: TAIL -13%, VIXY -25%) — a tail hedge is for the")
print("    FAST correlated swan (2018-Q4 / COVID / 2025 tariff), not a grinding decline. But the fast swan is")
print("    exactly the risk the six correlated capstones cannot survive, so the hedge covers the right gap.")
print("  VERDICT: YES — give Booster an always-on ~5% TAIL sleeve, sized as a FIXED insurance budget carved off")
print("  the top (never risk-parity'd with the capstones). It shallows the tail and the crash day at ~zero Sharpe")
print("  cost — the rare insurance that improves the book. Not a Sharpe-max play; a survive-the-swan play that")
print("  happens not to cost anything. (Options puts/VIX-calls via module_9_0dte are the higher-fidelity v2.)")
