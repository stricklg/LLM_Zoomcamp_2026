#!/bin/bash
# Start Kestra after a Codespace restart.
# Kestra runs with network_mode: host, so no iptables workaround is needed.
# Usage: ./start.sh  (run from llm-zoomcamp-orchestration/)

set -e
cd "$(dirname "$0")"

echo "Starting Postgres..."
docker compose up -d kestra-postgres

echo "Starting Kestra (host networking)..."
docker compose up -d kestra

echo "Waiting 60s for Kestra to boot..."
sleep 60

echo "--- Kestra logs (tail) ---"
docker compose logs kestra --tail 5

echo "--- Smoke test ---"
curl -s -o /dev/null -w "Kestra UI: HTTP %{http_code}\n" --max-time 10 http://localhost:8080/

echo ""
echo "Done. If the UI isn't reachable, forward port 8080 in the VS Code Ports tab."
echo "(Host mode has no ports: mapping, so VS Code won't auto-forward it.)"