#!/usr/bin/env python3
"""VT-Guard Buoc 8 moc 3 - chay pipeline (src/pipeline/infer.py) tren t_clean / t_hard / t_novel:
(1) kiem trung voi reports/preds/fusion_<split>.jsonl (quyet dinh nhi phan + TTP, diem), (2) reports/step8/alerts_<split>.jsonl,
(3) thong ke giai thich (ti le canh bao co luat khop, theo tap va TP / FP; phan bo decision_source), (4) vi du (chon tat dinh:
canh bao dau tien theo window_id cua moi loai + moi canh bao nham tren T-hard), (5) do tre dau-cuoi tren host CPU.
Nhan (window_malicious) CHI dung de thong ke TP / FP, khong vao pipeline. Chay: python src/pipeline/m3_check.py
"""
import json, os, sys, time
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../dataset", "../eval"): sys.path.insert(0, os.path.join(HERE, d))
import infer as INF                                        # noqa: E402
import featurize as FZ                                     # noqa: E402
from evaluate import check_dataset, load_all_meta, TEST_SPLITS, TTPS   # noqa: E402

S8 = os.path.join("reports", "step8")

def load_preds(path):
    return {json.loads(l)["window_id"]: json.loads(l) for l in open(path, encoding="utf-8")}

def main(root="."):
    print("checksum dataset:", check_dataset(root))
    meta = load_all_meta(root)
    P = INF.Pipeline(root, threads=1)
    out = {"check": {}, "stats": {}, "examples": {}, "latency": {}}
    results = {}
    for s in TEST_SPLITS:
        ids = [w["window_id"] for w in meta[s]]; W = INF.read_windows(os.path.join(root, "data", "processed", "windows.jsonl"), ids)
        R = []
        for i in range(0, len(W), 32): R += P.run(W[i:i + 32])
        results[s] = R
        fp_ = load_preds(os.path.join(root, "reports", "preds", f"fusion_{s}.jsonl"))
        rp = load_preds(os.path.join(root, "reports", "preds", f"rules_{s}.jsonl"))
        # dac trung == file split (featurizer dong bang)
        sp = {json.loads(l)["window_id"]: json.loads(l) for l in open(os.path.join(root, "data", "processed", "splits", f"{s}.jsonl"), encoding="utf-8")}
        feat_bad = 0
        for w in W:
            cat, cmd, num = FZ.featurize_window(w, P.vocab); r_ = sp[w["window_id"]]
            feat_bad += not (cat == r_["cat"] and [[list(x) for x in c] for c in cmd] == r_["cmd"] and num == r_["num"])
        d_bin = sum((r["score"] >= P.thr) != (fp_[r["window_id"]]["p_malicious"] >= P.thr) for r in R)
        d_ttp = sum(any((r["score_ttp"][t] >= P.thr_k[j]) != (fp_[r["window_id"]]["p_ttp"][t] >= P.thr_k[j]) for j, t in enumerate(TTPS)) for r in R)
        d_r = sum(r["r"] != int(rp[r["window_id"]]["p_malicious"] >= 0.5) for r in R)
        mx = max(max(abs(r["score"] - fp_[r["window_id"]]["p_malicious"]), max(abs(r["score_ttp"][t] - fp_[r["window_id"]]["p_ttp"][t]) for t in TTPS)) for r in R)
        out["check"][s] = {"n": len(R), "featurize_mismatch_vs_split": feat_bad, "decision_mismatch_binary": int(d_bin), "decision_mismatch_ttp": int(d_ttp),
                           "rule_r_mismatch": int(d_r), "max_abs_score_diff": float(mx)}
        with open(os.path.join(root, S8, f"alerts_{s}.jsonl"), "w", encoding="utf-8", newline="\n") as f:
            for r in R:
                if r["alert"]: f.write(json.dumps(P.alert_record(r)) + "\n")
        y = {w["window_id"]: bool(w["window_malicious"]) for w in meta[s]}
        A = [r for r in R if r["alert"]]
        grp = lambda rs: {"n": len(rs), "with_rule": sum(bool(r["rule_hits"]) for r in rs),
                          "share_with_rule": round(sum(bool(r["rule_hits"]) for r in rs) / len(rs), 4) if rs else None,
                          "decision_source": dict(Counter(r["decision_source"] for r in rs))}
        out["stats"][s] = {"n_windows": len(R), "alerts": grp(A), "tp": grp([r for r in A if y[r["window_id"]]]), "fp": grp([r for r in A if not y[r["window_id"]]]),
                           "rule_match_not_alerted": sum(bool(r["rule_hits"]) and not r["alert"] for r in R),
                           "positives_missed": sum(y[r["window_id"]] and not r["alert"] for r in R)}
        print(f"[{s}] kiem trung {out['check'][s]} | canh bao {out['stats'][s]['alerts']}", flush=True)
    # vi du (tat dinh: window_id nho nhat cua moi loai tren 3 tap)
    lab = {w["window_id"]: (s, bool(w["window_malicious"]), w["window_ttps"]) for s in TEST_SPLITS for w in meta[s]}
    allA = sorted([r for s in TEST_SPLITS for r in results[s] if r["alert"]], key=lambda r: r["window_id"])
    for src in ("rule", "ai", "both"):
        ex = next((r for r in allA if r["decision_source"] == src), None)
        out["examples"][src] = None if ex is None else {**P.alert_record(ex), "split": lab[ex["window_id"]][0], "label_malicious": lab[ex["window_id"]][1], "label_ttps": lab[ex["window_id"]][2]}
    nm = sorted([r for s in TEST_SPLITS for r in results[s] if r["rule_hits"] and not r["alert"]], key=lambda r: r["window_id"])
    out["examples"]["rule_match_not_alerted"] = [{**P.alert_record(r), "alert": False, "split": lab[r["window_id"]][0],
                                                  "label_malicious": lab[r["window_id"]][1], "label_ttps": lab[r["window_id"]][2]} for r in nm]
    out["examples"]["t_hard_fp"] = [{**P.alert_record(r), "split": "t_hard", "label_malicious": False} for r in results["t_hard"] if r["alert"]]
    # do tre dau-cuoi (host CPU, onnxruntime 1 thread, cache hash dong lenh xoa truoc moi luot)
    Wall = [r["window"] for s in TEST_SPLITS for r in results[s]]
    Q = INF.Pipeline(root, threads=1); Q.run(Wall[:16])                     # khoi dong
    def bench(bs, reps):
        per = {k: [] for k in ("total", "featurize", "onnx", "sigma", "fusion")}
        for _ in range(reps):
            FZ._cmd_cache.clear()
            for i in range(0, len(Wall), bs):
                chunk = Wall[i:i + bs]; t0 = dict(Q.timing); t = time.perf_counter()
                Q.run(chunk)
                tot = time.perf_counter() - t; n = len(chunk)
                per["total"].append(tot * 1000 / n)
                for k in ("featurize", "onnx", "sigma", "fusion"): per[k].append((Q.timing[k] - t0[k]) * 1000 / n)
        return {k: {"mean_ms": round(float(np.mean(v)), 3), "p95_ms": round(float(np.percentile(v, 95)), 3), "n": len(v)} for k, v in per.items()}
    import platform, onnxruntime
    out["latency"] = {"batch1": bench(1, 1), "batch32": bench(32, 3), "n_windows": len(Wall),
                      "host": {"cpu": platform.processor(), "onnxruntime": onnxruntime.__version__, "onnx_threads": 1},
                      "note": "ms/cua so; batch 32: thoi gian mot lo / so cua so trong lo; cache hash dong lenh xoa truoc moi luot"}
    with open(os.path.join(root, S8, "m3_explain.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(out, f, indent=1)
    print(json.dumps(out["latency"], indent=1))
    return out

if __name__ == "__main__":
    main(".")
