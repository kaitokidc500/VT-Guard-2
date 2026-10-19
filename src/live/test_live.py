#!/usr/bin/env python3
"""VT-Guard Buoc 9 - kiem thu che do truc tiep (src/live): connector, windower, vong lap run.stream, phat lai log mau.
Khong can Indexer, khong can mang, khong doc nhan. Dung samples/replay_demo.jsonl.gz (log tho Wazuh, khong sua).
  L1 FileSource: moi event doc dung 1 lan, theo thu tu timestamp Wazuh; poll tien dung poll_s; done() cuoi luong;
     speed > 0 khong doi ket qua, chi tua nhanh khoang im lang
  L2 load_env_file: doc KEY=VALUE, bo chu thich, khong ghi de bien da co; IndexerSource tu choi khi thieu dang nhap / CA
  L3 Windower: moi cua so <= W event, sap theo ts_system, khong conhost, parent cmd/powershell -> <launcher>, dung EVENT_FIELDS,
     khong event nao o 2 cua so, close_reason hop le, window_id duy nhat
  L4 dong cua so: du W event / host im lang qua idle_s / khoang trong su kien > gap_s / ket thuc luong
  L5 phat lai dau-cuoi qua infer.Pipeline: so canh bao + quyet dinh == ban tham chieu reports/step9/replay_reference.json
     (container == host); ban ghi canh bao = schema Buoc 8 + truong luong truc tiep, KHONG co truong nhan; do tre >= 0
  L6 AlertPusher: _bulk ndjson dung index vtguard-alerts-YYYY.MM.DD, dem ban ghi thanh cong
  L7 dashboard doc canh bao truc tiep: ma LIVE-xxxx, su co LINC-xxx, khong co truong nhan
Chay: python src/live/test_live.py [--write-ref]
"""
import argparse, gzip, json, os, sys, tempfile, time
from datetime import timedelta

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import connector as C                                                       # noqa: E402
from run import home, load_pipeline, stream                                  # noqa: E402
from windower import Windower, ts, dedup_key, W_DEFAULT                      # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "dataset"))
from windows import EVENT_FIELDS                                             # noqa: E402

ROOT = home()
SAMPLE = os.path.join(ROOT, "samples", "replay_demo.jsonl.gz")
REF = os.path.join(ROOT, "reports", "step9", "replay_reference.json")
LABEL_KEYS = ("y", "y_ttp", "label", "label_malicious", "label_ttps", "window_malicious", "window_ttps", "event_label", "origin")
STEP8_KEYS = {"window_id", "host", "t0", "t1", "score", "decision_source", "ttps", "rule_ids", "attention_top5", "p_ai", "threshold",
              "thresholds_ttp", "fusion_config"}
LIVE_KEYS = {"mode", "received_at", "closed_at", "ingest_first", "ingest_last", "n_events", "close_reason", "p_ttp_ai", "score_ttp", "latency"}
RESULTS = []

def check(name, ok, detail=""):
    RESULTS.append(bool(ok)); print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""), flush=True)

def decision_key(a):
    return {"window_id": a["window_id"], "decision_source": a["decision_source"], "ttps": a["ttps"],
            "rules": [r["id"] for r in a["rule_ids"]], "score": round(a["score"], 4)}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--write-ref", action="store_true"); a = ap.parse_args()
    t_start = time.time()
    rows = C.read_log(SAMPLE)

    # L1
    src = C.FileSource(SAMPLE, poll_s=10.0); got, clocks = [], []
    while not src.done():
        r, now = src.poll(); got += r; clocks.append(now)
    tsw = [C._parse(r["timestamp"]) for r in got]
    steps = {round((b - a_).total_seconds(), 6) for a_, b in zip(clocks, clocks[1:])}
    check("L1 FileSource doc moi event dung 1 lan, theo timestamp, buoc poll 10 s", len(got) == len(rows) and tsw == sorted(tsw) and steps == {10.0},
          f"{len(got)} / {len(rows)} event, {len(clocks)} chu ky")
    naps = []; real_sleep = C.time.sleep; C.time.sleep = naps.append
    try:
        fs = C.FileSource(SAMPLE, poll_s=10.0, speed=10); got2, clocks2 = [], []
        while not fs.done():
            r, now = fs.poll(); got2 += r; clocks2.append(now)
    finally: C.time.sleep = real_sleep
    check("L1b speed > 0: cung event + dong ho luong nhu speed 0; chi ngu o chu ky co event / gan event (tua nhanh khoang im lang)",
          got2 == got and clocks2 == clocks and 0 < len(naps) < len(clocks) and set(naps) == {1.0},
          f"ngu {len(naps)} / {len(clocks2)} chu ky -> ~{sum(naps):.0f} s o toc do x10")

    # L2
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "x.env")
        with open(p, "w", encoding="utf-8") as f: f.write("# chu thich\nVTG_TEST_A = 'mot'\n\nVTG_TEST_B=hai=ba\n")
        os.environ["VTG_TEST_B"] = "giu"; keys = C.load_env_file(p)
        ok_env = keys == ["VTG_TEST_A", "VTG_TEST_B"] and os.environ["VTG_TEST_A"] == "mot" and os.environ["VTG_TEST_B"] == "giu"
        saved = {k: os.environ.pop(k, None) for k in ("VTG_INDEXER_URL", "VTG_INDEXER_USER", "VTG_INDEXER_PASSWORD", "VTG_INDEXER_CA", "VTG_INDEXER_INSECURE")}
        refused = []
        for env in ({}, {"VTG_INDEXER_URL": "https://127.0.0.1:1", "VTG_INDEXER_USER": "u", "VTG_INDEXER_PASSWORD": "p"}):
            os.environ.update(env)
            try: C.IndexerSource(os.path.join(td, "st.json")); refused.append(False)
            except SystemExit: refused.append(True)
            for k in env: os.environ.pop(k, None)
        for k, v in saved.items():
            if v is not None: os.environ[k] = v
    check("L2 env-file KEY=VALUE khong ghi de; IndexerSource tu choi khi thieu dang nhap / CA", ok_env and all(refused), f"{keys}, tu choi {refused}")

    # L3 (khong suy luan): toan bo mau qua Windower
    win = Windower(); src = C.FileSource(SAMPLE, poll_s=10.0); W = []
    while not src.done():
        r, now = src.poll(); W += win.add(r, now)
    W += win.tick(now, force=True)
    keys_all = [k for w in W for k in w["_keys"]]
    bad_sort = [w["window_id"] for w in W if [e["ts"] for e in w["events"]] != sorted(e["ts"] for e in w["events"])]
    bad_img = sum((e.get("image_name") or "").lower() == "conhost.exe" for w in W for e in w["events"])
    bad_par = sum((e.get("parent_image_name") or "").lower() in ("cmd.exe", "powershell.exe") for w in W for e in w["events"])
    fields = set(EVENT_FIELDS) | {"ts", "has_dns_query"}
    bad_f = sum(set(e) != fields for w in W for e in w["events"])
    reasons = {w["close_reason"] for w in W}
    check("L3 cua so <= W, sap theo ts, khong conhost, <launcher>, dung truong, khong trung event / window_id",
          W and max(len(w["events"]) for w in W) <= W_DEFAULT and not bad_sort and not bad_img and not bad_par and not bad_f
          and len(keys_all) == len(set(keys_all)) and len({w["window_id"] for w in W}) == len(W)
          and reasons <= {"du_W", "host_im_lang", "khoang_trong_su_kien", "ket_thuc_luong"},
          f"{len(W)} cua so, {len(keys_all)} event, ly do dong {sorted(reasons)}; loai {dict(win.dropped)}")

    # L4: tung ly do dong tren event that cua mau
    by_host = {}
    for r in sorted(rows, key=lambda r: C._parse(r["timestamp"])):
        by_host.setdefault((r.get("agent") or {}).get("name"), []).append(r)
    host, hr = max(by_host.items(), key=lambda kv: len(kv[1]))
    t0 = C._parse(hr[0]["timestamp"])
    w1 = Windower(W=8); out = w1.add(hr[:400], t0)
    full = [w for w in out if w["close_reason"] == "du_W"]
    w2 = Windower(); w2.add(hr[:5], t0); before = w2.tick(t0 + timedelta(seconds=29)); after = w2.tick(t0 + timedelta(seconds=31))
    w3 = Windower(gap_s=0.0); g = w3.add(hr[:200], t0)
    w4 = Windower(); w4.add(hr[:5], t0); fin = w4.tick(t0, force=True)
    check("L4 dong khi du W / host im lang > idle / khoang trong > gap / ket thuc luong",
          full and all(len(w["events"]) == 8 for w in full) and not before and after and after[0]["close_reason"] == "host_im_lang"
          and any(w["close_reason"] == "khoang_trong_su_kien" for w in g) and fin and fin[0]["close_reason"] == "ket_thuc_luong",
          f"host {host}: du_W {len(full)}, im lang {len(after)}, khoang trong {sum(w['close_reason'] == 'khoang_trong_su_kien' for w in g)}")

    # L5: phat lai dau-cuoi
    P = load_pipeline(ROOT)
    with tempfile.TemporaryDirectory() as td:
        out_p = os.path.join(td, "alerts.jsonl"); st_p = os.path.join(td, "status.json")
        s = stream(C.FileSource(SAMPLE, poll_s=10.0), Windower(), P, out_p, None, st_p)
        al = [json.loads(l) for l in open(out_p, encoding="utf-8")]; status = json.load(open(st_p, encoding="utf-8"))
    cur = {"sample_sha256": __import__("hashlib").sha256(open(SAMPLE, "rb").read()).hexdigest(), "events_read": s["events_read"],
           "windows": s["windows"], "alerts": [decision_key(x) for x in al]}
    if a.write_ref:
        os.makedirs(os.path.dirname(REF), exist_ok=True)
        with open(REF, "w", encoding="utf-8", newline="\n") as f: json.dump(cur, f, indent=1)
    ref = json.load(open(REF, encoding="utf-8")) if os.path.exists(REF) else None
    leak = [k for x in al for k in x if k in LABEL_KEYS]
    schema = all(STEP8_KEYS | LIVE_KEYS <= set(x) for x in al)
    lat_ok = all(x["latency"]["infer_ms"] >= 0 and (x["latency"]["wait_s"] is None or x["latency"]["wait_s"] >= 0) for x in al)
    check("L5 phat lai dau-cuoi == ban tham chieu; schema Buoc 8 + truong truc tiep; khong truong nhan; status.json done",
          ref == cur and schema and not leak and lat_ok and status["done"] and status["alerts"] == len(al) and all(x["mode"] == "replay" for x in al),
          f"{s['events_read']} event -> {s['windows']} cua so -> {len(al)} canh bao "
          f"({sum(x['decision_source'] == 'both' for x in al)} both); tham chieu {'khop' if ref == cur else 'KHONG khop' if ref else 'chua co'}")

    # L6
    class Fake:
        def __init__(self): self.calls = []
        def req(self, path, ndjson=None, **kw):
            self.calls.append((path, ndjson)); n = ndjson.count("\n") // 2
            return {"items": [{"index": {"status": 201}}] * n}
    fk = Fake(); n = C.AlertPusher(fk).push(al[:3])
    lines = fk.calls[0][1].strip().split("\n") if fk.calls else []
    heads = [json.loads(x) for x in lines[0::2]]; docs = [json.loads(x) for x in lines[1::2]]
    check("L6 AlertPusher ghi _bulk vao vtguard-alerts-YYYY.MM.DD", fk.calls and fk.calls[0][0] == "/_bulk" and n == len(al[:3])
          and all(h["index"]["_index"].startswith("vtguard-alerts-") for h in heads) and all("@timestamp" in d for d in docs) and C.AlertPusher(fk).push([]) == 0,
          f"{n} ban ghi, index {heads[0]['index']['_index'] if heads else '-'}")

    # L7
    sys.path.insert(0, os.path.join(ROOT, "dashboard")); import data as D     # noqa: E402
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "alerts.jsonl")
        with open(p, "w", encoding="utf-8") as f:
            for x in al: f.write(json.dumps(x) + "\n")
            f.write('{"dong dang ghi do')
        os.environ["VTGUARD_LIVE_ALERTS"] = p
        try: L = D.live_alerts()
        finally: os.environ.pop("VTGUARD_LIVE_ALERTS", None)
    check("L7 dashboard doc canh bao truc tiep (bo dong dang ghi do), ma LIVE-xxxx / LINC-xxx",
          len(L) == len(al) and all(x["code"].startswith("LIVE-") and x["incident"].startswith("LINC-") and x["split"] == "live" for x in L),
          f"{len(L)} canh bao, {len({x['incident'] for x in L})} dot su co")

    print(f"\nKET QUA: {sum(RESULTS)}/{len(RESULTS)} PASS trong {time.time() - t_start:.1f}s")
    sys.exit(0 if all(RESULTS) else 1)

if __name__ == "__main__":
    main()
