#!/usr/bin/env python3
"""VT-Guard Buoc 5 - B1: TF-IDF + Logistic Regression (docs/STEP5-BRIEF.md muc 4.2), kem bien the B1-raw.

Tai lieu cua so = noi token cac event theo thu tu thoi gian. Token moi event:
  img=<image_name>, eid=<event_id>, c:<token command_line da CHUAN HOA nhu featurize.norm_cmd>
  (chu thuong, bo nhay, GUID/hex/so -> ky hieu). Khong dung text tho.
- B1 (b1_tfidf_lr): TfidfVectorizer word 1-2 gram, min_df=2, IDF + chuan L2 -> trung lap do dai.
- B1-raw (b1_raw_lr): CountVectorizer cung token, dem THO, khong IDF, khong chuan hoa -> de chung minh
  rang khong chuan hoa thi mo hinh hoc do dai cua so.
- LogisticRegression(class_weight="balanced"); da nhan: mot bo phan loai rieng moi TTP (one-vs-rest).
- C chon tren Train bang CV 5 fold theo nhom (evaluate.cv_folds), toi da PR-AUC out-of-fold; vectorizer
  fit LAI trong tung fold (IDF khong thay fold kiem dinh). Nguong chon tren OOF (evaluate.choose_thresholds).
  Mo hinh cuoi fit tren toan bo Train, cham test MOT lan.
- B1-canon (b1_canon_lr): nhu B1 nhung dong lenh qua common.canon_cmd TRUOC norm_cmd: bo duong dan file
  thuc thi dau dong lenh (-> basename), bo chuyen huong (>nul, 2>&1, 1>, 2>, >>) va toan tu & && | ||.
  Ap dong nhat moi event. Muc dich: dinh luong phan ket qua nho dau vet bo sinh du lieu (hard-negative
  goi C:/Windows/System32/cmd.exe (duong dan day du) kem >nul 2>&1, ART goi "cmd.exe").
- Do do nhay do dai (chi chan doan, n_events KHONG la feature): tuong quan Spearman diem~n_events tren
  cua so am, FPR cua so ngan (<64) vs du 64, va ROC-AUC cua rieng n_events lam diem (moc tham chieu).
Chay: python src/baselines/b1_tfidf_lr.py
"""
import json, os, re, sys

import numpy as np
from scipy.stats import spearmanr
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "eval")); sys.path.insert(0, os.path.join(HERE, "..", "dataset"))
from common import window_events, canon_cmd
from evaluate import (check_dataset, load_all_meta, evaluate, render_markdown, write_preds, check_predictions,
                      cv_folds, choose_thresholds, TTPS, SPLITS, TEST_SPLITS, SPLIT_NAME)
from bootstrap import average_precision, roc_auc, SEED
from featurize import norm_cmd

TOK_RE = re.compile(r"[a-z0-9_.<>/\\-]+")
LEAK_RE = re.compile(r"atomic|invoke-|\bt10\d\d|\bt1\d{3}\b|vt-?guard", re.I)
C_GRID = [0.01, 0.1, 1.0, 10.0, 100.0]

def event_tokens(e, canon=False):
    toks = [f"img={e['image_name'] or 'none'}", f"eid={e['event_id']}"]
    if e.get("command_line"):
        c = canon_cmd(e["command_line"]) if canon else e["command_line"]
        toks += ["c:" + t for t in TOK_RE.findall(norm_cmd(c))]
    return toks

def make_vec(kind):
    kw = dict(token_pattern=r"\S+", lowercase=False, ngram_range=(1, 2), min_df=2)
    return TfidfVectorizer(norm="l2", use_idf=True, **kw) if kind == "tfidf" else CountVectorizer(**kw)

def make_clf(C):
    return LogisticRegression(C=C, class_weight="balanced", solver="liblinear", max_iter=5000, random_state=SEED)

def fit_predict(kind, C, docs_tr, Y_tr, docs_te):
    """Y_tr: {target: y}. Tra ve {target: p} va vectorizer."""
    vec = make_vec(kind); Xtr = vec.fit_transform(docs_tr); Xte = vec.transform(docs_te)
    out = {}
    for k, y in Y_tr.items():
        if y.min() == y.max(): out[k] = np.full(Xte.shape[0], float(y[0])); continue
        out[k] = make_clf(C).fit(Xtr, y).predict_proba(Xte)[:, 1]
    return out, vec

def oof(kind, C, docs, Y, folds):
    P = {k: np.zeros(len(docs)) for k in Y}
    for tr, va in folds:
        p, _ = fit_predict(kind, C, docs[tr], {k: y[tr] for k, y in Y.items()}, docs[va])
        for k in Y: P[k][va] = p[k]
    return P

def length_probe(meta, preds, thr):
    out = {}
    for s in TEST_SPLITS:
        M = meta[s]
        n = np.array([w["n_events"] for w in M]); y = np.array([w["window_malicious"] for w in M], bool)
        p = np.array([preds[s][w["window_id"]]["p"] for w in M])
        neg = ~y; short = n < 64
        r = spearmanr(p[neg], n[neg]).statistic if neg.sum() > 2 else None
        out[s] = {"spearman_score_vs_len_negatives": None if r is None or np.isnan(r) else round(float(r), 3),
                  "fpr_short_neg": round(float((p[neg & short] >= thr).mean()), 3) if (neg & short).any() else None,
                  "n_short_neg": int((neg & short).sum()),
                  "fpr_full_neg": round(float((p[neg & ~short] >= thr).mean()), 3) if (neg & ~short).any() else None,
                  "n_full_neg": int((neg & ~short).sum()),
                  "mean_score_short_neg": round(float(p[neg & short].mean()), 3) if (neg & short).any() else None,
                  "mean_score_full_neg": round(float(p[neg & ~short].mean()), 3) if (neg & ~short).any() else None,
                  "len_only_roc_auc": None if s == "t_hard" else (lambda v: None if v is None else round(v, 3))(roc_auc(y, n.astype(float)))}
    return out

def run(kind, model, root, meta, docs, folds):
    tr = meta["train"]
    d_tr = np.array([docs[w["window_id"]] for w in tr], dtype=object)
    Y = {"bin": np.array([w["window_malicious"] for w in tr], int),
         **{t: np.array([t in w["window_ttps"] for w in tr], int) for t in TTPS}}
    # chon C theo PR-AUC OOF cua bai nhi phan
    grid = []
    for C in C_GRID:
        p = oof(kind, C, d_tr, {"bin": Y["bin"]}, folds)["bin"]
        grid.append({"C": C, "oof_pr_auc": round(average_precision(Y["bin"], p), 4), "oof_roc_auc": round(roc_auc(Y["bin"], p), 4)})
    best = max(grid, key=lambda g: (g["oof_pr_auc"], -g["C"]))
    C = best["C"]
    P_oof = oof(kind, C, d_tr, Y, folds)
    oof_pred = {w["window_id"]: {"p": float(P_oof["bin"][i]), "p_ttp": {t: float(P_oof[t][i]) for t in TTPS}} for i, w in enumerate(tr)}
    thr = choose_thresholds(tr, oof_pred)
    # mo hinh cuoi tren toan Train, cham test mot lan
    preds = {"train": oof_pred}
    vec = None
    for s in TEST_SPLITS:
        d_te = np.array([docs[w["window_id"]] for w in meta[s]], dtype=object)
        p, vec = fit_predict(kind, C, d_tr, Y, d_te)
        preds[s] = {w["window_id"]: {"p": float(p["bin"][i]), "p_ttp": {t: float(p[t][i]) for t in TTPS}} for i, w in enumerate(meta[s])}
    res = evaluate(model, meta, {s: preds[s] for s in TEST_SPLITS}, thr, root=root)
    vocab = vec.get_feature_names_out()
    res.update(C_grid=grid, C=C, vectorizer=kind, n_features=int(len(vocab)),
               vocab_leak_tokens=[v for v in vocab if LEAK_RE.search(v)][:20],
               length_probe=length_probe(meta, preds, thr["binary"]),
               acceptance={"one_pred_per_window_no_leak": check_predictions(meta, {s: preds[s] for s in TEST_SPLITS})["ok"],
                           "vectorizer_fit_on": "train only (refit per CV fold)"})
    # trong so lon nhat (tin hieu mo hinh dua vao) - fit lai tren Train de doc he so
    vec2 = make_vec(kind); X = vec2.fit_transform(d_tr); clf = make_clf(C).fit(X, Y["bin"])
    coef = clf.coef_[0]; names = vec2.get_feature_names_out(); o = np.argsort(coef)
    res["top_pos_features"] = [(names[i], round(float(coef[i]), 3)) for i in o[::-1][:15]]
    res["top_neg_features"] = [(names[i], round(float(coef[i]), 3)) for i in o[:10]]
    for s in SPLITS: write_preds(root, model, s, meta[s], preds[s])
    os.makedirs(os.path.join(root, "reports", "step5"), exist_ok=True)
    with open(os.path.join(root, "reports", "step5", f"{model}.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    md = render_markdown(res)
    with open(os.path.join(root, "reports", "step5", f"{model}.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    return res, md

def main(root="."):
    print("checksum dataset (so voi reports/dataset_stats.json):", check_dataset(root))
    meta = load_all_meta(root)
    wev = window_events(root, [w["window_id"] for s in SPLITS for w in meta[s]])
    docs = {wid: " ".join(" ".join(event_tokens(e)) for e in ev) for wid, (ev, _) in wev.items()}
    docs_c = {wid: " ".join(" ".join(event_tokens(e, canon=True)) for e in ev) for wid, (ev, _) in wev.items()}
    folds = cv_folds(meta["train"], root=root)
    out = {}
    for kind, model, dd in (("tfidf", "b1_tfidf_lr", docs), ("raw", "b1_raw_lr", docs), ("tfidf", "b1_canon_lr", docs_c)):
        res, md = run(kind, model, root, meta, dd, folds)
        out[model] = res
        print(md)
        print(f"[{model}] C grid (OOF):", res["C_grid"], "-> C =", res["C"], "| so dac trung:", res["n_features"],
              "| token nghi ro ri:", res["vocab_leak_tokens"])
        print(f"[{model}] dac trung trong so duong lon nhat:", res["top_pos_features"][:10])
        print(f"[{model}] dac trung trong so am lon nhat:", res["top_neg_features"][:6])
        print(f"[{model}] kiem tra:", res["acceptance"], "\n")
    print("== So sanh B1 / B1-raw / B1-canon (nguong khoa tren Train OOF; CI bootstrap 95%) ==")
    f = lambda c: "-" if c is None or c.get("point") is None else f"{c['point']:.3f} [{c['lo']:.3f},{c['hi']:.3f}]"
    print("model        | T-clean F1            | T-clean PR-AUC        | T-hard FPR (FP/87)          | FPR co cmd.exe | FPR khong cmd | T-novel F1            | T-novel PR-AUC        | macro-F1 TTP clean/novel | T1003 phien novel")
    for model, res in out.items():
        S = res["splits"]; h = S["t_hard"]["tuned"]; cm = h["fpr_by_cmd"]
        print(f"{model:12s} | {f(S['t_clean']['tuned']['f1'])} | {f(S['t_clean']['pr_auc'])} | {f(h['fpr'])} ({h['fp']}) | "
              f"{cm.get('co cmd.exe', {}).get('fp')}/{cm.get('co cmd.exe', {}).get('n')} | {cm.get('khong cmd.exe', {}).get('fp')}/{cm.get('khong cmd.exe', {}).get('n')} | "
              f"{f(S['t_novel']['tuned']['f1'])} | {f(S['t_novel']['pr_auc'])} | "
              f"{S['t_clean']['ttp_tuned']['macro_f1']['point']:.3f}/{S['t_novel']['ttp_tuned']['macro_f1']['point']:.3f} | "
              f"{S['t_novel']['tuned']['ntds_session_recall']['binary']['detected']}/6")
    print()
    print("== Do nhay do dai cua so (chi chan doan; n_events khong la feature) ==")
    print("model        tap      spearman(diem,len|am)  FPR am ngan(n)   FPR am du64(n)   diem TB am ngan/du   ROC-AUC chi do dai")
    for model, res in out.items():
        for s, v in res["length_probe"].items():
            print(f"{model:12s} {SPLIT_NAME[s]:8s} {str(v['spearman_score_vs_len_negatives']):>8s}"
                  f"   {str(v['fpr_short_neg'])}({v['n_short_neg']})   {str(v['fpr_full_neg'])}({v['n_full_neg']})"
                  f"   {v['mean_score_short_neg']}/{v['mean_score_full_neg']}   {v['len_only_roc_auc']}")

if __name__ == "__main__":
    main()
