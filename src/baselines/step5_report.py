#!/usr/bin/env python3
"""VT-Guard Buoc 5 - tong hop reports/step5_report.md + reports/step5_results.json tu reports/step5/<model>.json.

Gom B0, B1 (TF-IDF/raw), B2 (LightGBM), B3 (GRU, 3 seed) x ablation (a)(b)(c')((c) chi T-hard).
B3: trung binh +- do lech chuan (ddof=1) qua 3 seed; nguong khoa rieng moi seed. Moi chi so o nguong khoa
tren Train OOF (B0: L chon tren Train), CI bootstrap 95% (1000 lan, seed 1337).
Chi doc ket qua da sinh; khong chay lai mo hinh. Giu nguyen reports/preds/*.jsonl.
Chay: python src/baselines/step5_report.py
"""
import json, os, sys
from datetime import datetime, timezone, timedelta

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from summary import load, short, ms  # noqa: E402

SEEDS = (1337, 7, 42)
# (nhan hien thi, model_id co so, co nhieu seed?)
GROUPS = [
    ("B0", "b0_wazuh", False),
    ("B1 TF-IDF (a)", "b1_tfidf_a", False), ("B1 TF-IDF (b)", "b1_tfidf_b", False), ("B1 TF-IDF (c')", "b1_tfidf_cp", False),
    ("B1-raw (a)", "b1_raw_a", False), ("B1-raw (b)", "b1_raw_b", False), ("B1-raw (c')", "b1_raw_cp", False),
    ("B2 (a)", "b2_lgbm_a", False), ("B2 (b)", "b2_lgbm_b", False), ("B2 (c')", "b2_lgbm_cp", False),
    ("B3 (a)", "b3_gru_a", True), ("B3 (b)", "b3_gru_b", True), ("B3 (c')", "b3_gru_cp", True),
]
THARD_C = [("B1 TF-IDF (c)", "b1_tfidf_c", False), ("B1-raw (c)", "b1_raw_c", False),
           ("B2 (c)", "b2_lgbm_c", False), ("B3 (c)", "b3_gru_c", True)]
TT = ["T1016", "T1018", "T1087.002", "T1654", "T1003.003"]
KS = ["4", "8", "16", "32"]

def seeds_of(multi): return SEEDS if multi else ()

# -------- truy xuat chi so tu mot ket qua r --------
def m_f1(r, sp): return r["splits"][sp]["tuned"]["f1"]
def m_prauc(r, sp): return r["splits"][sp]["pr_auc"]
def m_fpr(r): return r["splits"]["t_hard"]["tuned"]["fpr"]
def m_fp(r): return r["splits"]["t_hard"]["tuned"]["fp"]
def m_fp_cmd(r, k): return r["splits"]["t_hard"]["tuned"]["fpr_by_cmd"].get(k, {}).get("fp", 0)
def m_len(r, sp, k): return r["splits"][sp]["tuned"]["fpr_by_length"][k]["fp"]
def m_spear(r, sp): return r["splits"][sp].get("spearman_score_len_neg")
def m_macro(r, sp): return r["splits"][sp].get("ttp_tuned", {}).get("macro_f1")
def m_ttp(r, sp, t): return r["splits"][sp]["ttp_tuned"]["per_ttp"][t]["f1"]
def m_sess(r, which): return r["splits"]["t_novel"]["tuned"]["ntds_session_recall"][which]["detected"]
def m_early(r, sp, k): return r["early"][sp][k]["recall"]
def m_early_ntds(r, k): return r["early"]["t_novel"][k]["ntds_sessions"]["detected"]

# -------- ket hop qua seed --------
def pt(c): return None if c is None or c.get("point") is None else c["point"]

def agg_val(rs, get):
    """CI (1 ket qua) hoac {mean,std,values} (nhieu seed) cho chi so co diem."""
    if len(rs) == 1:
        c = get(rs[0]); return None if c is None else {"point": c.get("point"), "lo": c.get("lo"), "hi": c.get("hi")}
    vs = [pt(get(r)) for r in rs]
    v = np.array([x for x in vs if x is not None], float)
    return {"mean": round(float(v.mean()), 4), "std": round(float(v.std(ddof=1)) if len(v) > 1 else 0.0, 4), "values": [round(x, 4) for x in vs]}

def agg_cnt(rs, get):
    if len(rs) == 1: return {"value": get(rs[0])}
    vs = [get(r) for r in rs]
    return {"mean": round(float(np.mean(vs)), 3), "std": round(float(np.std(vs, ddof=1)) if len(vs) > 1 else 0.0, 3), "values": vs}

def f_val(rs, get, d=3):
    if len(rs) == 1: return short(get(rs[0]), d)
    return ms([pt(get(r)) for r in rs], d)

def f_cnt(rs, get, n=None, d=1):
    s = str(get(rs[0])) if len(rs) == 1 else ms([get(r) for r in rs], d)
    return s + (f"/{n}" if n is not None else "")

# -------- bang markdown --------
def main_table(data):
    L = ["**(1) Bang chinh** - moi chi so o nguong khoa tren Train OOF; CI 95%; B3 = trung binh +- do lech chuan qua 3 seed", "",
         "| Mo hinh | T-clean F1 | T-novel F1 | T-novel PR-AUC | T-hard FPR | FP/88 | cmd/khong-cmd | du64/ngan | Spearman(T-hard) | macro-F1 TTP clean / novel |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    nh = data["B0"]["rs"][0]["splits"]["t_hard"]["n"]
    for lab, _, _ in GROUPS:
        rs = data[lab]["rs"]
        cmd = f_cnt(rs, lambda r: m_fp_cmd(r, "co cmd.exe")) + "/" + f_cnt(rs, lambda r: m_fp_cmd(r, "khong cmd.exe"))
        ln = f_cnt(rs, lambda r: m_len(r, "t_hard", "full64")) + "/" + f_cnt(rs, lambda r: m_len(r, "t_hard", "short"))
        mc = f_val(rs, lambda r: m_macro(r, "t_clean"), 2); mn = f_val(rs, lambda r: m_macro(r, "t_novel"), 2)
        L.append(f"| {lab} | {f_val(rs, lambda r: m_f1(r, 't_clean'))} | {f_val(rs, lambda r: m_f1(r, 't_novel'))} | "
                 f"{f_val(rs, lambda r: m_prauc(r, 't_novel'))} | {f_val(rs, m_fpr)} | {f_cnt(rs, m_fp)} | {cmd} | {ln} | "
                 f"{f_val(rs, lambda r: m_spear(r, 't_hard'), 2)} | {mc} / {mn} |")
    L += ["", f"T-hard: {nh} cua so, 0 duong. 'du64/ngan' = so FP o cua so du 64 event / cua so ngan.", ""]
    L += ["**(1b) Ablation (c) - CHI bao T-hard** (mat na cay tien trinh = co che gan nhan -> ro nhan theo cau truc)", "",
          "| Mo hinh | T-hard FPR | FP/88 | so voi (a) FP/88 |", "|---|---|---|---|"]
    for lab, _, _ in THARD_C:
        rs = data[lab]["rs"]; aref = data[lab.replace(" (c)", " (a)")]["rs"]
        L.append(f"| {lab} | {f_val(rs, m_fpr)} | {f_cnt(rs, m_fp)} | {f_cnt(aref, m_fp)} |")
    return "\n".join(L) + "\n"

def ttp_table(data):
    L = []
    for sp, nm in (("t_clean", "T-clean"), ("t_novel", "T-novel")):
        sup = data["B2 (a)"]["rs"][0]["splits"][sp]["ttp_tuned"]["per_ttp"]
        L += ["", f"**(2) F1 theo TTP - {nm}** (nguong theo TTP khoa tren Train OOF; support = so cua so mang nhan)", "",
              "| Mo hinh | " + " | ".join(f"{t} (n={sup[t]['n_pos']})" for t in TT) + " | macro-F1 |", "|---|" + "---|" * (len(TT) + 1)]
        for lab, _, _ in GROUPS:
            if lab == "B0" and sp == "t_novel": pass
            rs = data[lab]["rs"]
            L.append(f"| {lab} | " + " | ".join(f_val(rs, lambda r, t=t: m_ttp(r, sp, t), 2) for t in TT) + f" | {f_val(rs, lambda r: m_macro(r, sp), 2)} |")
    return "\n".join(L) + "\n"

def early_table(data):
    L = ["", "**(3) Phat hien som** - recall cua so duong khi chi giu k event dau tu event malicious dau tien (nguong khoa, khong chon lai)", "",
         "| Mo hinh | " + " | ".join(f"T-clean k={k}" for k in KS) + " | T-clean du | " + " | ".join(f"T-novel k={k}" for k in KS)
         + " | T-novel du | T1003 phien T-novel k=" + "/".join(KS) + "/du (cua 6) |", "|---|" + "---|" * (2 * len(KS) + 3)]
    for lab, _, _ in GROUPS:
        rs = data[lab]["rs"]
        cells = [f_val(rs, lambda r, k=k: m_early(r, "t_clean", k), 2) for k in KS] + [f_val(rs, lambda r: m_f1(r, "t_clean") and r["splits"]["t_clean"]["tuned"]["recall"], 2)]
        cells += [f_val(rs, lambda r, k=k: m_early(r, "t_novel", k), 2) for k in KS] + [f_val(rs, lambda r: r["splits"]["t_novel"]["tuned"]["recall"], 2)]
        d = 0 if len(rs) == 1 else 1
        nt = " / ".join([f_cnt(rs, lambda r, k=k: m_early_ntds(r, k), d=d) for k in KS] + [f_cnt(rs, lambda r: m_sess(r, "binary"), d=d)])
        L.append(f"| {lab} | " + " | ".join(cells) + f" | {nt} |")
    return "\n".join(L) + "\n"

# -------- so lieu cho phan dien giai --------
def g1(data, lab, get, d=3):
    rs = data[lab]["rs"]
    if len(rs) == 1: return pt(get(rs[0]))
    return float(np.mean([pt(get(r)) for r in rs]))

def build(root="."):
    data = {}
    for lab, mid, multi in GROUPS + THARD_C:
        rs = load(root, mid, seeds_of(multi))
        data[lab] = {"rs": rs, "ids": [mid] if not multi else [f"{mid}_s{s}" for s in SEEDS], "multi": multi}
    tz = timezone(timedelta(hours=7))
    # ---- step5_results.json ----
    out = {"generated": datetime.now(tz).replace(microsecond=0).isoformat(), "dataset_version": "v1.2",
           "seed": 1337, "b3_seeds": list(SEEDS), "n_boot": 1000,
           "note": "B3 (GRU) = trung binh/do lech chuan qua 3 seed; cac mo hinh khac 1 ket qua kem CI 95%.", "models": {}}
    for lab, mid, multi in GROUPS + THARD_C:
        rs = data[lab]["rs"]
        rec = {"model_ids": data[lab]["ids"], "multi_seed": multi, "engine": rs[0].get("engine", "wazuh rules" if mid == "b0_wazuh" else "sklearn")}
        rec["t_hard"] = {"fpr": agg_val(rs, m_fpr), "fp": agg_cnt(rs, m_fp), "n": rs[0]["splits"]["t_hard"]["n"],
                         "fp_cmd": agg_cnt(rs, lambda r: m_fp_cmd(r, "co cmd.exe")), "fp_nocmd": agg_cnt(rs, lambda r: m_fp_cmd(r, "khong cmd.exe")),
                         "fp_full64": agg_cnt(rs, lambda r: m_len(r, "t_hard", "full64")), "fp_short": agg_cnt(rs, lambda r: m_len(r, "t_hard", "short")),
                         "spearman": agg_val(rs, lambda r: m_spear(r, "t_hard"))}
        if lab.endswith("(c)"): out["models"][lab] = rec; continue
        for sp in ("t_clean", "t_novel"):
            rec[sp] = {"f1": agg_val(rs, lambda r, s=sp: m_f1(r, s)), "pr_auc": agg_val(rs, lambda r, s=sp: m_prauc(r, s)),
                       "macro_f1_ttp": agg_val(rs, lambda r, s=sp: m_macro(r, s)),
                       "per_ttp_f1": {t: agg_val(rs, lambda r, s=sp, tt=t: m_ttp(r, s, tt)) for t in TT},
                       "fp_full64": agg_cnt(rs, lambda r, s=sp: m_len(r, s, "full64")), "fp_short": agg_cnt(rs, lambda r, s=sp: m_len(r, s, "short")),
                       "spearman_len": agg_val(rs, lambda r, s=sp: m_spear(r, s))}
        rec["t_novel"]["ntds_session"] = {"binary": agg_cnt(rs, lambda r: m_sess(r, "binary")),
                                          "ttp_label": agg_cnt(rs, lambda r: m_sess(r, "ttp_label")), "of": 6}
        rec["early"] = {sp: {k: agg_val(rs, lambda r, s=sp, kk=k: m_early(r, s, kk)) for k in KS} for sp in ("t_clean", "t_novel")}
        rec["early"]["t1003_sessions_t_novel"] = {k: agg_cnt(rs, lambda r, kk=k: m_early_ntds(r, kk)) for k in KS}
        out["models"][lab] = rec
    with open(os.path.join(root, "reports", "step5_results.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # ---- step5_report.md ----
    b0fp = data["B0"]["rs"][0]["splits"]["t_hard"]["tuned"]["fp"]
    b2b_tn = g1(data, "B2 (b)", lambda r: m_f1(r, "t_novel")); b2a_tn = g1(data, "B2 (a)", lambda r: m_f1(r, "t_novel"))
    b3b_mn = g1(data, "B3 (b)", lambda r: m_macro(r, "t_novel")); b3a_mn = g1(data, "B3 (a)", lambda r: m_macro(r, "t_novel"))
    sp_b1 = g1(data, "B1 TF-IDF (a)", lambda r: m_spear(r, "t_novel")); sp_b3 = g1(data, "B3 (a)", lambda r: m_spear(r, "t_hard"))
    R = [f"# VT-Guard - Bao cao Buoc 5 (baseline B0-B3 tren dataset-v1.2)", "",
         f"Sinh tu dong boi `src/baselines/step5_report.py` luc {out['generated']}. So lieu: `reports/step5_results.json`, "
         f"chi tiet moi mo hinh: `reports/step5/<model>.json`, du doan: `reports/preds/<model>_<split>.jsonl` (giu cho Buoc 8 fusion).", "",
         "Dataset `dataset-v1.2` dong bang (809 cua so; Train 483 / T-clean 89 / T-hard 88 / T-novel 149; 272 duong). "
         "Khung danh gia `src/eval/evaluate.py`: nguong chon tren Train OOF (CV theo nhom chong thoi gian) roi KHOA, ap nguyen cho "
         "3 tap test; CI bootstrap 95% (1000 lan, seed 1337). T-clean = tool cung ho tro da thay; T-hard = hard-negative "
         "(hoat dong quan tri lanh tinh, 0 duong); T-novel = batch05 + ntds2v (bien the/cong cu chua thay khi train).", "",
         "Ablation: **(a)** du; **(b)** bo `image_name` + `parent_image_name`; **(c)** chi event trong cay tien trinh "
         "(mat na = co che gan nhan -> ro nhan theo cau truc, CHI bao T-hard); **(c')** che event nen mot-phia da biet "
         "(ESENT/Directory Service cua ntdsutil, svchost->rundll32 COM). B3 (GRU) chay 3 seed (1337, 7, 42), bao trung binh "
         "+- do lech chuan; nguong khoa rieng moi seed.", "",
         "Mo hinh: **B0** luat Wazuh (nguong muc do L chon tren Train); **B1** TF-IDF / dem tho (raw) + Logistic Regression "
         "tren token event (img/eid/dong lenh chuan hoa); **B2** LightGBM tren dac trung ti le theo cua so (khong n_events); "
         "**B3** GRU 1 lop (hidden 96, khong attention, don nhiem) tren chuoi event. B3 co hai bien the huan luyen RIENG: "
         "B3-bin (nhi phan) va B3-ttp (5 dau da nhan); bang duoi lay cot nhi phan tu B3-bin, cot TTP tu B3-ttp.", "",
         main_table(data), ttp_table(data), early_table(data),
         "## Phat hien chinh", "",
         f"1. **Hoc may cat manh bao dong gia tren T-hard.** B0 (luat Wazuh) bao nham {b0fp}/88 cua so hard-negative "
         f"(chu yeu khi co `cmd.exe` trong cay tien trinh: 14/19); moi mo hinh hoc may ha xuong 0-5/88. B1 (TF-IDF/raw) o (b) "
         f"dat 0/88; B2 (a) va B3 (b) deu <= 2/88.",
         f"2. **B2 phu thuoc ten cong cu, B1 va B3 thi khong.** Bo `image_name`/`parent_image_name` (ablation b), B2 sup: "
         f"T-novel F1 {b2a_tn:.2f} -> {b2b_tn:.2f}, FPR T-hard tang len 14/88 (13 trong so o phien khong cmd.exe). Nguoc lai "
         f"B3 giu macro-F1 T-novel {b3a_mn:.2f} -> {b3b_mn:.2f} va B1 giu ~0.95, nho token dong lenh + chuoi event.",
         "3. **O B1 va B3, (b) bang hoac tot hon (a).** Bo `image_name` khong lam giam (tham chi tang nhe T-clean F1 va giam "
         "FPR T-hard): ten anh dua mo hinh vao duong tat `ping/wevtutil/ntdsutil` thay vi hanh vi, lam giam kha nang tong quat "
         "hoa sang T-novel. Day la bang chung chinh ung ho cau hinh (b) cho Buoc 6.",
         "4. **(c') ~ (a) o moi mo hinh.** Che event nen mot-phia da biet (ESENT/DS, COM nen) gan nhu khong doi ket qua -> "
         "khong mo hinh nao song nho tac dong phu nen cua T1003.003; tin hieu den tu hanh vi trong cay tien trinh.",
         "5. **T1654 (Log Enumeration) la TTP kho nhat**, nhat la tren T-novel (F1 ~0.46-0.61 o moi mo hinh). **T1003.003** "
         "chi co 6 phien tren T-novel nen F1 muc cua so bao hoa 1.0 khong co y nghia thong ke; bao theo PHIEN: B1 va B3 bat 6/6 "
         "o muc nhi phan, B2 (a) 4/6.",
         "6. **Phat hien som**: B1 nhanh va on dinh nhat (recall >= 0.86 tu k=4 tren T-clean, 1.00 tren T-novel, 6/6 phien T1003 "
         "o moi k). B3 can k>=16 de bat du 6/6 phien T1003 va dao dong theo seed o k nho. B0 phai toi k=32 moi bat phien T1003 "
         "dau tien.", "",
         "## Han che", "",
         f"- **Confounder do dai cua so.** Spearman diem~n_events tren cua so am duong ro o B1 TF-IDF (T-novel ~{sp_b1:.2f}) va "
         f"B3 (T-hard ~{sp_b3:.2f}): cua so dai bi cham diem cao hon. Tap am T-hard phan lon ngan nen chua gay FP, nhung la rui ro "
         f"khi trien khai; B1-raw va B2 (a) trung lap hon (Spearman ~0). Buoc 6 phai kiem soat (xem duoi).",
         "- **Nguong B3 khong on dinh giua seed.** Nguong nhi phan khoa dao dong 0.51-0.95 giua 3 seed, keo theo phat hien som "
         "T1003 o k nho lech manh (vd (a): seed 1337/42 bat 6/6 tu k=4, seed 7 bat 0 toi k=16). Can bao trung binh +- do lech "
         "chuan, khong dua vao 1 seed.",
         "- **Tran epoch.** B3 gioi han 60 epoch/fold; 3/120 fold CV cham tran (a_s7, a_s42 o dau TTP; c_s1337 o dau nhi phan). "
         "Mo hinh CUOI cua moi luot fit lai voi so epoch = trung vi cac fold (18-49, deu duoi tran), nen anh huong nho; Buoc 6 nang "
         "tran 100, patience 10.",
         "- **T1003.003 test nho (6 phien T-novel, 12 cua so T-clean)**: moi chi so T1003 bao kem khoang tin cay / theo phien.",
         "- **Coverage gap (gioi han sinh du lieu, khong phai mo hinh).** `route.exe`/`netstat.exe` va truy van \"Domain Admins\" "
         "chi xuat hien o phia AM (kich ban benign/hard-negative; attack khong dung) -> duong tat nguoc: mo hinh co the hoc "
         "\"thay route/netstat = lanh tinh\". Da do bang ablation va bao trong dataset card muc 5b/7a.",
         "- **Loi trung PID khi loai orchestrator** (labeler): 7 tien trinh / 23 event (gom ntdsutil malicious) co the bi loai/giu "
         "sai do PID bi tai su dung sau khoi phuc snapshot. Ghi trong dataset card muc 9.",
         "- **Ro ri da phat hien va xu ly:** dau vet bo sinh (duong dan cmd, `conhost.exe`, launcher cha, duoi `.exe`) trung hoa o "
         "v1.1; bat doi xung 4688/EID1 sua o v1.2; cau hinh orchestrator `variant`/`tempo`/`user_role` (variant != mixed chi o "
         "attack -> ro nhan) cam lam feature o Buoc 5, quet tinh moi mo hinh (acceptance #2).", "",
         "## He qua cho Buoc 6 (VT-Seq: GRU-Attention da nhiem)", "",
         "- **Muc tieu chi so**: nang T1654 va macro-F1 TTP tren T-novel > 0.80 (tran hien tai B2/B3 ~0.74-0.81); giu FPR T-hard "
         "<= muc B1 (0/88) va PR-AUC T-novel cao.",
         "- **Chon nguong theo FPR muc tieu** (vd FPR T-hard <= 1%) thay vi chi max-F1, kem PR-AUC; bao trung binh nhieu seed.",
         "- **Kiem soat confounder do dai**: ep Spearman diem~do dai ~ 0 (random length crop manh hon, phat trong luong theo do "
         "dai, hoac chuan hoa); danh gia lai bang bang phan tang do dai.",
         "- **Can nhac lay cau hinh (b) lam chinh** (bo `image_name`): (b) tong quat hoa tot hon va giam phu thuoc ten cong cu.",
         "- **Attention** them o Buoc 6 phuc vu giai thich (trong so event) va sinh luat Sigma o Buoc 7, khong chi de tang diem.",
         "- **Huan luyen**: tran epoch 100, patience 10, nhieu seed (>=3), bao trung binh +- do lech chuan; giu reports/preds/ de "
         "Buoc 8 fusion dung lai.", ""]
    with open(os.path.join(root, "reports", "step5_report.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(R))
    print("OK: reports/step5_report.md + reports/step5_results.json")
    print("models:", len(out["models"]))

if __name__ == "__main__":
    build(".")
