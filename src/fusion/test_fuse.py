#!/usr/bin/env python3
"""VT-Guard Buoc 8 moc 1 - unit test cho src/fusion/fuse.py.
(1) hoc/chon chi doc OOF (khong rules_train.jsonl, khong preds test), (2) OOF AI = trung binh OOF 5 seed M3,
(3) F4 CV long (fold k khong thay nhan fold k), (4) nguong FPR <= 1% tren am OOF, (5) F2/F3 dung cong thuc + nguong khoa,
(6) bien the B che kenh luat TTP khong co trong bo luat cuoi, (7) tat dinh. Chay: python src/fusion/test_fuse.py
"""
import builtins, json, os, sys, time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval"): sys.path.insert(0, os.path.join(HERE, d))
import fuse as F                                        # noqa: E402
from evaluate import cv_folds, TTPS                     # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RES = []

def check(name, cond, detail=""):
    RES.append(bool(cond)); print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""), flush=True)

def main():
    t0 = time.time(); os.chdir(ROOT)
    # ---- 1. chi doc OOF ----
    opened = []; real = builtins.open
    def spy(f, mode="r", *a, **k):
        opened.append((str(f).replace("\\", "/"), mode)); return real(f, mode, *a, **k)
    builtins.open = spy
    try:
        D = F.load_oof(ROOT); folds = cv_folds(D["meta"], root=ROOT)
        DB = F.mask_rule_channels(D, F.final_rule_ttps(ROOT))
        outA, selA = F.select(D, folds); outB, selB = F.select(DB, folds)
    finally: builtins.open = real
    names = [f for f, m in opened]
    bad = [f for f in names if f.endswith("rules_train.jsonl") or any(f.endswith(f"_{s}.jsonl") and "/preds/" in f for s in ("t_clean", "t_hard", "t_novel"))]
    split_text = [(f, m) for f, m in opened if any(s in f for s in ("splits/t_clean", "splits/t_hard", "splits/t_novel")) and "b" not in m]
    check("1a hoc/chon KHONG doc rules_train.jsonl hay preds tap test", not bad, f"{bad}")
    check("1b split test chi mo 'rb' de bam sha256", not split_text)
    check("1c doc dung 2 file OOF", any(f.endswith("vtseq_M3_ens_train.jsonl") for f in names) and any(f.endswith("rules_oof_train.jsonl") for f in names))
    # ---- 2. OOF AI = trung binh 5 seed M3 (moc 2 Buoc 6) ----
    order = [w["window_id"] for w in D["meta"]]
    pb, pt = [], []
    for sd in (1337, 7, 42, 2024, 99):
        rows = {json.loads(l)["window_id"]: json.loads(l) for l in open(os.path.join("reports", "step6", "m2", "oof", f"M3_s{sd}.jsonl"), encoding="utf-8")}
        pb.append([rows[w]["p_malicious"] for w in order]); pt.append([[rows[w]["p_ttp"][t] for t in TTPS] for w in order])
    pb, pt = np.mean(pb, 0), np.mean(pt, 0)
    ok = np.allclose(D["pk"], pt, atol=2e-5) and np.allclose(D["p"], np.maximum(pb, pt.max(1)), atol=2e-5)
    check("2 OOF AI == trung binh OOF 5 seed M3 (p = p_bin' nhu Buoc 6)", ok, f"max lech {np.abs(D['pk'] - pt).max():.1e}")
    # ---- 3. F4 CV long ----
    prm, nested = F.fit_strategy("F4", D, folds)
    tr0, va0 = folds[0]; rng = np.random.default_rng(0)
    D2 = dict(D); y2 = D["y"].copy(); y2[va0] = rng.permutation(y2[va0]); yk2 = D["yk"].copy(); yk2[va0] = yk2[va0][rng.permutation(len(va0))]
    D2["y"], D2["yk"] = y2, yk2
    _, nested2 = F.fit_strategy("F4", D2, folds)
    check("3a F4: doi nhan fold 0 -> diem OOF long cua fold 0 KHONG doi (mo hinh fold 0 khong thay nhan fold 0)",
          np.allclose(nested[0][va0], nested2[0][va0]) and np.allclose(nested[1][va0], nested2[1][va0]))
    check("3b F4: cac fold roi nhau va phu du 483 cua so", sorted(np.concatenate([v for _, v in folds]).tolist()) == list(range(483)))
    check("3c F4: 7 dac trung moi hoi quy", all(m.coef_.shape[1] == 7 for m in prm["models"].values()), f"{len(prm['models'])} mo hinh")
    # ---- 4. nguong FPR ----
    for st, out in (("F3", outA["F3"]), ("F4", outA["F4"])):
        db, dk, s = F.decisions_oof(D, st, out["params"], out["nested"])
        check(f"4 {st}: FPR tren am OOF <= 1% tai nguong da chon", db[~D["y"]].mean() <= 0.01, f"FPR {db[~D['y']].mean():.4f}")
    # ---- 5. F2 / F3 ----
    db, dk, s, sk = F.decide("F2", outA["F2"]["params"], D["p"], D["pk"], D["r"], D["rk"])
    sel = json.load(open(F.AI_SEL, encoding="utf-8"))
    check("5a F2 = (p >= tau khoa Buoc 6) OR r; TTP tuong tu", np.array_equal(db, (D["p"] >= sel["binary"]) | (D["r"] >= 0.5))
          and np.array_equal(dk, (D["pk"] >= np.array([sel["ttp"][t] for t in TTPS])) | (D["rk"] >= 0.5)))
    b = outA["F3"]["params"]["beta"]; s3, _ = F.scores("F3", outA["F3"]["params"], D["p"], D["pk"], D["r"], D["rk"])
    check("5b F3: beta trong luoi, s = p + beta*r", b in F.BETAS and np.allclose(s3, D["p"] + b * D["r"]), f"beta {b}")
    # ---- 6. bien the B ----
    keep = F.final_rule_ttps(ROOT)
    m = np.array([t in keep for t in TTPS])
    check("6 bien the B: r_k = 0 cho TTP khong co luat cuoi, giu nguyen TTP co luat", np.all(DB["rk"][:, ~m] == 0) and np.array_equal(DB["rk"][:, m], D["rk"][:, m]),
          f"giu {keep}")
    # ---- 7. tat dinh ----
    outA2, selA2 = F.select(D, folds)
    same = selA2["chosen"] == selA["chosen"] and all(abs(outA2[s_]["m"]["macro_f1_ttp"] - outA[s_]["m"]["macro_f1_ttp"]) < 1e-12 for s_ in F.ORDER)
    check("7 chay lai -> cung lua chon va chi so", same, f"A: {selA['chosen']}, B: {selB['chosen']}")
    print(f"\nKET QUA: {sum(RES)}/{len(RES)} PASS trong {time.time() - t0:.1f}s")
    sys.exit(0 if all(RES) else 1)

if __name__ == "__main__":
    main()
