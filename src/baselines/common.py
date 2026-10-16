#!/usr/bin/env python3
"""VT-Guard Buoc 5 - tien ich dung chung cho baseline.

full_window_events(): dung lai CHINH XAC stream phien nhu src/dataset/windows.py (event cay phien + event
nen cung host trong [t_start, t_end], sap theo (ts_system, channel, record_id)) roi cat [start_idx, start_idx+W)
de lay event DAY DU (co wazuh_rule_*, label_* ...) cua tung cua so dataset-v1.0. Ham tu doi chieu voi
windows.jsonl (channel, event_id, image_name, ts) va DUNG neu lech -> dam bao dung cua so da dong bang.
Chi doc; khong ghi gi vao data/. Truong nao duoc dung lam feature la viec cua tung baseline.
"""
import json, os, sys
from bisect import bisect_left, bisect_right
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "dataset"))
sys.path.insert(0, os.path.join(HERE, "..", "eval"))
from windows import load_manifests, ts, is_scaffold_event   # noqa: E402

W = 64

def start_idx(window_id):
    return int(window_id.rsplit(":w", 1)[1])

def full_window_events(root, window_ids):
    """window_id -> list event day du (dict tu all.events.jsonl), dung thu tu nhu windows.jsonl."""
    want = defaultdict(list)
    for wid in window_ids: want[wid.rsplit(":w", 1)[0]].append(wid)
    man = load_manifests(root)
    own, bg = defaultdict(list), defaultdict(list)
    with open(os.path.join(root, "data", "processed", "all.events.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if is_scaffold_event(r): continue          # dataset-v1.1: conhost loai khi dung stream
            r["_t"] = ts(r["ts_system"])
            (own[r["run_id"]] if r["run_id"] else bg[r["host"]]).append(r)
    key = lambda r: (r["_t"], r["channel"] or "", r["record_id"] or -1)
    for h in bg: bg[h].sort(key=key)
    bg_t = {h: [r["_t"] for r in v] for h, v in bg.items()}
    out = {}
    for rid, wids in want.items():
        m = man[rid]; h = m["host"]
        lo = bisect_left(bg_t.get(h, []), m["_t0"]); hi = bisect_right(bg_t.get(h, []), m["_t1"])
        stream = sorted(own.get(rid, []) + bg.get(h, [])[lo:hi], key=key)
        for wid in wids:
            s = start_idx(wid); out[wid] = stream[s:s + W]
    # doi chieu voi windows.jsonl
    bad = 0
    with open(os.path.join(root, "data", "processed", "windows.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            w = json.loads(line)
            if w["window_id"] not in out: continue
            ev = out[w["window_id"]]
            if len(ev) != len(w["events"]) or any(
                    (a["channel"], a["event_id"], a["image_name"], a["ts_system"]) != (b["channel"], b["event_id"], b["image_name"], b["ts"])
                    for a, b in zip(ev, w["events"])):
                bad += 1
    missing = [wid for wid in window_ids if wid not in out]
    if bad or missing: sys.exit(f"LOI: dung lai cua so lech windows.jsonl ({bad} lech, {len(missing)} thieu). DUNG.")
    return out

def window_events(root, window_ids):
    """window_id -> (events_slim, event_origin) doc tu windows.jsonl (cac truong nguon duoc phep cua Buoc 4).
    event_origin ("own"/"bg") CHI dung de che event nen trong ablation (c), khong phai feature."""
    want = set(window_ids); out = {}
    with open(os.path.join(root, "data", "processed", "windows.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            w = json.loads(line)
            if w["window_id"] in want: out[w["window_id"]] = (w["events"], w["event_origin"])
    missing = want - set(out)
    if missing: sys.exit(f"LOI: thieu {len(missing)} cua so trong windows.jsonl")
    return out

# ---- chuan hoa dong lenh: tu dataset-v1.1 nam trong featurize (norm_cmd da goi canon_cmd) ----
from featurize import canon_cmd  # noqa: E402,F401

# ---- ablation (c'): event nen MOT PHIA da biet (dataset card #11) - che khi danh gia, khong xoa du lieu ----
NTDS_SIDE_EFFECT_EIDS = {98, 102, 103, 105, 216, 300, 301, 302, 325, 326, 327, 330, 2001, 2002, 2003, 2004, 2005, 2006}

def is_known_one_sided_bg(e, origin):
    """Event NEN (khong thuoc cay phien) da biet chi xuat hien o phia attack: ESENT/Directory Service cua ntdsutil ifm,
    va svchost -> rundll32 shell32.dll,SHCreateLocalServerRunDll (COM local server)."""
    if origin != "bg": return False
    if e.get("event_id") in NTDS_SIDE_EFFECT_EIDS: return True
    return (e.get("image_name") == "rundll32.exe" and "shcreatelocalserverrundll" in (e.get("command_line") or "").lower())
