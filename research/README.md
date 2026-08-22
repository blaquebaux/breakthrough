# Blaque Baux Breakthrough — research

The capstone question: does assembling the family's **keepers** into one risk-budgeted portfolio compound
past the best single sleeve and the Bogle hurdle? Six keepers reconstructed as ETF proxies, combined via
inverse-vol (equal-risk-contribution), causal, monthly, net of cost. Read-only Alpaca SIP bars, fat-tail toolkit.

```bash
export $(grep -v '^#' ~/.config/blaquebaux/alpaca.env | xargs)   # or source it
python research/breakthrough_1_allocator.py
```

## Scorecard (2016-01 → 2026-07 SIP)

| # | Question | Result | Verdict |
|---|----------|--------|---------|
| 1 | Does risk-budgeting the keepers compound? | **COMBINED Sharpe +1.16** (best single keeper +1.02, SPY +0.87), CAGR +11%, maxDD **−17%** (SPY −34%), Jensen α +4.4% / M² +5.1%, avg keeper corr **+0.37** | ✅ **it compounds — the capstone works** |

## The synthesis

**The payoff of the whole program.** After four trunk nulls proved there's no new premium hiding in listed
instruments, breakthrough shows the edge was never a single premium — it's the **disciplined assembly** of
what survived. A risk-budgeted (equal-risk-contribution) combination of the keepers —
[spine](https://github.com/blaquebaux/base) (diversification), trend (crisis hedge), tail
([bleed](https://github.com/blaquebaux/bleed)), gulf ([brics](https://github.com/blaquebaux/brics)), growth
([bull](https://github.com/blaquebaux/bull)), PE ([blackstone](https://github.com/blaquebaux/blackstone)) —
delivers a **higher Sharpe than any of its parts** (+1.16 vs the best +1.02) and clears the
[bogle](https://github.com/blaquebaux/bogle) hurdle by M² +5.1%, at half the market's drawdown. It works
because the keepers are genuinely diversifying (avg pairwise corr +0.37): risk-budgeting harvests that.

This is the first of the eight trunk branches to be a **keeper** — and the only one that didn't need a new
premium, because it monetizes the ones already validated. The natural graduation is the **governed,
regime-conditional live allocator** over the *real* books (the base's `PortfolioOpt` library + the five
published regime signals + `portable_alpha` for the neutral sleeves).

## Status
**Research validated — the capstone compounds.** Risk-budgeting the keepers beats the best single sleeve and
the index at half the drawdown (diversification, avg corr +0.37). ETF-proxy first pass; the governed
regime-conditional allocator over the real books is the graduation.
