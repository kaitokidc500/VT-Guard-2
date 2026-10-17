#!/usr/bin/env python3
"""VT-Guard Buoc 8 - pipeline suy luan dau-cuoi (docs/STEP8-BRIEF.md muc 6-7).

cua so (dinh dang windows.jsonl: window_id, host, t0, t1, events)
  -> featurize (src/dataset/featurize.featurize_window, vocab.json dong bang Buoc 4)
  -> ONNX VT-Seq-ens (models/vtseq_M3_ens.onnx: 5 mang M3, trung binh p_bin / p_ttp / alpha; onnxruntime CPU)
  -> matcher Sigma (rules/sigma/*.yml qua src/rules/apply.py)
  -> fusion KHOA (reports/step8/final_fusion.json: F3-B, s = p + 0.1 r, s_k = p_k + 0.1 r_k voi r_k chi T1018/T1654/T1003.003)
  -> alerts.jsonl (schema muc 6).
p = max(p_bin, max_k p_ttp) (diem nhi phan VT-Seq-ens da chon o Buoc 6); r = co luat khop; r_k = luat theo TTP k khop.
decision_source: "both" = p >= nguong va co luat khop; "ai" = p >= nguong, khong luat; "rule" = p < nguong nhung p + 0.1 >= nguong
(canh bao chi nho luat). Luat khop nhung p + 0.1 < nguong -> KHONG canh bao (F3-B khong phai OR).
Chay: python src/pipeline/infer.py --windows data/processed/windows.jsonl [--split t_novel] --out reports/step8/alerts.jsonl
"""
import argparse, json, os, sys, time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("../dataset", "../rules", "../eval", "../models"): sys.path.insert(0, os.path.join(HERE, d))
import featurize as FZ                                   # noqa: E402
from apply import load_sigma, score as rule_score        # noqa: E402

TTPS = ["T1016", "T1018", "T1087.002", "T1654", "T1003.003"]
CMD_DIM, NCAT = 256, 7
FUSION = os.path.join("reports", "step8", "final_fusion.json")
ONNX_ENS = os.path.join("models", "vtseq_M3_ens.onnx")
PROV = "reports/step7/rules_provenance.json"

class Pipeline:
    def __init__(self, root=".", threads=1):
        import onnxruntime as ort
        self.root = root
        self.vocab = json.load(open(os.path.join(root, "data", "processed", "vocab.json"), encoding="utf-8"))
        self.rules = load_sigma(root)
        FF = json.load(open(os.path.join(root, FUSION), encoding="utf-8")); ch = FF["chosen"]
        assert ch["strategy"] == "F3" and ch["variant"] == "B"
        self.beta = float(ch["beta"]); self.thr = float(ch["threshold_binary"])
        self.thr_k = np.array([ch["thresholds_ttp"][t] for t in TTPS], float)
        self.mask = np.array([t in ch["rule_ttp_channels"] for t in TTPS], float)
        self.config = {"strategy": "F3", "variant": "B", "beta": self.beta, "rule_ttp_channels": ch["rule_ttp_channels"],
                       "file": FUSION.replace(os.sep, "/"), "locked_commit": "3fd9531"}
        so = ort.SessionOptions(); so.intra_op_num_threads = threads; so.inter_op_num_threads = 1
        self.sess = ort.InferenceSession(os.path.join(root, ONNX_ENS), so, providers=["CPUExecutionProvider"])
        self.timing = {"featurize": 0.0, "onnx": 0.0, "sigma": 0.0, "fusion": 0.0}

    # ---- tung buoc ----
    def featurize(self, windows):
        t = time.perf_counter(); out = []
        for w in windows:
            cat, cmd, num = FZ.featurize_window(w, self.vocab)
            n = len(cat); dense = np.zeros((n, CMD_DIM), np.float32)
            for i, c in enumerate(cmd):
                for j, x in c: dense[i, j] = x
            out.append((np.asarray(cat, np.int64).reshape(n, NCAT), dense, np.asarray(num, np.float32).reshape(n, 5)))
        self.timing["featurize"] += time.perf_counter() - t
        return out

    def onnx(self, feats):
        t = time.perf_counter()
        L = max(len(c) for c, _, _ in feats); B = len(feats)
        cat = np.zeros((B, L, NCAT), np.int64); cmd = np.zeros((B, L, CMD_DIM), np.float32); num = np.zeros((B, L, 5), np.float32)
        lens = np.zeros(B, np.int64)
        for i, (c, m, nm) in enumerate(feats):
            k = len(c); cat[i, :k] = c; cmd[i, :k] = m; num[i, :k] = nm; lens[i] = k
        pb, pt, al = self.sess.run(None, {"cat": cat, "cmd": cmd, "num": num, "lens": lens})
        self.timing["onnx"] += time.perf_counter() - t
        return pb, pt, [al[i, :lens[i]] for i in range(B)]

    def sigma(self, windows):
        t = time.perf_counter(); out = [rule_score(self.rules, w["events"]) for w in windows]
        self.timing["sigma"] += time.perf_counter() - t
        return out

    def fuse(self, pb, pt, rs):
        t = time.perf_counter()
        p = np.maximum(pb, pt.max(1))
        r = np.array([x[0] >= 0.5 for x in rs], float)
        rk = np.array([[x[1][k] >= 0.5 for k in TTPS] for x in rs], float) * self.mask
        s = p + self.beta * r; sk = pt + self.beta * rk
        self.timing["fusion"] += time.perf_counter() - t
        return p, r, s, sk

    # ---- dau-cuoi ----
    def run(self, windows):
        feats = self.featurize(windows)
        pb, pt, al = self.onnx(feats)
        rs = self.sigma(windows)
        p, r, s, sk = self.fuse(pb, pt, rs)
        res = []
        for i, w in enumerate(windows):
            dec = bool(s[i] >= self.thr); ttps = [t for j, t in enumerate(TTPS) if sk[i, j] >= self.thr_k[j]]
            src = None
            if dec: src = "both" if (p[i] >= self.thr and r[i]) else ("ai" if p[i] >= self.thr else "rule")
            res.append({"window_id": w["window_id"], "p_ai": float(p[i]), "p_ttp_ai": pt[i].tolist(), "r": int(r[i]),
                        "score": float(s[i]), "score_ttp": dict(zip(TTPS, [float(x) for x in sk[i]])), "alert": dec, "ttps": ttps,
                        "decision_source": src, "rule_hits": rs[i][2], "alpha": al[i], "window": w})
        return res

    def alert_record(self, r):
        w = r["window"]; a = r["alpha"]; idx = np.argsort(-a)[:5]
        top = []
        for j in idx:
            e = w["events"][int(j)]
            top.append({"idx": int(j), "alpha": round(float(a[j]), 4), "image_name": e.get("image_name"), "parent_image_name": e.get("parent_image_name"),
                        "event_id": e.get("event_id"), "channel": e.get("channel"),
                        "cmd_canon": FZ.canon_cmd(e["command_line"]) if e.get("command_line") else None})
        rr = {x["rule_id"]: x for x in self.rules}
        return {"window_id": r["window_id"], "host": w.get("host"), "t0": w.get("t0"), "t1": w.get("t1"),
                "score": round(r["score"], 6), "decision_source": r["decision_source"], "ttps": r["ttps"],
                "rule_ids": [{"id": h, "target": rr[h]["target"], "sigma_file": f"rules/sigma/{rr[h]['file']}",
                              "provenance": {"file": PROV, "rule_id": h}} for h in r["rule_hits"]],
                "attention_top5": top, "p_ai": round(r["p_ai"], 6), "threshold": round(self.thr, 6),
                "thresholds_ttp": dict(zip(TTPS, [round(float(x), 6) for x in self.thr_k])), "fusion_config": self.config}

def read_windows(path, ids=None):
    want = None if ids is None else set(ids); out = []
    with open(path, encoding="utf-8") as fh:
        for l in fh:
            w = json.loads(l)
            if want is None or w["window_id"] in want:
                out.append({k: w[k] for k in ("window_id", "host", "t0", "t1", "events")})
    if ids is not None:
        pos = {w: i for i, w in enumerate(ids)}; out.sort(key=lambda w: pos[w["window_id"]])
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--windows", default=os.path.join("data", "processed", "windows.jsonl"))
    ap.add_argument("--split", default=None, help="chi lay cua so thuoc split (doc window_id tu splits/<split>.jsonl)")
    ap.add_argument("--batch", type=int, default=32); ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--out", default=os.path.join("reports", "step8", "alerts.jsonl"))
    a = ap.parse_args()
    ids = None
    if a.split: ids = [json.loads(l)["window_id"] for l in open(os.path.join("data", "processed", "splits", f"{a.split}.jsonl"), encoding="utf-8")]
    W = read_windows(a.windows, ids); P = Pipeline(".", a.threads); n = 0
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        for i in range(0, len(W), a.batch):
            for r in P.run(W[i:i + a.batch]):
                if r["alert"]: f.write(json.dumps(P.alert_record(r)) + "\n"); n += 1
    print(f"{len(W)} cua so -> {n} canh bao -> {a.out} | thoi gian (s): " + ", ".join(f"{k} {v:.2f}" for k, v in P.timing.items()))

if __name__ == "__main__":
    main()
