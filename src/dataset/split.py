#!/usr/bin/env python3
"""VT-Guard Buoc 4.4 - chia tap chong ro ri (theo PHIEN / NHOM PHIEN, khong theo cua so).
Doc data/processed/windows.jsonl (4.2) + manifests, gan moi phien vao 1 tap, fit lai vocab
CHI tren Train (goi featurize.py --fit-runs), ghi data/processed/splits/{train,t_clean,t_hard,t_novel}.jsonl
(cac cua so da trich dac trung) + splits/assignment.json + reports/split.stats.json.

Quy tac:
  - Nhom phien: cac phien cung host co khoang [t_start, t_end] chong nhau (noi bac cau) thuoc
    cung NHOM. Phien song song dung chung event nen trong stream (4.2) -> ca nhom vao cung mot phia
    (Train | kiem thu), khong event nen nao vua o Train vua o tap kiem thu.
  - T-novel = moi phien batch05 (holdout thoi gian).
  - T-hard  = ~40% phien hard_negative con lai, chon ngau nhien (seed) theo NHOM chi gom hard_negative
    (nhom tron co phien khac lop khong the dua tron vao T-hard; HN trong nhom tron o lai Train/T-clean).
  - Phan con lai: Train 80% / T-clean 20% theo nhom, phan tang tham lam theo (class, host, chu ky TTP).
Chay: python src/dataset/split.py [--root .] [--seed 1337] [--hard-frac 0.4] [--clean-frac 0.2]
"""
import argparse, hashlib, json, os, random, subprocess, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from windows import load_manifests

SPLITS = ["train", "t_clean", "t_hard", "t_novel"]

def sig(m):
    return "attack:" + "+".join(sorted(m["ttps"])) if m["class"] == "attack" else m["class"]

def stratum(m):
    return (m["class"], m["host"], sig(m))

def overlap_groups(sessions):
    """Gom phien chong thoi gian tren cung host (quet theo t_start, giu moc ket thuc lon nhat)."""
    groups = []
    byh = defaultdict(list)
    for m in sessions: byh[m["host"]].append(m)
    for h in sorted(byh):
        cur, end = None, None
        for m in sorted(byh[h], key=lambda m: (m["_t0"], m["run_id"])):
            if cur is not None and m["_t0"] <= end:
                cur.append(m); end = max(end, m["_t1"])
            else:
                cur = [m]; end = m["_t1"]; groups.append(cur)
    return groups

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--hard-frac", type=float, default=0.4)
    ap.add_argument("--clean-frac", type=float, default=0.2)
    a = ap.parse_args()
    P = lambda *p: os.path.join(a.root, *p)
    rng = random.Random(a.seed)

    man = load_manifests(a.root)
    win_runs = Counter()
    for l in open(P("data", "processed", "windows.jsonl"), encoding="utf-8"):
        win_runs[json.loads(l)["run_id"]] += 1
    sessions = [man[r] for r in sorted(win_runs)]          # chi phien co cua so
    groups = overlap_groups(sessions)
    gid = {m["run_id"]: i for i, g in enumerate(groups) for m in g}
    cross_batch = [i for i, g in enumerate(groups) if len({m["_batch"] for m in g}) > 1]
    assert not cross_batch, f"nhom phien vat qua 2 batch: {cross_batch}"

    assign = {}
    # 1) T-novel
    for g in groups:
        if g[0]["_batch"] == "batch05":
            for m in g: assign[m["run_id"]] = "t_novel"
    rest = [g for g in groups if g[0]["_batch"] != "batch05"]
    # 2) T-hard: nhom thuan hard_negative, chon ngau nhien den khi dat ~hard_frac so phien HN
    n_hn = sum(m["class"] == "hard_negative" for g in rest for m in g)
    target_hard = round(a.hard_frac * n_hn)
    pure = [g for g in rest if all(m["class"] == "hard_negative" for m in g)]
    rng.shuffle(pure)
    got = 0
    for g in pure:
        if got >= target_hard: break
        if abs(got + len(g) - target_hard) > abs(got - target_hard) and got > 0: continue
        for m in g: assign[m["run_id"]] = "t_hard"
        got += len(g)
    # 3) Train / T-clean: phan tang tham lam theo nhom
    rest = [g for g in rest if g[0]["run_id"] not in assign]
    tot = Counter(stratum(m) for g in rest for m in g)
    target = {k: a.clean_frac * v for k, v in tot.items()}
    cur = Counter(); n_clean = 0; n_all = sum(tot.values())
    order = rest[:]; rng.shuffle(order); order.sort(key=len, reverse=True)
    for g in order:
        add = Counter(stratum(m) for m in g)
        dev = lambda c: sum(abs(c[k] - target[k]) for k in add)
        d_clean = dev(cur + add); d_train = dev(cur)
        to_clean = d_clean < d_train or (d_clean == d_train and n_clean + len(g) <= a.clean_frac * n_all)
        for m in g: assign[m["run_id"]] = "t_clean" if to_clean else "train"
        if to_clean: cur += add; n_clean += len(g)

    os.makedirs(P("data", "processed", "splits"), exist_ok=True)
    train_runs = sorted(r for r, s in assign.items() if s == "train")
    runs_file = P("data", "processed", "splits", "train_runs.txt")
    with open(runs_file, "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(train_runs) + "\n")
    with open(P("data", "processed", "splits", "assignment.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({r: {"split": s, "group": gid[r], "class": man[r]["class"], "host": man[r]["host"],
                       "batch": man[r]["_batch"]} for r, s in sorted(assign.items())}, f, indent=1)

    # 4) fit lai vocab chi tren Train + trich dac trung lai
    print("== featurize.py --fit-runs train_runs.txt ==")
    subprocess.run([sys.executable, P("src", "dataset", "featurize.py"), "--root", a.root, "--fit-runs", runs_file], check=True)

    # 5) ghi file split
    outs = {s: open(P("data", "processed", "splits", f"{s}.jsonl"), "w", encoding="utf-8", newline="\n") for s in SPLITS}
    W = defaultdict(list)
    for l in open(P("data", "processed", "features.jsonl"), encoding="utf-8"):
        r = json.loads(l); s = assign[r["run_id"]]
        outs[s].write(l if l.endswith("\n") else l + "\n")
        W[s].append({k: r[k] for k in ("run_id", "host", "window_class", "window_malicious", "window_ttps", "batch")})
    for f in outs.values(): f.close()

    # 6) kiem tra chap nhan
    chk = {}
    where = defaultdict(set)
    for s, ws in W.items():
        for w in ws: where[w["run_id"]].add(s)
    chk["run_id_in_gt1_split"] = sorted(r for r, ss in where.items() if len(ss) > 1)
    chk["t_hard_non_hn_windows"] = sum(w["window_class"] != "hard_negative" for w in W["t_hard"])
    chk["t_novel_non_batch05_windows"] = sum(w["batch"] != "batch05" for w in W["t_novel"])
    chk["batch05_outside_t_novel"] = sum(w["batch"] == "batch05" for s in SPLITS if s != "t_novel" for w in W[s])
    leak_pairs = []
    for g in groups:
        ss = {assign[m["run_id"]] for m in g}
        if "train" in ss and len(ss) > 1: leak_pairs.append(g[0]["run_id"])
    # kiem tra doc lap voi cach gom nhom: moi cap (Train, test) cung host khong chong thoi gian
    tr = [man[r] for r in train_runs]; te = [man[r] for r, s in assign.items() if s != "train"]
    for x in tr:
        for y in te:
            if x["host"] == y["host"] and x["_t0"] <= y["_t1"] and y["_t0"] <= x["_t1"]:
                leak_pairs.append(f"{x['run_id']}~{y['run_id']}")
    chk["train_test_time_overlap"] = leak_pairs
    vocab_meta = json.load(open(P("data", "processed", "vocab.json"), encoding="utf-8"))["_meta"]
    chk["vocab_fit_sessions_eq_train"] = vocab_meta["fit_sessions"] == len(train_runs)
    n_pos = sum(w["window_malicious"] for ws in W.values() for w in ws)
    n_attack = sum(1 for m in sessions if m["class"] == "attack")
    chk["positive_windows_le_attack_x8"] = f"{n_pos} <= {n_attack}x8={n_attack * 8}: {n_pos <= n_attack * 8}"
    ok = (not chk["run_id_in_gt1_split"] and not chk["t_hard_non_hn_windows"] and not chk["t_novel_non_batch05_windows"]
          and not chk["batch05_outside_t_novel"] and not leak_pairs and chk["vocab_fit_sessions_eq_train"] and n_pos <= n_attack * 8)

    per = {}
    for s in SPLITS:
        ws = W[s]; runs = {w["run_id"] for w in ws}
        per[s] = {
            "sessions": len(runs), "groups": len({gid[r] for r in runs}), "windows": len(ws),
            "positive": sum(w["window_malicious"] for w in ws),
            "positive_rate": round(sum(w["window_malicious"] for w in ws) / max(1, len(ws)), 4),
            "sessions_by_class": dict(sorted(Counter(man[r]["class"] for r in runs).items())),
            "windows_by_class": dict(sorted(Counter(w["window_class"] for w in ws).items())),
            "windows_by_host": dict(sorted(Counter(w["host"] for w in ws).items())),
            "ttp_windows": dict(sorted(Counter(t for w in ws for t in w["window_ttps"]).items())),
            "sha256": sha256(P("data", "processed", "splits", f"{s}.jsonl")),
        }
    stats = {"seed": a.seed, "hard_frac": a.hard_frac, "clean_frac": a.clean_frac,
             "groups_total": len(groups), "group_size_dist": dict(sorted(Counter(len(g) for g in groups).items())),
             "hn_sessions_non_batch05": n_hn, "t_hard_target": target_hard,
             "hn_in_pure_groups": sum(len(g) for g in pure),
             "splits": per, "acceptance": chk, "acceptance_pass": ok,
             "vocab_sha256": sha256(P("data", "processed", "vocab.json"))}
    with open(P("reports", "split.stats.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print("== split ==")
    print(json.dumps({k: v for k, v in stats.items()}, ensure_ascii=False, indent=2))
    print("ACCEPTANCE:", "DAT" if ok else "KHONG DAT")

if __name__ == "__main__":
    main()
