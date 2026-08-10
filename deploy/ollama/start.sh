#!/bin/sh
set -eu

/bin/ollama serve &
server_pid=$!
until /bin/ollama list >/dev/null 2>&1; do
  sleep 1
done
/bin/ollama pull "${OLLAMA_MODEL:-qwen2.5:3b}"
wait "$server_pid"
