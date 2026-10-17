#!/usr/bin/env python3
"""VT-Guard Buoc 8 - hop nhat AI (VT-Seq-ens) + chi-luat (docs/STEP8-BRIEF.md muc 3-4). HOC / CHON CHI TREN OOF Train.

Nguon OOF (khong doc tap test, KHONG doc rules_train.jsonl in-sample):
  AI   : reports/preds/vtseq_M3_ens_train.jsonl - trung binh xac suat OOF 5 seed M3 (reports/step6/m2/oof/M3_s<seed>.jsonl,
         CV 5 fold theo nhom Buoc 6); p = diem nhi phan da chon (p_bin' = max(p_bin, max_k p_ttp)), p_k = xac suat TTP k.
         Nguong khoa Buoc 6 (reports/step6/m3/sel/vtseq_M3_ens.json): tau (FPR <= 1% OOF), tau_k (max-F1 OOF).
  Luat : reports/preds/rules_oof_train.jsonl - luat quy nap lai trong tung fold (Buoc 7, src/rules/oof.py).
         r = 1 neu co luat khop (p_malicious >= 0.5; cung dinh nghia chi-luat Buoc 7), r_k = 1 neu luat theo TTP k khop.
Chien luoc (dat truoc, it tham so):
  F0 chi-AI    : p >= tau, p_k >= tau_k (nguong Buoc 6).            0 tham so hoc
  F1 chi-luat  : r, r_k (nguong 0.5 Buoc 7).                         0 tham so hoc
  F2 OR        : (p >= tau) OR r ; (p_k >= tau_k) OR r_k. Diem xep hang s = max(p, r).   0 tham so hoc
  F3 boost     : s = p + beta*r, s_k = p_k + beta*r_k, beta in {0.1, 0.2, 0.3} chon tren OOF (tieu chi muc 4);
                 nguong s: FPR <= 1% tren cua so am OOF; nguong s_k: max-F1 OOF (nhu Buoc 6).
  F4 stacking  : LogisticRegression (C=1, lbfgs) - nhi phan tren [logit p, r, r_1..r_5]; TTP k tren [logit p_k, r, r_1..r_5]
                 (7 dac trung). Diem OOF cua F4 bang CV LONG theo nhom phien (evaluate.cv_folds) tren OOF: moi fold cham bang
                 mo hinh hoc tren 4 fold con lai. Nguong: FPR <= 1% (nhi phan) / max-F1 (TTP) tren diem OOF long.
                 Mo hinh dung cho test = fit tren toan OOF.
Chon cau hinh (muc 4): (1) macro-F1 TTP OOF, (2) PR-AUC nhi phan OOF, (3) FPR OOF tren cua so hard_negative; ngang nhau neu
  |chenh| <= do lech chuan bootstrap cua hieu so (1000, seed 1337, theo cua so) -> chon it tham so hon (F2 < F3 < F4).
"""
import json, math, os, sys

import numpy as np
from sklearn.linear_model import LogisticRegression

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("../eval", "../models"): sys.path.insert(0, os.path.join(HERE, d))
from evaluate import check_dataset, load_meta, cv_folds, TTPS          # noqa: E402
from bootstrap import best_f1_threshold, average_precision, SEED        # noqa: E402

AI_OOF = os.path.join("reports", "preds", "vtseq_M3_ens_train.jsonl")
RULES_OOF = os.path.join("reports", "preds", "rules_oof_train.jsonl")
RULES_INSAMPLE = os.path.join("reports", "preds", "rules_train.jsonl")       # CHI cho do nhay mo ta, KHONG hoc / chon
AI_SEL = os.path.join("reports", "step6", "m3", "sel", "vtseq_M3_ens.json")
BETAS = (0.1, 0.2, 0.3)
FPR_TARGET = 0.01
N_PARAMS = {"F2": 0, "F3": 1, "F4": 6 * 8}        # F4: 6 hoi quy logistic x (7 he so + chan)
ORDER = ("F2", "F3", "F4")

# ---------------- du lieu ----------------
def read_preds(path, order):
    rows = {}
    with open(path, encoding="utf-8") as fh:
        for l in fh:
            r = json.loads(l); rows[r["window_id"]] = r
    assert set(rows) == set(order), path
    p = np.array([rows[w]["p_malicious"] for w in order], float)
    pk = np.array([[rows[w]["p_ttp"][t] for t in TTPS] for w in order], float)
    return p, pk

def load_oof(root="."):
    """OOF Train: meta, AI (p, p_k), luat (r, r_k), nhan, mat na hard_negative, nguong khoa AI."""
    check_dataset(root)
    meta = load_meta(root, "train"); order = [w["window_id"] for w in meta]
    p, pk = read_preds(os.path.join(root, AI_OOF), order)
    rp, rpk = read_preds(os.path.join(root, RULES_OOF), order)
    sel = json.load(open(os.path.join(root, AI_SEL), encoding="utf-8"))
    return {"meta": meta, "p": p, "pk": pk, "r": (rp >= 0.5).astype(float), "rk": (rpk >= 0.5).astype(float),
            "y": np.array([bool(w["window_malicious"]) for w in meta]), "yk": np.array([[t in w["window_ttps"] for t in TTPS] for w in meta]),
            "hn": np.array([w["window_class"] == "hard_negative" for w in meta]),
            "tau": float(sel["binary"]), "tau_k": np.array([sel["ttp"][t] for t in TTPS], float), "ai_binary_score": sel["binary_score"]}

RULES_PROV = os.path.join("reports", "step7", "rules_provenance.json")

def final_rule_ttps(root="."):
    """TTP co it nhat mot luat theo TTP trong bo luat CUOI (Buoc 7, quy nap tu Train) - thong tin Train, khong phai test."""
    P = json.load(open(os.path.join(root, RULES_PROV), encoding="utf-8"))
    return sorted({r["target"] for r in P["rules"] if r["target"] != "bin"})

def mask_rule_channels(D, ttps):
    """Bien the B: chi giu kenh luat theo TTP (r_k) cho TTP co luat trong bo luat cuoi; TTP khac r_k = 0 - de dac trung
    luat tren OOF giong luc chay test (bo luat fold co luat cho TTP ma bo luat cuoi khong co, vd T1016)."""
    E = dict(D); m = np.array([t in ttps for t in TTPS], float); E["rk"] = D["rk"] * m; E["rule_ttp_channels"] = list(ttps)
    return E

def with_rules(D, path, root="."):
    """Ban sao D voi r / r_k tu file luat khac (do nhay mo ta)."""
    order = [w["window_id"] for w in D["meta"]]; rp, rpk = read_preds(os.path.join(root, path), order)
    E = dict(D); E["r"] = (rp >= 0.5).astype(float); E["rk"] = (rpk >= 0.5).astype(float)
    if "rule_ttp_channels" in D: E = mask_rule_channels(E, D["rule_ttp_channels"])
    return E

# ---------------- nguong ----------------
def threshold_at_fpr(y, s, target=FPR_TARGET):
    neg = np.sort(np.asarray(s, float)[~np.asarray(y, bool)])[::-1]
    k = int(math.floor(target * len(neg)))
    return float(np.nextafter(neg[k], np.inf)) if k < len(neg) else float(neg.min())

def logit(x):
    x = np.clip(np.asarray(x, float), 1e-6, 1 - 1e-6); return np.log(x / (1 - x))

# ---------------- chien luoc ----------------
def scores(strategy, params, p, pk, r, rk):
    """-> (s nhi phan (n,), s TTP (n,5)) cho mot chien luoc da co tham so."""
    if strategy == "F0": return p, pk
    if strategy == "F1": return r, rk
    if strategy == "F2": return np.maximum(p, r), np.maximum(pk, rk)
    if strategy == "F3": b = params["beta"]; return p + b * r, pk + b * rk
    if strategy == "F4":
        Xb = np.column_stack([logit(p), r, rk])
        sb = params["models"]["bin"].predict_proba(Xb)[:, 1]
        sk = np.column_stack([params["models"][t].predict_proba(np.column_stack([logit(pk[:, j]), r, rk]))[:, 1] for j, t in enumerate(TTPS)])
        return sb, sk
    raise ValueError(strategy)

def decide(strategy, params, p, pk, r, rk):
    """-> (quyet dinh nhi phan, quyet dinh TTP (n,5), s, s_k)."""
    s, sk = scores(strategy, params, p, pk, r, rk)
    if strategy == "F0": return p >= params["tau"], pk >= params["tau_k"], s, sk
    if strategy == "F1": return r >= 0.5, rk >= 0.5, s, sk
    if strategy == "F2": return (p >= params["tau"]) | (r >= 0.5), (pk >= params["tau_k"]) | (rk >= 0.5), s, sk
    return s >= params["thr"], sk >= params["thr_k"], s, sk

def fit_lr(X, y):
    return LogisticRegression(C=1.0, solver="lbfgs", max_iter=2000, random_state=SEED).fit(X, y)

def fit_f4(p, pk, r, rk, y, yk):
    m = {"bin": fit_lr(np.column_stack([logit(p), r, rk]), y)}
    for j, t in enumerate(TTPS): m[t] = fit_lr(np.column_stack([logit(pk[:, j]), r, rk]), yk[:, j])
    return m

def thresholds_from(y, yk, s, sk):
    return {"thr": threshold_at_fpr(y, s), "thr_k": np.array([best_f1_threshold(yk[:, j], sk[:, j])[0] for j in range(len(TTPS))])}

def fit_strategy(strategy, D, folds, beta=None):
    """Tham so + diem OOF dung de CHAM chien luoc tren OOF.
    F0/F1/F2: khong hoc. F3: beta co dinh (vong chon beta o select_beta). F4: diem OOF bang CV long theo nhom."""
    p, pk, r, rk, y, yk = D["p"], D["pk"], D["r"], D["rk"], D["y"], D["yk"]
    if strategy in ("F0", "F2"): return {"tau": D["tau"], "tau_k": D["tau_k"]}, None
    if strategy == "F1": return {}, None
    if strategy == "F3":
        params = {"beta": beta}; s, sk = scores("F3", params, p, pk, r, rk)
        params.update(thresholds_from(y, yk, s, sk)); return params, None
    if strategy == "F4":
        sb = np.zeros(len(y)); sk = np.zeros((len(y), len(TTPS))); fold_of = np.full(len(y), -1)
        for fi, (tr, va) in enumerate(folds):
            assert not set(tr) & set(va)
            m = fit_f4(p[tr], pk[tr], r[tr], rk[tr], y[tr], yk[tr])
            sb[va], sk[va] = scores("F4", {"models": m}, p[va], pk[va], r[va], rk[va]); fold_of[va] = fi
        assert (fold_of >= 0).all()
        thr = thresholds_from(y, yk, sb, sk)
        final = fit_f4(p, pk, r, rk, y, yk)                       # mo hinh cho test (fit toan OOF)
        return {"models": final, **thr, "n_features": 7}, (sb, sk)
    raise ValueError(strategy)

# ---------------- danh gia tren OOF ----------------
def oof_metrics(D, strategy, params, nested=None):
    """Chi so OOF. nested = (s, s_k) diem OOF long cua F4 (khong cham F4 bang mo hinh vua hoc)."""
    if nested is not None:
        s, sk = nested; db, dk = s >= params["thr"], sk >= params["thr_k"]
    else:
        db, dk, s, sk = decide(strategy, params, D["p"], D["pk"], D["r"], D["rk"])
    return metrics_from(D, db, dk, s)

def metrics_from(D, db, dk, s, idx=None):
    y, yk, hn = D["y"], D["yk"], D["hn"]
    if idx is not None: y, yk, hn, db, dk, s = y[idx], yk[idx], hn[idx], db[idx], dk[idx], s[idx]
    f1 = []
    for j in range(len(TTPS)):
        tp = int((dk[:, j] & yk[:, j]).sum()); fp = int((dk[:, j] & ~yk[:, j]).sum()); fn = int((~dk[:, j] & yk[:, j]).sum())
        f1.append(2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 0.0)
    tp = int((db & y).sum()); fp = int((db & ~y).sum()); fn = int((~db & y).sum())
    return {"macro_f1_ttp": float(np.mean(f1)), "f1_ttp": dict(zip(TTPS, [float(x) for x in f1])),
            "pr_auc": float(average_precision(y, s)) if y.any() else float("nan"),
            "fpr_hard_negative": float(db[hn].mean()) if hn.any() else float("nan"), "fpr_neg": float(db[~y].mean()),
            "recall": float(db[y].mean()), "precision": tp / max(1, tp + fp), "f1_bin": 2 * tp / max(1, 2 * tp + fp + fn)}

def decisions_oof(D, strategy, params, nested=None):
    if nested is not None:
        s, sk = nested; return s >= params["thr"], sk >= params["thr_k"], s
    db, dk, s, _ = decide(strategy, params, D["p"], D["pk"], D["r"], D["rk"]); return db, dk, s

def paired_sd(D, a, b, metric, n_boot=1000, seed=SEED):
    """Do lech chuan bootstrap (theo cua so) cua hieu so metric(a) - metric(b); a, b = (db, dk, s)."""
    rng = np.random.default_rng(seed); n = len(D["y"]); d = []
    for _ in range(n_boot):
        i = rng.integers(0, n, n)
        ma, mb = metrics_from(D, *a, idx=i)[metric], metrics_from(D, *b, idx=i)[metric]
        if np.isfinite(ma) and np.isfinite(mb): d.append(ma - mb)
    return float(np.std(d, ddof=1))

def select_beta(D, folds):
    """beta cua F3 theo cung tieu chi thu tu (macro-F1 TTP, PR-AUC, -FPR HN) tren OOF; hoa -> beta nho hon."""
    res = {}
    for b in BETAS:
        prm, _ = fit_strategy("F3", D, folds, beta=b); res[b] = (prm, oof_metrics(D, "F3", prm))
    best = max(BETAS, key=lambda b: (round(res[b][1]["macro_f1_ttp"], 6), round(res[b][1]["pr_auc"], 6), -res[b][1]["fpr_hard_negative"], -b))
    return best, res

def select(D, folds):
    """Cham F0-F4 tren OOF + chon cau hinh theo muc 4 (ung vien F2-F4)."""
    out = {}
    for st in ("F0", "F1", "F2"):
        prm, nested = fit_strategy(st, D, folds); out[st] = {"params": prm, "nested": nested, "m": oof_metrics(D, st, prm)}
    beta, beta_res = select_beta(D, folds)
    out["F3"] = {"params": beta_res[beta][0], "nested": None, "m": beta_res[beta][1], "beta_grid": {b: v[1] for b, v in beta_res.items()}}
    prm, nested = fit_strategy("F4", D, folds); out["F4"] = {"params": prm, "nested": nested, "m": oof_metrics(D, "F4", prm, nested)}
    dec = {st: decisions_oof(D, st, out[st]["params"], out[st]["nested"]) for st in ORDER}
    pool = list(ORDER); steps = []
    for metric, sign in (("macro_f1_ttp", 1), ("pr_auc", 1), ("fpr_hard_negative", -1)):
        best = max(pool, key=lambda st: (sign * out[st]["m"][metric], -ORDER.index(st)))
        keep = []
        for st in pool:
            if st == best: keep.append(st); continue
            sd = paired_sd(D, dec[best], dec[st], metric)
            diff = abs(out[best]["m"][metric] - out[st]["m"][metric])
            if diff <= sd: keep.append(st)
            steps.append({"metric": metric, "best": best, "other": st, "abs_diff": round(diff, 4), "boot_sd": round(sd, 4), "tie": diff <= sd})
        pool = keep
        if len(pool) == 1: break
    chosen = min(pool, key=lambda st: ORDER.index(st))       # hoa -> it tham so hon
    return out, {"chosen": chosen, "pool_after_criteria": pool, "steps": steps}

def params_json(st, prm):
    o = {}
    for k, v in prm.items():
        if k == "models":
            o[k] = {t: {"coef": [round(float(c), 6) for c in m.coef_[0]], "intercept": round(float(m.intercept_[0]), 6)} for t, m in v.items()}
        elif isinstance(v, np.ndarray): o[k] = [round(float(x), 6) for x in v]
        else: o[k] = v
    return o

# ---------------- moc 1: bang OOF + de xuat + do nhay ----------------
def fmt(m):
    return (f"{m['macro_f1_ttp']:.3f} | " + " | ".join(f"{m['f1_ttp'][t]:.3f}" for t in TTPS) +
            f" | {m['pr_auc']:.3f} | {m['fpr_hard_negative']:.3f} | {m['fpr_neg']:.3f} | {m['recall']:.3f} | {m['f1_bin']:.3f}")

def run_variant(D, folds, root="."):
    out, sel = select(D, folds)
    E = with_rules(D, RULES_INSAMPLE, root)                   # do nhay MO TA (luat cuoi tren Train = in-sample)
    sens = {}
    for st in ORDER:
        db, dk, s_, _ = decide(st, out[st]["params"], E["p"], E["pk"], E["r"], E["rk"]); sens[st] = metrics_from(E, db, dk, s_)
    diff = {"r": int((E["r"] != D["r"]).sum()), "rk": {t: int((E["rk"][:, j] != D["rk"][:, j]).sum()) for j, t in enumerate(TTPS)}}
    return out, sel, sens, diff

def main(root="."):
    D0 = load_oof(root); folds = cv_folds(D0["meta"], root=root)
    keep = final_rule_ttps(root)
    V = {"A": ("tat ca kenh luat theo TTP (dinh nghia brief)", D0), "B": (f"chi kenh luat theo TTP co trong bo luat cuoi: {keep}", mask_rule_channels(D0, keep))}
    R = {k: run_variant(D, folds, root) for k, (_, D) in V.items()}
    hdr = "| Cau hinh | macro-F1 TTP | " + " | ".join(TTPS) + " | PR-AUC bin | FPR hard_neg | FPR am | Recall | F1 bin |"
    sep = "|---|" + "---|" * (len(TTPS) + 7)
    L = ["# VT-Guard Buoc 8 moc 1 - fusion AI + luat: CHI OOF Train (chua cham test)", "",
         f"Nguon OOF: AI `{AI_OOF.replace(os.sep, '/')}` (trung binh 5 seed M3, OOF Buoc 6; nguong khoa tau = {D0['tau']:.4f}, diem {D0['ai_binary_score']}), "
         f"luat `{RULES_OOF.replace(os.sep, '/')}` (luat quy nap lai trong tung fold, Buoc 7). KHONG dung `{RULES_INSAMPLE.replace(os.sep, '/')}` de hoc/chon "
         f"(chi cho do nhay mo ta). Train 483 cua so ({int(D0['y'].sum())} duong, {int(D0['hn'].sum())} hard_negative). Seed 1337.", "",
         "F0 chi-AI, F1 chi-luat: tham chieu. F2 OR (0 tham so). F3 s = p + beta*r (beta chon tren OOF trong {0.1, 0.2, 0.3}; nguong "
         "FPR <= 1% am OOF, TTP max-F1 OOF). F4 LR 7 dac trung, diem OOF bang CV long theo nhom phien.", ""]
    for k, (vdesc, D) in V.items():
        out, sel, sens, diff = R[k]
        desc = {"F0": "chi-AI (nguong Buoc 6)", "F1": "chi-luat (nguong 0.5)", "F2": "OR", "F3": f"boost beta = {out['F3']['params']['beta']}", "F4": "stacking LR (CV long)"}
        L += [f"## Bien the {k}: {vdesc}", "", "**OOF F0-F4**", "", hdr, sep]
        for st in ("F0", "F1", "F2", "F3", "F4"): L.append(f"| {st}: {desc[st]} | {fmt(out[st]['m'])} |")
        L += ["", "**F3 - luoi beta (OOF)**", "", hdr, sep]
        for b, m in out["F3"]["beta_grid"].items(): L.append(f"| F3 beta = {b} | {fmt(m)} |")
        L += ["", "**Chon theo muc 4 (ung vien F2-F4; ngang nhau neu |chenh| <= DLC bootstrap hieu so -> it tham so hon)**", "",
              "| Tieu chi | Tot nhat | So voi | |chenh| | DLC bootstrap | Ngang nhau? |", "|---|---|---|---|---|---|"]
        for s_ in sel["steps"]: L.append(f"| {s_['metric']} | {s_['best']} | {s_['other']} | {s_['abs_diff']} | {s_['boot_sd']} | {'co' if s_['tie'] else 'khong'} |")
        L += ["", f"-> chon **{sel['chosen']}** ({desc[sel['chosen']]}).", "",
              f"**Do nhay (CHI mo ta): thay luat fold bang luat cuoi tren Train (in-sample)** - r khac o {diff['r']}/483 cua so, r_k: {diff['rk']}; "
              "giu nguyen tham so/nguong da hoc (F4: mo hinh fit toan OOF -> in-sample).", "", hdr, sep]
        for st in ORDER:
            L.append(f"| {st} OOF (luat fold) | {fmt(out[st]['m'])} |"); L.append(f"| {st} luat cuoi (mo ta) | {fmt(sens[st])} |")
        L.append("")
    os.makedirs(os.path.join(root, "reports", "step8"), exist_ok=True)
    with open(os.path.join(root, "reports", "step8", "m1_oof.md"), "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(L))
    res = {"sources": {"ai_oof": AI_OOF, "rules_oof": RULES_OOF, "ai_selection": AI_SEL, "not_used_for_learning": RULES_INSAMPLE},
           "variants": {k: {"desc": V[k][0], "oof": {st: {"params": params_json(st, R[k][0][st]["params"]), "metrics": R[k][0][st]["m"]} for st in R[k][0]},
                            "f3_beta_grid": {str(b): m for b, m in R[k][0]["F3"]["beta_grid"].items()}, "selection": R[k][1],
                            "sensitivity_final_rules": {"diff": R[k][3], "metrics": R[k][2]}} for k in V}}
    with open(os.path.join(root, "reports", "step8", "m1_oof.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(res, f, indent=1)
    print("\n".join(L))
    return R

if __name__ == "__main__":
    main(".")
