#!/usr/bin/env python3
"""VT-Guard Buoc 5 - B1: TF-IDF + Logistic Regression (docs/STEP5-BRIEF.md muc 4.2), kem B1-raw va ablation.

Tai lieu cua so = noi token cac event theo thu tu thoi gian (windows.jsonl cua dataset dong bang).
Token moi event: img=<image_name>, eid=<event_id>, c:<token dong lenh qua featurize.norm_cmd>
(tu dataset-v1.1, norm_cmd da gom canon_cmd: basename file thuc thi, bo chuyen huong, bo duoi .exe).
Khong dung text tho, khong dung parent_image_name.
- Bien the: tfidf (TfidfVectorizer word 1-2 gram, min_df=2, IDF + L2) va raw (CountVectorizer, dem tho, khong IDF,
  khong chuan hoa).
- Ablation: (a) du; (b) bo image_name + parent_image_name (B1 khong dung parent, nen la bo token img=; token dong
  lenh van giu - la hanh vi); (c) chi event trong cay tien trinh (event_origin == "own"; event nen bi che) - mat na lay tu
  cay tien trinh = chinh co che gan nhan -> ro nhan theo cau truc, CHI dung de so T-hard voi (a);
  (cp = c') che event nen mot-phia da biet (common.is_known_one_sided_bg), bao du 3 tap.
- LogisticRegression(class_weight="balanced", liblinear); da nhan: mot bo phan loai moi TTP (one-vs-rest).
- C chon tren Train bang CV 5 fold theo nhom (evaluate.cv_folds), toi da PR-AUC OOF; vectorizer fit LAI trong tung
  fold. Nguong chon tren OOF (evaluate.choose_thresholds), KHOA; mo hinh cuoi fit tren toan Train, cham test MOT lan.
Chay: python src/baselines/b1_tfidf_lr.py [--variants tfidf,raw] [--ablations a,b,c]
"""
import argparse, json, os, re, sys

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "eval")); sys.path.insert(0, os.path.join(HERE, "..", "dataset"))
from common import window_events, is_known_one_sided_bg
from evaluate import (check_dataset, load_all_meta, evaluate, render_markdown, write_preds, check_predictions,
                      cv_folds, choose_thresholds, TTPS, SPLITS, TEST_SPLITS)
from bootstrap import average_precision, roc_auc, SEED
from featurize import norm_cmd

TOK_RE = re.compile(r"[a-z0-9_.<>/\\-]+")
LEAK_RE = re.compile(r"atomic|invoke-|\bt10\d\d|\bt1\d{3}\b|vt-?guard", re.I)
C_GRID = [0.01, 0.1, 1.0, 10.0, 100.0]
ABLATIONS = {"a": "du", "b": "bo image_name + parent_image_name", "c": "chi event cay tien trinh (ro nhan theo cau truc - chi bao T-hard)",
             "cp": "che event nen mot-phia da biet (ESENT/Directory Service, svchost->rundll32 COM)"}

def event_tokens(e, use_img=True):
    toks = ([f"img={e['image_name'] or 'none'}"] if use_img else []) + [f"eid={e['event_id']}"]
    if e.get("command_line"):
        toks += ["c:" + t for t in TOK_RE.findall(norm_cmd(e["command_line"]))]
    return toks

def build_docs(wev, ablation):
    docs = {}
    for wid, (ev, origin) in wev.items():
        keep = [e for e, o in zip(ev, origin) if (ablation != "c" or o == "own") and not (ablation == "cp" and is_known_one_sided_bg(e, o))]
        docs[wid] = " ".join(" ".join(event_tokens(e, use_img=(ablation != "b"))) for e in keep)
    return docs

def make_vec(kind):
    kw = dict(token_pattern=r"\S+", lowercase=False, ngram_range=(1, 2), min_df=2)
    return TfidfVectorizer(norm="l2", use_idf=True, **kw) if kind == "tfidf" else CountVectorizer(**kw)

def make_clf(C):
    return LogisticRegression(C=C, class_weight="balanced", solver="liblinear", max_iter=5000, random_state=SEED)

def fit_predict(kind, C, docs_tr, Y_tr, docs_te):
    vec = make_vec(kind); Xtr = vec.fit_transform(docs_tr); Xte = vec.transform(docs_te)
    out = {}
    for k, y in Y_tr.items():
        if y.min() == y.max(): out[k] = np.full(Xte.shape[0], float(y[0])); continue
        out[k] = make_clf(C).fit(Xtr, y).predict_proba(Xte)[:, 1]
    return out

def oof(kind, C, docs, Y, folds):
    P = {k: np.zeros(len(docs)) for k in Y}
    for tr, va in folds:
        p = fit_predict(kind, C, docs[tr], {k: y[tr] for k, y in Y.items()}, docs[va])
        for k in Y: P[k][va] = p[k]
    return P

def run(kind, ablation, root, meta, docs, folds):
    model = f"b1_{kind}_{ablation}"
    tr = meta["train"]
    d_tr = np.array([docs[w["window_id"]] for w in tr], dtype=object)
    Y = {"bin": np.array([w["window_malicious"] for w in tr], int),
         **{t: np.array([t in w["window_ttps"] for w in tr], int) for t in TTPS}}
    grid = []
    for C in C_GRID:
        p = oof(kind, C, d_tr, {"bin": Y["bin"]}, folds)["bin"]
        grid.append({"C": C, "oof_pr_auc": round(average_precision(Y["bin"], p), 4), "oof_roc_auc": round(roc_auc(Y["bin"], p), 4)})
    C = max(grid, key=lambda g: (g["oof_pr_auc"], -g["C"]))["C"]
    P_oof = oof(kind, C, d_tr, Y, folds)
    oof_pred = {w["window_id"]: {"p": float(P_oof["bin"][i]), "p_ttp": {t: float(P_oof[t][i]) for t in TTPS}} for i, w in enumerate(tr)}
    thr = choose_thresholds(tr, oof_pred)
    preds = {"train": oof_pred}
    d_te_all = {s: np.array([docs[w["window_id"]] for w in meta[s]], dtype=object) for s in TEST_SPLITS}
    for s in TEST_SPLITS:
        p = fit_predict(kind, C, d_tr, Y, d_te_all[s])
        preds[s] = {w["window_id"]: {"p": float(p["bin"][i]), "p_ttp": {t: float(p[t][i]) for t in TTPS}} for i, w in enumerate(meta[s])}
    res = evaluate(model, meta, {s: preds[s] for s in TEST_SPLITS}, thr, root=root)
    vec = make_vec(kind); X = vec.fit_transform(d_tr); clf = make_clf(C).fit(X, Y["bin"])
    names = vec.get_feature_names_out(); coef = clf.coef_[0]; o = np.argsort(coef)
    res.update(variant=kind, ablation=ablation, ablation_desc=ABLATIONS[ablation], C_grid=grid, C=C,
               n_features=int(len(names)), vocab_leak_tokens=[v for v in names if LEAK_RE.search(v)][:20],
               top_pos_features=[(names[i], round(float(coef[i]), 3)) for i in o[::-1][:10]],
               top_neg_features=[(names[i], round(float(coef[i]), 3)) for i in o[:10]],
               acceptance={"one_pred_per_window_no_leak": check_predictions(meta, {s: preds[s] for s in TEST_SPLITS})["ok"],
                           "vectorizer_fit_on": "train only (refit per CV fold)",
                           "features_used": ["image_name" if ablation != "b" else None, "event_id", "command_line (norm_cmd)"]})
    for s in SPLITS: write_preds(root, model, s, meta[s], preds[s])
    with open(os.path.join(root, "reports", "step5", f"{model}.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(root, "reports", "step5", f"{model}.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_markdown(res))
    return model, res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--variants", default="tfidf,raw")
    ap.add_argument("--ablations", default="a,b,c,cp")
    a = ap.parse_args()
    print("checksum dataset (so voi reports/dataset_stats.json):", check_dataset(a.root))
    os.makedirs(os.path.join(a.root, "reports", "step5"), exist_ok=True)
    meta = load_all_meta(a.root)
    wev = window_events(a.root, [w["window_id"] for s in SPLITS for w in meta[s]])
    folds = cv_folds(meta["train"], root=a.root)
    for ab in a.ablations.split(","):
        docs = build_docs(wev, ab)
        for kind in a.variants.split(","):
            model, res = run(kind, ab, a.root, meta, docs, folds)
            print(f"[{model}] C={res['C']} | dac trung {res['n_features']} | token nghi ro ri {res['vocab_leak_tokens']} | "
                  f"kiem tra {res['acceptance']['one_pred_per_window_no_leak']}")

if __name__ == "__main__":
    main()
