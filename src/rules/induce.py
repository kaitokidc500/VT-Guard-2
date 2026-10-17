#!/usr/bin/env python3
"""VT-Guard Buoc 7 moc 1 - quy nap luat tu Train (docs/STEP7-BRIEF.md muc 4-5, tang 1). KHONG doc tap test.

Dac trung: ma tran nhi phan "cua so co >= 1 event thoa atom" (src/rules/predicates.py), atom xuat hien o >= 3 phien Train.
  (Lech brief 4.1/4.2 co chu y: dung vi tu CO MAT thay cho nguong ti le B2 vi chi dang nay anh xa CHINH XAC sang Sigma
  "co >= 1 event thoa ..."; ti le > 0 cua B2 tuong duong co mat.) Cot sap xep: atom co trong hat giong attention truoc.
Hai luot: "khong rang buoc" (moi atom, de do cong vi tu cam) va "rang buoc" (bo atom cam S1-S5 va atom nen mot-phia S4-auto:
  < 50% lan khop tren cua so duong Train nam trong cay tien trinh; event_origin CHI dung cho cong nay, khong phai dac trung).
Engine (brief 4.1): cay nong (max_depth 3 / 4, min_samples_leaf 10) va RIPPER (wittgenstein), mot-doi-con-lai cho 5 TTP +
  nhi phan; chon bang macro-F1 TTP OOF (CV 5 fold theo nhom) cua du doan cua chinh engine (literal day du), luot rang buoc.
Luat: moi la/luat du doan lop duong -> luat = cac literal DUONG (literal "vang mat" bi bo vi Sigma khong bieu dien duoc
  "khong co event nao trong cua so"), rut gon literal bi bao ham; precision cua luat rut gon do lai.
OOF cua mot luat: cung tap literal duong duoc quy nap LAI boi engine tren 4 fold con lai -> do tren fold con lai; gop qua
  cac fold tai lap. Khong tai lap -> khong co OOF -> loai.
Cong (thu tu): G0 khong literal duong -> G1 vi tu cam -> G2 Sigma -> G3 support Train >= 10, precision OOF >= 0.9 tren >= 10
  cua so OOF -> G4 khu trung (cung TTP, Jaccard tap cua so Train >= 0.8: giu precision OOF cao hon).
Dau ra: reports/step7/rules_provenance.json, reports/step7/m1_rules.md. Chay: python src/rules/induce.py
"""
import hashlib, json, os, re, sys
from collections import Counter, defaultdict

import numpy as np
from sklearn.tree import DecisionTreeClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval", "../baselines", "../dataset"): sys.path.insert(0, os.path.join(HERE, d))
from predicates import event_atoms, forbidden_reason, sigma_reason, match   # noqa: E402
from evaluate import check_dataset, load_meta, cv_folds, TTPS               # noqa: E402
from bootstrap import SEED                                                  # noqa: E402

TARGETS = ["bin"] + TTPS
DEPTHS = (3, 4)
MIN_LEAF, MIN_SESSIONS = 10, 3
PREC_OOF, MIN_SUPPORT, JACCARD = 0.9, 10, 0.8
MIN_OOF_MATCHES = 10          # precision OOF phai tinh tren >= 10 cua so OOF khop
MIN_OWN_SHARE = 0.5           # atom: >= 50% lan khop (cua so duong Train) nam trong cay tien trinh, neu khong -> nen mot-phia
OUT = os.path.join("reports", "step7")

# ---------------- du lieu (CHI Train) ----------------
WID_RE = re.compile(r'"window_id":\s*"([^"]+)"')

def load_train(root="."):
    """Train: meta (evaluate.load_meta) + event cua tung cua so Train. check_dataset chi BAM sha256 (rb) cac split;
    windows.jsonl: doc window_id cua dong bang regex TRUOC, chi json-parse dong thuoc Train (khong parse cua so test)."""
    check_dataset(root)
    meta = load_meta(root, "train")
    want = {w["window_id"] for w in meta}; got = {}
    with open(os.path.join(root, "data", "processed", "windows.jsonl"), encoding="utf-8") as fh:
        for l in fh:
            m = WID_RE.search(l)
            if m is None or m.group(1) not in want: continue
            w = json.loads(l); got[w["window_id"]] = (w["events"], w["event_origin"])
    assert set(got) == want
    events = [got[w["window_id"]][0] for w in meta]
    origins = [got[w["window_id"]][1] for w in meta]      # CHI dung cho cong nen mot-phia (Train), khong phai dac trung
    return meta, events, origins

def labels(meta):
    Y = {"bin": np.array([bool(w["window_malicious"]) for w in meta])}
    for t in TTPS: Y[t] = np.array([t in w["window_ttps"] for w in meta])
    return Y

def load_seeds(root="."):
    S = json.load(open(os.path.join(root, "reports", "step6", "rule_seeds_train.json"), encoding="utf-8"))
    seeds = defaultdict(dict)        # atom -> {ttp: {lift, share_pos, share_neg}}
    for t, v in S["ttp"].items():
        for cat, kind in (("image_name", "img"), ("event_id", "eid"), ("cmd_token", "tok")):
            for x in v[cat]:
                a = (kind, int(x["value"]) if kind == "eid" else x["value"])
                seeds[a][t] = {"lift": x["lift"], "share_pos": x["share_pos_windows"], "share_neg": x["share_neg_windows"]}
    return seeds

def build_vocab(meta, events, seeds):
    sess = defaultdict(set)
    win_atoms = []
    for w, ev in zip(meta, events):
        A = set()
        for e in ev: A |= event_atoms(e)
        win_atoms.append(A)
        for a in A: sess[a].add(w["run_id"])
    atoms = [a for a, s in sess.items() if len(s) >= MIN_SESSIONS]
    key = lambda a: (a not in seeds, a[0], str(a[1]))          # hat giong truoc, sau do tat dinh
    atoms.sort(key=key)
    return atoms, win_atoms

def own_shares(meta, events, origins, Y, atoms):
    """Ti le lan khop atom nam trong cay tien trinh (event_origin == own) tren cua so DUONG cua Train."""
    from predicates import _event_has
    o = defaultdict(int); n = defaultdict(int); want = set(atoms)
    for i in np.flatnonzero(Y["bin"]):
        for e, g in zip(events[i], origins[i]):
            for a in event_atoms(e) & want:
                n[a] += 1; o[a] += g == "own"
    return {a: (o[a] / n[a] if n[a] else 1.0) for a in atoms}

def bg_reason(a, share):
    return f"S4-auto nen mot-phia ({share.get(a, 1.0):.0%} khop trong cay tien trinh < {MIN_OWN_SHARE:.0%}, Train)" if share.get(a, 1.0) < MIN_OWN_SHARE else None

def matrix(win_atoms, atoms):
    idx = {a: j for j, a in enumerate(atoms)}
    X = np.zeros((len(win_atoms), len(atoms)), np.uint8)
    for i, A in enumerate(win_atoms):
        for a in A:
            j = idx.get(a)
            if j is not None: X[i, j] = 1
    return X

# ---------------- cay -> luat ----------------
def leaves(tree, atoms):
    """[(leaf_id, literals [(atom, present_bool)], n, n_pos)] cho la du doan duong."""
    t = tree.tree_; out = []
    def walk(node, path):
        if t.children_left[node] == -1:
            n = int(t.n_node_samples[node]); v = t.value[node][0]
            frac = v[1] / v.sum() if v.sum() else 0.0
            if frac > 0.5: out.append((int(node), list(path), n, int(round(frac * n))))
            return
        a = atoms[t.feature[node]]          # X nhi phan: <= 0.5 la vang mat
        walk(t.children_left[node], path + [(a, False)])
        walk(t.children_right[node], path + [(a, True)])
    walk(0, [])
    return out

def simplify(pos_atoms):
    """Bo literal bi bao ham: img=X bi bao boi imgtok(X, .), tok=T bi bao boi imgtok(., T)."""
    pos = set(pos_atoms)
    it = [a[1] for a in pos if a[0] == "imgtok"]
    pos -= {("img", x) for x, _ in it} | {("tok", t) for _, t in it}
    return sorted(pos, key=lambda a: (a[0], str(a[1])))

def rule_key(target, literals):
    return (target, tuple(simplify([a for a, p in literals if p])))

def fit_tree(X, y, depth):
    return DecisionTreeClassifier(max_depth=depth, min_samples_leaf=MIN_LEAF, random_state=SEED).fit(X, y)

def eval_pos(X, atoms, pos_atoms):
    idx = {a: j for j, a in enumerate(atoms)}
    m = np.ones(X.shape[0], bool)
    for a in pos_atoms: m &= X[:, idx[a]] == 1
    return m

def eval_lits(X, atoms, literals):
    idx = {a: j for j, a in enumerate(atoms)}
    m = np.ones(X.shape[0], bool)
    for a, p in literals: m &= (X[:, idx[a]] == 1) == p
    return m

RIPPER_CACHE = os.path.join("data", "processed", "step7", "ripper_cache")

def fit_ripper(X, y, atoms):
    """RIPPER (wittgenstein, random_state 1337) tren cot "0"/"1"; tra list literal day du (atom, co_mat) moi luat.
    Cache theo sha1(X, y, atoms) o data/processed/step7/ripper_cache (khong vao git)."""
    key = hashlib.sha1(X.tobytes() + y.astype(np.uint8).tobytes() + repr(atoms).encode()).hexdigest()
    p = os.path.join(RIPPER_CACHE, f"{key}.json")
    if os.path.exists(p):
        return [[(atoms[j], bool(v)) for j, v in r] for r in json.load(open(p, encoding="utf-8"))]
    import warnings, pandas as pd, wittgenstein as lw
    warnings.filterwarnings("ignore")
    df = pd.DataFrame(X.astype(str), columns=[f"f{j}" for j in range(len(atoms))]); df["y"] = y.astype(int)
    clf = lw.RIPPER(random_state=SEED); clf.fit(df, class_feat="y", pos_class=1)
    rules = [[(int(c.feature[1:]), str(c.val) == "1") for c in r.conds] for r in clf.ruleset_.rules]
    os.makedirs(RIPPER_CACHE, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f: json.dump(rules, f)
    return [[(atoms[j], v) for j, v in r] for r in rules]

def fit_rules(engine, X, y, atoms):
    """-> [{"literals": [(atom, bool)] DAY DU, "src": {...}}] cac luat/la du doan lop duong cua engine."""
    if engine.startswith("tree"):
        tr = fit_tree(X, y, int(engine[4:]))
        return [{"literals": lits, "src": {"leaf_id": leaf, "n": n, "n_pos": npos}} for leaf, lits, n, npos in leaves(tr, atoms)], tr
    rs = fit_ripper(X, y, atoms)
    out = []
    for i, lits in enumerate(rs):
        m = eval_lits(X, atoms, lits)
        out.append({"literals": lits, "src": {"ripper_rule": i, "n": int(m.sum()), "n_pos": int((m & y).sum())}})
    return out, None

def predict_model(rules, X, atoms):
    """Du doan cua chinh engine (ngu nghia day du): OR cac luat/la duong voi literal day du."""
    m = np.zeros(X.shape[0], bool)
    for r in rules: m |= eval_lits(X, atoms, r["literals"])
    return m

def induce_pass(engine, X, atoms, Y, folds):
    """-> (rules {rule_key: info} tu toan Train, models, OOF tai lap {rule_key: tp/fp/fn/folds}, macro-F1 TTP OOF cua engine)."""
    rules, models = {}, {}
    for tg in TARGETS:
        rs, mdl = fit_rules(engine, X, Y[tg], atoms); models[tg] = (rs, mdl)
        for r in rs:
            k = rule_key(tg, r["literals"])
            rules.setdefault(k, {"target": tg, "pos_atoms": list(k[1]), "sources": []})["sources"].append(r)
    oof = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "folds": []})
    cnt = {t: [0, 0, 0] for t in TTPS}
    for fi, (a_, va) in enumerate(folds):
        for tg in TARGETS:
            rs, _ = fit_rules(engine, X[a_], Y[tg][a_], atoms)
            y = Y[tg][va]
            if tg in cnt:
                pr = predict_model(rs, X[va], atoms)
                cnt[tg][0] += int((pr & y).sum()); cnt[tg][1] += int((pr & ~y).sum()); cnt[tg][2] += int((~pr & y).sum())
            for k in {rule_key(tg, r["literals"]) for r in rs}:
                if not k[1]: continue
                m = eval_pos(X[va], atoms, k[1])
                o = oof[k]; o["tp"] += int((m & y).sum()); o["fp"] += int((m & ~y).sum()); o["fn"] += int((~m & y).sum()); o["folds"].append(fi)
    f1 = {t: round(2 * c[0] / (2 * c[0] + c[1] + c[2]), 4) if c[0] else 0.0 for t, c in cnt.items()}
    return rules, models, oof, {"macro": round(float(np.mean(list(f1.values()))), 4), "per_ttp": f1}

def fmt_atom(a):
    k, v = a
    if k == "imgtok": return f"image={v[0]} & cmd~'{v[1]}'"
    return {"img": "image={}", "par": "parent={}", "eid": "event_id={}", "tok": "cmd~'{}'"}[k].format(v)

ENGINES = ("tree3", "tree4", "ripper")
ENGINE_DESC = {"tree3": "sklearn DecisionTreeClassifier max_depth 3", "tree4": "sklearn DecisionTreeClassifier max_depth 4",
               "ripper": "wittgenstein RIPPER (k=2, prune_size 0.33)"}

def run(root=".", engines=ENGINES):
    meta, events, origins = load_train(root)
    Y = labels(meta); seeds = load_seeds(root)
    atoms_all, win_atoms = build_vocab(meta, events, seeds)
    X_all = matrix(win_atoms, atoms_all)
    share = own_shares(meta, events, origins, Y, atoms_all)
    blocked = {a: forbidden_reason(a) or bg_reason(a, share) for a in atoms_all if forbidden_reason(a) or bg_reason(a, share)}
    atoms_c = [a for a in atoms_all if a not in blocked]
    X_c = matrix(win_atoms, atoms_c)
    folds = cv_folds(meta, root=root)
    # chon engine: macro-F1 TTP OOF cua chinh engine (ngu nghia day du) tren luot rang buoc
    sel = {e: induce_pass(e, X_c, atoms_c, Y, folds) for e in engines}
    engine = max(engines, key=lambda e: (sel[e][3]["macro"], -engines.index(e)))
    passes = {"rang_buoc": sel[engine], "khong_rang_buoc": induce_pass(engine, X_all, atoms_all, Y, folds)}
    # ---------------- cong ----------------
    cands = []
    for pname in ("khong_rang_buoc", "rang_buoc"):
        rules, models, oof, _ = passes[pname]
        for k, r in rules.items():
            c = {"pass": pname, "target": r["target"], "pos_atoms": r["pos_atoms"], "sources": r["sources"], "key": k}
            if not r["pos_atoms"]:
                c["reject"] = ("G0", "luat chi gom literal vang mat (khong co vi tu duong)"); cands.append(c); continue
            m = eval_pos(X_all, atoms_all, r["pos_atoms"]); y = Y[r["target"]]
            c["train"] = {"support": int(m.sum()), "tp": int((m & y).sum()), "fp": int((m & ~y).sum()),
                          "precision": round(float((m & y).sum() / max(1, m.sum())), 4), "recall": round(float((m & y).sum() / max(1, y.sum())), 4)}
            c["match_idx"] = np.flatnonzero(m)
            o = oof.get(k)
            c["oof"] = None if o is None else {"tp": o["tp"], "fp": o["fp"], "precision": round(o["tp"] / (o["tp"] + o["fp"]), 4) if o["tp"] + o["fp"] else None,
                                               "recall_on_folds": round(o["tp"] / max(1, o["tp"] + o["fn"]), 4), "folds_rediscovered": sorted(o["folds"])}
            why = lambda a: forbidden_reason(a) or bg_reason(a, share)
            bad = [(fmt_atom(a), why(a)) for a in r["pos_atoms"] if why(a)]
            c["dropped_negative_literals_forbidden"] = sorted({why(a) for s in r["sources"] for a, p in s["literals"] if not p and why(a)})
            if bad: c["reject"] = ("G1", "vi tu cam: " + "; ".join(f"{a} [{w}]" for a, w in bad))
            elif any(sigma_reason(a) for a in r["pos_atoms"]): c["reject"] = ("G2", "; ".join(sorted({sigma_reason(a) for a in r["pos_atoms"] if sigma_reason(a)})))
            elif c["oof"] is None or c["oof"]["precision"] is None: c["reject"] = ("G3", "khong tai lap tren fold nao (khong co OOF)")
            elif c["train"]["support"] < MIN_SUPPORT or c["oof"]["precision"] < PREC_OOF or c["oof"]["tp"] + c["oof"]["fp"] < MIN_OOF_MATCHES:
                c["reject"] = ("G3", f"support Train {c['train']['support']} (>= {MIN_SUPPORT}) / precision OOF {c['oof']['precision']} (>= {PREC_OOF}) "
                                     f"tren {c['oof']['tp'] + c['oof']['fp']} cua so OOF khop (>= {MIN_OOF_MATCHES})")
            cands.append(c)
    alive = {}
    for c in cands:
        if "reject" in c: continue
        if c["key"] in alive: c["reject"] = ("G4", "trung khoa voi luat cua luot khac"); continue
        alive[c["key"]] = c
    by_t = defaultdict(list)
    for c in alive.values(): by_t[c["target"]].append(c)
    for t, cs in by_t.items():
        cs.sort(key=lambda c: (-c["oof"]["precision"], -c["train"]["support"], len(c["pos_atoms"]), str(c["key"])))
        kept = []
        for c in cs:
            s = set(c["match_idx"].tolist())
            dup = next((k for k in kept if len(s & set(k["match_idx"].tolist())) / max(1, len(s | set(k["match_idx"].tolist()))) >= JACCARD), None)
            if dup is not None: c["reject"] = ("G4", f"Jaccard >= {JACCARD} voi luat {' AND '.join(fmt_atom(a) for a in dup['pos_atoms'])} (precision OOF cao hon/bang)")
            else: kept.append(c)
    final = [c for c in cands if "reject" not in c]
    viol = [c for c in final for a in c["pos_atoms"] if forbidden_reason(a) or bg_reason(a, share)]
    assert not viol, f"luat cuoi chua vi tu cam: {len(viol)}"
    final.sort(key=lambda c: (TARGETS.index(c["target"]), -c["oof"]["precision"], -c["train"]["support"]))
    order = defaultdict(int)
    for c in final:
        order[c["target"]] += 1
        c["id"] = ("VTR-BIN" if c["target"] == "bin" else "VTR-" + c["target"].replace(".", "")) + f"-{order[c['target']]:02d}"
    return dict(engine=engine, sel={e: v[3] for e, v in sel.items()}, share=share, meta=meta, Y=Y, atoms_all=atoms_all, atoms_c=atoms_c,
                blocked=blocked, X_all=X_all, cands=cands, final=final, seeds=seeds, events=events, passes=passes, folds=folds)

DEVIATIONS = [
    {"id": 1, "what": "vi tu CO MAT (cua so co >= 1 event thoa atom) thay cho nguong ti le dac trung B2 (brief 4.1/4.2)",
     "why": "chi dang nay anh xa CHINH XAC sang Sigma ('co >= 1 event thoa ...'); nguong ti le > 0 cua B2 tuong duong co mat, "
            "nguong ti le khac 0 khong bieu dien duoc trong Sigma -> matcher Sigma se lech dieu kien luat"},
    {"id": 2, "what": "engine = RIPPER (wittgenstein), khong phai cay",
     "why": "brief 4.1 yeu cau chon bang macro-F1 TTP OOF; RIPPER 0.756 > cay sau 4 0.675 > cay sau 3 0.658 (du doan cua chinh engine, "
            "literal day du, luot rang buoc). Cay van duoc chay va bao cao"},
    {"id": 3, "what": "them cong S5 (ten mien lab vtlab) va S4-auto (atom co < 50% lan khop tren cua so duong Train nam trong cay tien trinh)",
     "why": "S5: token ten mien lab khong khai quat ra moi truong khac. S4-auto: tong quat hoa canh bao 4 (event nen mot-phia) - bat "
            "duoc svchost dsmsvc / rundll32 -embedding (tac dong phu nen cua T1003, 0% trong cay tien trinh) ma danh sach tay bo sot; "
            "event_origin chi dung cho cong nay tren Train, khong bao gio la dac trung"},
    {"id": 4, "what": "cong phu: precision OOF phai tinh tren >= 10 cua so OOF khop (them vao G3)",
     "why": "precision OOF tren 3-9 cua so khong co y nghia thong ke (vd cmd~'system' cho T1087.002: 3 cua so, precision Train 0.72). "
            "Cong dat TRUOC khi cham test, CHI dua tren Train; nguoi dung duyet giu nguong 10 (khong ha de lay them luat)"},
]
NO_TTP_RULE_NOTE = ("T1016 va T1087.002 KHONG co luat theo TTP: ket qua cua cac cong (khong ha cong). Phien mixed gan nhieu TTP cho "
                    "cung cua so nen token cua TTP khac xuat hien trong cua so mang nhan TTP do -> precision OOF thap; cac luat T1087.002 "
                    "chinh xac (cmd~'.findall' 9 cua so OOF, image=cmd.exe & cmd~'user' bi cam S2) khong qua cong. Hanh vi T1087.002 "
                    "chi duoc phu o muc nhi phan (VTR-BIN-04 .findall, VTR-BIN-05 net administrator).")

def provenance(R, root="."):
    meta, seeds = R["meta"], R["seeds"]
    rules = []
    for c in R["final"]:
        idx = c["match_idx"]; y = R["Y"][c["target"]]
        rel = {}
        for a in c["pos_atoms"]:
            for b in ([a] + ([("img", a[1][0]), ("tok", a[1][1])] if a[0] == "imgtok" else [])):
                if b in seeds: rel[fmt_atom(b)] = seeds[b]
        rules.append({
            "id": c["id"], "target": c["target"], "ttp_tag": None if c["target"] == "bin" else c["target"],
            "predicates": [fmt_atom(a) for a in c["pos_atoms"]], "atoms": [[a[0], list(a[1]) if a[0] == "imgtok" else a[1]] for a in c["pos_atoms"]],
            "semantics": "cua so khop neu MOI vi tu co >= 1 event thoa (cac vi tu co the o event khac nhau)",
            "train": c["train"], "oof": c["oof"],
            "support_windows": [meta[i]["window_id"] for i in idx],
            "support_true_positive_windows": [meta[i]["window_id"] for i in idx if y[i]],
            "support_sessions": sorted({meta[i]["run_id"] for i in idx}),
            "related_attention_seeds": rel,
            "source": {"engine": ENGINE_DESC[R["engine"]], "params": {"min_samples_leaf": MIN_LEAF, "random_state": SEED} if R["engine"].startswith("tree")
                       else {"k": 2, "prune_size": 0.33, "random_state": SEED}, "pass": c["pass"], "origin_rules": [
                {**s_["src"], "full_literals": [("+" if p else "-") + fmt_atom(a) for a, p in s_["literals"]]} for s_ in c["sources"]],
                "dropped_negative_literals_forbidden": c["dropped_negative_literals_forbidden"]},
            "seed": SEED})
    rej = defaultdict(list)
    for c in R["cands"]:
        if "reject" in c:
            rej[c["reject"][0]].append({"pass": c["pass"], "target": c["target"], "predicates": [fmt_atom(a) for a in c["pos_atoms"]],
                                        "reason": c["reject"][1], "train": c.get("train"), "oof": c.get("oof")})
    out = {"dataset_version": "v1.2", "seed": SEED, "source": "CHI Train (483 cua so); khong doc tap test",
           "engine": {"chosen": R["engine"], "desc": ENGINE_DESC[R["engine"]],
                      "macro_f1_ttp_oof_by_engine": R["sel"],
                      "rule": "chon engine co macro-F1 TTP OOF cao nhat (du doan cua chinh engine, literal day du, luot rang buoc)"},
           "features": {"n_atoms_all": len(R["atoms_all"]), "n_atoms_constrained": len(R["atoms_c"]),
                        "n_atoms_blocked_forbidden": len(R["blocked"]), "blocked_by_reason": dict(Counter(R["blocked"].values())),
                        "min_sessions": MIN_SESSIONS},
           "gates": {"G0": "luat khong co literal duong", "G1": "vi tu cam (scaffold S1-S5 / nen mot-phia S4-auto)", "G2": "khong anh xa Sigma nguyen van",
                     "G3": f"support Train >= {MIN_SUPPORT}, precision OOF >= {PREC_OOF} tren >= {MIN_OOF_MATCHES} cua so OOF (can tai lap tren fold)",
                     "G4": f"khu trung (Jaccard >= {JACCARD}, cung TTP)"},
           "deviations_from_brief": DEVIATIONS, "ttp_without_rule": {"ttps": ["T1016", "T1087.002"], "note": NO_TTP_RULE_NOTE},
           "approved": "nguoi dung duyet 11 luat (giu cong >= 10 cua so OOF)",
           "n_rejected_by_gate": {g: len(v) for g, v in sorted(rej.items())}, "rules": rules, "rejected": dict(sorted(rej.items()))}
    os.makedirs(os.path.join(root, OUT), exist_ok=True)
    with open(os.path.join(root, OUT, "rules_provenance.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(out, f, indent=1)
    return out

def report(P, root="."):
    L = ["# VT-Guard Buoc 7 moc 1 - luat ung vien (CHI Train; chua Sigma, chua test)", "",
         "Engine (macro-F1 TTP OOF, du doan cua chinh engine): " +
         "; ".join(f"{e} = {v['macro']}" for e, v in P["engine"]["macro_f1_ttp_oof_by_engine"].items()) +
         f" -> chon **{P['engine']['chosen']}** ({P['engine']['desc']}), seed 1337. "
         f"Atom: {P['features']['n_atoms_all']} (>= 3 phien Train); bi chan o luot rang buoc: {P['features']['n_atoms_blocked_forbidden']} "
         f"{P['features']['blocked_by_reason']}.", "",
         "Ngu nghia: cua so khop luat neu moi vi tu co >= 1 event thoa; `cmd~'x'` = command line (norm_cmd) chua token x. "
         "Luat = cac literal DUONG cua mot luat/la cua engine (literal vang mat bi bo vi Sigma khong bieu dien duoc), da rut gon. "
         "OOF: luat duoc quy nap lai boi engine tren 4/5 Train va do tren fold con lai; precision OOF can >= 10 cua so khop.", "",
         f"## Luat giu lai: {len(P['rules'])}", "",
         "| id | Muc tieu | Vi tu | Support Train (TP/FP) | Precision Train | Recall Train | Precision OOF (TP/FP) | Fold tai lap | Hat giong lien quan (TTP: lift) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in P["rules"]:
        sd = "; ".join(f"{k}: " + ", ".join(f"{t} {v['lift']}" for t, v in d.items()) for k, d in r["related_attention_seeds"].items()) or "-"
        L.append(f"| {r['id']} | {r['target']} | " + " AND ".join(f"`{p}`" for p in r["predicates"]) +
                 f" | {r['train']['support']} ({r['train']['tp']}/{r['train']['fp']}) | {r['train']['precision']:.3f} | {r['train']['recall']:.3f} | "
                 f"{r['oof']['precision']:.3f} ({r['oof']['tp']}/{r['oof']['fp']}) | {len(r['oof']['folds_rediscovered'])}/5 | {sd} |")
    L += ["", f"**TTP khong co luat rieng:** {P['ttp_without_rule']['note']}", "", "## Sai khac so voi brief (va ly do)", ""]
    for d in P["deviations_from_brief"]: L.append(f"{d['id']}. **{d['what']}** - {d['why']}.")
    L += ["", "## Luat bi loai theo cong", "", "| Cong | So luat | Mo ta |", "|---|---|---|"]
    for g, d in P["gates"].items(): L.append(f"| {g} | {P['n_rejected_by_gate'].get(g, 0)} | {d} |")
    for g in ("G0", "G1", "G2", "G3", "G4"):
        rows = P["rejected"].get(g, [])
        if not rows: continue
        L += ["", f"**{g}** ({P['gates'][g]}) - {len(rows)} luat", "", "| Luot | Muc tieu | Vi tu | Ly do | Support / precision Train | Precision OOF |", "|---|---|---|---|---|---|"]
        for r in rows:
            tr = r.get("train") or {}; oo = r.get("oof") or {}
            L.append(f"| {r['pass']} | {r['target']} | " + " AND ".join(f"`{p}`" for p in r["predicates"]) + f" | {r['reason']} | "
                     f"{tr.get('support', '-')} / {tr.get('precision', '-')} | {oo.get('precision', '-') if oo else '-'} |")
    L.append("")
    with open(os.path.join(root, OUT, "m1_rules.md"), "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(L))
    return "\n".join(L)

if __name__ == "__main__":
    R = run("."); P = provenance(R, "."); print(report(P, "."))
