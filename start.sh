#!/usr/bin/env bash
# Start NyayaSetu locally (no Docker): Postgres, Redis, Qdrant, FastAPI backend, Streamlit UI.
# Service binaries/data live in $NYAYASETU_SERVICES (default ~/.local/lexai-services).
# Safe to re-run: anything already listening on its port is left alone.
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
S="${NYAYASETU_SERVICES:-$HOME/.local/lexai-services}"
LOGS="$S/logs"
PG_BIN="${PG_BIN:-$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | sort -V | tail -1)}"
mkdir -p "$LOGS"

listening() { ss -ltn "sport = :$1" | grep -q LISTEN; }

wait_for() {  # wait_for <name> <port> <seconds>
  for _ in $(seq 1 "$3"); do listening "$2" && { echo "  ✔ $1 on :$2"; return 0; }; sleep 1; done
  echo "  ✘ $1 did not start on :$2 — see $LOGS"; return 1
}

echo "Starting NyayaSetu services…"

listening 5433 || "$PG_BIN/pg_ctl" -D "$S/pgdata" -l "$LOGS/postgres.log" \
  -o "-p 5433 -k $S/pgsock -c listen_addresses=127.0.0.1" start >/dev/null
wait_for Postgres 5433 30

listening 6379 || "$S/redis-7.4.2/src/redis-server" --port 6379 --bind 127.0.0.1 \
  --daemonize yes --dir "$S" --logfile "$LOGS/redis.log"
wait_for Redis 6379 15

if ! listening 6333; then
  (cd "$S" && QDRANT__STORAGE__STORAGE_PATH="$S/qdrant_storage" QDRANT__SERVICE__HOST=127.0.0.1 \
    nohup ./qdrant >"$LOGS/qdrant.log" 2>&1 &)
fi
wait_for Qdrant 6333 30

cd "$APP_DIR"
if ! listening 8001; then
  PYTHONUNBUFFERED=1 nohup .venv/bin/uvicorn app.api.main:app --host 127.0.0.1 --port 8001 \
    >"$LOGS/backend.log" 2>&1 &
fi
wait_for "Backend (loads embedding model)" 8001 180

if ! listening 8501; then
  nohup .venv/bin/streamlit run ui.py --server.port 8501 --server.address 127.0.0.1 \
    --server.headless true --server.fileWatcherType poll >"$LOGS/ui.log" 2>&1 &
fi
wait_for UI 8501 60

echo
echo "NyayaSetu is running → http://localhost:8501   (API: http://localhost:8001, logs: $LOGS)"
