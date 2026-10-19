#!/usr/bin/env python3
"""VT-Guard Buoc 9 (kieu B) - luong truc tiep: connector -> windower -> infer.py -> reports/step9/live/alerts.jsonl.

Goi lai NGUYEN src/pipeline/infer.Pipeline (featurize vocab dong bang -> ONNX VT-Seq-ens -> matcher Sigma -> fusion F3-B da
khoa); khong doi nguong / cau hinh. Ban ghi canh bao = schema Buoc 8 (Pipeline.alert_record) + truong cua luong truc tiep:
  mode (live / replay), received_at (gio may luc ghi), closed_at / ingest_first / ingest_last (dong ho luong: gio that o live,
  gio mo phong o replay), n_events, close_reason, p_ttp_ai + score_ttp (de trang Chi tiet phan ra diem), latency:
    wazuh_s  = ingest_last - t1       (Wazuh nhan event cuoi cua cua so sau khi no phat sinh)
    wait_s   = closed_at - ingest_last (chu ky doc + cho dong cua so)
    infer_ms = thoi gian pipeline / cua so
    total_s  = wazuh_s + wait_s + infer_ms / 1000
Che do:
  python src/live/run.py replay --input <log.jsonl[.gz] | thu_muc> [--speed 10] [--poll 10]
  python src/live/run.py live --env-file <file> [--push-alerts]        (chi dung trong lab; dang nhap nap luc chay)
Moi duong dan tinh tu VTGUARD_HOME (mac dinh goc repo).
"""
import argparse, json, os, sys, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "pipeline"))
from windower import Windower, ts, IDLE_DEFAULT, GAP_DEFAULT, W_DEFAULT   # noqa: E402
import connector as C                                                  # noqa: E402

TTPS = ["T1016", "T1018", "T1087.002", "T1654", "T1003.003"]
RATE_KEEP = 180                                                         # so chu ky poll giu trong status.json (bieu do luu luong)

def home():
    return os.environ.get("VTGUARD_HOME") or os.path.abspath(os.path.join(HERE, "..", ".."))

def live_dir(root): return os.path.join(root, "reports", "step9", "live")

def load_pipeline(root):
    from infer import Pipeline                                         # noqa: E402  (onnxruntime chi nap khi can)
    return Pipeline(root, threads=1)

def score(P, wins, mode):
    """Cham cac cua so da dong -> (moi ket qua, ban ghi canh bao). Khong sua quyet dinh cua Pipeline."""
    if not wins: return [], []
    t = time.perf_counter(); res = P.run(wins); dt_ms = (time.perf_counter() - t) * 1000 / len(wins)
    alerts = []
    for r in res:
        if not r["alert"]: continue
        w = r["window"]; a = P.alert_record(r)
        lat = {"wazuh_s": None, "wait_s": None, "infer_ms": round(dt_ms, 3), "total_s": None}
        if w.get("ingest_last") and w.get("t1"):
            lat["wazuh_s"] = round((ts(w["ingest_last"]) - ts(w["t1"])).total_seconds(), 1)
            lat["wait_s"] = round((ts(w["closed_at"]) - ts(w["ingest_last"])).total_seconds(), 1)
            lat["total_s"] = round(lat["wazuh_s"] + lat["wait_s"] + dt_ms / 1000, 1)
        a.update({"mode": mode, "received_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                  "closed_at": w.get("closed_at"), "ingest_first": w.get("ingest_first"), "ingest_last": w.get("ingest_last"),
                  "n_events": w.get("n_events"), "close_reason": w.get("close_reason"),
                  "p_ttp_ai": dict(zip(TTPS, [round(float(x), 6) for x in r["p_ttp_ai"]])),
                  "score_ttp": {k: round(v, 6) for k, v in r["score_ttp"].items()}, "latency": lat})
        alerts.append(a)
    return res, alerts

def stream(source, windower, P, out_path=None, pusher=None, status_path=None, keep_results=False, max_polls=None):
    """Vong lap chinh. keep_results=True: giu moi ket qua cua so (cho drift.py)."""
    allres, n_alert, n_win, n_src, polls = [], 0, 0, 0, 0
    agents, rate = {}, []                                              # suc khoe agent + luu luong event (cho trang Truc tiep)
    fh = open(out_path, "a", encoding="utf-8", newline="\n") if out_path else None
    try:
        while True:
            srcs, now = source.poll(); polls += 1; n_src += len(srcs)
            for s in srcs:
                h = (s.get("agent") or {}).get("name") or "?"; ag = agents.setdefault(h, {"events": 0, "last": None})
                ag["events"] += 1; ag["last"] = max(ag["last"] or "", s.get("timestamp") or "")
            rate = (rate + [[now.strftime("%Y-%m-%dT%H:%M:%SZ"), len(srcs)]])[-RATE_KEEP:]
            wins = windower.add(srcs, now)
            if source.done(): wins += windower.tick(now, force=True)
            res, alerts = score(P, wins, source.mode); n_win += len(wins)
            if keep_results: allres += res
            for a in alerts:
                if fh: fh.write(json.dumps(a, ensure_ascii=False) + "\n")
            if fh: fh.flush()
            n_alert += len(alerts)
            if pusher and alerts:
                try: pusher.push(alerts)
                except Exception as e: print(f"CANH BAO: khong ghi duoc vtguard-alerts-*: {type(e).__name__}", file=sys.stderr)
            if status_path:
                st = {"mode": source.mode, "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "stream_clock": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "polls": polls, "events_read": n_src, "windows": n_win,
                      "alerts": n_alert, "poll_s": source.poll_s,
                      "params": windower.params, "dropped": dict(windower.dropped), "prep": dict(windower.prep.stats),
                      "source": source.info(), "push_alerts": bool(pusher), "agents": agents, "rate": rate, "done": source.done()}
                tmp = status_path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f: json.dump(st, f, ensure_ascii=False)
                os.replace(tmp, status_path)
            if source.done() or (max_polls and polls >= max_polls): break
    finally:
        if fh: fh.close()
    return {"polls": polls, "events_read": n_src, "windows": n_win, "alerts": n_alert, "results": allres}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["replay", "live"])
    ap.add_argument("--input", help="replay: file log (.jsonl / .gz) hoac thu muc")
    ap.add_argument("--env-file", help="live: file KEY=VALUE chua thong tin Indexer (mount tu ngoai)")
    ap.add_argument("--poll", type=float, default=None, help="chu ky doc (s); mac dinh replay 10, live 12")
    ap.add_argument("--speed", type=float, default=0.0, help="replay: 0 = nhanh nhat; k = nhanh gap k lan thoi gian that")
    ap.add_argument("--W", type=int, default=W_DEFAULT); ap.add_argument("--idle", type=float, default=IDLE_DEFAULT)
    ap.add_argument("--gap", type=float, default=GAP_DEFAULT)
    ap.add_argument("--tool-mode", choices=["orchestrator", "console"], default="orchestrator")
    ap.add_argument("--out", default=None); ap.add_argument("--append", action="store_true", help="replay: ghi tiep thay vi lam moi")
    ap.add_argument("--push-alerts", action="store_true", help="live: ghi canh bao vao vtguard-alerts-* (mac dinh tat)")
    ap.add_argument("--start", default=None, help="live: moc bat dau (ISO) neu chua co file trang thai")
    a = ap.parse_args()
    root = home(); d = live_dir(root); os.makedirs(d, exist_ok=True)
    out = a.out or os.path.join(d, "alerts.jsonl"); status = os.path.join(d, "status.json")
    if a.mode == "replay":
        if not a.input: sys.exit("replay can --input")
        src = C.FileSource(a.input, poll_s=a.poll or 10.0, speed=a.speed); pusher = None
        if not a.append: open(out, "w").close()
    else:
        C.load_env_file(a.env_file)
        src = C.IndexerSource(os.path.join(d, "connector_state.json"), poll_s=a.poll or 12.0, start=a.start)
        pusher = C.AlertPusher(src) if a.push_alerts else None
    win = Windower(a.W, a.idle, a.gap, a.tool_mode); P = load_pipeline(root)
    print(f"[{a.mode}] bat dau -> {out} (W={a.W}, idle={a.idle}s, gap={a.gap}s, tool_mode={a.tool_mode}"
          + (", ghi vtguard-alerts-*" if pusher else "") + ")", flush=True)
    s = stream(src, win, P, out, pusher, status)
    print(f"[{a.mode}] xong: {s['events_read']} event doc, {s['windows']} cua so, {s['alerts']} canh bao; loai: {dict(win.dropped)}; "
          f"tien xu ly: {dict(win.prep.stats)}")

if __name__ == "__main__":
    main()
