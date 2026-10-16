#!/usr/bin/env python3
"""VT-Guard - quet dac trung don le tach attack vs hard_negative (tim dau vet bo sinh / scaffold).

Chi DOC (windows.jsonl + splits), khong sua du lieu.
Don vi = cua so. Nhom duong = cua so window_malicious=1 (attack); nhom am = cua so lop hard_negative.
Moi dac trung -> diem cua so = TI LE event trong cua so mang gia tri do (khong phu thuoc do dai).
Muc tach = max(AUC, 1-AUC) cua diem do giua hai nhom (AUC = P(diem attack > diem HN), hoa = 0.5).
Kem ti le cua so CO chua gia tri o tung nhom, va so phien co chua.
Ho dac trung: image_name, parent_image_name, cap cha->con, event_id, channel, integrity_level, logon_type,
token dong lenh (featurize.norm_cmd; tuy chon --canon de qua chuan hoa lenh truoc), 4 co nhi phan.
Chay: python src/dataset/scaffold_scan.py [--canon] [--min-sep 0.9] [--top 60] [--json out.json]
"""
import argparse, json, os, re, sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "eval"))
from featurize import norm_cmd
from bootstrap import roc_auc

TOK_RE = re.compile(r"[a-z0-9_.<>/\\-]+")

def event_feats(e, canon_fn=None):
    f = [f"image={e['image_name']}", f"parent={e['parent_image_name']}",
         f"pair={e['parent_image_name']}->{e['image_name']}", f"eid={e['event_id']}", f"channel={e['channel']}",
         f"integrity={e['integrity_level']}", f"logon_type={e['logon_type']}"]
    if e.get("command_line"):
        c = canon_fn(e["command_line"]) if canon_fn else e["command_line"]
        f += [f"cmdtok={t}" for t in set(TOK_RE.findall(norm_cmd(c)))]
    if e["event_id"] == 3 or e.get("dst_port") is not None: f.append("flag=has_network")
    if e["event_id"] == 22 or e.get("has_dns_query"): f.append("flag=has_dns")
    if "PowerShell" in (e["channel"] or ""): f.append("flag=powershell_channel")
    if e["channel"] == "Security": f.append("flag=security_channel")
    return f

def scan(root=".", canon=False, min_sep=0.9, min_windows=3):
    canon_fn = None
    if canon:
        sys.path.insert(0, os.path.join(HERE, "..", "baselines"))
        from common import canon_cmd as canon_fn
    groups = {}
    for s in ("train", "t_clean", "t_hard", "t_novel"):
        with open(os.path.join(root, "data", "processed", "splits", f"{s}.jsonl"), encoding="utf-8") as fh:
            for l in fh:
                w = json.loads(l)
                if w["window_malicious"]: groups[w["window_id"]] = ("attack", w["run_id"])
                elif w["window_class"] == "hard_negative": groups[w["window_id"]] = ("hn", w["run_id"])
    frac = defaultdict(dict)      # feat -> {wid: ti le}
    wins = {"attack": [], "hn": []}
    with open(os.path.join(root, "data", "processed", "windows.jsonl"), encoding="utf-8") as fh:
        for l in fh:
            w = json.loads(l)
            if w["window_id"] not in groups: continue
            g, rid = groups[w["window_id"]]; wins[g].append((w["window_id"], rid))
            c = Counter(); n = len(w["events"])
            for e in w["events"]:
                for f in event_feats(e, canon_fn): c[f] += 1
            for f, k in c.items(): frac[f][w["window_id"]] = k / n
    A = [wid for wid, _ in wins["attack"]]; H = [wid for wid, _ in wins["hn"]]
    run = {wid: rid for g in wins.values() for wid, rid in g}
    y = np.r_[np.ones(len(A), bool), np.zeros(len(H), bool)]
    rows = []
    for f, d in frac.items():
        if len(d) < min_windows: continue
        sc = np.array([d.get(w, 0.0) for w in A] + [d.get(w, 0.0) for w in H])
        auc = roc_auc(y, sc); sep = max(auc, 1 - auc)
        if sep < min_sep: continue
        pa = sum(1 for w in A if w in d) / len(A); ph = sum(1 for w in H if w in d) / len(H)
        sa = len({run[w] for w in A if w in d}); sh = len({run[w] for w in H if w in d})
        rows.append({"feature": f, "auc_attack_gt_hn": round(auc, 4), "separation": round(sep, 4),
                     "side": "attack" if auc >= 0.5 else "hard_negative",
                     "pct_windows_attack": round(pa, 3), "pct_windows_hn": round(ph, 3),
                     "sessions_attack": sa, "sessions_hn": sh})
    rows.sort(key=lambda r: (-r["separation"], -max(r["pct_windows_attack"], r["pct_windows_hn"]), r["feature"]))   # tat dinh
    meta = {"n_attack_windows": len(A), "n_hn_windows": len(H),
            "n_attack_sessions": len({run[w] for w in A}), "n_hn_sessions": len({run[w] for w in H}),
            "canon": canon, "min_sep": min_sep}
    return rows, meta

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--canon", action="store_true")
    ap.add_argument("--min-sep", type=float, default=0.9)
    ap.add_argument("--top", type=int, default=80)
    ap.add_argument("--json")
    a = ap.parse_args()
    rows, meta = scan(a.root, a.canon, a.min_sep)
    print(json.dumps(meta))
    print(f"{'#':>3} {'dac trung':58s} {'tach':>6} {'AUC':>6} {'phia':>13} {'%cua so attack':>15} {'%cua so HN':>11} {'phien A/HN':>10}")
    for i, r in enumerate(rows[:a.top], 1):
        print(f"{i:3d} {r['feature'][:58]:58s} {r['separation']:6.3f} {r['auc_attack_gt_hn']:6.3f} {r['side']:>13} "
              f"{100 * r['pct_windows_attack']:14.1f}% {100 * r['pct_windows_hn']:10.1f}% {r['sessions_attack']:>4}/{r['sessions_hn']:<4}")
    print(f"... tong {len(rows)} dac trung co muc tach >= {a.min_sep}; >= 0.98: {sum(r['separation'] >= 0.98 for r in rows)}")
    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f: json.dump({"meta": meta, "rows": rows}, f, indent=1)

if __name__ == "__main__":
    main()
