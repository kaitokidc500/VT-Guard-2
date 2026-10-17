#!/usr/bin/env python3
"""VT-Guard Buoc 7 moc 2 - bo phat hien CHI-LUAT: doc rules/sigma/*.yml (KHONG doc provenance de so khop) -> matcher noi bo
cung ngu nghia Sigma -> cham cua so windows.jsonl.

Ngu nghia Sigma duoc ho tro (dung dung tap con cac file xuat ra; gap cau truc khac -> loi):
  logsource category process_creation -> event_id in {1 (Sysmon), 4688 (Security)}
  Image|endswith: '\\X' -> '\\' + image_name ket thuc bang X (khong phan biet hoa thuong; dataset chi giu ten anh, tuong
                           duong endswith tren duong dan day du)
  CommandLine|re: R    -> re.search(R, command_line tho)
  EventID: E
  condition: selection (AND cac truong cua selection tren CUNG event)
  correlation type temporal -> cua so khop neu MOI luat con co >= 1 event khop trong cua so (timespan khong mo phong: cua so
                           <= 64 event cua mot phien; tren Train 2 event cach nhau <= 0.07 s < timespan 1m)
Cua so khop luat = co >= 1 event khop (luat don) / moi luat con khop (correlation).
Diem (dinh dang Buoc 5-6, cho Buoc 8): p_malicious = max precision OOF cua cac luat khop (0 neu khong luat nao);
  p_ttp[T] = max precision OOF cua luat theo TTP T khop. Nguong CO DINH 0.5 cho nhi phan va moi TTP (dat truoc, khong chon
  tren test): nhi phan = co luat nao khop; da nhan = hop TTP cac luat theo TTP khop (luat nhi phan khong gan TTP).
Train: du doan IN-SAMPLE (luat quy nap tu toan Train) - KHONG phai OOF.
Chay: python src/rules/apply.py
"""
import glob, json, os, re, sys
from collections import Counter, defaultdict

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval", "../baselines", "../dataset"): sys.path.insert(0, os.path.join(HERE, d))
from evaluate import (check_dataset, load_all_meta, evaluate, render_markdown, write_preds, check_predictions, early_starts,
                      hn_signatures, TTPS, SPLITS, TEST_SPLITS, EARLY_KS)          # noqa: E402

SIGMA_DIR = os.path.join("rules", "sigma")
PROC_EIDS = {1, 4688}
OUT = os.path.join("reports", "step7")

# ---------------- doc Sigma ----------------
def _compile_selection(sel):
    out = []
    for k, v in sel.items():
        if k == "Image|endswith": out.append(("img_end", str(v).lower()))
        elif k == "CommandLine|re": out.append(("cmd_re", re.compile(str(v))))
        elif k == "EventID": out.append(("eid", int(v)))
        else: raise ValueError(f"truong/modifier Sigma chua ho tro: {k}")
    return out

def _base_rule(doc):
    ls = doc["logsource"]
    if ls.get("category") != "process_creation" or ls.get("product") != "windows": raise ValueError(f"logsource chua ho tro: {ls}")
    det = doc["detection"]
    if det.get("condition") != "selection" or set(det) != {"selection", "condition"}: raise ValueError(f"condition chua ho tro: {det}")
    return {"title": doc["title"], "id": doc["id"], "name": doc.get("name"), "sel": _compile_selection(det["selection"])}

def load_sigma(root="."):
    """-> list {rule_id, target, conf, file, kind, parts: [base_rule]} doc tu YAML."""
    rules = []
    for fp in sorted(glob.glob(os.path.join(root, SIGMA_DIR, "*.yml"))):
        docs = [d for d in yaml.safe_load_all(open(fp, encoding="ascii")) if d]
        base = {d["name"]: _base_rule(d) for d in docs if "correlation" not in d and d.get("name")}
        heads = [d for d in docs if "correlation" in d] or [d for d in docs if "vtguard_provenance" in d]
        assert len(heads) == 1, fp
        h = heads[0]; pv = h["vtguard_provenance"]
        if "correlation" in h:
            c = h["correlation"]
            if c["type"] != "temporal": raise ValueError(f"correlation chua ho tro: {c['type']}")
            parts = [base[n] for n in c["rules"]]; kind = "temporal"
        else:
            parts = [_base_rule(h)]; kind = "single"
        rules.append({"rule_id": pv["rule_id"], "target": pv["target"], "conf": float(pv["oof_precision"]), "file": os.path.basename(fp),
                      "kind": kind, "parts": parts})
    return rules

# ---------------- matcher ----------------
def event_match(part, e):
    if int(e.get("event_id")) not in PROC_EIDS: return False
    for kind, v in part["sel"]:
        if kind == "img_end":
            if not ("\\" + (e.get("image_name") or "")).lower().endswith(v): return False
        elif kind == "cmd_re":
            if not v.search(e.get("command_line") or ""): return False
        elif kind == "eid":
            if int(e.get("event_id")) != v: return False
    return True

def window_match(rule, events):
    return all(any(event_match(p, e) for e in events) for p in rule["parts"])

def score(rules, events):
    hit = [r for r in rules if window_match(r, events)]
    p = max([r["conf"] for r in hit], default=0.0)
    pt = {t: max([r["conf"] for r in hit if r["target"] == t], default=0.0) for t in TTPS}
    return p, pt, [r["rule_id"] for r in hit]

def load_windows(root, ids):
    want = set(ids); out = {}
    with open(os.path.join(root, "data", "processed", "windows.jsonl"), encoding="utf-8") as fh:
        for l in fh:
            w = json.loads(l)
            if w["window_id"] in want: out[w["window_id"]] = w["events"]
    assert set(out) == want
    return out

# ---------------- chay ----------------
def main(root="."):
    print("checksum dataset:", check_dataset(root))
    rules = load_sigma(root)
    meta = load_all_meta(root)
    W = load_windows(root, [w["window_id"] for s in SPLITS for w in meta[s]])
    # 1. matcher Sigma == vi tu luat tren Train (provenance chi dung de DOI CHIEU)
    import predicates as Pd
    P = json.load(open(os.path.join(root, OUT, "rules_provenance.json"), encoding="utf-8"))
    by_id = {r["id"]: r for r in P["rules"]}
    eq = {}
    for r in rules:
        pr = by_id[r["rule_id"]]; atoms = [(a[0], tuple(a[1]) if a[0] == "imgtok" else a[1]) for a in pr["atoms"]]
        res = {}
        for s in SPLITS:
            a = np.array([window_match(r, W[w["window_id"]]) for w in meta[s]]); b = np.array([Pd.match([(x, True) for x in atoms], W[w["window_id"]]) for w in meta[s]])
            res[s] = int((a != b).sum())
        sup = {meta["train"][i]["window_id"] for i, w in enumerate(meta["train"]) if window_match(r, W[w["window_id"]])}
        eq[r["rule_id"]] = {"train_mismatch": res["train"], "train_support_equal_provenance": sup == set(pr["support_windows"]),
                            "test_mismatch_diagnostic": {s: res[s] for s in TEST_SPLITS}}
    # 2. du doan
    preds, hits = {}, {}
    for s in SPLITS:
        preds[s], hits[s] = {}, {}
        for w in meta[s]:
            p, pt, h = score(rules, W[w["window_id"]])
            preds[s][w["window_id"]] = {"p": p, "p_ttp": pt}; hits[s][w["window_id"]] = h
        write_preds(root, "rules", s, meta[s], preds[s])
    st = early_starts(root, meta)
    early = {s: {k: {wid: score(rules, W[wid][i0:i0 + k])[0] for wid, (i0, _) in byw.items()} for k in EARLY_KS} for s, byw in st.items()}
    y = np.array([w["window_malicious"] for w in meta["train"]], bool); pb = np.array([preds["train"][w["window_id"]]["p"] for w in meta["train"]]) >= 0.5
    f1 = lambda y, p: 2 * (p & y).sum() / max(1, 2 * (p & y).sum() + (p & ~y).sum() + (~p & y).sum())
    ttp_f1 = {t: float(f1(np.array([t in w["window_ttps"] for w in meta["train"]]), np.array([preds["train"][w["window_id"]]["p_ttp"][t] for w in meta["train"]]) >= 0.5)) for t in TTPS}
    thr = {"binary": 0.5, "binary_train_oof_f1": float(f1(y, pb)), "binary_rule": "co dinh 0.5 = co luat khop (dat truoc test)",
           "ttp": {t: 0.5 for t in TTPS}, "ttp_train_oof_f1": ttp_f1, "note": "F1 Train IN-SAMPLE (luat quy nap tu toan Train)"}
    res = evaluate("rules", meta, {s: preds[s] for s in TEST_SPLITS}, thr, root=root, early=early)
    res.update(engine="chi-luat: rules/sigma/*.yml (11 luat, RIPPER tren Train) qua matcher Sigma noi bo", n_rules=len(rules),
               sigma_equivalence=eq, acceptance={"one_pred_per_window_no_leak": check_predictions(meta, {s: preds[s] for s in TEST_SPLITS})["ok"],
                                                  "thresholds": "co dinh 0.5, dat truoc khi cham test"})
    os.makedirs(os.path.join(root, OUT, "eval"), exist_ok=True)
    with open(os.path.join(root, OUT, "eval", "rules.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(root, OUT, "eval", "rules.md"), "w", encoding="utf-8", newline="\n") as f: f.write(render_markdown(res))
    # 3. bang tung luat
    hn = hn_signatures(root, {w["run_id"] for w in meta["t_hard"]})
    per = {}
    for r in rules:
        row = {"target": r["target"], "file": r["file"]}
        for s in SPLITS:
            tp = fp = 0; sig = Counter()
            for w in meta[s]:
                if r["rule_id"] not in hits[s][w["window_id"]]: continue
                pos = w["window_malicious"] if r["target"] == "bin" else (r["target"] in w["window_ttps"])
                tp += bool(pos); fp += not pos
                if s == "t_hard": sig[hn[w["run_id"]][0]] += 1
            row[s] = {"tp": tp, "fp": fp}
            if s == "t_hard": row["t_hard_fp_by_signature"] = dict(sig)
        per[r["rule_id"]] = row
    with open(os.path.join(root, OUT, "per_rule.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(per, f, indent=1)
    print("matcher Sigma == vi tu luat tren Train:", all(v["train_mismatch"] == 0 and v["train_support_equal_provenance"] for v in eq.values()),
          {k: v["train_mismatch"] for k, v in eq.items()})
    print("lech tren tap test (chan doan):", {k: v["test_mismatch_diagnostic"] for k, v in eq.items() if any(v["test_mismatch_diagnostic"].values())})
    S = res["splits"]
    print(f"T-clean F1 {S['t_clean']['tuned']['f1']['point']:.3f} | T-hard FP {S['t_hard']['tuned']['fp']}/{S['t_hard']['n']} | T-novel F1 {S['t_novel']['tuned']['f1']['point']:.3f}")
    return res, per

if __name__ == "__main__":
    main(".")
