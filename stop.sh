#!/usr/bin/env bash
# Stop NyayaSetu. By default stops only the app (backend + UI); pass --all to also stop
# Postgres, Redis and Qdrant. Data is kept either way.
set -uo pipefail

S="${NYAYASETU_SERVICES:-$HOME/.local/lexai-services}"
PG_BIN="${PG_BIN:-$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | sort -V | tail -1)}"

stop_port() {  # stop_port <name> <port>
  local pids
  pids=$(ss -ltnpH "sport = :$2" | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u)
  [ -z "$pids" ] && { echo "  · $1 not running"; return; }
  kill $pids
  for _ in $(seq 1 20); do ss -ltn "sport = :$2" | grep -q LISTEN || { echo "  ✔ stopped $1"; return; }; sleep 0.5; done
  kill -9 $pids 2>/dev/null; echo "  ✔ stopped $1 (forced)"
}

echo "Stopping NyayaSetu…"
stop_port UI 8501
stop_port Backend 8001

if [ "${1:-}" = "--all" ]; then
  stop_port Qdrant 6333
  "$S/redis-7.4.2/src/redis-cli" -p 6379 shutdown >/dev/null 2>&1 && echo "  ✔ stopped Redis" || echo "  · Redis not running"
  "$PG_BIN/pg_ctl" -D "$S/pgdata" stop -m fast >/dev/null 2>&1 && echo "  ✔ stopped Postgres" || echo "  · Postgres not running"
fi
