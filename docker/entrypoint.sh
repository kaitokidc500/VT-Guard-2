#!/bin/sh
# VT-Guard Buoc 9 - entrypoint image (docs/STEP9-BRIEF.md muc 6.2). Moi duong dan tinh tu VTGUARD_HOME (= /app).
#   dashboard (mac dinh)     dashboard cong 8501, doc canh bao da dong bang
#   demo [--speed k]          phat lai log mau (nen, mac dinh x10 ~3 phut) + dashboard: trang Truc tiep tu cap nhat (kieu B khong can lab)
#   verify                    chay lai infer.py + evaluate.py tren 3 tap test, so so lieu bao cao, DAT / KHONG DAT
#   infer --input <file> [--out <file>]   pipeline tren file cua so (dinh dang windows.jsonl) mount tu ngoai
#   replay [--input <log>] [--speed k]    phat lai log qua pipeline truc tiep (mac dinh samples/replay_demo.jsonl.gz)
#   live --env-file <file> [--push-alerts]  (chi trong lab) noi Indexer that + dashboard; dang nhap mount tu ngoai, khong nam trong image
#   selftest                  kiem thu khong can GPU / mang (dashboard + luong truc tiep + quet file nhay cam)
#   scan                      quet image: 0 checkpoint / log tho / thong tin dang nhap
set -e
cd "${VTGUARD_HOME:-/app}"
cmd="${1:-dashboard}"; [ $# -gt 0 ] && shift

dash() { exec python -m streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true \
           --browser.gatherUsageStats false "$@"; }

# chay luong (replay / live) nen, log ra stdout container; dung trong 5 s dau (vd sai dang nhap) -> thoat loi, khong mo dashboard rong
stream_bg() {
  python src/live/run.py "$@" &
  pid=$!; sleep 5
  kill -0 "$pid" 2>/dev/null || { wait "$pid" || true; echo "Luong $1 dung ngay khi khoi dong (xem log o tren)."; exit 1; }
}

case "$cmd" in
  dashboard) dash "$@" ;;
  demo) stream_bg replay --input samples/replay_demo.jsonl.gz --speed 10 "$@"; dash ;;
  verify) exec python src/pipeline/verify.py --out /tmp/verify.json "$@" ;;
  infer)
    in=""; out="/out/alerts.jsonl"
    while [ $# -gt 0 ]; do case "$1" in --input) in="$2"; shift 2 ;; --out) out="$2"; shift 2 ;; *) echo "tham so la: $1"; exit 2 ;; esac; done
    [ -n "$in" ] || { echo "infer can --input <file windows.jsonl>"; exit 2; }
    mkdir -p "$(dirname "$out")"
    exec python src/pipeline/infer.py --windows "$in" --out "$out" ;;
  replay)
    case " $* " in *" --input "*) ;; *) set -- --input samples/replay_demo.jsonl.gz "$@" ;; esac
    exec python src/live/run.py replay "$@" ;;
  live) stream_bg live "$@"; dash ;;
  selftest)
    rc=0
    python dashboard/test_data.py || rc=1
    python src/live/test_live.py || rc=1
    python docker/scan.py /app || rc=1
    [ $rc -eq 0 ] && echo "SELFTEST: DAT" || echo "SELFTEST: KHONG DAT"
    exit $rc ;;
  scan) exec python docker/scan.py "${1:-/app}" ;;
  sh|bash) exec /bin/sh "$@" ;;
  *) echo "Lenh: dashboard | demo | verify | infer | replay | live | selftest | scan"; exit 2 ;;
esac
