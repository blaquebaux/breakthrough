# Blaque Baux Breakthrough

> **CAPSTONE · GOVERNED RESEARCH** &nbsp;|&nbsp; Python / Julia &nbsp;|&nbsp; [Interactive Capstone](https://www.blaquebaux.com/capstone/) &nbsp;|&nbsp; [Research corpus](https://www.blaquebaux.com/corpus/) &nbsp;|&nbsp; [Citation](CITATION.cff)

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

## The graduation — the governed live allocator (built)

The proof is now a **governed live product.** Two governed steps:

1. [`live/breakthrough_allocator.py`](live/breakthrough_allocator.py) computes today's target book —
   **risk parity (default) over the brigade ingredient set** (keepers + curated void-fillers crypto/defensive)
   **+ the bastion bear insurance overlay**, which shorts SPY only when benchmark's `market_regime` is risk-off
   (the validated regime-conditional tilt). Modes: `BB_ALLOC_MODE=riskparity|minvar|levered`
   ([breakthrough](https://github.com/blaquebaux/breakthrough) / [brilliant](https://github.com/blaquebaux/brilliant) /
   [bossy](https://github.com/blaquebaux/bossy)); `BB_BEAR_WEIGHT` is the [bastion](https://github.com/blaquebaux/bastion) dial.
2. [`live/breakthrough_live.jl`](live/breakthrough_live.jl) reads that target and routes it through the engine's
   **Layer-3 safety gate** (preflight, idempotency, reconciliation, HWM, kill switch) — exactly like every
   other sleeve. Own ledger/HWM; dry-run/paper by default; real money needs `BB_LIVE_CONFIRM`.

**No LLM in the order path** — both the allocator and the rail are reproducible code (research emits the
target, the governed rail executes it). Dry-run verified end-to-end: a 19-name, gross-1.0x, risk-parity book
across the brigade ingredients, gate **PASS**.

```bash
python3 live/breakthrough_allocator.py && julia --project=engine live/breakthrough_live.jl   # emit + route
BB_DRYRUN=1 bash live/run_breakthrough_daily.sh                                               # governed dry-run
```

*Honest scope:* the allocator reconstructs the keepers as **ETF proxies** (the fully-faithful aggregation over
the real sleeve drivers is the base's [`multi_sleeve_portfolio.jl`](https://github.com/blaquebaux/base) +
`PortfolioOpt`, a future consolidation). The proxy result is what was validated (+1.16); numbers shift with the
real books, but the structure — diversifying ingredients, humble risk-parity, regime-conditional insurance — is
the product.

## Status
**Governed live allocator built — the capstone graduated.** The validated meta-allocator (risk parity over the
brigade ingredient set + regime-conditional bastion bear insurance) now emits a target book that routes through
the Layer-3 safety gate; dry-run PASS (19 names, gross 1.0x). Defaults to breakthrough (risk parity), with
brilliant (min-variance) and bossy (leverage) as modes. The first trunk branch that is a keeper, and the sleeve
that turns 40 ingredients into one governed product. Ships dry-run/paper; not yet run as real money.

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
live/       breakthrough_allocator.py (emits the target) + breakthrough_live.jl (governed Layer-3 rail)
            + run_breakthrough_daily.sh + com.blaquebaux.breakthrough.plist
```

## License
[MIT](LICENSE). (c) 2026 Carter Warrens.
