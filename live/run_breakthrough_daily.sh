#!/bin/bash
# run_breakthrough_daily.sh — the governed meta-allocator (Blaque Baux capstone). Two steps: (1) the Python
# allocator emits today's validated target book; (2) the Julia governed driver routes it through the Layer-3
# safety gate. DRY-RUN by default; graduates to PAPER once ~/.config/blaquebaux/alpaca_breakthrough.env exists.
# Config: BB_ALLOC_MODE (riskparity|minvar|levered), BB_BEAR_WEIGHT (bastion insurance), BB_LEVERAGE (bossy dial).
set -uo pipefail
REPO="/Users/malcolmx/blaquebaux-breakthrough"; ENGINE="$REPO/engine"; JULIA="/Users/malcolmx/.juliaup/bin/julia"
DATAENV="$HOME/.config/blaquebaux/alpaca.env"; SLEEVEENV="$HOME/.config/blaquebaux/alpaca_breakthrough.env"
LOGDIR="$REPO/logs"; mkdir -p "$LOGDIR"; LOG="$LOGDIR/breakthrough_$(TZ=America/New_York date +%Y%m%d).log"
exec >> "$LOG" 2>&1
echo "======== $(TZ=America/New_York date '+%F %T %Z') breakthrough meta-allocator run ========"
export BB_LEDGER_PATH="$REPO/alpaca_ledger_breakthrough.sqlite" BB_AUDIT_PATH="$REPO/alpaca_audit_breakthrough.jsonl"
export BB_HWM_PATH="$HOME/.config/blaquebaux/equity_hwm_breakthrough.txt" BB_EQUITY_PATH="$HOME/.config/blaquebaux/equity_last_breakthrough.txt"
export BB_ALLOC_TARGET="$REPO/breakthrough_target.txt" BB_ALLOC_MODE="${BB_ALLOC_MODE:-riskparity}"
if [ -f "$SLEEVEENV" ]; then set -a; source "$SLEEVEENV"; set +a
else [ -f "$DATAENV" ] && { set -a; source "$DATAENV"; set +a; }; export BB_DRYRUN=1; fi
if [ -z "${ALPACA_KEY_ID:-}" ] || [ -z "${ALPACA_SECRET_KEY:-}" ]; then echo "no ALPACA keys — skipping"; exit 0; fi
MODE=$([ "${BB_DRYRUN:-}" = "1" ] && echo dryrun || echo paper); echo "mode=$MODE alloc=$BB_ALLOC_MODE"
if [ "$MODE" = "paper" ]; then
  CLOCK=$(curl -s --max-time 15 -H "APCA-API-KEY-ID: $ALPACA_KEY_ID" -H "APCA-API-SECRET-KEY: $ALPACA_SECRET_KEY" https://paper-api.alpaca.markets/v2/clock)
  IS_OPEN=$(echo "$CLOCK" | grep -Eo '"is_open":(true|false)' | grep -Eo 'true|false' | head -1)
  NEXT_OPEN=$(echo "$CLOCK" | grep -o '"next_open":"[^"]*"' | grep -Eo '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)
  ET_TODAY=$(TZ=America/New_York date +%F)
  if { [ -n "$IS_OPEN" ] || [ -n "$NEXT_OPEN" ]; } && [ "$IS_OPEN" != "true" ] && [ "$NEXT_OPEN" != "$ET_TODAY" ]; then echo "not a trading day — skipping"; exit 0; fi
  ORDERS_TODAY=$(curl -s --max-time 15 -H "APCA-API-KEY-ID: $ALPACA_KEY_ID" -H "APCA-API-SECRET-KEY: $ALPACA_SECRET_KEY" "https://paper-api.alpaca.markets/v2/orders?status=all&limit=10&after=${ET_TODAY}T00:00:00Z" | grep -o '"id"' | wc -l | tr -d ' ')
  [ "${ORDERS_TODAY:-0}" -gt 0 ] && { echo "already placed today — skipping (catch-up no-op)"; exit 0; }
fi
cd "$REPO" || exit 1
echo "--- step 1: allocator (emit target) ---"; /usr/bin/python3 "$REPO/live/breakthrough_allocator.py" || { echo "allocator failed"; exit 1; }
echo "--- step 2: governed driver (route target) ---"; "$JULIA" --project="$ENGINE" "$REPO/live/breakthrough_live.jl"; RC=$?
echo "======== done rc=$RC $(TZ=America/New_York date '+%T %Z') ========"; exit $RC
