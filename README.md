# Blaque Baux Breakthrough

**The capstone — assemble the keepers into one risk-budgeted portfolio. It compounds: Sharpe +1.16, half the market's drawdown, clear of the Bogle hurdle.**

Breakthrough is the meta-allocator of the Blaque Baux family. The [core repo](https://github.com/blaquebaux/base)
is the **engine and blueprint** — a governed, systematic platform (Julia) with a venue-agnostic execution
controller and a Layer-3 live-money safety gate, and a `PortfolioOpt` optimization library. Breakthrough uses
all of it to turn the family's *many validated ingredients* into **one portfolio.**

> **Not investment advice.** Educational/research software. Nothing here is validated to a live-money bar. See [LICENSE](LICENSE).

```bash
git clone --recursive https://github.com/blaquebaux/breakthrough.git
julia --project=engine -e 'using Pkg; Pkg.instantiate()'   # one-time engine setup
```

## The thesis

Breakthrough is **not a new premium** — the trunk-branch program proved the classic harvestable premia
(vol/pairs/carry/merger-arb) are dead in listed form. It doesn't need one. It takes the **keepers the family
already validated** and asks the only question that ultimately matters: *does assembling them into one
risk-budgeted portfolio beat the best single sleeve and the low-cost index?* If the keepers are genuinely
diversifying, the combination should compound — higher risk-adjusted return than any of its parts. That's the
entire reason a *family* of strategies exists rather than one bet.

## The test — and the verdict: **it compounds**

[`research/breakthrough_1_allocator.py`](research/breakthrough_1_allocator.py) reconstructs six keepers as
priceable ETF proxies and combines them via **inverse-vol (equal-risk-contribution)**, causal, monthly, net
of cost (Alpaca SIP 2016–2026):

| keeper (ETF proxy) | Sharpe | CAGR | vol | maxDD | corr-SPY |
|---|---|---|---|---|---|
| spine (risk-parity) | +1.02 | +7% | 6.8% | −15% | +0.55 |
| trend (12-1 mom) | +0.91 | +10% | 11.7% | −24% | +0.49 |
| tail (GLD/TLT) | +0.63 | +7% | 11.6% | −30% | −0.01 |
| gulf (KSA) | +0.42 | +7% | 19.9% | −41% | +0.52 |
| growth (QQQ) | +0.95 | +21% | 22.9% | −35% | +0.93 |
| PE (blackstone) | +0.82 | +23% | 31.2% | −45% | +0.80 |
| **COMBINED (risk-parity)** | **+1.16** | **+11%** | **9.3%** | **−17%** | +0.78 |
| SPY (Bogle hurdle) | +0.87 | +15% | 18.0% | −34% | +1.00 |

**The combined portfolio beats every single keeper *and* the Bogle hurdle.** Sharpe **+1.16** tops the best
sleeve (spine +1.02) and the market (+0.87); it earns Jensen α **+4.4%** / M² **+5.1%** over SPY at **half the
drawdown** (−17% vs −34%). The keepers average just **+0.37 pairwise correlation**, so risk-budgeting across
them harvests the diversification — the whole is genuinely more than its parts. *This is the payoff of the
entire program:* not one premium, but the disciplined *assembly* of what survived.

## Honest scope (first pass vs the graduation)
- This is an **ETF-proxy** reconstruction of the keepers — the faithful Julia reconstruction over the real
  books lives in the base's [`scripts/research/multi_sleeve_portfolio.jl`](https://github.com/blaquebaux/base)
  (risk-parity / HRP / min-CVaR over the `PortfolioOpt` library). The proxy result proves the *compounding*;
  numbers will shift with the real books, but the diversification structure (avg corr +0.37) is the point.
- **Next — the governed allocator driver:** aggregate the live keeper books into one governed order set,
  risk-budgeted and **regime-conditional** (tilt via the five published signals — bonds/market/dollar/rate
  regimes — and size portable-alpha sleeves like [bore](https://github.com/blaquebaux/bore) onto the beta).
  That is the graduation from "it compounds" to "one governed product."

## Status
**Research validated — the capstone compounds; governed allocator is the graduation.** A risk-budgeted
combination of the family's keepers (spine/trend/tail/gulf/growth/PE) delivers Sharpe **+1.16** — above the
best single keeper and the Bogle hurdle — at half the market's drawdown, because the keepers are genuinely
diversifying (avg corr +0.37). The **first trunk branch that is a keeper**, and the one that turns 40
ingredients into a portfolio. The governed, regime-conditional live allocator (over the real books) is the
next build.

## About Blaque Baux

**Blaque Baux** is a quantitative research initiative and a subsidiary of **[Carter Warrens](https://carterwarrens.com)**.
[**BlaqueBaux.com**](https://blaquebaux.com) is the home for the work; the code lives here on GitHub — open to
study, test, and build bespoke strategies on top of.

Anyone can point an AI at a market. The edge is **understanding what the data actually says — and turning it
into something you can act on.** We test relentlessly and put most of it *on the record as rejected, with the
reason*; what survives is built, governed, and validated before it is ever called real. That combination —
honest research, reproducible evidence, and execution you can trust — is why Carter Warrens leads on
**strategy and implementation**, not merely uses the tools everyone now has.

## The Blaque Baux family
This repo is one sleeve of the **Blaque Baux** family — a single governed engine steered in
many directions. The [core repo](https://github.com/blaquebaux/base) is the
base/blueprint and holds the [full family roster](https://github.com/blaquebaux/base#the-blaquebaux-family).

## Layout
```
engine/     the Blaque Baux platform (git submodule -> blaquebaux/base; incl. the PortfolioOpt library)
research/   _breakthrough_common.py + breakthrough_1_allocator.py (the meta-allocator proof) + scorecard
live/       governed regime-conditional allocator over the real keeper books  [the graduation — to build]
```

## License
[MIT](LICENSE). (c) 2026 Carter Warrens.
