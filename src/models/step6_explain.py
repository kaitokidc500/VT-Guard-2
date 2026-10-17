#!/usr/bin/env python3
"""VT-Guard Buoc 6 moc 4 (brief muc 6 da SUA, chay TREN HOST): giai thich bang attention + ONNX.

  seeds : hat giong luat cho Buoc 7 - CHI TRAIN. Huan luyen lai 5 fold x 5 seed cua M3 tren host (cung cv_folds, cung
          cau hinh khoa) de moi cua so Train lay alpha tu mo hinh fold KHONG thay no (attention OOF); alpha trung binh 5 seed.
          Thong ke theo TTP: image_name / event_id / token lenh (norm_cmd) trong top-5 event theo alpha cua cua so Train
          mang TTP do, so voi cua so am Train (lift) -> reports/step6/rule_seeds_train.json. Khong dung cua so test.
  test  : attention tren test CHI de giai thich: VT-Seq-ens (5 checkpoint M3, alpha trung binh), cua so duong duoc phat
          hien o T-clean / T-novel -> top-5 event -> reports/step6/attention_topk_test.jsonl.
  faith : faithfulness cho ens va tung seed: xoa top-k theo alpha vs xoa k event ngau nhien (10 lan, cung k), k=1/3/5,
          tren cua so duong duoc ens phat hien (n > k); muc giam p_bin va p_ttp (trung binh cac TTP that cua cua so);
          CI bootstrap 95% (1000, seed 1337, theo cua so) cua hieu so (giam top-k - giam ngau nhien) -> faithfulness.json.
  onnx  : xuat seed 1337 (seed chinh, chon truoc) va ens (mot do thi 5 mang, trung binh xac suat + alpha), opset 17,
          truc dong batch + do dai; parity voi PyTorch tren toan T-novel; do tre CPU (onnxruntime) batch 1 / 32.
Doc windows.jsonl (host) CHI de hien thi image/event/lenh trong giai thich - khong lam dau vao mo hinh.
Chay: python src/models/step6_explain.py [seeds|test|faith|onnx|all] [--threads 2]
"""
import argparse, json, os, re, sys, time
from collections import Counter, defaultdict

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval", "../baselines", "../dataset"): sys.path.insert(0, os.path.join(HERE, d))
import vtseq as V                                                     # noqa: E402
from evaluate import load_meta, cv_folds, TTPS                        # noqa: E402
from bootstrap import SEED, N_BOOT                                    # noqa: E402
from common import window_events                                      # noqa: E402
from featurize import norm_cmd, canon_cmd                             # noqa: E402

ROOT = "."
OUT = os.path.join("reports", "step6")
CK = os.path.join(OUT, "m3", "ckpt")
TOK_RE = re.compile(r"[a-z0-9_.<>/\\-]+")
KS = (1, 3, 5)

def readable(root, wids):
    ev = window_events(root, wids)
    out = {}
    for wid, (es, origin) in ev.items():
        out[wid] = [{"image_name": e.get("image_name"), "parent_image_name": e.get("parent_image_name"), "event_id": e.get("event_id"),
                     "channel": e.get("channel"), "cmd_canon": canon_cmd(e["command_line"]) if e.get("command_line") else None,
                     "cmd_tokens": sorted(set(TOK_RE.findall(norm_cmd(e["command_line"])))) if e.get("command_line") else [],
                     "origin": o} for e, o in zip(es, origin)]
    return out

def load_ens():
    nets = []
    for sd in V.SEEDS:
        n, cfg, _ = V.load_nets(os.path.join(CK, f"vtseq_M3_s{sd}.pt")); nets.append(n["joint"])
    return nets, cfg

# ---------------- 1. hat giong luat (CHI Train, attention OOF) ----------------
def rule_seeds(data, threads):
    cfg = V.PRESETS["M3"]; vocab = json.load(open(os.path.join(ROOT, "data", "processed", "vocab.json"), encoding="utf-8"))
    vs = V.vocab_sizes(vocab); tr = data["train"]; meta = load_meta(ROOT, "train"); folds = cv_folds(meta, root=ROOT)
    fc = json.load(open(os.path.join(OUT, "final_config.json"), encoding="utf-8")); assert fc["config"] == V.asdict(cfg)
    A = [[None] * len(tr) for _ in V.SEEDS]; P = np.zeros((len(V.SEEDS), len(tr)))
    colab = {}
    t0 = time.time()
    for si, sd in enumerate(V.SEEDS):
        for fi, (a_, va) in enumerate(folds):
            nets, _ = V.fit_nets(cfg, vs, [tr[i] for i in a_], [tr[i] for i in va], None, sd, fi + 1)
            pb, pt, al = V.predict(nets, [tr[i] for i in va], cfg)
            sc = np.maximum(pb, pt.max(1))
            for j, i in enumerate(va): A[si][i] = al[j]; P[si, i] = sc[j]
        oo = {r["window_id"]: r for r in V.read_jsonl(os.path.join(OUT, "m2", "oof", f"M3_s{sd}.jsonl"))}
        ref = np.array([max(oo[w.wid]["p_malicious"], max(oo[w.wid]["p_ttp"].values())) for w in tr])
        colab[sd] = float(np.corrcoef(P[si], ref)[0, 1])
        print(f"  seed {sd}: 5 fold xong ({(time.time() - t0) / 60:.1f} ph), tuong quan diem OOF host vs Colab {colab[sd]:.3f}", flush=True)
    alpha = [np.mean([A[si][i] for si in range(len(V.SEEDS))], 0) for i in range(len(tr))]
    rd = readable(ROOT, [w.wid for w in tr])

    def top_events(i, k=5):
        a = alpha[i]; idx = np.argsort(-a)[:k]
        return [(int(j), float(a[j])) for j in idx]
    def feats(e):
        return ([("image_name", e["image_name"] or "<none>"), ("event_id", str(e["event_id"]))] +
                [("cmd_token", t) for t in e["cmd_tokens"]])
    neg = [i for i, w in enumerate(tr) if not w.y_bin]
    neg_cnt = Counter()
    for i in neg:
        seen = set()
        for j, _ in top_events(i): seen |= set(feats(rd[tr[i].wid][j]))
        neg_cnt.update(seen)
    out = {"source": "CHI Train; alpha OOF (mo hinh fold khong thay cua so), trung binh 5 seed M3, huan luyen lai tren host CPU",
           "oof_score_corr_host_vs_colab": colab, "top_k_events": 5, "n_train_neg": len(neg), "ttp": {}}
    for j_t, t in enumerate(TTPS):
        pos = [i for i, w in enumerate(tr) if w.y_ttp[j_t] > 0]
        cnt, mass = Counter(), defaultdict(float); org = Counter(); examples = Counter()
        for i in pos:
            seen = set()
            for j, a in top_events(i):
                e = rd[tr[i].wid][j]; org[e["origin"]] += 1
                if e["cmd_canon"]: examples[e["cmd_canon"][:160]] += 1
                for f in feats(e): mass[f] += a / len(pos); seen.add(f)
            cnt.update(seen)
        rows = {}
        for cat_ in ("image_name", "event_id", "cmd_token"):
            items = [f for f in cnt if f[0] == cat_]
            items.sort(key=lambda f: (-mass[f], f[1]))
            rows[cat_] = [{"value": f[1], "alpha_mass": round(mass[f], 4), "share_pos_windows": round(cnt[f] / len(pos), 3),
                           "share_neg_windows": round(neg_cnt[f] / len(neg), 3),
                           "lift": round((cnt[f] / len(pos)) / max(neg_cnt[f] / len(neg), 1.0 / len(neg)), 2)} for f in items[:15]]
        out["ttp"][t] = {"n_windows": len(pos), "top5_origin_share": {k: round(v / max(1, sum(org.values())), 3) for k, v in org.items()},
                         **rows, "top_cmd_canon": [{"cmd": c, "n": n} for c, n in examples.most_common(5)]}
    with open(os.path.join(OUT, "rule_seeds_train.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(out, f, indent=1)
    np.save(os.path.join(OUT, "m4_oof_alpha_cache.npy"), np.array([np.pad(a, (0, 64 - len(a))) for a in alpha]))
    return out

# ---------------- 2. attention tren test (ens) ----------------
def ens_scores(nets, ws, cfg, idx_fn=None):
    R = [V.predict({"joint": n}, ws, cfg, idx_fn=idx_fn) for n in nets]
    pb = np.mean([r[0] for r in R], 0); pt = np.mean([r[1] for r in R], 0)
    al = [np.mean([r[2][i] for r in R], 0) for i in range(len(ws))]
    return pb, pt, al, R

def detected_positives(data, nets, cfg, sel):
    out = {}
    for s in ("t_clean", "t_novel"):
        ws = [w for w in data[s] if w.y_bin]
        pb, pt, al, R = ens_scores(nets, ws, cfg)
        sc = V.chosen_score(pb, pt, sel["binary_score"])
        keep = [i for i in range(len(ws)) if sc[i] >= sel["binary"]]
        out[s] = {"ws": [ws[i] for i in keep], "pb": pb[keep], "pt": pt[keep], "al": [al[i] for i in keep],
                  "seed": [(r[0][keep], r[1][keep], [r[2][i] for i in keep]) for r in R], "n_pos": len(ws)}
    return out

def test_attention(data, det, sel):
    rd = readable(ROOT, [w.wid for s in det for w in det[s]["ws"]])
    rows = []
    for s, d in det.items():
        for i, w in enumerate(d["ws"]):
            a = d["al"][i]; idx = np.argsort(-a)[:5]
            pred_ttp = [t for j, t in enumerate(TTPS) if d["pt"][i, j] >= sel["ttp"][t]]
            rows.append({"window_id": w.wid, "split": s, "p_ens": round(float(V.chosen_score(d["pb"][i:i + 1], d["pt"][i:i + 1], sel["binary_score"])[0]), 4),
                         "ttp_true": [t for j, t in enumerate(TTPS) if w.y_ttp[j] > 0], "ttp_pred": pred_ttp, "n_events": len(a),
                         "top5": [{"idx": int(j), "alpha": round(float(a[j]), 4), **{k: v for k, v in rd[w.wid][j].items() if k != "cmd_tokens"}} for j in idx]})
    V.write_jsonl(os.path.join(OUT, "attention_topk_test.jsonl"), rows)
    return rows

# ---------------- 3. faithfulness ----------------
def faithfulness(data, nets, cfg, det, sel):
    ws_all = [w for s in det for w in det[s]["ws"]]
    al_ens = [a for s in det for a in det[s]["al"]]
    al_seed = [[a for s in det for a in det[s]["seed"][si][2]] for si in range(len(nets))]
    rng = np.random.default_rng(SEED)
    res = {"n_windows_detected": {s: len(det[s]["ws"]) for s in det}, "n_pos": {s: det[s]["n_pos"] for s in det},
           "random_repeats": 10, "n_boot": N_BOOT, "models": {}}
    rnd = {k: [[np.sort(rng.choice(len(w), size=k, replace=False)) if len(w) > k else None for _ in range(10)] for w in ws_all] for k in KS}

    def run(netlist, del_sets):
        """del_sets: list (per window) cac chi so xoa -> (p_bin, p_ttp) trung binh netlist."""
        keep = {w.wid: np.setdiff1d(np.arange(len(w)), d) for w, d in zip(ws_all, del_sets)}
        R = [V.predict({"joint": n}, ws_all, cfg, idx_fn=lambda w: keep[w.wid]) for n in netlist]
        return np.mean([r[0] for r in R], 0), np.mean([r[1] for r in R], 0)
    ytt = np.stack([w.y_ttp for w in ws_all]) > 0
    for mname, netlist, alist in [("ens", nets, al_ens)] + [(f"s{sd}", [nets[si]], al_seed[si]) for si, sd in enumerate(V.SEEDS)]:
        base_b, base_t = run(netlist, [np.array([], int)] * len(ws_all))
        res["models"][mname] = {}
        for k in KS:
            ok = np.array([len(w) > k for w in ws_all])
            top = [np.sort(np.argsort(-a)[:k]) if len(a) > k else np.array([], int) for a in alist]
            tb, tt = run(netlist, top)
            rb = np.zeros((10, len(ws_all))); rt = np.zeros((10, len(ws_all)))
            for r in range(10):
                b_, t_ = run(netlist, [d[r] if d[r] is not None else np.array([], int) for d in rnd[k]])
                rb[r] = b_; rt[r] = ((base_t - t_) * ytt).sum(1) / np.maximum(ytt.sum(1), 1)
            d_top_b = base_b - tb; d_rnd_b = (base_b[None] - rb).mean(0)
            d_top_t = ((base_t - tt) * ytt).sum(1) / np.maximum(ytt.sum(1), 1); d_rnd_t = rt.mean(0)
            out = {"n": int(ok.sum())}
            for nm, dt, dr in (("p_bin", d_top_b, d_rnd_b), ("p_ttp_true", d_top_t, d_rnd_t)):
                diff = (dt - dr)[ok]; b = np.random.default_rng(SEED)
                bs = [diff[b.integers(0, len(diff), len(diff))].mean() for _ in range(N_BOOT)]
                lo, hi = np.percentile(bs, [2.5, 97.5])
                out[nm] = {"drop_topk": round(float(dt[ok].mean()), 4), "drop_random": round(float(dr[ok].mean()), 4),
                           "diff": round(float(diff.mean()), 4), "lo": round(float(lo), 4), "hi": round(float(hi), 4),
                           "faithful": bool(lo > 0)}
            res["models"][mname][str(k)] = out
        print(f"  faithfulness {mname}: " + " | ".join(f"k={k} bin {res['models'][mname][str(k)]['p_bin']['diff']:+.3f} ttp {res['models'][mname][str(k)]['p_ttp_true']['diff']:+.3f}" for k in KS), flush=True)
    with open(os.path.join(OUT, "faithfulness.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(res, f, indent=1)
    return res

# ---------------- 4. ONNX ----------------
def onnx_export(data):
    import onnxruntime as ort
    nets, cfg = load_ens()
    os.makedirs("models", exist_ok=True)
    ws = data["t_novel"]
    batches = [V.collate([V.eval_seq(w, cfg) for w in ws[i:i + 32]]) for i in range(0, len(ws), 32)]
    rep = {"opset": 17, "dynamic_axes": "batch, time", "parity_set": "toan T-novel (149 cua so), batch 32", "models": {}}
    for name, mods in (("vtseq_M3_s1337", [nets[0]]), ("vtseq_M3_ens", nets)):
        m = V.ExportVTSeq(mods).eval(); path = f"models/{name}.onnx"
        ex = batches[0]
        torch.onnx.export(m, tuple(ex), path, opset_version=17, dynamo=False,
                          input_names=["cat", "cmd", "num", "lens"], output_names=["p_bin", "p_ttp", "alpha"],
                          dynamic_axes={"cat": {0: "batch", 1: "time"}, "cmd": {0: "batch", 1: "time"}, "num": {0: "batch", 1: "time"},
                                        "lens": {0: "batch"}, "p_bin": {0: "batch"}, "p_ttp": {0: "batch"}, "alpha": {0: "batch", 1: "time"}})
        so = ort.SessionOptions(); so.intra_op_num_threads = 1; so.inter_op_num_threads = 1
        sess = ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])
        mx = {"p_bin": 0.0, "p_ttp": 0.0, "alpha": 0.0}
        for cat, cmd, num, lens in batches:
            o = sess.run(None, {"cat": cat.numpy(), "cmd": cmd.numpy(), "num": num.numpy(), "lens": lens.numpy()})
            with torch.no_grad():
                outs = [n(cat, cmd, num, lens) for n in mods]                     # ban pack (chuan)
                pb = torch.stack([torch.sigmoid(x["logit_bin"]) for x in outs]).mean(0).numpy()
                pt = torch.stack([torch.sigmoid(x["logit_ttp"]) for x in outs]).mean(0).numpy()
                al = torch.stack([x["alpha"] for x in outs]).mean(0).numpy()
            msk = (np.arange(cat.shape[1])[None] < lens.numpy()[:, None])
            mx["p_bin"] = max(mx["p_bin"], float(np.abs(o[0] - pb).max())); mx["p_ttp"] = max(mx["p_ttp"], float(np.abs(o[1] - pt).max()))
            mx["alpha"] = max(mx["alpha"], float(np.abs(o[2] - al)[msk].max()))
        # do tre: batch 1 (tung cua so) va batch 32, 1 thread
        lat = {}
        singles = [V.collate([V.eval_seq(w, cfg)]) for w in ws]
        for _ in range(10): sess.run(None, {k_: v.numpy() for k_, v in zip(["cat", "cmd", "num", "lens"], singles[0])})
        t1 = []
        for _ in range(3):
            for b in singles:
                feed = {k_: v.numpy() for k_, v in zip(["cat", "cmd", "num", "lens"], b)}
                t = time.perf_counter(); sess.run(None, feed); t1.append((time.perf_counter() - t) * 1000)
        t32 = []
        for _ in range(10):
            for b in batches:
                feed = {k_: v.numpy() for k_, v in zip(["cat", "cmd", "num", "lens"], b)}
                t = time.perf_counter(); sess.run(None, feed); t32.append((time.perf_counter() - t) * 1000 / len(b[3]))
        lat["batch1_ms_per_window"] = {"mean": round(float(np.mean(t1)), 3), "p95": round(float(np.percentile(t1, 95)), 3), "n": len(t1)}
        lat["batch32_ms_per_window"] = {"mean": round(float(np.mean(t32)), 3), "p95": round(float(np.percentile(t32, 95)), 3), "n": len(t32)}
        rep["models"][name] = {"file": path, "bytes": os.path.getsize(path), "n_nets": len(mods),
                               "parity_max_abs_diff": mx, "parity_ok_1e-4": all(v < 1e-4 for v in mx.values()),
                               "latency_onnxruntime_cpu_1thread": lat}
        print(f"  {name}: parity {mx} | b1 {lat['batch1_ms_per_window']} | b32 {lat['batch32_ms_per_window']}", flush=True)
    import platform
    rep["host"] = {"cpu": platform.processor(), "onnxruntime": ort.__version__, "torch": torch.__version__, "threads": 1}
    with open(os.path.join(OUT, "onnx_report.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(rep, f, indent=1)
    return rep

def report():
    F = json.load(open(os.path.join(OUT, "faithfulness.json"), encoding="utf-8"))
    O = json.load(open(os.path.join(OUT, "onnx_report.json"), encoding="utf-8"))
    S = json.load(open(os.path.join(OUT, "rule_seeds_train.json"), encoding="utf-8"))
    L = ["# VT-Guard Buoc 6 moc 4 - giai thich bang attention + ONNX (chay tren host)", "",
         "Brief muc 6 da SUA (2026-10-17): hat giong luat CHI tu Train (attention OOF); attention test CHI de giai thich.", "",
         f"**(1) Faithfulness** - cua so duong duoc VT-Seq-ens phat hien: T-clean {F['n_windows_detected']['t_clean']}/{F['n_pos']['t_clean']}, "
         f"T-novel {F['n_windows_detected']['t_novel']}/{F['n_pos']['t_novel']}. Xoa top-k event theo alpha vs xoa k event ngau nhien "
         "(10 lan, cung k); muc giam p_bin va p_ttp (trung binh cac TTP that). Hieu = giam top-k - giam ngau nhien, CI bootstrap 95% "
         "(1000, theo cua so). 'Dat' = CI > 0.", "",
         "| Mo hinh | k | n | p_bin: giam top-k / ngau nhien / hieu [CI] | p_ttp dung TTP: giam top-k / ngau nhien / hieu [CI] |", "|---|---|---|---|---|"]
    for m, byk in F["models"].items():
        for k, r in byk.items():
            c = lambda x: f"{r[x]['drop_topk']:.3f} / {r[x]['drop_random']:.3f} / **{r[x]['diff']:+.3f}** [{r[x]['lo']:+.3f}, {r[x]['hi']:+.3f}] {'dat' if r[x]['faithful'] else 'KHONG dat'}"
            L.append(f"| {m} | {k} | {r['n']} | {c('p_bin')} | {c('p_ttp_true')} |")
    L += ["", "**(2) Hat giong luat theo TTP - CHI Train, attention OOF** (alpha tu mo hinh fold khong thay cua so, trung binh 5 seed; "
          f"mo hinh fold huan luyen lai tren host, tuong quan diem OOF voi Colab {min(S['oof_score_corr_host_vs_colab'].values()):.3f}-"
          f"{max(S['oof_score_corr_host_vs_colab'].values()):.3f}). Top-5 event/cua so; pos/neg = ti le cua so Train duong (TTP) / am "
          "co gia tri trong top-5; lift = pos/neg. Day du: `reports/step6/rule_seeds_train.json`.", ""]
    for t, v in S["ttp"].items():
        L.append(f"- **{t}** ({v['n_windows']} cua so; top-5 tu event cay {v['top5_origin_share'].get('own', 0):.0%} / nen {v['top5_origin_share'].get('bg', 0):.0%})")
        for c_ in ("image_name", "event_id", "cmd_token"):
            L.append(f"  - {c_}: " + "; ".join(f"`{x['value']}` {x['share_pos_windows']:.2f}/{x['share_neg_windows']:.2f} (lift {x['lift']})" for x in v[c_][:6]))
    L += ["", "**Canh bao cho Buoc 7 (khong dung truc tiep lam luat):**",
          "- `\\windows\\temp\\ntds_t0` = duong dan mac dinh cua ART (`ntds_T1003`), chua ma ky thuat -> dau vet bo sinh; loai khoi hat giong.",
          "- `cmd.exe` / `cmd /c` dung dau moi TTP: ART chay qua cmd (cmd.exe chi o 8% cua so am Train) - bat doi xung bo sinh da biet (#9); "
          "luat phai dua tren lenh con, khong dua tren vo cmd.",
          "- Attention dung chung cho moi TTP (mot pooling): cua so nhieu TTP (phien mixed) lam token cua TTP khac xuat hien (vd nslookup o "
          "moi TTP) -> Buoc 7 can do do dac hieu theo TTP (cua so mot TTP / so voi cua so TTP khac).",
          "- T1003.003: 34% top-5 la event NEN (ESENT 216/103, vssvc, rundll32) - tac dong phu mot-phia (#10/#11); luat nen dua tren "
          "ntdsutil `ifm create full`, khong tren event nen.",
          "- T1087.002: token dau la `powershell.exe` (lift ~81) va EID 40961/4104 - dau vet bo sinh (ART chay test trong "
          "powershell con; gioi han `<launcher>`->powershell.exe da biet, dataset card #11). Luat T1087.002 phai dua tren lenh that "
          "(`net user /domain`, `adsisearcher`, `objectcategory`), khong dua tren su hien dien cua PowerShell.", "",
          "**(3) ONNX** (opset 17, truc dong batch + time; dau ra p_bin, p_ttp, alpha). Parity voi PyTorch (ban pack) tren toan T-novel; "
          f"do tre onnxruntime {O['host']['onnxruntime']} CPU 1 thread tren host ({O['host']['cpu']}).", "",
          "| Mo hinh | File | So mang | max abs diff p_bin / p_ttp / alpha | Parity < 1e-4 | batch 1: ms/cua so (TB / p95) | batch 32: ms/cua so (TB / p95) |",
          "|---|---|---|---|---|---|---|"]
    for n, r in O["models"].items():
        mx = r["parity_max_abs_diff"]; l1 = r["latency_onnxruntime_cpu_1thread"]["batch1_ms_per_window"]; l32 = r["latency_onnxruntime_cpu_1thread"]["batch32_ms_per_window"]
        L.append(f"| {n} | `{r['file']}` ({r['bytes'] / 1e6:.2f} MB) | {r['n_nets']} | {mx['p_bin']:.1e} / {mx['p_ttp']:.1e} / {mx['alpha']:.1e} | "
                 f"{'dat' if r['parity_ok_1e-4'] else 'KHONG'} | {l1['mean']:.3f} / {l1['p95']:.3f} | {l32['mean']:.3f} / {l32['p95']:.3f} |")
    L.append("")
    with open(os.path.join(OUT, "m4_explain.md"), "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(L))
    print("\n".join(L))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("what", nargs="?", default="all"); ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    torch.set_num_threads(a.threads); torch.use_deterministic_algorithms(True, warn_only=True)
    if a.what == "report": report(); return
    data, _ = V.load_data(ROOT)
    if a.what in ("seeds", "all"): rule_seeds(data, a.threads)
    if a.what in ("test", "faith", "all"):
        nets, cfg = load_ens()
        sel = json.load(open(os.path.join(OUT, "m3", "sel", "vtseq_M3_ens.json"), encoding="utf-8"))
        det = detected_positives(data, nets, cfg, sel)
        if a.what in ("test", "all"): test_attention(data, det, sel)
        if a.what in ("faith", "all"): faithfulness(data, nets, cfg, det, sel)
    if a.what in ("onnx", "all"): onnx_export(data)
    if a.what in ("report", "all"): report()

if __name__ == "__main__":
    main()
