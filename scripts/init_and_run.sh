#!/usr/bin/env bash
set -euo pipefail

APP_CMD=("$@")
BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
MODEL="${OLLAMA_MODEL_NAME:-qwen3:8b}"
EMBED_MODEL="${OLLAMA_EMBED_MODEL_NAME:-embeddinggemma}"

echo "[init] Waiting for Ollama at ${BASE_URL} ..."
for i in $(seq 1 60); do
  if curl -sf "${BASE_URL}/api/tags" >/dev/null 2>&1; then
    echo "[init] Ollama is up."
    ready=1
    break
  fi
  sleep 2
done

if [ "${ready:-0}" != "1" ]; then
  echo "[init] Ollama is not reachable after wait. Exiting."
  exit 1
fi

pull_model() {
  local name="$1"
  if [ -z "$name" ]; then
    return
  fi
  echo "[init] Pulling model ${name} ..."
  curl -sf -X POST "${BASE_URL}/api/pull" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"${name}\"}" >/dev/null
  echo "[init] Done: ${name}"
}

pull_model "$MODEL"
pull_model "$EMBED_MODEL"

echo "[init] Starting app: ${APP_CMD[*]}"
exec "${APP_CMD[@]}"
