#!/usr/bin/env python3
"""VT-Guard Buoc 7 moc 1 - unit test cho src/rules/induce.py + predicates.py.
(1) chi doc Train, (2) chi doc truong event cho phep, (3) vi tu cam bi chan + 0 vi pham o luat cuoi,
(4) matcher noi bo == dieu kien engine (cay: tree.apply; RIPPER: ruleset doc lai == wittgenstein.predict) va == ma tran (luat cuoi),
(5) provenance day du, (6) tat dinh. Chay: python src/rules/test_induce.py
"""
import builtins, json, os, sys, time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval", "../baselines", "../dataset"): sys.path.insert(0, os.path.join(HERE, d))
import induce as I                                                     # noqa: E402
import predicates as Pd                                                # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RES = []

def check(name, cond, detail=""):
    RES.append(bool(cond)); print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""), flush=True)

class TrackDict(dict):
    seen = set()
    def __getitem__(self, k): TrackDict.seen.add(k); return dict.__getitem__(self, k)
    def get(self, k, d=None): TrackDict.seen.add(k); return dict.get(self, k, d)

def main():
    t0 = time.time(); os.chdir(ROOT)
    # ---- 1. chi doc Train ----
    opened = []; real_open = builtins.open; real_loads = I.json.loads; parsed = []
    def spy(f, mode="r", *a, **k):
        opened.append((str(f).replace("\\", "/"), mode)); return real_open(f, mode, *a, **k)
    def spy_loads(x, *a, **k):
        o = real_loads(x, *a, **k)
        if isinstance(o, dict) and "window_id" in o: parsed.append(o["window_id"])
        return o
    builtins.open = spy; I.json.loads = spy_loads
    try: meta, events, origins = I.load_train(ROOT)
    finally: builtins.open = real_open; I.json.loads = real_loads
    train_ids = {json.loads(l)["window_id"] for l in open(os.path.join("data", "processed", "splits", "train.jsonl"), encoding="utf-8")}
    test_text = [(f, m) for f, m in opened if any(s_ in f for s_ in ("splits/t_clean", "splits/t_hard", "splits/t_novel")) and "b" not in m]
    test_hash = [f for f, m in opened if any(s_ in f for s_ in ("splits/t_clean", "splits/t_hard", "splits/t_novel")) and "b" in m]
    check("1a file split test chi mo che do 'rb' de bam sha256 (check_dataset), khong doc noi dung", not test_text,
          f"bam {len(test_hash)} file; doc text: {test_text}")
    check("1b windows.jsonl: chi json-parse cua so Train", set(parsed) == train_ids, f"parse {len(set(parsed))} cua so khac nhau (train.jsonl + windows.jsonl), ngoai Train {len(set(parsed) - train_ids)}")
    check("1c tra ve dung 483 cua so Train", len(meta) == 483 and {w["window_id"] for w in meta} == train_ids)
    # ---- 2. truong event ----
    TrackDict.seen = set()
    for ev in events[:50]:
        for e in ev: Pd.event_atoms(TrackDict(e))
    check("2 event_atoms chi doc EVENT_KEYS", TrackDict.seen <= set(Pd.EVENT_KEYS), f"{sorted(TrackDict.seen)}")
    # ---- 3. vi tu cam ----
    must = [("img", "cmd.exe"), ("tok", "/c"), ("tok", "cmd"), ("par", "<launcher>"), ("img", "powershell.exe"), ("eid", 4104), ("eid", 40961),
            ("eid", 216), ("eid", 98), ("img", "vssvc.exe"), ("tok", "c:\\windows\\temp\\ntds_t0"), ("tok", "\\windows\\temp\\ntds_t0"),
            ("tok", "_ldap._tcp.dc._msdcs.corp.vtlab.test"), ("imgtok", ("cmd.exe", "ntdsutil")), ("imgtok", ("powershell.exe", "adsisearcher"))]
    ok_ = [("tok", "ntdsutil"), ("tok", "enum-logs"), ("img", "nltest.exe"), ("tok", "adsisearcher"), ("imgtok", ("net.exe", "/domain")), ("eid", 1)]
    check("3a vi tu cam bi nhan dien (S1-S5)", all(Pd.forbidden_reason(a) for a in must), f"{[a for a in must if not Pd.forbidden_reason(a)]}")
    check("3b vi tu hanh vi KHONG bi chan", not any(Pd.forbidden_reason(a) for a in ok_), f"{[a for a in ok_ if Pd.forbidden_reason(a)]}")
    R = I.run(ROOT)
    check("3c tu vung luot rang buoc khong chua atom cam / nen", not any(Pd.forbidden_reason(a) or I.bg_reason(a, R["share"]) for a in R["atoms_c"]),
          f"chan {len(R['blocked'])}/{len(R['atoms_all'])}")
    check("3d nen tu dong: dsmsvc / rundll32 -embedding bi chan", all(I.bg_reason(a, R["share"]) for a in
          [("tok", "dsmsvc"), ("imgtok", ("rundll32.exe", "-embedding"))] if a in R["share"]))
    viol = [c["id"] for c in R["final"] for a in c["pos_atoms"] if Pd.forbidden_reason(a) or I.bg_reason(a, R["share"])]
    check("3e luat cuoi: 0 vi pham vi tu cam", not viol, f"{len(R['final'])} luat, vi pham {viol}")
    g1 = [c for c in R["cands"] if c.get("reject", ("",))[0] == "G1"]
    check("3f cong G1 da loai luat chua vi tu cam (luot khong rang buoc)", len(g1) > 0 and all(c["pass"] == "khong_rang_buoc" for c in g1), f"{len(g1)} luat")
    # ---- 4. matcher == dieu kien engine ----
    n_rule = n_bad = 0
    for pname, (rules, models, oof, sel) in R["passes"].items():
        atoms = R["atoms_all"] if pname == "khong_rang_buoc" else R["atoms_c"]
        X = I.matrix([set().union(*[Pd.event_atoms(e) for e in ev]) if ev else set() for ev in events], atoms)
        for tg, (rs, mdl) in models.items():
            ap = mdl.apply(X) if mdl is not None else None
            for r in rs:
                m = np.array([Pd.match(r["literals"], ev) for ev in events])
                ref = (ap == r["src"]["leaf_id"]) if ap is not None else I.eval_lits(X, atoms, r["literals"])
                n_rule += 1; n_bad += not np.array_equal(m, ref)
    check(f"4a matcher noi bo (su kien tho) == dieu kien {R['engine']} tren Train (moi luat/la duong, ca literal am)", n_bad == 0, f"{n_rule} luat/la, lech {n_bad}")
    if R["engine"] == "ripper":       # doc lai ruleset cua wittgenstein dung ngu nghia: fit moi (khong cache) 1 muc tieu, so voi predict goc
        import warnings, pandas as pd, wittgenstein as lw
        warnings.filterwarnings("ignore")
        Xc = I.matrix([set().union(*[Pd.event_atoms(e) for e in ev]) if ev else set() for ev in events], R["atoms_c"])
        df = pd.DataFrame(Xc.astype(str), columns=[f"f{j}" for j in range(len(R["atoms_c"]))]); df["y"] = R["Y"]["T1654"].astype(int)
        clf = lw.RIPPER(random_state=1337); clf.fit(df, class_feat="y", pos_class=1)
        own = np.asarray(clf.predict(df.drop(columns="y")), bool)
        parsed = I.predict_model([{"literals": lits} for lits in I.fit_ripper(Xc, R["Y"]["T1654"], R["atoms_c"])], Xc, R["atoms_c"])
        check("4b ruleset RIPPER doc lai (literal) == wittgenstein.predict tren Train (T1654)", np.array_equal(own, parsed), f"{int(own.sum())} cua so")
    bad = 0
    for c in R["final"]:
        m = np.array([Pd.match([(a, True) for a in c["pos_atoms"]], ev) for ev in events])
        bad += not np.array_equal(m, I.eval_pos(R["X_all"], R["atoms_all"], c["pos_atoms"]))
        bad += int(m.sum()) != c["train"]["support"]
    check("4c luat cuoi: matcher == ma tran dac trung == support provenance", bad == 0, f"{len(R['final'])} luat")
    # ---- 5. provenance ----
    P = I.provenance(R, ROOT)
    okp = all(r["support_windows"] and set(r["support_windows"]) <= train_ids and r["oof"]["folds_rediscovered"] and r["source"]["origin_rules"]
              and r["seed"] == 1337 and r["train"]["support"] == len(r["support_windows"]) for r in P["rules"])
    check("5 provenance day du (cua so/phien Train, OOF, la nguon, engine, seed)", okp, f"{len(P['rules'])} luat")
    # ---- 6. tat dinh ----
    R2 = I.run(ROOT)
    same = [(c["id"], c["pos_atoms"], c["train"], c["oof"]) for c in R["final"]] == [(c["id"], c["pos_atoms"], c["train"], c["oof"]) for c in R2["final"]]
    check("6 chay lai -> cung tap luat", same)
    print(f"\nKET QUA: {sum(RES)}/{len(RES)} PASS trong {time.time() - t0:.1f}s")
    sys.exit(0 if all(RES) else 1)

if __name__ == "__main__":
    main()
