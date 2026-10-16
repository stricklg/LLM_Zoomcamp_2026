#!/bin/bash
# start.sh — (Re)start the Kestra stack on GitHub Codespaces.
# Works around the image-level Docker quirk that blocks container-to-container
# bridge traffic. The iptables rule is runtime-only, so this script re-applies
# it on every run (safe to run repeatedly).
set -e
cd "$(dirname "$0")"

echo "== Starting postgres (creates the Docker network) =="
docker compose up -d kestra-postgres

echo "== Applying bridge-networking workaround =="
SUBNET=$(docker network inspect llm-zoomcamp-orchestration_kestra_net --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
if [ -z "$SUBNET" ]; then
  echo "ERROR: could not determine Docker subnet" >&2
  exit 1
fi
for cmd in iptables iptables-legacy; do
  if sudo "$cmd" -C DOCKER-USER -s "$SUBNET" -d "$SUBNET" -j ACCEPT 2>/dev/null; then
    echo "  $cmd: rule already present"
  else
    sudo "$cmd" -I DOCKER-USER -s "$SUBNET" -d "$SUBNET" -j ACCEPT
    echo "  $cmd: ACCEPT rule added for $SUBNET"
  fi
done

echo "== Starting Kestra =="
docker compose up -d kestra

echo "== Waiting 60s for Kestra to boot =="
sleep 60
docker compose logs kestra --tail 4
curl -s -o /dev/null -w "Kestra UI: HTTP %{http_code}\n" --max-time 10 http://localhost:8080/ || true
