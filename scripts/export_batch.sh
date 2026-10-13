#!/usr/bin/env bash
# Xuat log tho theo khoang thoi gian cho mot dot chay. Chay tren VT-SIEM01.
# Dung: ./export_batch.sh <GTE> <LTE> <ten_dot>
# vd:   ./export_batch.sh 2026-10-13T14:00:00Z 2026-10-13T18:00:00Z batch01
set -uo pipefail
GTE="${1:?gte}"; LTE="${2:?lte}"; NAME="${3:?ten_dot}"
ES="https://localhost:9200"; OUT="$HOME/vt-guard/data/raw/$NAME"; mkdir -p "$OUT"
read -s -p "Mat khau Indexer: " PW; echo
curl -sk -u "admin:$PW" "$ES/" | grep -q cluster_name || { echo "Sai mat khau"; exit 1; }
for AG in DC01 WIN10-01; do
  curl -sk -u "admin:$PW" -H 'Content-Type: application/json' \
    "$ES/wazuh-archives-*/_search?size=10000" -d "{
      \"sort\":[{\"timestamp\":\"asc\"}],
      \"query\":{\"bool\":{\"filter\":[
        {\"term\":{\"agent.name\":\"$AG\"}},
        {\"range\":{\"timestamp\":{\"gte\":\"$GTE\",\"lte\":\"$LTE\"}}}
      ]}}}" > "$OUT/${AG}.json"
  n=$(python3 -c "import json;print(len(json.load(open('$OUT/${AG}.json'))['hits']['hits']))")
  echo "$AG: $n event -> $OUT/${AG}.json"
done
echo "Xong. Chep thu muc $OUT ve host de chay normalize.py + label.py."
