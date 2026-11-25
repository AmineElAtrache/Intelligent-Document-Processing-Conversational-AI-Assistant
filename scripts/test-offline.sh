#!/usr/bin/env bash
# One-command check: no GPU, no OpenAI key. Ollama is not required.
set -euo pipefail
cd "$(dirname "$0")/.."

export OPENAI_API_KEY=""
export LLM_PROVIDER="mock"

if docker info >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif sudo docker info >/dev/null 2>&1; then
  COMPOSE=(sudo docker compose)
else
  echo "Docker is not running. Install Docker and start the daemon, then rerun this script." >&2
  exit 1
fi

echo "Checking compose file"
"${COMPOSE[@]}" config >/dev/null

echo "Recreating the CPU stack (this wipes the idp-data volume)"
"${COMPOSE[@]}" down -v --remove-orphans
"${COMPOSE[@]}" up --build -d --wait --wait-timeout 180

python3 scripts/smoke_check.py "http://127.0.0.1:8080"
echo "UI:  http://127.0.0.1:8080"
echo "API: http://127.0.0.1:8000/docs"
