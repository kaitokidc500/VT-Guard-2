#!/usr/bin/env python3
"""VT-Guard Buoc 5 - bang so sanh nhieu mo hinh tu reports/step5/<model>.json (ket qua evaluate.py).

Bang: (1) chinh: T-clean F1/PR-AUC, T-novel F1/PR-AUC, macro-F1 TTP, recall T1003.003 muc phien;
(2) T-hard: FPR tong, co/khong cmd.exe, phan tang do dai, Spearman diem~do dai; (3) T-hard FPR theo chu ky cong cu;
(4) phan tang do dai T-clean/T-novel; (5) F1 theo TTP; (6) phat hien som; top trong so (neu ket qua co).
Moi chi so o NGUONG DA KHOA tren Train OOF, kem CI bootstrap 95%.
Mo hinh nhieu seed: ten nhom (vd b3_gru_a) khi khong co <ten>.json nhung co <ten>_s<seed>.json (--seeds) ->
o bang ghi "trung binh +- do lech chuan (n seed)" cua gia tri diem (khong CI), so dem ghi trung binh +- do lech chuan.
Chay: python src/baselines/summary.py --models b0_wazuh,b1_tfidf_a,b3_gru_a,... [--seeds 1337,7,42] [--weights ...] [--out f.md]
"""
import argparse, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "eval"))
from evaluate import fci, fw  # noqa: F401

TT = ["T1016", "T1018", "T1087.002", "T1654", "T1003.003"]

def short(c, d=3):
    if c is None or c.get("point") is None: return "-"
    if c.get("lo") is None: return f"{c['point']:.{d}f}"
    return f"{c['point']:.{d}f} [{c['lo']:.{d}f}, {c['hi']:.{d}f}]"

def ms(vals, d):
    v = np.array([x for x in vals if x is not None], float)
    if len(v) == 0: return "-"
    return f"{v.mean():.{d}f} +- {v.std(ddof=1) if len(v) > 1 else 0.0:.{d}f}"

def val(rs, get, d=3):
    """Chi so co CI: 1 ket qua -> diem [CI]; nhieu seed -> trung binh +- do lech chuan cua diem."""
    if len(rs) == 1: return short(get(rs[0]), d)
    return ms([(get(r) or {}).get("point") for r in rs], d)

def cnt(rs, get, d=1):
    """So dem (FP, so phien...): 1 ket qua -> so nguyen; nhieu seed -> trung binh +- do lech chuan."""
    if len(rs) == 1: return str(get(rs[0]))
    return ms([get(r) for r in rs], d)

RESULT_DIRS = (("reports", "step5"), ("reports", "step6", "eval"))

def load(root, m, seeds):
    """<m>.json (1 ket qua) hoac <m>_s<seed>.json (nhieu seed; chi cac seed co file) trong reports/step5 hoac reports/step6/eval."""
    for d in RESULT_DIRS:
        p = os.path.join(root, *d, f"{m}.json")
        if os.path.exists(p): return [json.load(open(p, encoding="utf-8"))]
    for d in RESULT_DIRS:
        ps = [os.path.join(root, *d, f"{m}_s{s}.json") for s in seeds]
        rs = [json.load(open(q, encoding="utf-8")) for q in ps if os.path.exists(q)]
        if rs: return rs
    raise FileNotFoundError(f"khong co ket qua cho {m}")

def tables(root, models, weights=(), thard_only=(), seeds=()):
    R = {m: load(root, m, seeds) for m in models}
    lab = {m: (f"{m} ({len(rs)} seed)" if len(rs) > 1 else m) for m, rs in R.items()}
    dsv = {r.get("dataset_version", "?") for rs in R.values() for r in rs}
    L = [f"Dataset: {', '.join(sorted(dsv))}. Moi chi so o nguong khoa tren Train OOF (B0: L chon tren Train); CI bootstrap 95%, 1000 lan, seed 1337.",
         "Mo hinh nhieu seed (ghi '(n seed)'): trung binh +- do lech chuan (ddof=1) cua gia tri diem qua cac seed; nguong khoa rieng moi seed.", ""]
    L += ["**(1) Bang chinh**", "",
          "| Mo hinh | T-clean F1 | T-clean PR-AUC | T-novel F1 | T-novel PR-AUC | macro-F1 TTP clean / novel | T1003.003 phien T-novel: nhi phan / nhan TTP (cua 6) |",
          "|---|---|---|---|---|---|---|"]
    for m, rs in R.items():
        if m in thard_only: continue
        sr = lambda r: r["splits"]["t_novel"]["tuned"]["ntds_session_recall"]
        has_ttp = all(sr(r).get("ttp_label") for r in rs)
        mac = lambda sp: (lambda r: r["splits"][sp].get("ttp_tuned", {}).get("macro_f1"))
        mc = val(rs, mac("t_clean"), 2) if all(mac("t_clean")(r) for r in rs) else "-"
        mn = val(rs, mac("t_novel"), 2) if all(mac("t_novel")(r) for r in rs) else "-"
        L.append(f"| {lab[m]} | {val(rs, lambda r: r['splits']['t_clean']['tuned']['f1'])} | {val(rs, lambda r: r['splits']['t_clean']['pr_auc'])} | "
                 f"{val(rs, lambda r: r['splits']['t_novel']['tuned']['f1'])} | {val(rs, lambda r: r['splits']['t_novel']['pr_auc'])} | {mc} / {mn} | "
                 f"{cnt(rs, lambda r: sr(r)['binary']['detected'])} / " + (cnt(rs, lambda r: sr(r)['ttp_label']['detected']) if has_ttp else "-") + " |")
    nh = sorted({r["splits"]["t_hard"]["n"] for rs in R.values() for r in rs})
    L += ["", f"**(2) T-hard ({'/'.join(map(str, nh))} cua so, 0 duong)**", "",
          "| Mo hinh | FPR tong | FP (cua n) | Co cmd.exe: FP | Khong cmd.exe: FP | Du 64: FP | Ngan: FP | Spearman(diem, n_events) cua so am T-hard |",
          "|---|---|---|---|---|---|---|---|"]
    for m, rs in R.items():
        h0 = rs[0]["splits"]["t_hard"]; t0 = h0["tuned"]
        T = lambda r: r["splits"]["t_hard"]["tuned"]
        name = lab[m] + (" (chi T-hard, so voi (a))" if m in thard_only else "")
        g = lambda k: (cnt(rs, lambda r: T(r)["fpr_by_cmd"].get(k, {}).get("fp", 0)) + f"/{t0['fpr_by_cmd'].get(k, {}).get('n', '-')}")
        lb = lambda k: cnt(rs, lambda r: T(r)["fpr_by_length"][k]["fp"]) + f"/{t0['fpr_by_length'][k]['n_neg']}"
        L.append(f"| {name} | {val(rs, lambda r: T(r)['fpr'])} | {cnt(rs, lambda r: T(r)['fp'])}/{h0['n']} | {g('co cmd.exe')} | {g('khong cmd.exe')} | "
                 f"{lb('full64')} | {lb('short')} | {val(rs, lambda r: r['splits']['t_hard'].get('spearman_score_len_neg'), 2)} |")
    sigs = []
    for rs in R.values():
        for sg in rs[0]["splits"]["t_hard"]["tuned"]["fpr_by_signature"]:
            if sg not in sigs: sigs.append(sg)
    L += ["", "**(3) T-hard - FP/n theo chu ky cong cu** (nhieu seed: FP trung binh)", "", "| Chu ky | " + " | ".join(lab[m] for m in R) + " |", "|---|" + "---|" * len(R)]
    for sg in sigs:
        cells = []
        for rs in R.values():
            vs = [r["splits"]["t_hard"]["tuned"]["fpr_by_signature"].get(sg) for r in rs]
            if vs[0] is None: cells.append("-"); continue
            fp = float(np.mean([v["fp"] for v in vs])); n = vs[0]["n"]
            s = (f"{fp:.0f}" if len(vs) == 1 else f"{fp:.1f}") + f"/{n}"
            cells.append(f"**{s}**" if fp else s)
        L.append(f"| `{sg}` | " + " | ".join(cells) + " |")
    L += ["", "**(4) Phan tang do dai tren T-clean / T-novel (cua so am, nguong khoa)**", "",
          "| Mo hinh | T-clean du64 | T-clean ngan | Spearman T-clean | T-novel du64 | T-novel ngan | Spearman T-novel |", "|---|---|---|---|---|---|---|"]
    for m, rs in R.items():
        if m in thard_only: continue
        f_ = lambda sp, k: cnt(rs, lambda r: r["splits"][sp]["tuned"]["fpr_by_length"][k]["fp"]) + f"/{rs[0]['splits'][sp]['tuned']['fpr_by_length'][k]['n_neg']}"
        sp_ = lambda sp: val(rs, lambda r: r["splits"][sp].get("spearman_score_len_neg"), 2)
        L.append(f"| {lab[m]} | {f_('t_clean', 'full64')} | {f_('t_clean', 'short')} | {sp_('t_clean')} | "
                 f"{f_('t_novel', 'full64')} | {f_('t_novel', 'short')} | {sp_('t_novel')} |")
    for sp, nm in (("t_clean", "T-clean"), ("t_novel", "T-novel")):
        rr = {m: rs for m, rs in R.items() if m not in thard_only and all("ttp_tuned" in r["splits"][sp] for r in rs)}
        if not rr: continue
        sup = next(iter(rr.values()))[0]["splits"][sp]["ttp_tuned"]["per_ttp"]
        L += ["", f"**(5) F1 theo TTP - {nm}** (nguong theo TTP khoa tren Train OOF; support = so cua so mang nhan)", "",
              "| Mo hinh | " + " | ".join(f"{t} (n={sup[t]['n_pos']})" for t in TT) + " | macro-F1 |", "|---|" + "---|" * (len(TT) + 1)]
        for m, rs in rr.items():
            B = lambda r: r["splits"][sp]["ttp_tuned"]
            L.append(f"| {lab[m]} | " + " | ".join(val(rs, lambda r, t=t: B(r)["per_ttp"][t]["f1"], 2) if sup[t]["n_pos"] else "-" for t in TT)
                     + f" | {val(rs, lambda r: B(r)['macro_f1'], 2)} |")
    re_ = {m: rs for m, rs in R.items() if m not in thard_only and all(r.get("early") for r in rs)}
    if re_:
        ks = [str(k) for k in next(iter(re_.values()))[0]["early_ks"]]
        L += ["", "**(6) Phat hien som** - recall cua so duong khi chi giu k event dau tu event malicious dau tien (nguong khoa, khong chon lai)", "",
              "| Mo hinh | " + " | ".join(f"T-clean k={k}" for k in ks) + " | T-clean du | " + " | ".join(f"T-novel k={k}" for k in ks)
              + " | T-novel du | T1003 phien T-novel k=" + "/".join(ks) + "/du (cua 6) |", "|---|" + "---|" * (2 * len(ks) + 3)]
        for m, rs in re_.items():
            cells = []
            for sp in ("t_clean", "t_novel"):
                cells += [val(rs, lambda r, k=k: r["early"][sp][k]["recall"], 2) for k in ks] + [val(rs, lambda r: r["splits"][sp]["tuned"]["recall"], 2)]
            d = 0 if len(rs) == 1 else 1
            nt = " / ".join([cnt(rs, lambda r, k=k: r["early"]["t_novel"][k]["ntds_sessions"]["detected"], d) for k in ks]
                            + [cnt(rs, lambda r: r["splits"]["t_novel"]["tuned"]["ntds_session_recall"]["binary"]["detected"], d)])
            L.append(f"| {lab[m]} | " + " | ".join(cells) + f" | {nt} |")
    for m in weights:
        r = R.get(m, [None])[0]
        if not r or "top_pos_features" not in r: continue
        L += ["", f"**Top trong so - {m}** ({r.get('ablation_desc', '')}; C={r.get('C')})", "",
              "| # | Duong (huong attack) | w | Am (huong benign) | w |", "|---|---|---|---|---|"]
        for i, (p, n) in enumerate(zip(r["top_pos_features"], r["top_neg_features"]), 1):
            L.append(f"| {i} | `{p[0]}` | {p[1]} | `{n[0]}` | {n[1]} |")
    return "\n".join(L) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--models", required=True)
    ap.add_argument("--seeds", default="1337,7,42,2024,99", help="seed cho mo hinh nhieu seed (<ten>_s<seed>.json)")
    ap.add_argument("--weights", default="")
    ap.add_argument("--thard-only", default="", help="mo hinh chi bao T-hard (vd ablation (c) ro nhan theo cau truc)")
    ap.add_argument("--out")
    a = ap.parse_args()
    md = tables(a.root, a.models.split(","), [w for w in a.weights.split(",") if w], [m for m in a.thard_only.split(",") if m],
                [s for s in a.seeds.split(",") if s])
    print(md)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f: f.write(md)

if __name__ == "__main__":
    main()
