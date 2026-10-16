#!/usr/bin/env python3
"""VT-Guard Buoc 5 - bang so sanh nhieu mo hinh tu reports/step5/<model>.json (ket qua evaluate.py).

Bang: (1) chinh: T-clean F1/PR-AUC, T-novel F1/PR-AUC, macro-F1 TTP, recall T1003.003 muc phien;
(2) T-hard: FPR tong, co/khong cmd.exe, phan tang do dai, Spearman diem~do dai; (3) T-hard FPR theo chu ky cong cu;
(4) top trong so (neu ket qua co). Moi chi so o NGUONG DA KHOA tren Train OOF, kem CI bootstrap 95%.
Chay: python src/baselines/summary.py --models b0_wazuh,b1_tfidf_a,... [--weights b1_tfidf_a,b1_tfidf_b] [--out f.md]
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "eval"))
from evaluate import fci, fw

def short(c, d=3):
    if c is None or c.get("point") is None: return "-"
    if c.get("lo") is None: return f"{c['point']:.{d}f}"
    return f"{c['point']:.{d}f} [{c['lo']:.{d}f}, {c['hi']:.{d}f}]"

def tables(root, models, weights=(), thard_only=()):
    R = {m: json.load(open(os.path.join(root, "reports", "step5", f"{m}.json"), encoding="utf-8")) for m in models}
    dsv = {r.get("dataset_version", "?") for r in R.values()}
    L = [f"Dataset: {', '.join(sorted(dsv))}. Moi chi so o nguong khoa tren Train OOF (B0: L chon tren Train); CI bootstrap 95%, 1000 lan, seed 1337.", ""]
    L += ["**(1) Bang chinh**", "",
          "| Mo hinh | T-clean F1 | T-clean PR-AUC | T-novel F1 | T-novel PR-AUC | macro-F1 TTP clean / novel | T1003.003 phien T-novel: nhi phan / nhan TTP |",
          "|---|---|---|---|---|---|---|"]
    for m, r in R.items():
        if m in thard_only: continue
        S = r["splits"]; sr = S["t_novel"]["tuned"]["ntds_session_recall"]
        mc = S["t_clean"].get("ttp_tuned", {}).get("macro_f1"); mn = S["t_novel"].get("ttp_tuned", {}).get("macro_f1")
        ttp = sr.get("ttp_label")
        L.append(f"| {m} | {short(S['t_clean']['tuned']['f1'])} | {short(S['t_clean']['pr_auc'])} | {short(S['t_novel']['tuned']['f1'])} | "
                 f"{short(S['t_novel']['pr_auc'])} | {short(mc, 2) if mc else '-'} / {short(mn, 2) if mn else '-'} | "
                 f"{sr['binary']['detected']}/{sr['binary']['of']} / " + (f"{ttp['detected']}/{ttp['of']}" if ttp else "-") + " |")
    nh = sorted({r["splits"]["t_hard"]["n"] for r in R.values()})
    L += ["", f"**(2) T-hard ({'/'.join(map(str, nh))} cua so, 0 duong)**", "",
          "| Mo hinh | FPR tong (FP/n) | Co cmd.exe: FP/n | Khong cmd.exe: FP/n | Du 64: FP/n | Ngan: FP/n | Spearman(diem, n_events) cua so am T-hard |",
          "|---|---|---|---|---|---|---|"]
    for m, r in R.items():
        h = r["splits"]["t_hard"]; t = h["tuned"]; cm = t["fpr_by_cmd"]; lb = t["fpr_by_length"]
        if m in thard_only: m = m + " (chi T-hard, so voi (a))"
        g = lambda d, k: f"{d.get(k, {}).get('fp', '-')}/{d.get(k, {}).get('n', '-')}"
        L.append(f"| {m} | {short(t['fpr'])} ({t['fp']}/{h['n']}) | {g(cm, 'co cmd.exe')} | {g(cm, 'khong cmd.exe')} | "
                 f"{lb['full64']['fp']}/{lb['full64']['n_neg']} | {lb['short']['fp']}/{lb['short']['n_neg']} | {short(h.get('spearman_score_len_neg'), 2)} |")
    sigs = []
    for r in R.values():
        for sg in r["splits"]["t_hard"]["tuned"]["fpr_by_signature"]:
            if sg not in sigs: sigs.append(sg)
    L += ["", "**(3) T-hard - FP/n theo chu ky cong cu**", "", "| Chu ky | " + " | ".join(R) + " |", "|---|" + "---|" * len(R)]
    for sg in sigs:
        cells = []
        for r in R.values():
            v = r["splits"]["t_hard"]["tuned"]["fpr_by_signature"].get(sg)
            cells.append("-" if v is None else (f"**{v['fp']}/{v['n']}**" if v["fp"] else f"0/{v['n']}"))
        L.append(f"| `{sg}` | " + " | ".join(cells) + " |")
    L += ["", "**(4) Phan tang do dai tren T-clean / T-novel (cua so am, nguong khoa)**", "",
          "| Mo hinh | T-clean du64 | T-clean ngan | Spearman T-clean | T-novel du64 | T-novel ngan | Spearman T-novel |", "|---|---|---|---|---|---|---|"]
    for m, r in R.items():
        if m in thard_only: continue
        c = r["splits"]["t_clean"]; n = r["splits"]["t_novel"]
        f_ = lambda o, k: f"{o['tuned']['fpr_by_length'][k]['fp']}/{o['tuned']['fpr_by_length'][k]['n_neg']}"
        L.append(f"| {m} | {f_(c, 'full64')} | {f_(c, 'short')} | {short(c.get('spearman_score_len_neg'), 2)} | "
                 f"{f_(n, 'full64')} | {f_(n, 'short')} | {short(n.get('spearman_score_len_neg'), 2)} |")
    TT = ["T1016", "T1018", "T1087.002", "T1654", "T1003.003"]
    for sp, nm in (("t_clean", "T-clean"), ("t_novel", "T-novel")):
        rr = {m: r for m, r in R.items() if m not in thard_only and "ttp_tuned" in r["splits"][sp]}
        if not rr: continue
        sup = next(iter(rr.values()))["splits"][sp]["ttp_tuned"]["per_ttp"]
        L += ["", f"**(5) F1 theo TTP - {nm}** (nguong theo TTP khoa tren Train OOF; support = so cua so mang nhan)", "",
              "| Mo hinh | " + " | ".join(f"{t} (n={sup[t]['n_pos']})" for t in TT) + " | macro-F1 |", "|---|" + "---|" * (len(TT) + 1)]
        for m, r in rr.items():
            b = r["splits"][sp]["ttp_tuned"]
            L.append(f"| {m} | " + " | ".join(short(b["per_ttp"][t]["f1"], 2) if b["per_ttp"][t]["n_pos"] else "-" for t in TT)
                     + f" | {short(b['macro_f1'], 2)} |")
    re_ = {m: r for m, r in R.items() if m not in thard_only and r.get("early")}
    if re_:
        ks = [str(k) for k in next(iter(re_.values()))["early_ks"]]
        L += ["", "**(6) Phat hien som** - recall cua so duong khi chi giu k event dau tu event malicious dau tien (nguong khoa, khong chon lai)", "",
              "| Mo hinh | " + " | ".join(f"T-clean k={k}" for k in ks) + " | T-clean du | " + " | ".join(f"T-novel k={k}" for k in ks)
              + " | T-novel du | T1003 phien T-novel k=" + "/".join(ks) + "/du |", "|---|" + "---|" * (2 * len(ks) + 3)]
        for m, r in re_.items():
            e = r["early"]; S = r["splits"]
            cells = [short(e["t_clean"][k]["recall"], 2) for k in ks] + [short(S["t_clean"]["tuned"]["recall"], 2)]
            cells += [short(e["t_novel"][k]["recall"], 2) for k in ks] + [short(S["t_novel"]["tuned"]["recall"], 2)]
            nt = "/".join(str(e["t_novel"][k]["ntds_sessions"]["detected"]) for k in ks) + f"/{S['t_novel']['tuned']['ntds_session_recall']['binary']['detected']} (cua 6)"
            L.append(f"| {m} | " + " | ".join(cells) + f" | {nt} |")
    for m in weights:
        r = R.get(m)
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
    ap.add_argument("--weights", default="")
    ap.add_argument("--thard-only", default="", help="mo hinh chi bao T-hard (vd ablation (c) ro nhan theo cau truc)")
    ap.add_argument("--out")
    a = ap.parse_args()
    md = tables(a.root, a.models.split(","), [w for w in a.weights.split(",") if w], [m for m in a.thard_only.split(",") if m])
    print(md)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f: f.write(md)

if __name__ == "__main__":
    main()
