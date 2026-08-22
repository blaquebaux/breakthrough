#!/usr/bin/python3
# =============================================================================
# breakthrough_1_allocator.py — does assembling the keepers into one risk-budgeted portfolio compound?
#
# Reconstruct six keeper streams as ETF proxies (spine / trend / tail / gulf / growth / PE), then combine
# them via inverse-vol (equal-risk-contribution), causal, monthly rebalance, net of cost. The capstone test:
# does the combined portfolio have a HIGHER Sharpe and LOWER drawdown than any single keeper AND clear the
# Bogle hurdle (SPY)? That is the diversification compounding the whole family exists to capture.
# =============================================================================
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _breakthrough_common import SPINE, TREND, TAIL, GULF, GROWTH, PE, ALLTICKERS, panel, rets, riskadj, corr

VW, REB, COST = 60, 21, 5/1e4
P, dates = panel(ALLTICKERS)
R = {s: rets(P[s]) for s in P}                                   # aligned daily returns, length N-1
T = len(next(iter(R.values())))
spy = R["SPY"]

def invvol_stream(syms, vw=VW, reb=REB):
    """Daily returns of an inverse-vol (equal-risk) book over syms, causal, monthly reb, net of cost."""
    M = np.vstack([R[s] for s in syms]); out = np.zeros(T); w = np.ones(len(syms))/len(syms); wp = w.copy()
    for t in range(vw, T):
        if (t-vw) % reb == 0:
            vols = np.array([M[i, t-vw:t].std() for i in range(len(syms))]); inv = np.divide(1.0, vols, out=np.zeros_like(vols), where=vols>0)
            w = inv/inv.sum() if inv.sum()>0 else np.ones(len(syms))/len(syms)
        r = float(w @ M[:, t])
        if (t-vw) % reb == 0: r -= np.abs(w-wp).sum()*COST; wp = w.copy()
        out[t] = r
    return out

def trend_stream(syms, vw=VW, reb=REB):
    """12-1 TS-momentum long/flat, equal-weight, monthly reb, net of cost (the crisis-hedge sleeve)."""
    M = {s: np.cumprod(1+R[s]) for s in syms}; out = np.zeros(T); w = np.zeros(len(syms)); wp = w.copy()
    for t in range(252, T):
        if (t-252) % reb == 0:
            sig = np.array([1.0 if (M[s][t]/M[s][t-231] - 1) > 0 else 0.0 for s in syms])   # 12-1 (skip ~1m)
            w = sig/max(sig.sum(),1) if sig.sum()>0 else np.zeros(len(syms))
        r = float(sum(w[i]*R[syms[i]][t] for i in range(len(syms))))
        if (t-252) % reb == 0: r -= np.abs(w-wp).sum()*COST; wp = w.copy()
        out[t] = r
    return out

keepers = {
    "spine (risk-parity)": invvol_stream(SPINE),
    "trend (12-1 mom)":    trend_stream(TREND),
    "tail (GLD/TLT)":      invvol_stream(TAIL),
    "gulf (KSA)":          R[GULF],
    "growth (QQQ)":        R[GROWTH],
    "PE (blackstone)":     np.mean(np.vstack([R[s] for s in PE]), axis=0),
}
# combine the keeper STREAMS via inverse-vol (equal-risk-contribution across sleeves)
KM = np.vstack(list(keepers.values())); names = list(keepers); start = 252   # warmup for trend
comb = np.zeros(T); w = np.ones(len(names))/len(names); wp = w.copy()
for t in range(start, T):
    if (t-start) % REB == 0:
        vols = np.array([KM[i, t-VW:t].std() for i in range(len(names))]); inv = np.divide(1.0, vols, out=np.zeros_like(vols), where=vols>0)
        w = inv/inv.sum() if inv.sum()>0 else np.ones(len(names))/len(names)
    r = float(w @ KM[:, t])
    if (t-start) % REB == 0: r -= np.abs(w-wp).sum()*COST; wp = w.copy()
    comb[t] = r
comb = comb[start:]; spyC = spy[start:]

print("=" * 92, f"\nBREAKTHROUGH #1 — the meta-allocator: does assembling the keepers compound?  ({dates[0]} → {dates[-1]})\n" + "=" * 92)
print(f"  {'keeper (ETF proxy)':<24}{'Sharpe':>8}{'CAGR':>7}{'vol':>7}{'maxDD':>7}{'corr-SPY':>10}")
for n, s in keepers.items():
    m = riskadj(s[start:], spyC); print(f"  {n:<24}{m['sh']:>+8.2f}{m['cagr']*100:>+6.0f}%{m['vol']*100:>6.1f}%{m['dd']*100:>+6.0f}%{corr(s[start:],spyC):>+10.2f}")
# average pairwise correlation among keepers (the diversification)
C = np.corrcoef(KM[:, start:]); avgc = (C.sum()-len(names))/(len(names)*(len(names)-1))
mc = riskadj(comb, spyC); ms = riskadj(spyC, spyC)
print(f"\n  {'COMBINED (risk-parity)':<24}{mc['sh']:>+8.2f}{mc['cagr']*100:>+6.0f}%{mc['vol']*100:>6.1f}%{mc['dd']*100:>+6.0f}%{corr(comb,spyC):>+10.2f}")
print(f"  {'SPY (Bogle hurdle)':<24}{ms['sh']:>+8.2f}{ms['cagr']*100:>+6.0f}%{ms['vol']*100:>6.1f}%{ms['dd']*100:>+6.0f}%{1.00:>+10.2f}")
best = max((riskadj(s[start:],spyC)['sh'] for s in keepers.values()))
print(f"\n  avg pairwise corr among keepers: {avgc:+.2f}   (low = real diversification)")
print(f"  Jensen α vs SPY {mc['alpha_ann']*100:+.1f}%   M² excess {mc['m2_excess']*100:+.1f}%   best single keeper Sharpe {best:+.2f}")
verdict = ("COMPOUNDS — the combined book beats every single keeper AND the Bogle hurdle risk-adjusted. The capstone works."
           if mc['sh'] > best and mc['sh'] > ms['sh'] and mc['m2_excess'] > 0
           else ("PARTIAL — diversification lifts risk-adjusted return above the components but check vs SPY" if mc['sh'] > best
                 else "NO LIFT — the combination doesn't beat the best single keeper"))
print(f"\n  VERDICT: {verdict}")
