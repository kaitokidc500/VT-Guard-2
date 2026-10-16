#!/usr/bin/env python3
"""VT-Guard Buoc 5 - B2: LightGBM tren dac trung tong hop moc cua so (docs/STEP5-BRIEF.md muc 4.3).

Moi cua so -> mot vector (KHONG dung thu tu chuoi), tinh tren event cua cua so (windows.jsonl dataset dong bang):
  - eid_<id>, img_<image_name>, par_<parent_image_name>, ch_<channel>: TI LE event mang gia tri (chia so event cua cua so);
    tap gia tri lay tu vocab.json (fit tren Train, token xuat hien o >= 2 phien Train); gia tri la -> <unk>.
  - img_distinct_ratio: so image_name phan biet / so event.
  - flag_network / flag_dns / flag_powershell / flag_security: ti le event co co tuong ung (nhu featurize).
  - dt_mean, dt_std: thong ke log(1 + dt giay) giua cac event lien tiep (theo ts_system).
  - host_role (one-hot).
  KHONG dung n_events / so dem tuyet doi (brief 4.5). KHONG dung tempo, user_role, variant: day la cau hinh orchestrator
  trong manifest, khong quan sat duoc trong log - va variant != "mixed" chi co o phien attack (ro nhan).
  KHONG dung command_line (B2 la baseline tong hop, khong van ban).
- Ablation: (a) du; (b) bo moi dac trung tu image_name + parent_image_name (img_*, par_*, img_distinct_ratio);
  (c) chi event cay tien trinh (ro nhan theo cau truc - chi bao T-hard); (cp) che event nen mot-phia da biet.
- Sieu tham so chon bang CV 5 fold theo nhom (evaluate.cv_folds, nhom chong thoi gian chua tron run_id), toi da PR-AUC OOF;
  nguong khoa tren OOF; mo hinh cuoi fit toan Train, cham test MOT lan. Da nhan: mot mo hinh moi TTP (cung sieu tham so).
- Neu khong import duoc lightgbm -> HistGradientBoostingClassifier (sklearn), ghi ro trong ket qua.
Chay: python src/baselines/b2_lgbm.py [--ablations a,b,c,cp]
"""
import argparse, json, math, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "eval")); sys.path.insert(0, os.path.join(HERE, "..", "dataset"))
from common import window_events, is_known_one_sided_bg
from evaluate import (check_dataset, load_all_meta, evaluate, render_markdown, write_preds, check_predictions,
                      cv_folds, choose_thresholds, early_starts, TTPS, SPLITS, TEST_SPLITS, EARLY_KS)
from bootstrap import average_precision, roc_auc, SEED
from featurize import token, ts

try:
    import lightgbm as lgb
    ENGINE = f"lightgbm {lgb.__version__}"
except ImportError:          # fallback theo brief
    lgb = None
    from sklearn.ensemble import HistGradientBoostingClassifier
    ENGINE = "sklearn HistGradientBoostingClassifier (fallback: khong import duoc lightgbm)"

ABLATIONS = {"a": "du", "b": "bo image_name + parent_image_name", "c": "chi event cay tien trinh (ro nhan theo cau truc - chi bao T-hard)",
             "cp": "che event nen mot-phia da biet (ESENT/Directory Service, svchost->rundll32 COM)"}
GRID = [{"num_leaves": nl, "min_child_samples": mc, "n_estimators": 300, "learning_rate": 0.05}
        for nl in (7, 15) for mc in (5, 20)]

class Featurizer:
    """Danh sach dac trung co dinh tu vocab.json (fit tren Train). ablation b bo nhom img_/par_."""
    def __init__(self, vocab, ablation):
        self.ab = ablation
        self.cats = {"event_id": "eid", "channel": "ch"}
        if ablation != "b": self.cats.update({"image_name": "img", "parent_image_name": "par"})
        self.vals = {f: [t for t in vocab[f] if t not in ("<pad>",)] for f in self.cats}   # gom <unk>, <none>
        self.vocab = vocab
        self.names = [f"{self.cats[f]}_{t}" for f in self.cats for t in self.vals[f]]
        if ablation != "b": self.names.append("img_distinct_ratio")
        self.names += ["flag_network", "flag_dns", "flag_powershell", "flag_security", "dt_mean", "dt_std",
                       "host_role_dc", "host_role_ws"]
        self.idx = {n: i for i, n in enumerate(self.names)}

    def keep(self, ev, origin):
        return [e for e, o in zip(ev, origin) if (self.ab != "c" or o == "own") and not (self.ab == "cp" and is_known_one_sided_bg(e, o))]

    def vector(self, ev, origin, host_role):
        x = np.zeros(len(self.names), np.float32)
        evs = self.keep(ev, origin); n = len(evs)
        hr = "dc" if host_role == "domain_controller" else "ws"
        x[self.idx[f"host_role_{hr}"]] = 1.0
        if n == 0: return x
        for e in evs:
            for f, pre in self.cats.items():
                t = token(f, e.get(f))
                if t not in self.vocab[f]: t = "<unk>"
                x[self.idx[f"{pre}_{t}"]] += 1.0 / n
            ch = e.get("channel") or ""
            x[self.idx["flag_network"]] += (e["event_id"] == 3 or e.get("dst_port") is not None) / n
            x[self.idx["flag_dns"]] += (e["event_id"] == 22 or bool(e.get("has_dns_query"))) / n
            x[self.idx["flag_powershell"]] += ("PowerShell" in ch) / n
            x[self.idx["flag_security"]] += (ch == "Security") / n
        if self.ab != "b": x[self.idx["img_distinct_ratio"]] = len({e.get("image_name") for e in evs}) / n
        t_ = [ts(e["ts"]) for e in evs]
        d = [math.log1p(max(0.0, (b - a).total_seconds())) for a, b in zip(t_, t_[1:])]
        if d: x[self.idx["dt_mean"]] = float(np.mean(d)); x[self.idx["dt_std"]] = float(np.std(d))
        return x

def make_clf(p):
    if lgb is not None:
        return lgb.LGBMClassifier(objective="binary", class_weight="balanced", subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                                  reg_lambda=1.0, random_state=SEED, n_jobs=1, deterministic=True, force_col_wise=True, verbose=-1, **p)
    return HistGradientBoostingClassifier(max_leaf_nodes=p["num_leaves"], min_samples_leaf=p["min_child_samples"],
                                          max_iter=p["n_estimators"], learning_rate=p["learning_rate"], class_weight="balanced",
                                          random_state=SEED)

def fit_all(p, X, Y):
    out = {}
    for k, y in Y.items():
        out[k] = float(y[0]) if y.min() == y.max() else make_clf(p).fit(X, y)
    return out

def predict_all(models, X):
    return {k: (np.full(X.shape[0], m) if isinstance(m, float) else m.predict_proba(X)[:, 1]) for k, m in models.items()}

def oof(p, X, Y, folds):
    P = {k: np.zeros(X.shape[0]) for k in Y}
    for tr, va in folds:
        pr = predict_all(fit_all(p, X[tr], {k: y[tr] for k, y in Y.items()}), X[va])
        for k in Y: P[k][va] = pr[k]
    return P

def run(ablation, root, meta, wev, folds, starts, vocab, host_role):
    model = f"b2_lgbm_{ablation}"
    fz = Featurizer(vocab, ablation)
    X = {s: np.stack([fz.vector(*wev[w["window_id"]], host_role[w["window_id"]]) for w in meta[s]]) for s in SPLITS}
    tr = meta["train"]
    Y = {"bin": np.array([w["window_malicious"] for w in tr], int), **{t: np.array([t in w["window_ttps"] for w in tr], int) for t in TTPS}}
    grid = []
    for p in GRID:
        pb = oof(p, X["train"], {"bin": Y["bin"]}, folds)["bin"]
        grid.append({**p, "oof_pr_auc": round(average_precision(Y["bin"], pb), 4), "oof_roc_auc": round(roc_auc(Y["bin"], pb), 4)})
    best = max(grid, key=lambda g: (g["oof_pr_auc"], -g["num_leaves"], g["min_child_samples"]))
    p = {k: best[k] for k in GRID[0]}
    P_oof = oof(p, X["train"], Y, folds)
    oof_pred = {w["window_id"]: {"p": float(P_oof["bin"][i]), "p_ttp": {t: float(P_oof[t][i]) for t in TTPS}} for i, w in enumerate(tr)}
    thr = choose_thresholds(tr, oof_pred)
    final = fit_all(p, X["train"], Y)
    preds = {"train": oof_pred}
    for s in TEST_SPLITS:
        pr = predict_all(final, X[s])
        preds[s] = {w["window_id"]: {"p": float(pr["bin"][i]), "p_ttp": {t: float(pr[t][i]) for t in TTPS}} for i, w in enumerate(meta[s])}
    early = {}
    for s, st in starts.items():
        early[s] = {}
        for k in EARLY_KS:
            ids = list(st)
            Xe = np.stack([fz.vector(wev[wid][0][i0:i0 + k], wev[wid][1][i0:i0 + k], host_role[wid]) for wid, (i0, _) in st.items()])
            early[s][k] = dict(zip(ids, predict_all({"bin": final["bin"]}, Xe)["bin"].astype(float)))
    res = evaluate(model, meta, {s: preds[s] for s in TEST_SPLITS}, thr, root=root, early=early)
    imp = []
    if lgb is not None and not isinstance(final["bin"], float):
        g = final["bin"].booster_.feature_importance(importance_type="gain"); o = np.argsort(-g)
        imp = [(fz.names[i], round(float(g[i]), 2)) for i in o[:15] if g[i] > 0]
    res.update(engine=ENGINE, ablation=ablation, ablation_desc=ABLATIONS[ablation], grid=grid, params=p, n_features=len(fz.names),
               top_importance_gain=imp,
               excluded_metadata=["n_events", "tempo", "user_role", "variant"],
               acceptance={"one_pred_per_window_no_leak": check_predictions(meta, {s: preds[s] for s in TEST_SPLITS})["ok"],
                           "vocab_from": "data/processed/vocab.json (fit Train, dataset dong bang)"})
    for s in SPLITS: write_preds(root, model, s, meta[s], preds[s])
    with open(os.path.join(root, "reports", "step5", f"{model}.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(root, "reports", "step5", f"{model}.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_markdown(res))
    return model, res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--ablations", default="a,b,c,cp")
    a = ap.parse_args()
    print("checksum dataset (so voi reports/dataset_stats.json):", check_dataset(a.root), "| engine:", ENGINE)
    meta = load_all_meta(a.root)
    vocab = json.load(open(os.path.join(a.root, "data", "processed", "vocab.json"), encoding="utf-8"))
    wev = window_events(a.root, [w["window_id"] for s in SPLITS for w in meta[s]])
    host_role = {wid: (ev[0].get("host_role") if ev else None) for wid, (ev, _) in wev.items()}
    folds = cv_folds(meta["train"], root=a.root); starts = early_starts(a.root, meta)
    for ab in a.ablations.split(","):
        model, res = run(ab, a.root, meta, wev, folds, starts, vocab, host_role)
        print(f"[{model}] params={res['params']} | dac trung {res['n_features']} | kiem tra {res['acceptance']['one_pred_per_window_no_leak']}")
        print("   top gain:", res["top_importance_gain"][:15])

if __name__ == "__main__":
    main()
