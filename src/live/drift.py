#!/usr/bin/env python3
"""VT-Guard Buoc 9 (kieu B) - do DO LECH truc tiep <-> offline (docs/STEP9-BRIEF.md muc 6.3).

Cho luong truc tiep (FileSource -> Windower -> infer.Pipeline) chay tren MOT dot da export (mac dinh data/raw/batch05, toan bo
thuoc T-novel), roi so voi pipeline offline tren cung du lieu (canh bao reports/step8/alerts_<split>.jsonl cua cac cua so dot do
trong data/processed/windows.jsonl). Nhan (data/processed/<dot>.labeled.jsonl) CHI dung o day de cham do lech, khong vao luong.

Chi so (khong chinh gi de so dep hon):
  (a) trung cua so-canh bao, ghep theo host + giao khoang thoi gian [t0, t1]:
      - ty le cua so canh bao OFFLINE co it nhat 1 canh bao truc tiep giao thoi gian (bao phu);
      - ty le canh bao TRUC TIEP giao it nhat 1 cua so canh bao offline;
      - muc event: tren cac event nam trong cua so offline, Jaccard giua tap event thuoc cua so canh bao hai ben.
  (b) canh bao sai tren phan lanh tinh: cua so truc tiep KHONG chua event doc hai nao (theo nhan event) ma bi canh bao;
      doi chieu so canh bao offline nham cua cung dot.
  (c) lech tien xu ly: event truc tiep giu ma dataset loai (theo ly do labeler) va nguoc lai.
Chay ca hai cach hieu quy tac tien trinh khung ART (tool_mode orchestrator / console). Ghi reports/step9/live/drift_report.json.
Chay: python src/live/drift.py [--batch batch05] [--split t_novel]
"""
import argparse, json, os, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import connector as C                                            # noqa: E402
from run import home, live_dir, load_pipeline, stream             # noqa: E402
from windower import Windower, ts, dedup_key                      # noqa: E402

def overlap(a0, a1, b0, b1): return a0 <= b1 and b0 <= a1

def offline_side(root, batch, split):
    W = {}
    for l in open(os.path.join(root, "data", "processed", "windows.jsonl"), encoding="utf-8"):
        w = json.loads(l)
        if w["batch"] == batch: W[w["window_id"]] = w
    alerted = {json.loads(l)["window_id"] for l in open(os.path.join(root, "reports", "step8", f"alerts_{split}.jsonl"), encoding="utf-8")}
    y = {json.loads(l)["window_id"]: json.loads(l)["y"] for l in open(os.path.join(root, "reports", "preds", f"fusion_{split}.jsonl"), encoding="utf-8")}
    return W, alerted & set(W), y

def ev_key(host, e): return (host, e["ts"], e["channel"], e["event_id"])

def run_mode(root, batch, split, tool_mode, P, labels, W, off_alert, y):
    src = C.FileSource(os.path.join(root, "data", "raw", batch), poll_s=10.0)
    win = Windower(tool_mode=tool_mode)
    s = stream(src, win, P, keep_results=True)
    live = [{"id": r["window_id"], "host": r["window"]["host"], "t0": ts(r["window"]["t0"]), "t1": ts(r["window"]["t1"]), "alert": r["alert"],
             "keys": r["window"]["_keys"], "ev": {ev_key(r["window"]["host"], e) for e in r["window"]["events"]}} for r in s["results"]]
    offa = [{"id": i, "host": W[i]["host"], "t0": ts(W[i]["t0"]), "t1": ts(W[i]["t1"])} for i in off_alert]
    la = [x for x in live if x["alert"]]
    rec = sum(any(l["host"] == o["host"] and overlap(o["t0"], o["t1"], l["t0"], l["t1"]) for l in la) for o in offa)
    prec = sum(any(l["host"] == o["host"] and overlap(o["t0"], o["t1"], l["t0"], l["t1"]) for o in offa) for l in la)
    # muc event tren pham vi cua so offline
    U = {ev_key(w["host"], e) for w in W.values() for e in w["events"]}
    off_ev = {ev_key(W[i]["host"], e) for i in off_alert for e in W[i]["events"]}
    live_ev = {k for x in la for k in x["ev"]} & U
    jac = len(off_ev & live_ev) / max(1, len(off_ev | live_ev))
    # (b) nhan cua so truc tiep theo nhan event (chi de cham)
    def mal(x): return any(labels.get(k, (False, None, None))[0] for k in x["keys"])
    benign = [x for x in live if not mal(x)]; fa = [x for x in benign if x["alert"]]
    off_fp = sorted(i for i in off_alert if not y.get(i))
    # (c) lech tien xu ly
    kept_live = {k for x in live for k in x["keys"]}
    reasons = Counter(labels[k][2] if labels[k][1] else "dataset_giu" for k in kept_live if k in labels)
    not_in_labels = sum(k not in labels for k in kept_live)
    ds_kept = {k for k, v in labels.items() if not v[1] and (v[3] or "") != "conhost.exe"}
    lost = ds_kept - kept_live
    return {
        "tool_mode": tool_mode, "luong": {k: s[k] for k in ("polls", "events_read", "windows", "alerts")},
        "loai_theo_quy_tac": dict(win.dropped), "tien_xu_ly": dict(win.prep.stats),
        "a_trung_cua_so_canh_bao": {
            "offline_cua_so_canh_bao": len(offa), "offline_duoc_truc_tiep_phu": rec, "ty_le_offline_duoc_phu": round(rec / max(1, len(offa)), 4),
            "truc_tiep_canh_bao": len(la), "truc_tiep_giao_offline": prec, "ty_le_truc_tiep_giao_offline": round(prec / max(1, len(la)), 4),
            "jaccard_event_tren_pham_vi_offline": round(jac, 4), "event_pham_vi_offline": len(U)},
        "b_canh_bao_sai_phan_lanh_tinh": {
            "truc_tiep_cua_so_lanh_tinh": len(benign), "truc_tiep_canh_bao_sai": len(fa),
            "ty_le": round(len(fa) / max(1, len(benign)), 4), "vi_du": [x["id"] for x in fa[:10]],
            "offline_canh_bao_sai_cung_dot": len(off_fp), "offline_cua_so_lanh_tinh_cung_dot": sum(1 for i in W if not y.get(i))},
        "c_lech_tien_xu_ly": {
            "event_truc_tiep_giu": len(kept_live), "theo_trang_thai_dataset": dict(reasons), "khong_co_trong_nhan": not_in_labels,
            "dataset_giu_nhung_truc_tiep_loai": len(lost)},
    }

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--batch", default="batch05"); ap.add_argument("--split", default="t_novel")
    a = ap.parse_args(); root = home()
    labels = {}
    for l in open(os.path.join(root, "data", "processed", f"{a.batch}.labeled.jsonl"), encoding="utf-8"):
        r = json.loads(l); labels[dedup_key(r)] = (bool(r["label_malicious"]) and not r["dropped"], bool(r["dropped"]), r["drop_reason"], r.get("image_name"))
    W, off_alert, y = offline_side(root, a.batch, a.split); P = load_pipeline(root)
    modes = [run_mode(root, a.batch, a.split, m, P, labels, W, off_alert, y) for m in ("orchestrator", "console")]
    rep = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "batch": a.batch, "split": a.split,
           "offline": {"cua_so": len(W), "cua_so_canh_bao": len(off_alert),
                       "ghi_chu": "cua so offline: truot 64/32 trong khung manifest, toi da 8 cua so/phien (windows.py)"},
           "dinh_nghia": {
               "a": "ghep theo host + giao khoang [t0, t1]; jaccard tren event thuoc pham vi cua so offline (khoa host, ts_system, channel, event_id)",
               "b": "cua so truc tiep lanh tinh = khong chua event doc hai nao theo nhan dataset (nhan chi dung de cham)",
               "c": "khoa event (host, channel, record_id, event_id, ts_system) so voi data/processed/<dot>.labeled.jsonl"},
           "che_do": modes, "che_do_mac_dinh": "orchestrator",
           "ghi_chu": "So lieu chinh thuc van la ket qua tren tap test dong bang; bao cao nay chi do muc lech khi chay truc tiep."}
    out = os.path.join(live_dir(root), "drift_report.json"); os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f: json.dump(rep, f, ensure_ascii=False, indent=1)
    for m in modes:
        print(m["tool_mode"], json.dumps({k: m[k] for k in ("luong", "a_trung_cua_so_canh_bao", "b_canh_bao_sai_phan_lanh_tinh", "c_lech_tien_xu_ly")}, ensure_ascii=False))
    print("->", out)

if __name__ == "__main__":
    main()
