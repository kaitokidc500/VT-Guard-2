#!/usr/bin/env python3
"""VT-Guard Buoc 4.4 - chia tap chong ro ri (theo PHIEN / NHOM PHIEN, khong theo cua so).
Doc data/processed/windows.jsonl (4.2) + manifests, gan moi phien vao 1 tap, fit lai vocab
CHI tren Train (goi featurize.py --fit-runs), ghi data/processed/splits/{train,t_clean,t_hard,t_novel}.jsonl
(cac cua so da trich dac trung) + splits/assignment.json + reports/split.stats.json.

Quy tac:
  - Nhom phien: cac phien cung host co khoang [t_start, t_end] chong nhau (noi bac cau) thuoc
    cung NHOM. Phien song song dung chung event nen trong stream (4.2) -> ca nhom vao cung mot phia
    (Train | kiem thu), khong event nen nao vua o Train vua o tap kiem thu.
  - T-novel = moi phien cua NOVEL_BATCHES: batch05 (holdout thoi gian) + ntds2v (bien the T1003.003 held-out).
  - T-hard  = theo CHU KY CONG CU cua phien hard_negative (tap image_name cua cay phien, tach rieng phien
    revert_control): moi chu ky >=1 phien vao T-hard va >=50% vao Train (neu >=2 phien), muc tieu ~hard_frac.
    Chi nhom chi gom hard_negative moi vao T-hard (nhom tron o lai Train/T-clean).
  - Phan con lai: Train 80% / T-clean 20% theo nhom, phan tang tham lam theo (class, host, chu ky TTP).
Chay: python src/dataset/split.py [--root .] [--seed 1337] [--hard-frac 0.4] [--clean-frac 0.2]
"""
import argparse, hashlib, json, math, os, random, subprocess, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from windows import load_manifests, NOVEL_BATCHES

SPLITS = ["train", "t_clean", "t_hard", "t_novel"]

def sig(m):
    return "attack:" + "+".join(sorted(m["ttps"])) if m["class"] == "attack" else m["class"]

GENERIC_IMG = {"cmd.exe", "conhost.exe", "powershell.exe", "&lt;unknown process&gt;", None}

def hn_signature(m, own_imgs):
    """(tap image_name dac trung cua cay phien, revert_control)."""
    s = "+".join(sorted(i for i in own_imgs.get(m["run_id"], ()) if i not in GENERIC_IMG)) or "none"
    return (s, bool(m.get("snapshot_before")))

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
    ap.add_argument("--pin-assignment", help="assignment.json cua ban truoc: giu nguyen tap cua phien cu, chi xep phien moi")
    a = ap.parse_args()
    P = lambda *p: os.path.join(a.root, *p)
    rng = random.Random(a.seed)

    man = load_manifests(a.root)
    win_runs = Counter()
    for l in open(P("data", "processed", "windows.jsonl"), encoding="utf-8"):
        win_runs[json.loads(l)["run_id"]] += 1
    sessions = [man[r] for r in sorted(win_runs)]          # chi phien co cua so
    own_imgs = defaultdict(set)
    for l in open(P("data", "processed", "all.events.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        if r["run_id"]: own_imgs[r["run_id"]].add(r["image_name"])
    groups = overlap_groups(sessions)
    gid = {m["run_id"]: i for i, g in enumerate(groups) for m in g}
    # nhom khong duoc tron dot T-novel voi dot thuong (neu khong, phai chon giua ep T-novel va chong ro ri)
    mixed = [g[0]["run_id"] for g in groups if len({m["_batch"] in NOVEL_BATCHES for m in g}) > 1]
    assert not mixed, f"nhom phien tron dot T-novel va dot thuong: {mixed}"

    assign = {}
    rest = [g for g in groups if g[0]["_batch"] not in NOVEL_BATCHES]
    hn = [m for g in rest for m in g if m["class"] == "hard_negative"]
    n_hn = len(hn)
    hsig = {m["run_id"]: hn_signature(m, own_imgs) for m in hn}
    n_sig = Counter(hsig.values())
    cap_hard = {k: (1 if n == 1 else n - math.ceil(n / 2)) for k, n in n_sig.items()}
    want_hard = {k: max(1, min(round(a.hard_frac * n), cap_hard[k])) for k, n in n_sig.items()}
    pure = [g for g in rest if all(m["class"] == "hard_negative" for m in g)]
    rng.shuffle(pure); pure.sort(key=len)            # uu tien nhom nho (it keo theo chu ky khac)
    pin_log, pin_dropped = [], []
    if a.pin_assignment:
        # Giu co dinh thanh vien cac tap cua mot ban truoc (vd dataset-v1.1): phien cu lay nguyen tap da gan;
        # phien MOI xep theo dung quy tac nhom phien: chong thoi gian voi nhom da co tap -> theo tap do;
        # nhom don/moi -> dot T-novel -> t_novel; thuan hard_negative -> T-hard neu chu ky chua du chi tieu;
        # con lai -> Train/T-clean phan tang tham lam theo so dem hien tai.
        pinned = {r: v["split"] for r, v in json.load(open(a.pin_assignment, encoding="utf-8")).items()}
        cur_split = lambda: Counter(assign.values())
        moved, target_hard = 0, sum(want_hard.values())
        for g in groups:
            for m in g:
                if m["run_id"] in pinned: assign[m["run_id"]] = pinned[m["run_id"]]
        for g in groups:
            new = [m for m in g if m["run_id"] not in pinned]
            if not new: continue
            ps = {pinned[m["run_id"]] for m in g if m["run_id"] in pinned}
            if len(ps) > 1: sys.exit(f"LOI: nhom {g[0]['run_id']} co phien cu o nhieu tap {ps}")
            if ps:
                sp = ps.pop(); why = f"chong thoi gian voi nhom da co tap ({[m['run_id'] for m in g if m['run_id'] in pinned]}) -> {sp}"
            elif g[0]["_batch"] in NOVEL_BATCHES:
                sp = "t_novel"; why = "nhom don thuoc dot T-novel"
            elif all(m["class"] == "hard_negative" for m in g):
                ks = {hsig[m["run_id"]] for m in g}
                have = {k: sum(1 for r, x in hsig.items() if x == k and assign.get(r) == "t_hard") for k in ks}
                sp = "t_hard" if any(have[k] < want_hard[k] for k in ks) else "train"
                why = f"nhom thuan hard_negative, chu ky {sorted(ks)}: T-hard hien co {have} / chi tieu {[want_hard[k] for k in ks]} -> {sp}"
            else:
                pool = [m for gg in groups for m in gg if assign.get(m["run_id"]) in ("train", "t_clean")] + new
                tot = Counter(stratum(m) for m in pool)
                curc = Counter(stratum(m) for m in pool if assign.get(m["run_id"]) == "t_clean")
                add = Counter(stratum(m) for m in new)
                dev = lambda c: sum(abs(c[k] - a.clean_frac * tot[k]) for k in add)
                sp = "t_clean" if dev(curc + add) < dev(curc) else "train"
                why = (f"nhom don (khong chong thoi gian voi phien co tap), phan tang {dict(add)}: "
                       f"T-clean hien co {dict((k, curc[k]) for k in add)} / muc tieu {dict((k, round(a.clean_frac * tot[k], 2)) for k in add)} "
                       f"-> lech neu vao T-clean {round(dev(curc + add), 2)} vs Train {round(dev(curc), 2)} -> {sp}")
            for m in new:
                assign[m["run_id"]] = sp
                pin_log.append({"run_id": m["run_id"], "class": m["class"], "batch": m["_batch"], "host": m["host"], "split": sp, "why": why})
        pin_dropped = sorted(r for r in pinned if r not in assign)
        pure = [g for g in rest if all(m["class"] == "hard_negative" for m in g)]
        for x in pin_log: print("[pin] phien moi", x["run_id"], "->", x["split"], "|", x["why"])
        if pin_dropped: print("[pin] phien co trong assignment cu nhung khong con cua so:", pin_dropped)
    else:
        # 1) T-novel
        for g in groups:
            if g[0]["_batch"] in NOVEL_BATCHES:
                for m in g: assign[m["run_id"]] = "t_novel"
        # 2) T-hard theo CHU KY CONG CU (tap image_name dac trung cua cay phien, bo cmd/conhost/powershell),
        #    tach rieng phien revert_control. Moi chu ky: >=1 phien vao T-hard, >=50% vao Train (neu >=2 phien).
        #    Chi nhom THUAN hard_negative moi vao duoc T-hard (nhom tron phai o phia Train/T-clean).
        got = Counter()
        for k in sorted(n_sig, key=lambda k: (n_sig[k], k)):   # chu ky hiem truoc
            for g in pure:
                if got[k] >= want_hard[k]: break
                if g[0]["run_id"] in assign or k not in {hsig[m["run_id"]] for m in g}: continue
                add = Counter(hsig[m["run_id"]] for m in g)
                if any(got[x] + c > cap_hard[x] for x, c in add.items()): continue
                for m in g: assign[m["run_id"]] = "t_hard"
                got += add
        target_hard = sum(want_hard.values())
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
        # 3b) dam bao moi chu ky hard_negative co >= 50% phien o Train: chuyen ca nhom tu T-clean sang Train
        moved = 0
        for k in sorted(n_sig):
            need = math.ceil(n_sig[k] / 2) if n_sig[k] >= 2 else 0
            for g in [g for g in rest if assign[g[0]["run_id"]] == "t_clean"]:
                if sum(1 for r, x in hsig.items() if x == k and assign[r] == "train") >= need: break
                if k in {hsig.get(m["run_id"]) for m in g}:
                    for m in g: assign[m["run_id"]] = "train"
                    moved += 1
    sig_table = {}
    for k in sorted(n_sig, key=lambda k: -n_sig[k]):
        c = Counter(assign[r] for r, x in hsig.items() if x == k)
        sig_table[f"{k[0]}{' [revert_control]' if k[1] else ''}"] = {
            "n": n_sig[k], **{s: c.get(s, 0) for s in ("train", "t_clean", "t_hard")},
            "ok_hard_ge1": c.get("t_hard", 0) >= 1,
            "ok_train_ge50": n_sig[k] < 2 or c.get("train", 0) >= math.ceil(n_sig[k] / 2)}

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
    chk["t_novel_non_novel_batch_windows"] = sum(w["batch"] not in NOVEL_BATCHES for w in W["t_novel"])
    chk["novel_batch_outside_t_novel"] = sum(w["batch"] in NOVEL_BATCHES for s in SPLITS if s != "t_novel" for w in W[s])
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
    ok = (not chk["run_id_in_gt1_split"] and not chk["t_hard_non_hn_windows"] and not chk["t_novel_non_novel_batch_windows"]
          and not chk["novel_batch_outside_t_novel"] and not leak_pairs and chk["vocab_fit_sessions_eq_train"] and n_pos <= n_attack * 8)

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
             "hn_sessions_non_novel": n_hn, "t_hard_target": target_hard,
             "hn_in_pure_groups": sum(len(g) for g in pure), "hn_signature_split": sig_table,
             "pinned_from": a.pin_assignment, "pin_new_sessions": pin_log, "pin_dropped_sessions": pin_dropped,
             "hn_groups_moved_to_train": moved,
             "splits": per, "acceptance": chk, "acceptance_pass": ok,
             "vocab_sha256": sha256(P("data", "processed", "vocab.json"))}
    with open(P("reports", "split.stats.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print("== split ==")
    print(json.dumps({k: v for k, v in stats.items()}, ensure_ascii=False, indent=2))
    print("ACCEPTANCE:", "DAT" if ok else "KHONG DAT")

if __name__ == "__main__":
    main()
