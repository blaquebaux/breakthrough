#!/usr/bin/python3
# =============================================================================
# breakthrough_allocator.py — emit today's governed meta-allocator target (the validated capstone, live).
#
# Computes the current target book by risk-budgeting the keeper sleeves (default = breakthrough risk parity),
# over the brigade ingredient set (keepers + curated void-fillers crypto/defensive), with a bastion bear
# insurance overlay that shorts SPY when benchmark's market_regime is risk-off — the validated regime-
# conditional tilt. Emits {symbol: weight} JSON; the governed Julia driver (breakthrough_live.jl) reads it and
# routes it through the Layer-3 safety gate. No LLM in the order path — reproducible code both sides.
#
# Modes (BB_ALLOC_MODE): riskparity (breakthrough, default) | minvar (brilliant) | levered (bossy).
#   python3 live/breakthrough_allocator.py            # emit target book
#   BB_ALLOC_MODE=minvar python3 live/breakthrough_allocator.py
# =============================================================================
import os, sys, json, datetime
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research"))
import _breakthrough_common as _C
_C.END = (datetime.date.today() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")   # settled close, aligned with the driver
from _breakthrough_common import panel, rets

VW = 60
MODE = os.environ.get("BB_ALLOC_MODE", "riskparity")
BEAR_W = float(os.environ.get("BB_BEAR_WEIGHT", "0.15"))        # bastion insurance sleeve (risk-off only)
LEV = float(os.environ.get("BB_LEVERAGE", "1.0"))              # bossy dial
CFG = os.path.join(os.path.expanduser("~"), ".config", "blaquebaux")
OUT = os.environ.get("BB_ALLOC_TARGET", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "breakthrough_target.json"))

# --- sleeve books: each returns (current weights dict, recent return stream for cross-sleeve vol) ----------
SPINE=["SPY","IEF","GLD","DBC","DBA"]; TREND=["SPY","IEF","GLD","DBC"]; TAIL=["GLD","TLT"]
PE=["BX","KKR","APO","CG","ARES","BAM"]; DEFN=["QUAL","USMV","VLUE","MOAT"]
TICKERS = sorted(set(SPINE+TREND+TAIL+PE+DEFN+["KSA","QQQ","BITO","SPY"]))

def _invvol(P, syms):
    v = np.array([rets(P[s])[-VW:].std() for s in syms]); inv = np.divide(1.0,v,out=np.zeros_like(v),where=v>0)
    w = inv/inv.sum() if inv.sum()>0 else np.ones(len(syms))/len(syms)
    stream = np.sum([w[i]*rets(P[syms[i]]) for i in range(len(syms))], axis=0)
    return dict(zip(syms, w)), stream

def _single(P, s): return {s: 1.0}, rets(P[s])
def _eqw(P, syms):
    w = 1.0/len(syms); return {s: w for s in syms}, np.mean(np.vstack([rets(P[s]) for s in syms]),axis=0)
def _trend(P, syms):                                           # 12-1 long/flat, equal-weight (current signal)
    sig = {s: (1.0 if (np.prod(1+rets(P[s])[-231:])-1) > 0 else 0.0) for s in syms}
    n = sum(sig.values()) or 1
    w = {s: sig[s]/n for s in syms}; stream = np.sum([w[s]*rets(P[s]) for s in syms],axis=0)
    return w, stream

def read_regime_riskoff():
    p = os.path.join(CFG, "market_regime.txt")
    if not os.path.exists(p): return False
    d = {}
    for ln in open(p):
        ln=ln.strip()
        if "=" in ln and not ln.startswith("#"): k,v=ln.split("=",1); d[k.strip()]=v.strip()
    return d.get("risk_on") == "0"

def main():
    P, dates = panel(TICKERS)
    sleeves = {"spine": _invvol(P,SPINE), "trend": _trend(P,TREND), "tail": _invvol(P,TAIL),
               "gulf": _single(P,"KSA"), "growth": _single(P,"QQQ"), "PE": _eqw(P,PE),
               "defensive": _eqw(P,DEFN), "crypto": _single(P,"BITO")}
    names = list(sleeves); books = {n: sleeves[n][0] for n in names}
    S = np.vstack([sleeves[n][1][-VW:] for n in names])         # recent streams for cross-sleeve weighting
    if MODE == "minvar":
        cov = np.cov(S) + 1e-6*np.eye(len(names)); cw = np.clip(np.linalg.solve(cov, np.ones(len(names))),0,None)
    else:                                                       # riskparity (default) and levered use inverse-vol
        v = S.std(axis=1); cw = np.divide(1.0,v,out=np.zeros_like(v),where=v>0)
    cw = cw/cw.sum()
    scale = LEV * (1.0 - BEAR_W if read_regime_riskoff() else 1.0)   # bastion: make room for the bear hedge in risk-off
    weights = {}
    for i, n in enumerate(names):
        for s, w in books[n].items(): weights[s] = weights.get(s,0.0) + scale*cw[i]*w
    riskoff = read_regime_riskoff()
    if riskoff: weights["SPY"] = weights.get("SPY",0.0) - BEAR_W*LEV   # bear insurance: short SPY in risk-off
    weights = {s: round(w,5) for s,w in weights.items() if abs(w) > 1e-4}
    gross = sum(abs(w) for w in weights.values())
    out = {"asof": dates[-1], "mode": MODE, "bear_weight": BEAR_W if riskoff else 0.0, "leverage": LEV,
           "regime": "risk-off" if riskoff else "risk-on", "gross": round(gross,3), "weights": weights}
    print(f"BREAKTHROUGH allocator [{MODE}]  asof {dates[-1]}  regime {out['regime']}  gross {gross:.2f}x  {len(weights)} names")
    for s,w in sorted(weights.items(), key=lambda x:-abs(x[1])): print(f"    {s:<6} {w*100:+6.1f}%")
    if os.environ.get("BB_DRYRUN","") in ("1","true","yes"): print("DRYRUN — not writing target"); return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT,"w"), indent=2)
    txt = OUT.replace(".json", ".txt")                         # dependency-free target for the Julia driver
    with open(txt,"w") as f:
        f.write(f"# breakthrough target  asof={dates[-1]} mode={MODE} regime={out['regime']} gross={gross:.3f}\n")
        for s,w in sorted(weights.items()): f.write(f"{s} {w}\n")
    print(f"target -> {OUT}  +  {txt}")

if __name__ == "__main__":
    main()
