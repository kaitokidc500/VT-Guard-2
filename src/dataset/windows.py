#!/usr/bin/env python3
"""VT-Guard Buoc 4.2 - cat cua so phien.
Doc data/processed/all.events.jsonl (4.1) + manifests/<batch>/*.manifest.json,
dung "session stream" cho moi phien, cat cua so truot W=64 / stride=32, toi da K=8 cua so/phien,
ghi data/processed/windows.jsonl va reports/windows.stats.json.

Session stream cua phien X (host H, [t_start, t_end]):
  = moi event co run_id == X (cay tien trinh cua phien, khong loc theo thoi gian vi tre log)
  + event nen (run_id None) tren H co ts_system trong [t_start, t_end].
  Event thuoc cay cua phien KHAC (phien chay song song cung host) KHONG dua vao, tranh
  cua so class=benign mang nhan malicious cua phien attack ben canh.
Thoi gian = ts_system (gio that cua event); `ts` cua Wazuh tre toi ~85 s nen khop manifest kem hon.
Cua so: bat dau 0, 32, 64, ... va them 1 cua so cuoi de phu duoi stream; stream < W -> 1 cua so ngan.
Gioi han K: lay mau ngau nhien (seed + run_id) PHAN TANG theo cua so duong/am, giu it nhat
1 cua so duong neu phien co.
dataset-v1.1 - trung hoa dau vet bo sinh du lieu (scaffold), ap DONG NHAT moi lop:
  - Loai han moi event image_name == conhost.exe khi dung stream (console host, khong mang hanh vi;
    ART chay cmd trong console rieng -> co conhost, script hard-negative dung -NoNewWindow -> khong co).
  - parent_image_name thuoc {powershell.exe, cmd.exe} -> "<launcher>" (cach khoi chay tool khac nhau
    giua ART va script hard-negative; khong xoa event). Ap ngay trong windows.jsonl de moi noi dung chung.
  - Chuan hoa dong lenh (basename file thuc thi, bo chuyen huong) nam o featurize.norm_cmd.
Phien attack khong co event malicious nao trong stream -> loai, KHONG coi la benign (khong sinh cua so
attack am gia). Truong hop labeled=0 (atomic khong sinh tien trinh con nao) ghi ly do rieng.
Chay: python src/dataset/windows.py [--root .] [--W 64] [--stride 32] [--K 8] [--seed 1337]
"""
import argparse, glob, json, os, random, sys
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime

BATCHES = ["batch01", "batch02", "batch03", "batch04", "batch05", "batch06", "batch07", "ntds", "ntds2", "ntds2v"]
# Dot ep TOAN BO vao T-novel: batch05 = holdout thoi gian, ntds2v = bien the T1003.003 held-out
NOVEL_BATCHES = ["batch05", "ntds2v"]
DATASET_VERSION = "v1.2"
# Trung hoa scaffold (dataset-v1.1), ap dong nhat moi lop
SCAFFOLD_DROP_IMAGES = {"conhost.exe"}
LAUNCHERS = {"powershell.exe", "cmd.exe"}
LAUNCHER_TOKEN = "<launcher>"

def neutral_parent(v):
    return LAUNCHER_TOKEN if v and str(v).lower() in LAUNCHERS else v

def is_scaffold_event(r):
    return (r.get("image_name") or "").lower() in SCAFFOLD_DROP_IMAGES
# Truong giu lai cho moi event trong cua so: chi nhung gi 4.3 can (khong label_*, wazuh_*, run_id,
# event_uid, process_guid, script_block_text, ps_payload).
EVENT_FIELDS = ["channel", "event_id", "image_name", "parent_image_name", "host_role",
                "integrity_level", "logon_type", "command_line", "dst_port"]

def ts(s):
    s = s.replace("Z", "+00:00").replace("+0000", "+00:00")
    if "." in s:
        head, rest = s.split(".", 1)
        digs = "".join(c for c in rest.split("+")[0].split("-")[0] if c.isdigit())[:6]
        s = f"{head}.{digs}+00:00"
    return datetime.fromisoformat(s)

def load_manifests(root):
    man = {}
    for b in BATCHES:
        for f in sorted(glob.glob(os.path.join(root, "manifests", b, "*.manifest.json"))):
            with open(f, encoding="utf-8-sig") as fh: txt = fh.read().strip()
            if not txt: continue
            m = json.loads(txt); m["_batch"] = b
            m["_t0"], m["_t1"] = ts(m["t_start"]), ts(m["t_end"])
            man[m["run_id"]] = m
    return man

def slim(r):
    e = {k: r.get(k) for k in EVENT_FIELDS}
    e["parent_image_name"] = neutral_parent(e["parent_image_name"])
    e["ts"] = r["ts_system"]
    e["has_dns_query"] = bool(r.get("dns_query"))
    return e

def starts_for(n, W, stride):
    if n <= W: return [0]
    s = list(range(0, n - W + 1, stride))
    if s[-1] != n - W: s.append(n - W)
    return s

def cap(wins, K, rng):
    if len(wins) <= K: return wins
    pos = [w for w in wins if w["window_malicious"]]
    neg = [w for w in wins if not w["window_malicious"]]
    kp = min(len(pos), max(1 if pos else 0, round(K * len(pos) / len(wins))))
    kn = min(len(neg), K - kp); kp = K - kn  # bu sang phia con du
    pick = rng.sample(pos, kp) + rng.sample(neg, kn)
    return sorted(pick, key=lambda w: w["start_idx"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--W", type=int, default=64)
    ap.add_argument("--stride", type=int, default=32)
    ap.add_argument("--K", type=int, default=8)
    ap.add_argument("--seed", type=int, default=1337)
    a = ap.parse_args()
    man = load_manifests(a.root)

    scaffold_dropped = Counter()
    own = defaultdict(list)          # run_id -> event
    bg = defaultdict(list)           # host -> event nen
    with open(os.path.join(a.root, "data", "processed", "all.events.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if is_scaffold_event(r):
                scaffold_dropped["own" if r["run_id"] else "bg", bool(r["label_malicious"])] += 1; continue
            r["_t"] = ts(r["ts_system"])
            (own[r["run_id"]] if r["run_id"] else bg[r["host"]]).append(r)
    unknown = [rid for rid in own if rid not in man]
    if unknown: sys.exit(f"LOI: run_id khong co manifest: {unknown[:5]}")
    key = lambda r: (r["_t"], r["channel"] or "", r["record_id"] or -1)
    for h in bg: bg[h].sort(key=key)
    bg_t = {h: [r["_t"] for r in v] for h, v in bg.items()}

    st = Counter(); excluded = []; per_session = {}; bg_use = Counter()
    out_path = os.path.join(a.root, "data", "processed", "windows.jsonl")
    with open(out_path, "w", encoding="utf-8", newline="\n") as w:
        for rid in sorted(man):
            m = man[rid]; h = m["host"]
            lo = bisect_left(bg_t.get(h, []), m["_t0"]); hi = bisect_right(bg_t.get(h, []), m["_t1"])
            seg = bg.get(h, [])[lo:hi]
            stream = sorted(own.get(rid, []) + seg, key=key)
            n_mal = sum(1 for r in stream if r["label_malicious"])
            if m["class"] == "attack" and not own.get(rid):
                excluded.append((rid, m["class"], "attack_khong_co_event_cay_tien_trinh")); continue
            if m["class"] == "hard_negative" and not own.get(rid):
                # quy tac chung (batch07): hard_negative labeled=0 cung loai, khong dung lam benign
                excluded.append((rid, m["class"], "hard_negative_khong_co_event_cay_tien_trinh")); continue
            if not stream:
                excluded.append((rid, m["class"], "stream_rong")); continue
            if m["class"] == "attack" and n_mal == 0:
                excluded.append((rid, m["class"], "attack_khong_co_event_malicious")); continue
            for r in seg: bg_use[id(r)] += 1
            wins = []
            for s in starts_for(len(stream), a.W, a.stride):
                ev = stream[s:s + a.W]
                mal = [r for r in ev if r["label_malicious"]]
                wins.append({
                    "window_id": f"{rid}:w{s:05d}", "run_id": rid, "batch": m["_batch"], "host": h,
                    "user_role": m.get("user_role"), "tempo": m.get("tempo"), "variant": m.get("variant"),
                    "t0": ev[0]["ts_system"], "t1": ev[-1]["ts_system"], "n_events": len(ev), "start_idx": s,
                    "window_malicious": bool(mal),
                    "window_ttps": sorted({t for r in mal for t in r["label_ttps"]}),
                    "window_class": m["class"],
                    # revert_control: phien hard_negative chay sau khoi phuc snapshot (doi chung nhieu snapshot).
                    # CHI dung cho card + kiem tra #10, KHONG lam feature.
                    "revert_control": m["class"] == "hard_negative" and bool(m.get("snapshot_before")),
                    "events": [slim(r) for r in ev],
                    # nguon goc event (cay phien / nen) - CHI cho kiem tra #10, khong chep sang features.jsonl
                    "event_origin": ["own" if r["run_id"] == rid else "bg" for r in ev],
                })
            kept = cap(wins, a.K, random.Random(f"{a.seed}:{rid}"))
            per_session[rid] = dict(cls=m["class"], batch=m["_batch"], host=h, n_stream=len(stream),
                                    n_own=len(own.get(rid, [])), n_mal=n_mal, n_win_full=len(wins), n_win=len(kept),
                                    n_pos=sum(x["window_malicious"] for x in kept))
            for x in kept:
                x["session_windows_total"] = len(wins)
                w.write(json.dumps(x, ensure_ascii=False) + "\n")
                st["windows"] += 1; st["pos" if x["window_malicious"] else "neg"] += 1

    # ---- thong ke ----
    ps = per_session
    def tab(keyf):
        t = defaultdict(lambda: Counter())
        for rid, s in ps.items():
            k = keyf(s); t[k]["sessions"] += 1; t[k]["windows"] += s["n_win"]; t[k]["pos"] += s["n_pos"]
        return {k: dict(v, neg=v["windows"] - v["pos"]) for k, v in sorted(t.items())}
    shared_bg = sum(1 for v in bg_use.values() if v > 1)
    stats = {
        "params": {"W": a.W, "stride": a.stride, "K": a.K, "seed": a.seed, "time_field": "ts_system"},
        "dataset_version": DATASET_VERSION,
        "scaffold": {"dropped_images": sorted(SCAFFOLD_DROP_IMAGES), "launcher_parents": sorted(LAUNCHERS),
                     "launcher_token": LAUNCHER_TOKEN,
                     "dropped_events": {f"{k[0]}|{'malicious' if k[1] else 'benign'}": v for k, v in sorted(scaffold_dropped.items())},
                     "dropped_total": sum(scaffold_dropped.values())},
        "windows": st["windows"], "positive": st["pos"], "negative": st["neg"],
        "positive_rate": round(st["pos"] / max(1, st["windows"]), 4),
        "sessions_with_windows": len(ps), "sessions_excluded": excluded,
        "by_class": tab(lambda s: s["cls"]), "by_host": tab(lambda s: s["host"]),
        "by_host_class": tab(lambda s: f"{s['host']}|{s['cls']}"), "by_batch": tab(lambda s: s["batch"]),
        "sessions_capped": sum(1 for s in ps.values() if s["n_win_full"] > a.K),
        "windows_before_cap": sum(s["n_win_full"] for s in ps.values()),
        "short_sessions_lt_W": sum(1 for s in ps.values() if s["n_stream"] < a.W),
        "stream_len": {"min": min(s["n_stream"] for s in ps.values()), "max": max(s["n_stream"] for s in ps.values()),
                       "median": sorted(s["n_stream"] for s in ps.values())[len(ps) // 2]},
        "attack_neg_windows": sum(s["n_win"] - s["n_pos"] for s in ps.values() if s["cls"] == "attack"),
        "nonattack_pos_windows": sum(s["n_pos"] for s in ps.values() if s["cls"] != "attack"),
        "bg_events_shared_by_overlapping_sessions": shared_bg,
        "ttp_windows": dict(sorted(Counter(t for line in open(out_path, encoding="utf-8")
                                           for t in json.loads(line)["window_ttps"]).items())),
        "per_session": ps,
    }
    with open(os.path.join(a.root, "reports", "windows.stats.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in stats.items() if k != "per_session"}, ensure_ascii=False, indent=2))
    big = sorted(ps.items(), key=lambda kv: -kv[1]["n_stream"])[:4]
    print("Phien dai nhat (kiem tra gioi han K):")
    for rid, s in big:
        print(f"  {rid} {s['cls']:13s} stream={s['n_stream']:4d} cua_so_day_du={s['n_win_full']:3d} -> giu={s['n_win']} (duong {s['n_pos']})")
    print(f"OK: {st['windows']} cua so -> {out_path}")

if __name__ == "__main__":
    main()
