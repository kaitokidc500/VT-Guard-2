#!/usr/bin/env python3
"""VT-Guard Buoc 9 - lenh `verify` (kieu A, docs/STEP9-BRIEF.md muc 6.2-6.3): chay lai pipeline suy luan + evaluate.py tren 3 tap
test da dong bang, so voi so lieu da bao cao, in DAT / KHONG DAT tung muc (0 lech). Khong huan luyen, khong chon lai gi.
Pipeline (featurize -> ONNX -> Sigma -> F3-B) KHONG doc nhan; nhan chi vao buoc cham (evaluate.py) nhu Buoc 8.

  V1 checksum dataset-v1.2 (splits + vocab) == reports/dataset_stats.json            (evaluate.check_dataset)
  V2 checksum artefact: models/vtseq_M3_ens.onnx == step6_results.json; artefact dashboard == dashboard/artefacts_sha256.json
  V3 featurize(windows.jsonl) == vector trong splits/<tap>.jsonl                         (featurizer + vocab dong bang)
  V4 infer.py: quyet dinh nhi phan + TTP == reports/preds/fusion_<tap>.jsonl; |diem lech| <= 1e-5
  V5 canh bao == reports/step8/alerts_<tap>.jsonl (window_id, decision_source, ttps, luat khop, top-5 attention)
  V6 evaluate() tren diem VUA CHAY (F3-B, nguong khoa) == reports/step8/eval/fusion_F3B.json (moi chi so + CI bootstrap seed 1337)
     va bang tom tat reports/step8_results.json test.F3B
  V7 so lieu bang chinh: dem lai TP / FP / FN tu du doan da luu (B0 Wazuh, VT-Seq-ens, chi-luat) == eval JSON Buoc 5 / 6 / 7

Chu ky cong cu T-hard (FPR theo chu ky) doc tu data/processed/all.events.jsonl neu co (host), khong co (container: khong dua
event da gan nhan vao image) thi doc ban da tinh san reports/step9/hn_signatures.json (--write-cache tao tu host).
Chay: python src/pipeline/verify.py [--root .] [--out reports/step9/verify.json] [--write-cache]
Ma thoat 0 = DAT moi muc, 1 = co muc KHONG DAT.
"""
import argparse, hashlib, json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../dataset", "../eval"): sys.path.insert(0, os.path.join(HERE, d))
import infer as INF                                                               # noqa: E402
import featurize as FZ                                                            # noqa: E402
from evaluate import check_dataset, load_all_meta, evaluate, hn_signatures, TEST_SPLITS, TTPS   # noqa: E402

TOL_SCORE, TOL_METRIC = 1e-5, 1e-9
HN_CACHE = os.path.join("reports", "step9", "hn_signatures.json")
REF7 = [("b0_wazuh", "reports/step5/b0_wazuh.json"), ("vtseq_M3_ens", "reports/step6/eval/vtseq_M3_ens.json"),
        ("rules", "reports/step7/eval/rules.json")]

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def jl(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]

def diff(a, b, path="", out=None, tol=TOL_METRIC):
    """So sanh de quy hai cay JSON; float so voi dung sai tol. -> danh sach duong dan lech (toi da 20)."""
    out = [] if out is None else out
    if len(out) >= 20: return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b: out.append(f"{path}/{k} (thieu)")
            else: diff(a[k], b[k], f"{path}/{k}", out, tol)
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b): out.append(f"{path} (do dai {len(a)} != {len(b)})")
        else:
            for i, (x, y) in enumerate(zip(a, b)): diff(x, y, f"{path}[{i}]", out, tol)
    elif isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        if a != b: out.append(f"{path}: {a!r} != {b!r}")
    elif not ((math.isnan(a) and math.isnan(b)) or abs(a - b) <= tol):
        out.append(f"{path}: {a} != {b}")
    return out

def load_hn_sig(root, write_cache):
    ev = os.path.join(root, "data", "processed", "all.events.jsonl"); cache = os.path.join(root, HN_CACHE)
    meta = load_all_meta(root); rids = {w["run_id"] for w in meta["t_hard"]}
    if os.path.exists(ev):
        sig = hn_signatures(root, rids); src = "data/processed/all.events.jsonl"
        if write_cache:
            os.makedirs(os.path.dirname(cache), exist_ok=True)
            with open(cache, "w", encoding="utf-8", newline="\n") as f:
                json.dump({k: list(v) for k, v in sorted(sig.items())}, f, indent=1, ensure_ascii=False)
        elif os.path.exists(cache):                                          # host: ban luu phai trung ban tinh lai
            c = json.load(open(cache, encoding="utf-8"))
            assert {k: tuple(v) for k, v in c.items()} == sig, f"{HN_CACHE} khac ban tinh tu all.events.jsonl"
        return sig, src
    if not os.path.exists(cache): sys.exit(f"Thieu {HN_CACHE} (chay tren host: python src/pipeline/verify.py --write-cache)")
    c = json.load(open(cache, encoding="utf-8"))
    assert set(c) == rids, f"{HN_CACHE} khong khop run_id T-hard"
    return {k: tuple(v) for k, v in c.items()}, HN_CACHE.replace(os.sep, "/")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("VTGUARD_HOME") or ".")
    ap.add_argument("--out", default=os.path.join("reports", "step9", "verify.json"))
    ap.add_argument("--write-cache", action="store_true", help=f"(host) ghi {HN_CACHE} tu all.events.jsonl")
    a = ap.parse_args(); root = a.root; t_start = time.time()
    R = {}                                                                       # id -> (dat?, chi tiet)
    def check(k, name, ok, detail):
        R[k] = {"ten": name, "dat": bool(ok), "chi_tiet": detail}
        print(f"[{'DAT' if ok else 'KHONG DAT'}] {k} {name} - {detail}", flush=True)

    # V1, V2
    cd = check_dataset(root); check("V1", "checksum dataset-v1.2 (splits + vocab)", all(v is True for v in cd.values()), cd)
    s6 = json.load(open(os.path.join(root, "reports", "step6_results.json"), encoding="utf-8"))["onnx"]["vtseq_M3_ens"]["sha256"]
    onnx_ok = sha(os.path.join(root, INF.ONNX_ENS)) == s6
    man = json.load(open(os.path.join(root, "dashboard", "artefacts_sha256.json"), encoding="utf-8"))
    bad = [k for k, h in man.items() if not os.path.exists(os.path.join(root, k)) or sha(os.path.join(root, k)) != h]
    check("V2", "checksum ONNX + artefact bao cao", onnx_ok and not bad, {"onnx_ens": onnx_ok, "artefact": f"{len(man) - len(bad)}/{len(man)}", "lech": bad})

    # V3-V5: chay pipeline
    meta = load_all_meta(root); P = INF.Pipeline(root, threads=1); fresh, n_win, feat_bad, dec_bad, mx, al_bad, n_al = {}, 0, 0, 0, 0.0, [], 0
    for s in TEST_SPLITS:
        ids = [w["window_id"] for w in meta[s]]
        W = INF.read_windows(os.path.join(root, "data", "processed", "windows.jsonl"), ids)
        assert [w["window_id"] for w in W] == ids, f"windows.jsonl thieu cua so {s}"
        sp = {r["window_id"]: r for r in jl(os.path.join(root, "data", "processed", "splits", f"{s}.jsonl"))}
        for w in W:
            cat, cmd, num = FZ.featurize_window(w, P.vocab); r_ = sp[w["window_id"]]
            feat_bad += not (cat == r_["cat"] and [[list(x) for x in c] for c in cmd] == r_["cmd"] and num == r_["num"])
        res = []
        for i in range(0, len(W), 32): res += P.run(W[i:i + 32])
        n_win += len(res)
        ref = {r["window_id"]: r for r in jl(os.path.join(root, "reports", "preds", f"fusion_{s}.jsonl"))}
        for r in res:
            f = ref[r["window_id"]]
            dec_bad += (r["score"] >= P.thr) != (f["p_malicious"] >= P.thr)
            dec_bad += sum((r["score_ttp"][t] >= P.thr_k[j]) != (f["p_ttp"][t] >= P.thr_k[j]) for j, t in enumerate(TTPS))
            mx = max(mx, abs(r["score"] - f["p_malicious"]), *(abs(r["score_ttp"][t] - f["p_ttp"][t]) for t in TTPS))
        fresh[s] = {r["window_id"]: {"p": r["score"], "p_ttp": dict(r["score_ttp"])} for r in res}
        got = {x["window_id"]: x for x in (P.alert_record(r) for r in res if r["alert"])}
        want = {x["window_id"]: x for x in jl(os.path.join(root, "reports", "step8", f"alerts_{s}.jsonl"))}
        n_al += len(got)
        if set(got) != set(want): al_bad.append(f"{s}: tap window_id khac ({len(got)} vs {len(want)})")
        for k in set(got) & set(want):
            g, h = got[k], want[k]
            key = lambda x: (x["decision_source"], x["ttps"], [r_["id"] for r_ in x["rule_ids"]], [e["idx"] for e in x["attention_top5"]])
            if key(g) != key(h) or abs(g["score"] - h["score"]) > TOL_SCORE: al_bad.append(f"{s}:{k}")
    check("V3", "featurize == vector trong file split", feat_bad == 0, f"{n_win} cua so, {feat_bad} lech")
    check("V4", "infer.py == reports/preds/fusion_<tap>.jsonl", dec_bad == 0 and mx <= TOL_SCORE,
          f"{dec_bad} quyet dinh lech (nhi phan + 5 TTP x {n_win} cua so); diem lech lon nhat {mx:.2e}")
    check("V5", "canh bao == reports/step8/alerts_<tap>.jsonl", not al_bad, f"{n_al} canh bao; lech {al_bad[:5]}")

    # V6: cham lai bang evaluate.py tren diem vua chay
    F3 = json.load(open(os.path.join(root, "reports", "step8", "eval", "fusion_F3B.json"), encoding="utf-8"))
    hn_sig, hn_src = load_hn_sig(root, a.write_cache)
    res = evaluate("fusion_F3B", meta, fresh, F3["thresholds"], root=root, hn_sig=hn_sig)
    d6 = diff(res["splits"], F3["splits"])
    S8 = json.load(open(os.path.join(root, "reports", "step8_results.json"), encoding="utf-8"))["test"]["F3B"]
    head = {s: {"f1": res["splits"][s]["tuned"]["f1"], "fp": res["splits"][s]["tuned"]["fp"],
                "pr_auc": res["splits"][s]["pr_auc"] if s != "t_hard" else None,
                "macro_f1_ttp": res["splits"][s]["ttp_tuned"]["macro_f1"] if s != "t_hard" else None} for s in TEST_SPLITS}
    def r4(o):
        if isinstance(o, dict): return {k: (round(v, 4) if isinstance(v, float) and k in ("point", "lo", "hi") else r4(v)) for k, v in o.items()}
        return o
    d6b = diff(r4(head), S8, tol=5e-5)
    sm = {s: f"F1 {res['splits'][s]['tuned']['f1']['point']:.4f}, FP {res['splits'][s]['tuned']['fp']}/{res['splits'][s]['tuned']['n'] - res['splits'][s]['tuned']['n_pos']}"
             + (f", PR-AUC {res['splits'][s]['pr_auc']['point']:.4f}, macro-F1 TTP {res['splits'][s]['ttp_tuned']['macro_f1']['point']:.4f}" if s != "t_hard" else "")
          for s in TEST_SPLITS}
    check("V6", "evaluate() tren diem vua chay == eval Buoc 8 (F3-B, gom CI)", not d6 and not d6b,
          {"tom_tat": sm, "lech_eval": d6[:5], "lech_step8_results": d6b[:5], "chu_ky_t_hard": hn_src})

    # V7: bang chinh tu du doan da luu
    d7 = {}
    for model, ref in REF7:
        E = json.load(open(os.path.join(root, ref), encoding="utf-8")); thr = E["thresholds"]["binary"]
        for s in TEST_SPLITS:
            y = {w["window_id"]: bool(w["window_malicious"]) for w in meta[s]}
            pr = {r["window_id"]: r["p_malicious"] for r in jl(os.path.join(root, "reports", "preds", f"{model}_{s}.jsonl"))}
            tp = sum(pr[k] >= thr and y[k] for k in y); fp = sum(pr[k] >= thr and not y[k] for k in y); fn = sum(pr[k] < thr and y[k] for k in y)
            t = E["splits"][s]["tuned"]
            d7[f"{model}/{s}"] = {"tp_fp_fn": [tp, fp, fn], "ok": [tp, fp, fn] == [t["tp"], t["fp"], t["fn"]]}
    check("V7", "TP/FP/FN B0 / VT-Seq-ens / chi-luat == eval Buoc 5/6/7", all(v["ok"] for v in d7.values()),
          {"T-hard FP": {m: d7[f"{m}/t_hard"]["tp_fp_fn"][1] for m, _ in REF7}, "lech": [k for k, v in d7.items() if not v["ok"]]})

    ok = all(v["dat"] for v in R.values())
    import platform, onnxruntime
    out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "ket_qua": "DAT" if ok else "KHONG DAT",
           "dat": f"{sum(v['dat'] for v in R.values())}/{len(R)}", "kiem": R, "thoi_gian_s": round(time.time() - t_start, 1),
           "moi_truong": {"python": platform.python_version(), "onnxruntime": onnxruntime.__version__, "platform": platform.platform(),
                          "container": os.path.exists("/.dockerenv")}}
    if a.out:
        p = a.out if os.path.isabs(a.out) else os.path.join(root, a.out)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f: json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"\nVERIFY: {out['ket_qua']} ({out['dat']} muc) trong {out['thoi_gian_s']} s")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
