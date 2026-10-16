#!/usr/bin/env python3
"""VT-Guard Buoc 5 - khung danh gia dung chung cho Buoc 5-8 (docs/STEP5-BRIEF.md muc 5).

Quy uoc:
  - Du lieu: dataset-v1.0 dong bang. check_dataset() so sha256 cac split + vocab voi
    reports/dataset_stats.json; lech -> dung.
  - Du doan cua mot mo hinh: {split: {window_id: {"p": xac suat duong, "p_ttp": {TTP: xs} | None}}}.
    Train chi co du doan OUT-OF-FOLD (cross-validation theo nhom) de chon nguong.
  - Nguong: chon tren Train OOF (toi da F1), KHOA, ap nguyen cho T-clean/T-hard/T-novel; bao them nguong 0.5.
  - Moi chi so kem CI bootstrap 95% (1000 lan, seed 1337) lay mau theo CUA SO; recall T1003.003 muc
    phien lay mau theo PHIEN.
  - Bao cao RIENG tung tap: T-clean (P/R/F1/PR-AUC/ROC-AUC + per-TTP F1, macro-F1), T-hard (FPR, FPR theo
    chu ky cong cu va theo co/khong cmd.exe trong cay tien trinh), T-novel (nhu T-clean + recall T1003.003
    muc phien x/6).
  - Moc C: FPR PHAN TANG THEO DO DAI cua so (du 64 event / ngan < 64) tren cua so am, moi tap, va tuong quan
    Spearman diem ~ n_events tren cua so am (confounder da biet: ti le cua so du 64 lech theo lop).
    n_events CHI dung de phan tang bao cao, KHONG bao gio la feature.
  - Metadata cua so (run_id, nhom, chu ky) chi dung de chia fold / nhom bao cao, KHONG bao gio la feature.
Chay tu kiem: python src/eval/evaluate.py --selftest
"""
import argparse, hashlib, json, os, sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "dataset"))
from bootstrap import (bootstrap_ci, precision, recall, f1, fpr, average_precision, roc_auc,
                       best_f1_threshold, counts, wilson, spearman, N_BOOT, SEED)

TTPS = ["T1016", "T1018", "T1087.002", "T1654", "T1003.003"]
SPLITS = ["train", "t_clean", "t_hard", "t_novel"]
TEST_SPLITS = ["t_clean", "t_hard", "t_novel"]
SPLIT_NAME = {"train": "Train", "t_clean": "T-clean", "t_hard": "T-hard", "t_novel": "T-novel"}
META_KEYS = ["window_id", "run_id", "batch", "host", "window_malicious", "window_ttps", "window_class",
             "revert_control", "n_events"]
NTDS = "T1003.003"

def P(root, *p): return os.path.join(root, *p)

def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

# ---------------- du lieu ----------------
def check_dataset(root="."):
    """So sha256 split + vocab voi dataset-v1.0 (reports/dataset_stats.json). Lech -> SystemExit."""
    ref = json.load(open(P(root, "reports", "dataset_stats.json"), encoding="utf-8"))["files_sha256"]
    out = {}
    for k in ["vocab.json"] + [f"splits/{s}.jsonl" for s in SPLITS]:
        got = _sha(P(root, "data", "processed", *k.split("/")))
        out[k] = got == ref[k]
        if got != ref[k]: sys.exit(f"LOI: {k} khac dataset-v1.0 (sha256 {got[:16]} != {ref[k][:16]}). DUNG.")
    return out

def load_meta(root, split):
    """Metadata cua so (khong lay cat/cmd/num)."""
    out = []
    with open(P(root, "data", "processed", "splits", f"{split}.jsonl"), encoding="utf-8") as fh:
        for l in fh:
            w = json.loads(l)
            out.append({k: w.get(k) for k in META_KEYS})
    return out

def load_all_meta(root="."):
    return {s: load_meta(root, s) for s in SPLITS}

def hn_signatures(root, run_ids):
    """run_id -> (chu ky cong cu nhu split.py, co cmd.exe trong cay tien trinh?)."""
    from split import hn_signature
    from windows import load_manifests
    man = load_manifests(root); run_ids = set(run_ids)
    imgs = defaultdict(set)
    with open(P(root, "data", "processed", "all.events.jsonl"), encoding="utf-8") as fh:
        for l in fh:
            r = json.loads(l)
            if r["run_id"] in run_ids: imgs[r["run_id"]].add(r["image_name"])
    out = {}
    for rid in run_ids:
        sig, rc = hn_signature(man[rid], imgs)
        out[rid] = (sig + (" [revert_control]" if rc else ""), "cmd.exe" in imgs[rid])
    return out

def cv_folds(train_meta, k=5, seed=SEED, root="."):
    """K fold theo NHOM: nhom chong thoi gian cua split.py (splits/assignment.json) - chat hon nhom run_id
    (moi run_id nam tron trong mot nhom; phien song song dung chung event nen cung fold).
    Gan nhom vao fold co it cua so nhat (thu tu nhom xao tron theo seed). Tra ve list (idx_train, idx_val)."""
    try:
        asg = json.load(open(P(root, "data", "processed", "splits", "assignment.json"), encoding="utf-8"))
        gkey = lambda w: f"g{asg[w['run_id']]['group']}"
    except (OSError, KeyError):
        gkey = lambda w: w["run_id"]
    groups = defaultdict(list)
    for i, w in enumerate(train_meta): groups[gkey(w)].append(i)
    names = sorted(groups); rng = np.random.default_rng(seed); rng.shuffle(names)
    names.sort(key=lambda g: -len(groups[g]))           # nhom lon truoc, on dinh nho sort on dinh
    fold_of, size = {}, [0] * k
    for g in names:
        f_ = int(np.argmin(size)); fold_of[g] = f_; size[f_] += len(groups[g])
    folds = []
    for f_ in range(k):
        va = [i for g, idx in groups.items() if fold_of[g] == f_ for i in idx]
        tr = [i for g, idx in groups.items() if fold_of[g] != f_ for i in idx]
        folds.append((np.array(sorted(tr)), np.array(sorted(va))))
    return folds

# ---------------- du doan ----------------
def write_preds(root, model, split, meta, preds):
    """reports/preds/<model>_<split>.jsonl - dinh dang dung chung cho Buoc 8 (fusion)."""
    os.makedirs(P(root, "reports", "preds"), exist_ok=True)
    with open(P(root, "reports", "preds", f"{model}_{split}.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for w in meta:
            p = preds[w["window_id"]]
            f.write(json.dumps({"window_id": w["window_id"], "run_id": w["run_id"], "split": split,
                                "p_malicious": round(float(p["p"]), 6),
                                "p_ttp": None if p.get("p_ttp") is None else {t: round(float(v), 6) for t, v in p["p_ttp"].items()},
                                "y": int(w["window_malicious"]), "y_ttp": w["window_ttps"]}) + "\n")

def load_preds(root, model, split):
    out = {}
    with open(P(root, "reports", "preds", f"{model}_{split}.jsonl"), encoding="utf-8") as fh:
        for l in fh:
            r = json.loads(l); out[r["window_id"]] = {"p": r["p_malicious"], "p_ttp": r["p_ttp"]}
    return out

def check_predictions(meta, preds):
    """Moi cua so co dung mot du doan; khong co du doan thua; khong run_id Train nao lot vao test."""
    probs = {}
    for s, pr in preds.items():
        ids = [w["window_id"] for w in meta[s]]
        missing = [i for i in ids if i not in pr]; extra = set(pr) - set(ids)
        if missing or extra or len(ids) != len(set(ids)):
            probs[s] = {"missing": len(missing), "extra": len(extra), "dup_ids": len(ids) - len(set(ids))}
    train_runs = {w["run_id"] for w in meta["train"]}
    leak = sorted({w["run_id"] for s in TEST_SPLITS for w in meta[s]} & train_runs)
    return {"ok": not probs and not leak, "problems": probs, "train_run_ids_in_test": leak}

# ---------------- nguong ----------------
def choose_thresholds(train_meta, oof):
    """Nguong toi da F1 tren du doan OUT-OF-FOLD cua Train: nhi phan + tung TTP (neu mo hinh co p_ttp)."""
    y = np.array([w["window_malicious"] for w in train_meta], bool)
    s = np.array([oof[w["window_id"]]["p"] for w in train_meta], float)
    tb, fb = best_f1_threshold(y, s)
    out = {"binary": tb, "binary_train_oof_f1": fb, "ttp": {}, "ttp_train_oof_f1": {}}
    if all(oof[w["window_id"]].get("p_ttp") for w in train_meta):
        for t in TTPS:
            yt = np.array([t in w["window_ttps"] for w in train_meta], bool)
            st = np.array([oof[w["window_id"]]["p_ttp"][t] for w in train_meta], float)
            out["ttp"][t], out["ttp_train_oof_f1"][t] = best_f1_threshold(yt, st)
    return out

# ---------------- danh gia ----------------
def _ci(n, fn, n_boot, seed):
    r = bootstrap_ci(n, fn, n_boot=n_boot, seed=seed)
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}

def _binary_block(y, s, thr, n_boot, seed):
    yhat = s >= thr; n = len(y)
    blk = {"threshold": thr, "n": int(n), "n_pos": int(y.sum()), **counts(y, yhat)}
    for name, fn in (("precision", lambda i: precision(y[i], yhat[i])), ("recall", lambda i: recall(y[i], yhat[i])),
                     ("f1", lambda i: f1(y[i], yhat[i])), ("fpr", lambda i: fpr(y[i], yhat[i]))):
        blk[name] = _ci(n, fn, n_boot, seed)
    c = counts(y, yhat)
    blk["fpr_wilson"] = wilson(c["fp"], c["fp"] + c["tn"])
    blk["recall_wilson"] = wilson(c["tp"], c["tp"] + c["fn"])
    return blk

def _ttp_block(meta, pr, thr_ttp, n_boot, seed):
    n = len(meta); out = {"per_ttp": {}}
    Y = {t: np.array([t in w["window_ttps"] for w in meta], bool) for t in TTPS}
    S = {t: np.array([pr[w["window_id"]]["p_ttp"][t] for w in meta], float) for t in TTPS}
    H = {t: S[t] >= thr_ttp[t] for t in TTPS}
    for t in TTPS:
        out["per_ttp"][t] = {"threshold": thr_ttp[t], "n_pos": int(Y[t].sum()), **counts(Y[t], H[t]),
                             "f1": _ci(n, lambda i, t=t: f1(Y[t][i], H[t][i]), n_boot, seed),
                             "recall": _ci(n, lambda i, t=t: recall(Y[t][i], H[t][i]), n_boot, seed),
                             "precision": _ci(n, lambda i, t=t: precision(Y[t][i], H[t][i]), n_boot, seed)}
    present = [t for t in TTPS if Y[t].sum() > 0]
    def macro(i):
        v = [f1(Y[t][i], H[t][i]) for t in present]
        v = [x for x in v if x is not None]
        return float(np.mean(v)) if v else None
    out["macro_f1"] = _ci(n, macro, n_boot, seed)
    out["macro_over"] = present
    return out

def _session_recall(meta, pr, thr, thr_ttp, n_boot, seed, ttp=NTDS):
    """Recall muc PHIEN cho cac phien co cua so mang nhan `ttp`: phien duoc phat hien neu co it nhat
    mot cua so du doan duong (nhi phan) / du doan `ttp` (da nhan). Bootstrap theo PHIEN."""
    sess = defaultdict(list)
    for w in meta:
        sess[w["run_id"]].append(w)
    target = sorted(r for r, ws in sess.items() if any(ttp in w["window_ttps"] for w in ws))
    det_bin = np.array([any(pr[w["window_id"]]["p"] >= thr for w in sess[r]) for r in target], bool)
    has_ttp = bool(meta) and all(pr[w["window_id"]].get("p_ttp") for w in meta) and thr_ttp
    det_ttp = np.array([any(pr[w["window_id"]]["p_ttp"][ttp] >= thr_ttp[ttp] for w in sess[r]) for r in target], bool) if has_ttp else None
    n = len(target)
    out = {"ttp": ttp, "n_sessions": n,
           "binary": {"detected": int(det_bin.sum()), "of": n,
                      "recall": _ci(n, lambda i: float(det_bin[i].mean()) if len(i) else None, n_boot, seed),
                      "wilson": wilson(int(det_bin.sum()), n)},
           "sessions": {r: {"binary": bool(det_bin[k]), "ttp": None if det_ttp is None else bool(det_ttp[k]),
                            "n_windows": len(sess[r]),
                            "max_p": round(max(pr[w["window_id"]]["p"] for w in sess[r]), 4)} for k, r in enumerate(target)}}
    if det_ttp is not None:
        out["ttp_label"] = {"detected": int(det_ttp.sum()), "of": n,
                            "recall": _ci(n, lambda i: float(det_ttp[i].mean()) if len(i) else None, n_boot, seed),
                            "wilson": wilson(int(det_ttp.sum()), n)}
    return out

def evaluate(model, meta, preds, thresholds, root=".", n_boot=N_BOOT, seed=SEED, hn_sig=None):
    """meta: load_all_meta(); preds: {split: {window_id: {...}}} cho 3 tap test; thresholds: choose_thresholds()."""
    chk = check_predictions({s: meta[s] for s in SPLITS if s in preds or s == "train"},
                            {s: preds[s] for s in TEST_SPLITS})
    if not chk["ok"]: sys.exit(f"LOI du doan: {chk}")
    if hn_sig is None: hn_sig = hn_signatures(root, {w["run_id"] for w in meta["t_hard"]})
    dsv = json.load(open(P(root, "reports", "dataset_stats.json"), encoding="utf-8")).get("dataset_version", "v1.0")
    res = {"model": model, "dataset_version": dsv, "thresholds": thresholds, "n_boot": n_boot, "seed": seed, "checks": chk, "splits": {}}
    has_ttp = bool(thresholds.get("ttp"))
    for s in TEST_SPLITS:
        M, pr = meta[s], preds[s]
        y = np.array([w["window_malicious"] for w in M], bool)
        sc = np.array([pr[w["window_id"]]["p"] for w in M], float)
        out = {"n": len(M), "n_pos": int(y.sum())}
        for tag, thr in (("tuned", thresholds["binary"]), ("t05", 0.5)):
            out[tag] = _binary_block(y, sc, thr, n_boot, seed)
        if s == "t_hard":
            for tag, thr in (("tuned", thresholds["binary"]), ("t05", 0.5)):
                yhat = sc >= thr
                by_sig, by_cmd = defaultdict(list), defaultdict(list)
                for k, w in enumerate(M):
                    sig, has_cmd = hn_sig[w["run_id"]]
                    by_sig[sig].append(k); by_cmd["co cmd.exe" if has_cmd else "khong cmd.exe"].append(k)
                def grp(d):
                    o = {}
                    for g, idx in sorted(d.items(), key=lambda x: -len(x[1])):
                        idx = np.array(idx)
                        o[g] = {"n": len(idx), "fp": int(yhat[idx].sum()),
                                "fpr": _ci(len(idx), lambda i, idx=idx: float(yhat[idx][i].mean()), n_boot, seed),
                                "fpr_wilson": wilson(int(yhat[idx].sum()), len(idx))}
                    return o
                out[tag]["fpr_by_signature"] = grp(by_sig)
                out[tag]["fpr_by_cmd"] = grp(by_cmd)
        else:
            out["pr_auc"] = _ci(len(M), lambda i: average_precision(y[i], sc[i]), n_boot, seed)
            out["roc_auc"] = _ci(len(M), lambda i: roc_auc(y[i], sc[i]), n_boot, seed)
            if has_ttp:
                out["ttp_tuned"] = _ttp_block(M, pr, thresholds["ttp"], n_boot, seed)
                out["ttp_t05"] = _ttp_block(M, pr, {t: 0.5 for t in TTPS}, n_boot, seed)
            for tag, thr, tt in (("tuned", thresholds["binary"], thresholds.get("ttp")), ("t05", 0.5, {t: 0.5 for t in TTPS} if has_ttp else None)):
                out[tag]["ntds_session_recall"] = _session_recall(M, pr, thr, tt, n_boot, seed)
        # moc C: phan tang theo do dai (chi bao cao)
        nev = np.array([w["n_events"] for w in M]); full = nev >= 64; neg = ~y
        for tag, thr in (("tuned", thresholds["binary"]), ("t05", 0.5)):
            yhat = sc >= thr; strata = {}
            for name, m in (("full64", full), ("short", ~full)):
                idx = np.where(neg & m)[0]
                strata[name] = {"n_neg": int(len(idx)), "fp": int(yhat[idx].sum()),
                                "fpr": _ci(len(idx), lambda i, idx=idx: float(yhat[idx][i].mean()) if len(i) else None, n_boot, seed),
                                "fpr_wilson": wilson(int(yhat[idx].sum()), int(len(idx)))}
            out[tag]["fpr_by_length"] = strata
        ineg = np.where(neg)[0]
        out["spearman_score_len_neg"] = _ci(len(ineg), lambda i: spearman(sc[ineg][i], nev[ineg][i]), n_boot, seed)
        out["n_neg_full64"] = int((neg & full).sum()); out["n_neg_short"] = int((neg & ~full).sum())
        res["splits"][s] = out
    return res

# ---------------- bang ----------------
def fci(c, pct=False):
    if c is None or c.get("point") is None: return "-"
    f = (lambda v: f"{100 * v:.1f}") if pct else (lambda v: f"{v:.3f}")
    if c.get("lo") is None: return f(c["point"])
    return f"{f(c['point'])} [{f(c['lo'])}, {f(c['hi'])}]"

def fw(w):
    return "-" if w is None or w.get("lo") is None else f"[{w['lo']:.3f}, {w['hi']:.3f}]"

def render_markdown(res):
    L = [f"### {res['model']} (dataset-{res.get('dataset_version', '?')})", "",
         f"Nguong nhi phan chon tren Train OOF: **{res['thresholds']['binary']:.4f}** "
         f"(F1 OOF {res['thresholds']['binary_train_oof_f1'] if res['thresholds']['binary_train_oof_f1'] is None else round(res['thresholds']['binary_train_oof_f1'], 3)}). "
         f"CI bootstrap 95%, {res['n_boot']} lan, seed {res['seed']}.", ""]
    for tag, name in (("tuned", "nguong da khoa"), ("t05", "nguong 0.5")):
        L += [f"**Nhi phan - {name}**", "",
              "| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |", "|---|---|---|---|---|---|---|---|"]
        for s in TEST_SPLITS:
            o = res["splits"][s]; b = o[tag]
            if s == "t_hard":   # 0 mau duong: precision/recall/F1/AUC khong xac dinh -> chi FPR
                L.append(f"| {SPLIT_NAME[s]} | {o['n']} ({o['n_pos']}) | - | - | - | "
                         f"{fci(b['fpr'])}, Wilson {fw(b['fpr_wilson'])} ({b['fp']}/{o['n']}) | - | - |")
            else:
                L.append(f"| {SPLIT_NAME[s]} | {o['n']} ({o['n_pos']}) | {fci(b['precision'])} | {fci(b['recall'])} | {fci(b['f1'])} | "
                         f"{fci(b['fpr'])} | {fci(o.get('pr_auc'))} | {fci(o.get('roc_auc'))} |")
        L.append("")
    L += ["**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) "
          "va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)", "",
          "| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |",
          "|---|---|---|---|---|---|---|"]
    for s in TEST_SPLITS:
        o = res["splits"][s]
        for tag, name in (("tuned", "khoa"), ("t05", "0.5")):
            st = o[tag]["fpr_by_length"]
            L.append(f"| {SPLIT_NAME[s]} | {name} | {st['full64']['fp']}/{st['full64']['n_neg']} | {fci(st['full64']['fpr'])} | "
                     f"{st['short']['fp']}/{st['short']['n_neg']} | {fci(st['short']['fpr'])} | {fci(o['spearman_score_len_neg']) if tag == 'tuned' else ''} |")
    L.append("")
    h = res["splits"]["t_hard"]["tuned"]
    L += ["**T-hard - FPR theo chu ky cong cu (nguong da khoa)**", "", "| Chu ky | n | FP | FPR [bootstrap] | Wilson 95% |", "|---|---|---|---|---|"]
    for g, v in h["fpr_by_signature"].items(): L.append(f"| `{g}` | {v['n']} | {v['fp']} | {fci(v['fpr'])} | {fw(v['fpr_wilson'])} |")
    for g, v in h["fpr_by_cmd"].items(): L.append(f"| *{g} trong cay tien trinh* | {v['n']} | {v['fp']} | {fci(v['fpr'])} | {fw(v['fpr_wilson'])} |")
    L.append("")
    if "ttp_tuned" in res["splits"]["t_clean"]:
        L += ["**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**", "",
              "| Tap | " + " | ".join(TTPS) + " | macro-F1 |", "|---|" + "---|" * (len(TTPS) + 1)]
        for s in ("t_clean", "t_novel"):
            b = res["splits"][s]["ttp_tuned"]
            L.append(f"| {SPLIT_NAME[s]} | " + " | ".join(
                (fci(b["per_ttp"][t]["f1"]) + f" (n={b['per_ttp'][t]['n_pos']})") if b["per_ttp"][t]["n_pos"] else "- (n=0)"
                for t in TTPS) + f" | {fci(b['macro_f1'])} |")
        L.append("")
    L += ["**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)", "",
          "| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |",
          "|---|---|---|---|---|---|---|---|"]
    for s in ("t_novel", "t_clean"):
        for tag, name in (("tuned", "khoa"), ("t05", "0.5")):
            r = res["splits"][s][tag]["ntds_session_recall"]; t = r.get("ttp_label")
            L.append(f"| {SPLIT_NAME[s]} | {name} | {r['binary']['detected']}/{r['binary']['of']} | {fci(r['binary']['recall'])} | {fw(r['binary']['wilson'])} | "
                     + (f"{t['detected']}/{t['of']} | {fci(t['recall'])} | {fw(t['wilson'])} |" if t else "- | - | - |"))
    L.append("")
    return "\n".join(L)

# ---------------- tu kiem ----------------
def _fake_model(kind, meta, seed=SEED):
    """random: p~U(0,1) doc lap nhan; oracle: p gan dung nhan (de kiem tra bang/CI)."""
    rng = np.random.default_rng(seed); out = {}
    for s in SPLITS:
        out[s] = {}
        for w in meta[s]:
            if kind == "random":
                p = float(rng.random()); pt = {t: float(rng.random()) for t in TTPS}
            else:
                p = 0.9 if w["window_malicious"] else 0.1
                pt = {t: (0.9 if t in w["window_ttps"] else 0.1) for t in TTPS}
            out[s][w["window_id"]] = {"p": p, "p_ttp": pt}
    return out

def selftest(root="."):
    print("== kiem tra checksum dataset (reports/dataset_stats.json) ==", check_dataset(root))
    meta = load_all_meta(root)
    folds = cv_folds(meta["train"], root=root)
    print("== fold Train (theo nhom chong thoi gian) ==",
          [(len(va), int(sum(meta["train"][i]["window_malicious"] for i in va))) for _, va in folds])
    # khong nhom nao nam o 2 fold
    asg = json.load(open(P(root, "data", "processed", "splits", "assignment.json"), encoding="utf-8"))
    gf = defaultdict(set)
    for f_, (_, va) in enumerate(folds):
        for i in va: gf[asg[meta["train"][i]["run_id"]]["group"]].add(f_)
    assert all(len(v) == 1 for v in gf.values()), "nhom nam o >1 fold"
    hn_sig = hn_signatures(root, {w["run_id"] for w in meta["t_hard"]})
    results = {}
    for kind in ("random", "oracle"):
        pr = _fake_model(kind, meta)
        thr = choose_thresholds(meta["train"], pr["train"])         # gia lap OOF: dung du doan gia tren Train
        res = evaluate(f"selftest-{kind}", meta, {s: pr[s] for s in TEST_SPLITS}, thr, root=root, hn_sig=hn_sig)
        results[kind] = res
        print(render_markdown(res))
    # kiem tra hop ly
    o = results["oracle"]["splits"]; r = results["random"]["splits"]
    assert o["t_clean"]["tuned"]["f1"]["point"] == 1.0 and o["t_hard"]["tuned"]["fpr"]["point"] == 0.0
    assert o["t_novel"]["tuned"]["ntds_session_recall"]["binary"]["detected"] == o["t_novel"]["tuned"]["ntds_session_recall"]["n_sessions"]
    ra = r["t_clean"]["roc_auc"]
    assert ra["lo"] <= 0.5 <= ra["hi"] or abs(ra["point"] - 0.5) < 0.15, ra
    for sp in TEST_SPLITS:      # moc C: diem ngau nhien khong tuong quan voi do dai
        c = r[sp]["spearman_score_len_neg"]; assert c["lo"] <= 0.0 <= c["hi"], (sp, c)
        assert set(r[sp]["tuned"]["fpr_by_length"]) == {"full64", "short"}
    print("SELFTEST: DAT (oracle F1=1, FPR=0, recall phien = 1; random ROC-AUC quanh 0.5:", ra,
          "; random Spearman diem~do dai chua 0 o ca 3 tap)")
    return results

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: selftest(a.root)
    else: ap.print_help()

if __name__ == "__main__":
    main()
