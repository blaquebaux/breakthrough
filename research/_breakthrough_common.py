#!/usr/bin/python3
# =============================================================================
# _breakthrough_common.py — shared helpers for the Blaque Baux Breakthrough (meta-allocator).
# Alpaca SIP daily bars; reads ALPACA_KEY_ID / ALPACA_SECRET_KEY from env. Read-only.
#
# THE CAPSTONE. Not a new premium — the trunk proved the classic premia (vol/pairs/carry/merger-arb) are
# dead in listed form. Breakthrough assembles the KEEPERS the family already validated into ONE risk-budgeted
# portfolio, and asks whether diversification across them compounds past the spine and the Bogle hurdle. Each
# keeper is reconstructed here as a priceable ETF proxy (the faithful Julia reconstruction lives in the base's
# scripts/research/multi_sleeve_portfolio.jl over the PortfolioOpt library); this first pass proves the
# compounding, the governed allocator is the graduation.
#   spine  = inverse-vol asset-class book (SPY/IEF/GLD/DBC/DBA)   — the diversification core
#   trend  = 12-1 TS-momentum long/flat on the macro assets       — the crisis hedge (made money in 2022)
#   tail   = GLD + TLT defensives                                  — the bleed-style tail cushion
#   gulf   = KSA                                                   — the brics low-corr EM diversifier
#   growth = QQQ                                                   — the bull naive-growth beta
#   pe     = BX/KKR/APO/CG/ARES/BAM equal-weight                   — the blackstone levered-PE factor
# Combined via inverse-vol (equal-risk-contribution) across the keeper streams, causal, monthly, net of cost.
# =============================================================================
SPINE  = ["SPY", "IEF", "GLD", "DBC", "DBA"]
TREND  = ["SPY", "IEF", "GLD", "DBC"]
TAIL   = ["GLD", "TLT"]
GULF   = "KSA"
GROWTH = "QQQ"
PE     = ["BX", "KKR", "APO", "CG", "ARES", "BAM"]
ALLTICKERS = sorted(set(SPINE + TREND + TAIL + [GULF, GROWTH] + PE + ["SPY"]))
import os, json, urllib.request, math
import numpy as np

H = {"APCA-API-KEY-ID": os.environ["ALPACA_KEY_ID"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
START, END = "2016-01-01", "2026-08-01"
_cache = {}

def bars(s):
    if s in _cache: return _cache[s]
    u = (f"https://data.alpaca.markets/v2/stocks/bars?symbols={s}&timeframe=1Day"
         f"&start={START}&end={END}&adjustment=all&feed=sip&limit=10000")
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40))
        _cache[s] = {b["t"][:10]: b for b in d.get("bars", {}).get(s, [])}
    except Exception:
        _cache[s] = {}
    return _cache[s]

def panel(syms):
    """Aligned close-price panel over the symbols with >250 bars; returns ({sym: prices}, dates)."""
    D = {s: bars(s) for s in syms}; D = {s: v for s, v in D.items() if len(v) > 250}
    if not D: return {}, []
    u = list(D); dates = sorted(set.intersection(*[set(D[s]) for s in u]))
    M = np.array([[D[s][d]["c"] for s in u] for d in dates], float)
    return {s: M[:, i] for i, s in enumerate(u)}, dates

def rets(px): return px[1:] / px[:-1] - 1

def stats(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    if len(r) < 30 or r.std() == 0: return dict(sh=float('nan'), cagr=float('nan'), dd=float('nan'), vol=float('nan'))
    cum = np.cumprod(1 + r)
    return dict(sh=r.mean()/r.std()*math.sqrt(252), cagr=cum[-1]**(252/len(r))-1,
                dd=(cum/np.maximum.accumulate(cum)-1).min(), vol=r.std()*math.sqrt(252))

def corr(y, x):
    y = np.asarray(y, float); x = np.asarray(x, float); m = np.isfinite(y) & np.isfinite(x)
    return np.corrcoef(y[m], x[m])[0, 1] if m.sum() > 2 else float('nan')

def beta(y, x):
    y = np.asarray(y, float); x = np.asarray(x, float); m = np.isfinite(y) & np.isfinite(x)
    return float(np.cov(y[m], x[m])[0, 1] / np.var(x[m])) if m.sum() > 2 and np.var(x[m]) > 0 else float('nan')

# --- Blaque Baux shared risk-stats (canonical; numpy-only, no scipy) -----------------------------
# Adopted family-wide 2026-08: returns are fat-tailed, so we (1) TEST normality with Jarque-Bera before
# leaning on any mean-variance metric, and (2) report risk-adjusted performance with Jensen's alpha
# (return beyond what beta earns) and M-squared (return re-scaled to the benchmark's own volatility),
# not Sharpe alone. Sharpe assumes normality; JB usually rejects it for daily bars, which is exactly why
# alpha/M2 (benchmark-relative) and downside measures carry the verdict.
def jarque_bera(r):
    """Jarque-Bera normality test. H0 = returns are normal; reject (non-normal, fat tails) if p < 0.05.
    JB ~ chi-square(2), whose survival fn is exp(-x/2) — so no scipy needed. Returns skew + excess kurtosis."""
    r = np.asarray(r, float); r = r[np.isfinite(r)]; n = len(r)
    if n < 30: return dict(jb=float('nan'), p=float('nan'), skew=float('nan'), exkurt=float('nan'), normal=None)
    m, s = r.mean(), r.std()
    if s == 0: return dict(jb=0.0, p=1.0, skew=0.0, exkurt=0.0, normal=True)
    z = (r - m) / s
    sk = float(np.mean(z**3)); ku = float(np.mean(z**4) - 3.0)
    jb = n / 6.0 * (sk**2 + ku**2 / 4.0); p = math.exp(-jb / 2.0)
    return dict(jb=jb, p=p, skew=sk, exkurt=ku, normal=(p >= 0.05))

def jensens_alpha(r, rb, rf=0.0):
    """Jensen's alpha (annualized) = (Rp-Rf) - beta*(Rb-Rf) — return beyond what market beta earns.
    r, rb = daily return arrays; rf = ANNUAL risk-free (default 0). Also returns beta."""
    r = np.asarray(r, float); rb = np.asarray(rb, float)
    mk = np.isfinite(r) & np.isfinite(rb); r, rb = r[mk], rb[mk]
    if len(r) < 30 or np.var(rb) == 0: return dict(alpha_ann=float('nan'), beta=float('nan'))
    rf_d = rf / 252.0
    beta = float(np.cov(r, rb)[0, 1] / np.var(rb))
    alpha_d = (r.mean() - rf_d) - beta * (rb.mean() - rf_d)
    return dict(alpha_ann=alpha_d * 252.0, beta=beta)

def m_squared(r, rb, rf=0.0):
    """Modigliani M^2 (annualized, RETURN units): the book levered/de-levered to the benchmark's vol.
    m2_ann = rf + Sharpe_p * sigma_bench.  m2_excess = M^2-alpha = (Sharpe_p - Sharpe_bench) * sigma_bench
    — the Sharpe-DIFFERENCE form, so the benchmark vs itself is exactly 0 (no arithmetic/geometric offset)."""
    r = np.asarray(r, float); rb = np.asarray(rb, float)
    r = r[np.isfinite(r)]; rb = rb[np.isfinite(rb)]
    if len(r) < 30 or r.std() == 0 or rb.std() == 0 or len(rb) < 30: return dict(m2_ann=float('nan'), m2_excess=float('nan'))
    rf_d = rf / 252.0
    sh_p = (r.mean() - rf_d) / r.std() * math.sqrt(252)
    sh_b = (rb.mean() - rf_d) / rb.std() * math.sqrt(252)
    sig_b_ann = rb.std() * math.sqrt(252)
    return dict(m2_ann=rf + sh_p * sig_b_ann, m2_excess=(sh_p - sh_b) * sig_b_ann)

def riskadj(r, rb, rf=0.0):
    """One-call bundle: Sharpe/CAGR/DD/vol (from stats) + JB normality + Jensen's alpha + M^2, all vs a
    benchmark return series rb. This is the family's standard scorecard row for a return stream."""
    out = dict(stats(r)); out.update(jarque_bera(r))
    out.update(jensens_alpha(r, rb, rf)); out.update(m_squared(r, rb, rf))
    return out

def portable_alpha(alpha, beta, rf=0.0, w=1.0):
    """Evaluate an alpha stream PORTED onto a beta stream (beta + w*alpha) — the portable-alpha construction.
    Returns the ported riskadj vs beta, plus full and CRISIS correlation (beta's worst-5% days — the 2008
    tell). A viable portable-alpha ingredient CLEARS the hurdle (Jensen alpha > 0 AND M2 excess > 0 vs beta)
    with a low crisis correlation; a hedge with negative carry fails it even if full-sample it looks diversifying."""
    import numpy as _np
    alpha = _np.asarray(alpha, float); beta = _np.asarray(beta, float)
    m = _np.isfinite(alpha) & _np.isfinite(beta); alpha, beta = alpha[m], beta[m]
    if len(beta) < 30: return dict(clears=None)
    ported = beta + w * alpha
    crash = beta <= _np.percentile(beta, 5)
    out = dict(riskadj(ported, beta, rf))
    out["fullcorr"] = float(_np.corrcoef(alpha, beta)[0, 1])
    out["crisiscorr"] = float(_np.corrcoef(alpha[crash], beta[crash])[0, 1]) if crash.sum() > 2 else float("nan")
    out["clears"] = bool(out["alpha_ann"] > 0 and out["m2_excess"] > 0)
    return out
# --------------------------------------------------------------------------------------------------
