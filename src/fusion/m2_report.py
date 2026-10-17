#!/usr/bin/env python3
"""VT-Guard Buoc 8 moc 2 - bang test F0-F4 canh B0/B1/B2 + paired bootstrap / Holm -> reports/step8/m2_test.md.
Chi doc ket qua da sinh (reports/step8/eval, paired_bootstrap.json). Chay: python src/fusion/m2_report.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("../eval", "../baselines"): sys.path.insert(0, os.path.join(HERE, d))
from summary import tables      # noqa: E402

S8 = os.path.join("reports", "step8")
LAB = {"F3B - F0": "F3-B vs F0 (chi-AI)", "F3B - F1": "F3-B vs F1 (chi-luat)"}
MET = {"macro_f1_ttp_t_novel": "macro-F1 TTP T-novel", "pr_auc_t_novel": "PR-AUC T-novel", "fpr_t_hard": "FPR T-hard"}

def main():
    pb = json.load(open(os.path.join(S8, "paired_bootstrap.json"), encoding="utf-8"))
    L = ["# VT-Guard Buoc 8 moc 2 - fusion tren test (cham MOT lan bang evaluate.py)", "",
         "Cau hinh + tham so khoa o `reports/step8/final_fusion.json`, commit `3fd9531` TRUOC khi cham test. Ten mo hinh: "
         "fusion_F0 = chi-AI (VT-Seq-ens, nguong Buoc 6); fusion_F0p = chi-AI nguong chon lai tren cung OOF (FPR <= 1%, doi chung MO TA); "
         "fusion_F1 = chi-luat (Buoc 7); fusion_F2 = OR; **fusion_F3B = CHON (s = p + 0.1 r, kenh luat TTP chi T1018/T1654/T1003.003)**; "
         "fusion_F4B = stacking LR. Kiem tu dong: F0 trung VT-Seq-ens Buoc 6 = " + str(pb["sanity"]["F0_equals_step6_vtseq_M3_ens"]) +
         ", F1 trung chi-luat Buoc 7 = " + str(pb["sanity"]["F1_equals_step7_rules"]) + ".", ""]
    L.append(tables(".", ["b0_wazuh", "b1_tfidf_b", "b2_lgbm_a", "fusion_F0", "fusion_F0p", "fusion_F1", "fusion_F2", "fusion_F3B", "fusion_F4B"], (), (), ()))
    L += ["## Paired bootstrap + Holm (6 so sanh: F3-B vs F0 va vs F1 x 3 chi so)", "",
          "1000 lan, seed 1337, cung mau cua so (T-novel cho macro-F1 / PR-AUC, T-hard cho FPR); p hai phia tu phan bo bootstrap. "
          "'Hon' chi khi p Holm < 0.05. 'Khong kem' doc tu CI 95% cua hieu so (FPR: am la tot hon).", "",
          "| So sanh | Chi so | F3-B | Doi chung | Hieu [CI 95%] | p | p Holm | Ket luan |", "|---|---|---|---|---|---|---|---|"]
    for c, d in pb["holm_family"].items():
        for m, v in d.items():
            good = v["diff"] > 0 if m != "fpr_t_hard" else v["diff"] < 0
            concl = ("F3-B hon" if good else "F3-B kem") if v["p_holm"] < 0.05 else "khong khac co y nghia"
            L.append(f"| {LAB[c]} | {MET[m]} | {v['a']:.3f} | {v['b']:.3f} | {v['diff']:+.3f} [{v['lo']:+.3f}, {v['hi']:+.3f}] | {v['p']:.3f} | {v['p_holm']:.3f} | {concl} |")
    L += ["", "**Mo ta (ngoai ho Holm): F3-B vs F0' (chi-AI nguong chon lai tren cung OOF)** - tach phan do luat khoi phan do chon lai nguong.", "",
          "| Chi so | F3-B | F0' | Hieu [CI 95%] | p (chua hieu chinh) |", "|---|---|---|---|---|"]
    for m, v in list(pb["descriptive"].values())[0].items():
        L.append(f"| {MET[m]} | {v['a']:.3f} | {v['b']:.3f} | {v['diff']:+.3f} [{v['lo']:+.3f}, {v['hi']:+.3f}] | {v['p']:.3f} |")
    L += ["", "## Ghi chu doc ket qua", "",
          "- **'Khong kem' kiem voi bien 0**: F3-B khong kem doi chung o mot chi so neu can duoi CI 95% cua hieu so (F3-B - doi chung) "
          ">= 0 (voi FPR: can tren CI <= 0). F3-B vs F0: macro-F1 TTP T-novel [+0.000, +0.011], PR-AUC T-novel [+0.002, +0.029], "
          "FPR T-hard [0, 0] -> khong kem chi-AI o ca 3 chi so; khong khac co y nghia sau Holm.",
          "- **Muc giam FPR thay o OOF khong lap lai tren test**: tren OOF, F3 co FPR hard_negative 0.028 so voi 0.037 cua F0, nhung "
          "nguong nhi phan cua F3 (0.869166) gan nhu trung tau cua F0 (0.8691656) - khac biet do hoa diem tai nguong (diem lam tron 6 chu so), "
          "khong phai do luat. Tren test F3-B va F0 cung 1/88 FP.",
          "- **F0' trung F0 tren moi chi so test** (nguong chon lai tren cung OOF ~ tau Buoc 6) -> moi khac biet F3-B vs F0 hoan toan do "
          "luat: xep hang nhi phan (PR-AUC 0.986 -> 0.998) va T1018 (T-novel 0.83 -> 0.85, T-clean 0.71 -> 0.74).", ""]
    with open(os.path.join(S8, "m2_test.md"), "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(L))
    print("\n".join(L))

if __name__ == "__main__":
    main()
