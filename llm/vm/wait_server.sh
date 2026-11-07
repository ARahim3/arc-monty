#!/usr/bin/env bash
# Block until the server on port $1 answers (or its log shows a fatal error). Prints the outcome.
PORT=$1; M=${2:-}
for i in $(seq 1 360); do
  curl -sf -m 5 http://127.0.0.1:$PORT/v1/models >/dev/null && { echo "READY port $PORT after $((i*10))s"; exit 0; }
  if [ -n "$M" ] && grep -qE "Traceback|EngineCore failed|Error:" /mnt/data/logs/serve_${M}_${PORT}.log 2>/dev/null \
     && ! pgrep -f "port $PORT" >/dev/null; then echo "FAILED port $PORT"; tail -40 /mnt/data/logs/serve_${M}_${PORT}.log; exit 1; fi
  sleep 10
done; echo "TIMEOUT port $PORT"; exit 1
