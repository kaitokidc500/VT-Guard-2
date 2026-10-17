# VT-Guard - Bao cao Buoc 8: Hybrid Fusion (AI + luat tu sinh)

Sinh tu dong boi `src/fusion/step8_report.py` luc 2026-10-17T16:43:48+07:00. So lieu: `reports/step8_results.json`; chi tiet: `reports/step8/` (m1_oof.md, final_fusion.json, m2_test.md, m3_explain.md, eval/, alerts_<split>.jsonl); du doan: `reports/preds/fusion_<split>.jsonl`.

## 0. Tom tat

- **Cau hinh trien khai: F3-B** - `s = p + 0.1 r`, `s_k = p_k + 0.1 r_k` (r_k chi cho T1003.003, T1018, T1654), nguong nhi phan 0.8692 (FPR <= 1% am OOF). Chon CHI tren OOF Train va KHOA o commit `3fd9531` truoc khi cham test.
- **Luat la kenh XAC NHAN / tang diem** (beta = 0.1), khong phai kenh tu canh bao: tren test KHONG co canh bao nao chi do luat. F2 (OR) cho phep luat tu canh bao nhung thua F3 tren OOF (PR-AUC, muc 1).
- **Yeu cau (2) cua mon hoc:** F3-B **hon chi-luat co y nghia sau Holm** (macro-F1 TTP T-novel +0.403, PR-AUC T-novel +0.146, p Holm 0.006); **khong kem chi-AI** (can duoi CI hieu so >= 0 o ca 3 chi so, bien 0) nhung **khong hon co y nghia**. F0' = F0 nen moi khac biet F3-B vs chi-AI la do luat.
- **Gia tri chinh = giai thich + phan loai muc tin cay canh bao:** 75% canh bao co luat Sigma giai thich; canh bao co luat xac nhan (`both`) dung 76/76, canh bao chi-AI dung 20/25 (mo ta, mau nho).

## 1. OOF F2-F4 va ly do chon (muc 4)

Nguon OOF: AI `reports/preds/vtseq_M3_ens_train.jsonl` (trung binh OOF 5 seed M3, Buoc 6), luat `reports/preds/rules_oof_train.jsonl` (luat quy nap lai trong tung fold, Buoc 7); KHONG dung `rules_train.jsonl` (in-sample). F3: beta trong {0.1, 0.2, 0.3}; F4: LR 7 dac trung, diem OOF bang CV long theo nhom phien. Tieu chi: macro-F1 TTP OOF -> PR-AUC OOF -> FPR hard_negative OOF; ngang nhau (|chenh| <= DLC bootstrap hieu so) -> it tham so hon.

| Bien the / cau hinh | macro-F1 TTP | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | PR-AUC | FPR hard_neg | Recall |
|---|---|---|---|---|---|---|---|---|---|
| A: F0 | 0.830 | 0.752 | 0.776 | 0.791 | 0.828 | 1.000 | 0.997 | 0.037 | 0.994 |
| A: F1 | 0.545 | 0.707 | 0.286 | 0.257 | 0.712 | 0.765 | 0.801 | 0.018 | 0.705 |
| A: F2 | 0.831 | 0.752 | 0.791 | 0.791 | 0.820 | 1.000 | 0.982 | 0.055 | 0.994 |
| A: F3 | 0.847 | 0.816 | 0.791 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.994 |
| A: F4 | 0.832 | 0.785 | 0.751 | 0.793 | 0.830 | 1.000 | 0.995 | 0.028 | 0.994 |
| B: F0 | 0.830 | 0.752 | 0.776 | 0.791 | 0.828 | 1.000 | 0.997 | 0.037 | 0.994 |
| B: F1 | 0.353 | 0.000 | 0.286 | 0.000 | 0.712 | 0.765 | 0.801 | 0.018 | 0.705 |
| B: F2 | 0.831 | 0.752 | 0.791 | 0.791 | 0.820 | 1.000 | 0.982 | 0.055 | 0.994 |
| B: F3 | 0.835 | 0.752 | 0.791 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.994 |
| B: F4 | 0.836 | 0.798 | 0.758 | 0.793 | 0.830 | 1.000 | 0.995 | 0.028 | 0.994 |

- Bien the A (moi kenh r_k, dinh nghia brief) chon F3 (macro-F1 0.847) nho kenh T1016 - kenh nay chi co trong bo luat FOLD, bo luat cuoi KHONG co luat T1016.
- **Bien the B (khoa):** kenh luat theo TTP (r_k) CHI cho ['T1003.003', 'T1018', 'T1654']; brief muc 3 dinh nghia da nhan dung moi r_k. Ly do (su kien cau truc chi tu Train): su kien cau truc CHI dua tren Train: bo luat cuoi (quy nap tu toan bo Train, Buoc 7) chi co luat theo TTP cho ['T1003.003', 'T1018', 'T1654']. Luc chay test r_k cua T1016 va T1087.002 luon = 0, nen tren OOF cung phai = 0 de dac trung fusion giong luc trien khai. Khong dung so lieu do nhay (in-sample, chi mo ta) lam can cu.
- B: macro-F1 F2 / F3 / F4 ngang nhau (chenh <= 0.005, DLC ~0.011); PR-AUC F3 > F2 (0.997 vs 0.982) va > F4 (sit sao) -> F3, beta 0.1 (ba beta cho ket qua OOF giong nhau). Do nhay khi thay luat fold bang luat cuoi chi la MO TA (in-sample), khong dung de chon.

## 2. Test F0-F4 canh B0 / B1 / B2

F0 chi-AI (VT-Seq-ens, nguong Buoc 6); F0' chi-AI nguong chon lai tren cung OOF (doi chung mo ta); F1 chi-luat (Buoc 7); F2 OR; **F3-B chon**; F4-B stacking. Kiem: F0 trung VT-Seq-ens Buoc 6, F1 trung chi-luat Buoc 7.

Dataset: v1.2. Moi chi so o nguong khoa tren Train OOF (B0: L chon tren Train); CI bootstrap 95%, 1000 lan, seed 1337.
Mo hinh nhieu seed (ghi '(n seed)'): trung binh +- do lech chuan (ddof=1) cua gia tri diem qua cac seed; nguong khoa rieng moi seed.

**(1) Bang chinh**

| Mo hinh | T-clean F1 | T-clean PR-AUC | T-novel F1 | T-novel PR-AUC | macro-F1 TTP clean / novel | T1003.003 phien T-novel: nhi phan / nhan TTP (cua 6) |
|---|---|---|---|---|---|---|
| b0_wazuh | 0.988 [0.962, 1.000] | 0.987 [0.955, 1.000] | 0.898 [0.837, 0.948] | 0.820 [0.726, 0.903] | 0.12 [0.09, 0.14] / 0.12 [0.09, 0.14] | 5 / 0 |
| b1_tfidf_b | 0.988 [0.959, 1.000] | 0.998 [0.993, 1.000] | 0.946 [0.899, 0.984] | 0.979 [0.947, 0.998] | 0.84 [0.78, 0.89] / 0.73 [0.67, 0.79] | 6 / 6 |
| b2_lgbm_a | 0.976 [0.937, 1.000] | 0.999 [0.995, 1.000] | 0.936 [0.882, 0.979] | 0.990 [0.975, 0.999] | 0.88 [0.82, 0.92] / 0.80 [0.75, 0.85] | 4 / 6 |
| fusion_F0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.964 [0.927, 0.992] | 0.986 [0.967, 0.998] | 0.87 [0.83, 0.92] / 0.82 [0.76, 0.87] | 6 / 6 |
| fusion_F0p | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.964 [0.927, 0.992] | 0.986 [0.967, 0.998] | 0.87 [0.83, 0.92] / 0.82 [0.76, 0.87] | 6 / 6 |
| fusion_F1 | 0.880 [0.789, 0.951] | 0.887 [0.809, 0.953] | 0.878 [0.796, 0.942] | 0.852 [0.763, 0.928] | 0.39 [0.32, 0.45] / 0.42 [0.35, 0.47] | 6 / 6 |
| fusion_F2 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.956 [0.914, 0.991] | 0.976 [0.924, 1.000] | 0.88 [0.83, 0.92] / 0.81 [0.76, 0.87] | 6 / 6 |
| fusion_F3B | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.964 [0.927, 0.992] | 0.998 [0.993, 1.000] | 0.88 [0.83, 0.92] / 0.82 [0.76, 0.87] | 6 / 6 |
| fusion_F4B | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.964 [0.927, 0.992] | 0.988 [0.972, 0.998] | 0.88 [0.83, 0.92] / 0.81 [0.75, 0.86] | 6 / 6 |

**(2) T-hard (88 cua so, 0 duong)**

| Mo hinh | FPR tong | FP (cua n) | Co cmd.exe: FP | Khong cmd.exe: FP | Du 64: FP | Ngan: FP | Spearman(diem, n_events) cua so am T-hard |
|---|---|---|---|---|---|---|---|
| b0_wazuh | 0.193 [0.114, 0.273] | 17/88 | 14/19 | 3/69 | 6/36 | 11/52 | 0.05 [-0.13, 0.23] |
| b1_tfidf_b | 0.000 [0.000, 0.000] | 0/88 | 0/19 | 0/69 | 0/36 | 0/52 | 0.78 [0.68, 0.84] |
| b2_lgbm_a | 0.011 [0.000, 0.034] | 1/88 | 1/19 | 0/69 | 1/36 | 0/52 | 0.02 [-0.20, 0.25] |
| fusion_F0 | 0.011 [0.000, 0.045] | 1/88 | 1/19 | 0/69 | 1/36 | 0/52 | 0.01 [-0.20, 0.23] |
| fusion_F0p | 0.011 [0.000, 0.045] | 1/88 | 1/19 | 0/69 | 1/36 | 0/52 | 0.01 [-0.20, 0.23] |
| fusion_F1 | 0.000 [0.000, 0.000] | 0/88 | 0/19 | 0/69 | 0/36 | 0/52 | - |
| fusion_F2 | 0.011 [0.000, 0.045] | 1/88 | 1/19 | 0/69 | 1/36 | 0/52 | 0.01 [-0.20, 0.23] |
| fusion_F3B | 0.011 [0.000, 0.045] | 1/88 | 1/19 | 0/69 | 1/36 | 0/52 | 0.01 [-0.20, 0.23] |
| fusion_F4B | 0.000 [0.000, 0.000] | 0/88 | 0/19 | 0/69 | 0/36 | 0/52 | 0.01 [-0.20, 0.23] |

**(3) T-hard - FP/n theo chu ky cong cu** (nhieu seed: FP trung binh)

| Chu ky | b0_wazuh | b1_tfidf_b | b2_lgbm_a | fusion_F0 | fusion_F0p | fusion_F1 | fusion_F2 | fusion_F3B | fusion_F4B |
|---|---|---|---|---|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | **2/41** | 0/41 | 0/41 | 0/41 | 0/41 | 0/41 | 0/41 | 0/41 | 0/41 |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | **1/12** | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 |
| `net.exe+net1.exe` | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | **3/5** | 0/5 | 0/5 | **1/5** | **1/5** | 0/5 | **1/5** | **1/5** | 0/5 |
| `ntdsutil.exe+vssadmin.exe [revert_control]` | **3/4** | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| `net.exe+nltest.exe+ping.exe` | **2/3** | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| `net.exe+net1.exe+vssadmin.exe` | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| `net.exe+net1.exe+nltest.exe` | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| `ipconfig.exe+netsh.exe` | **2/2** | 0/2 | **1/2** | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| `net.exe+nltest.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `vssadmin.exe+wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `arp.exe+ipconfig.exe+net.exe+netstat.exe+nltest.exe+route.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `nltest.exe+wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `nltest.exe+vssadmin.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `arp.exe+ipconfig.exe+netstat.exe+route.exe+wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `ntdsutil.exe+vssadmin.exe+wevtutil.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `arp.exe+net.exe+nltest.exe+ntdsutil.exe+ping.exe+vssadmin.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `arp.exe+net.exe+nltest.exe+ping.exe+wevtutil.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `nbtstat.exe+netsh.exe+nslookup.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `netsh.exe+nslookup.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |

**(4) Phan tang do dai tren T-clean / T-novel (cua so am, nguong khoa)**

| Mo hinh | T-clean du64 | T-clean ngan | Spearman T-clean | T-novel du64 | T-novel ngan | Spearman T-novel |
|---|---|---|---|---|---|---|
| b0_wazuh | 0/23 | 1/24 | 0.03 [-0.26, 0.37] | 11/54 | 0/41 | 0.24 [0.05, 0.42] |
| b1_tfidf_b | 0/23 | 0/24 | 0.33 [0.01, 0.60] | 4/54 | 0/41 | 0.68 [0.54, 0.79] |
| b2_lgbm_a | 0/23 | 0/24 | -0.09 [-0.38, 0.20] | 4/54 | 0/41 | 0.29 [0.10, 0.47] |
| fusion_F0 | 0/23 | 0/24 | 0.03 [-0.25, 0.34] | 4/54 | 0/41 | 0.12 [-0.09, 0.34] |
| fusion_F0p | 0/23 | 0/24 | 0.03 [-0.25, 0.34] | 4/54 | 0/41 | 0.12 [-0.09, 0.34] |
| fusion_F1 | 0/23 | 0/24 | - | 1/54 | 0/41 | 0.09 [0.07, 0.16] |
| fusion_F2 | 0/23 | 0/24 | 0.03 [-0.25, 0.34] | 5/54 | 0/41 | 0.12 [-0.09, 0.34] |
| fusion_F3B | 0/23 | 0/24 | 0.03 [-0.25, 0.34] | 4/54 | 0/41 | 0.12 [-0.09, 0.34] |
| fusion_F4B | 0/23 | 0/24 | 0.03 [-0.25, 0.34] | 4/54 | 0/41 | 0.12 [-0.09, 0.34] |

**(5) F1 theo TTP - T-clean** (nguong theo TTP khoa tren Train OOF; support = so cua so mang nhan)

| Mo hinh | T1016 (n=21) | T1018 (n=23) | T1087.002 (n=24) | T1654 (n=17) | T1003.003 (n=12) | macro-F1 |
|---|---|---|---|---|---|---|
| b0_wazuh | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.58 [0.44, 0.72] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.12 [0.09, 0.14] |
| b1_tfidf_b | 0.88 [0.75, 0.97] | 0.61 [0.38, 0.79] | 0.80 [0.65, 0.92] | 0.92 [0.80, 1.00] | 1.00 [1.00, 1.00] | 0.84 [0.78, 0.89] |
| b2_lgbm_a | 0.91 [0.81, 0.98] | 0.68 [0.50, 0.83] | 0.94 [0.86, 1.00] | 0.86 [0.71, 0.96] | 1.00 [1.00, 1.00] | 0.88 [0.82, 0.92] |
| fusion_F0 | 0.82 [0.70, 0.93] | 0.71 [0.53, 0.86] | 0.89 [0.79, 0.97] | 0.94 [0.86, 1.00] | 1.00 [1.00, 1.00] | 0.87 [0.83, 0.92] |
| fusion_F0p | 0.82 [0.70, 0.93] | 0.71 [0.53, 0.86] | 0.89 [0.79, 0.97] | 0.94 [0.86, 1.00] | 1.00 [1.00, 1.00] | 0.87 [0.83, 0.92] |
| fusion_F1 | 0.00 [0.00, 0.00] | 0.52 [0.29, 0.72] | 0.00 [0.00, 0.00] | 0.64 [0.38, 0.83] | 0.80 [0.57, 0.96] | 0.39 [0.32, 0.45] |
| fusion_F2 | 0.82 [0.70, 0.93] | 0.74 [0.56, 0.88] | 0.89 [0.79, 0.97] | 0.94 [0.86, 1.00] | 1.00 [1.00, 1.00] | 0.88 [0.83, 0.92] |
| fusion_F3B | 0.82 [0.70, 0.93] | 0.74 [0.56, 0.88] | 0.89 [0.79, 0.97] | 0.94 [0.86, 1.00] | 1.00 [1.00, 1.00] | 0.88 [0.83, 0.92] |
| fusion_F4B | 0.82 [0.67, 0.93] | 0.74 [0.56, 0.88] | 0.89 [0.79, 0.97] | 0.94 [0.86, 1.00] | 1.00 [1.00, 1.00] | 0.88 [0.83, 0.92] |

**(5) F1 theo TTP - T-novel** (nguong theo TTP khoa tren Train OOF; support = so cua so mang nhan)

| Mo hinh | T1016 (n=37) | T1018 (n=36) | T1087.002 (n=33) | T1654 (n=16) | T1003.003 (n=6) | macro-F1 |
|---|---|---|---|---|---|---|
| b0_wazuh | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.59 [0.47, 0.70] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.12 [0.09, 0.14] |
| b1_tfidf_b | 0.77 [0.65, 0.86] | 0.58 [0.41, 0.72] | 0.75 [0.62, 0.86] | 0.57 [0.38, 0.75] | 1.00 [1.00, 1.00] | 0.73 [0.67, 0.79] |
| b2_lgbm_a | 0.83 [0.73, 0.91] | 0.83 [0.73, 0.91] | 0.76 [0.64, 0.85] | 0.59 [0.42, 0.73] | 1.00 [1.00, 1.00] | 0.80 [0.75, 0.85] |
| fusion_F0 | 0.81 [0.72, 0.89] | 0.83 [0.73, 0.91] | 0.76 [0.65, 0.85] | 0.68 [0.52, 0.82] | 1.00 [1.00, 1.00] | 0.82 [0.76, 0.87] |
| fusion_F0p | 0.81 [0.72, 0.89] | 0.83 [0.73, 0.91] | 0.76 [0.65, 0.85] | 0.68 [0.52, 0.82] | 1.00 [1.00, 1.00] | 0.82 [0.76, 0.87] |
| fusion_F1 | 0.00 [0.00, 0.00] | 0.47 [0.27, 0.63] | 0.00 [0.00, 0.00] | 0.62 [0.35, 0.80] | 1.00 [1.00, 1.00] | 0.42 [0.35, 0.47] |
| fusion_F2 | 0.81 [0.72, 0.89] | 0.85 [0.75, 0.92] | 0.76 [0.65, 0.85] | 0.65 [0.50, 0.79] | 1.00 [1.00, 1.00] | 0.81 [0.76, 0.87] |
| fusion_F3B | 0.81 [0.72, 0.89] | 0.85 [0.75, 0.92] | 0.76 [0.65, 0.85] | 0.68 [0.52, 0.82] | 1.00 [1.00, 1.00] | 0.82 [0.76, 0.87] |
| fusion_F4B | 0.73 [0.60, 0.84] | 0.86 [0.77, 0.93] | 0.77 [0.67, 0.85] | 0.68 [0.51, 0.82] | 1.00 [1.00, 1.00] | 0.81 [0.75, 0.86] |

**(6) Phat hien som** - recall cua so duong khi chi giu k event dau tu event malicious dau tien (nguong khoa, khong chon lai)

| Mo hinh | T-clean k=4 | T-clean k=8 | T-clean k=16 | T-clean k=32 | T-clean du | T-novel k=4 | T-novel k=8 | T-novel k=16 | T-novel k=32 | T-novel du | T1003 phien T-novel k=4/8/16/32/du (cua 6) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| b0_wazuh | 0.69 [0.55, 0.83] | 0.71 [0.57, 0.86] | 0.76 [0.64, 0.88] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 0.87 [0.78, 0.94] | 0.87 [0.78, 0.94] | 0.87 [0.78, 0.94] | 0.94 [0.89, 1.00] | 0.98 [0.94, 1.00] | 0 / 0 / 0 / 3 / 5 |
| b1_tfidf_b | 0.86 [0.76, 0.95] | 0.88 [0.79, 0.98] | 0.90 [0.81, 0.98] | 0.93 [0.83, 1.00] | 0.98 [0.92, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.96 [0.91, 1.00] | 6 / 6 / 6 / 6 / 6 |
| b2_lgbm_a | 0.71 [0.57, 0.86] | 0.79 [0.67, 0.90] | 0.81 [0.69, 0.93] | 0.83 [0.71, 0.93] | 0.95 [0.88, 1.00] | 0.91 [0.83, 0.98] | 0.85 [0.76, 0.94] | 1.00 [1.00, 1.00] | 0.93 [0.85, 0.98] | 0.94 [0.88, 1.00] | 1 / 0 / 6 / 2 / 4 |
| fusion_F0 | 0.88 [0.79, 0.98] | 0.95 [0.88, 1.00] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.96 [0.91, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 6 / 6 / 6 / 6 / 6 |
| fusion_F0p | 0.88 [0.79, 0.98] | 0.95 [0.88, 1.00] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.96 [0.91, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 6 / 6 / 6 / 6 / 6 |
| fusion_F1 | 0.55 [0.40, 0.69] | 0.57 [0.43, 0.71] | 0.57 [0.43, 0.71] | 0.67 [0.52, 0.81] | 0.79 [0.65, 0.91] | 0.70 [0.59, 0.81] | 0.70 [0.59, 0.81] | 0.72 [0.61, 0.83] | 0.74 [0.63, 0.85] | 0.80 [0.68, 0.90] | 6 / 6 / 6 / 6 / 6 |
| fusion_F2 | 0.88 [0.79, 0.98] | 0.95 [0.88, 1.00] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.96 [0.91, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 6 / 6 / 6 / 6 / 6 |
| fusion_F3B | 0.88 [0.79, 0.98] | 0.95 [0.88, 1.00] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.96 [0.91, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 6 / 6 / 6 / 6 / 6 |
| fusion_F4B | 0.86 [0.76, 0.95] | 0.95 [0.88, 1.00] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.96 [0.91, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 6 / 6 / 6 / 6 / 6 |

## 3. Paired bootstrap + Holm (6 so sanh)

1000 lan, seed 1337, cung mau cua so; 'hon' chi khi p Holm < 0.05; 'khong kem' = can duoi CI 95% cua hieu so >= 0 (FPR: can tren <= 0).

| So sanh | Chi so | Hieu [CI 95%] | p | p Holm | Ket luan |
|---|---|---|---|---|---|
| F3-B - F0 | macro-F1 TTP T-novel | +0.003 [+0.000, +0.011] | 0.730 | 1.000 | khong khac; khong kem (bien 0) |
| F3-B - F0 | PR-AUC T-novel | +0.012 [+0.002, +0.029] | 0.026 | 0.104 | khong khac; khong kem (bien 0) |
| F3-B - F0 | FPR T-hard | +0.000 [+0.000, +0.000] | 1.000 | 1.000 | khong khac; khong kem (bien 0) |
| F3-B - F1 | macro-F1 TTP T-novel | +0.403 [+0.316, +0.481] | 0.001 | 0.006 | hon |
| F3-B - F1 | PR-AUC T-novel | +0.146 [+0.071, +0.235] | 0.001 | 0.006 | hon |
| F3-B - F1 | FPR T-hard | +0.011 [+0.000, +0.034] | 0.722 | 1.000 | khong khac |

- **F0' trung F0 tren moi chi so test** -> khac biet F3-B vs F0 hoan toan do luat: xep hang nhi phan (PR-AUC T-novel 0.986 -> 0.998) va T1018 (T-novel 0.83 -> 0.85, T-clean 0.71 -> 0.74). Khong co y nghia sau Holm.
- **Muc giam FPR thay o OOF khong lap lai tren test:** tren OOF F3 co FPR hard_negative 0.028 so voi 0.037 cua F0, nhung nguong F3 (0.869166) gan trung tau F0 (0.8691656) - do hoa diem tai nguong (lam tron 6 chu so), khong phai do luat; tren test cung 1/88.

## 4. Giai thich canh bao (muc 6) va pipeline (muc 7)

| Tap | Canh bao | Co >= 1 luat | TP (co luat) | FP (co luat) | decision_source | Luat khop nhung khong canh bao |
|---|---|---|---|---|---|---|
| t_clean | 42 | 33 (79%) | 42 (33) | 0 (0) | {'both': 33, 'ai': 9} | 0 |
| t_hard | 1 | 0 (0%) | 0 (0) | 1 (0) | {'ai': 1} | 0 |
| t_novel | 58 | 43 (74%) | 54 (43) | 4 (0) | {'both': 43, 'ai': 15} | 1 |

**Precision theo decision_source (KET QUA MO TA, so mau nho; CI Wilson 95%)**

| Tap | `both` (AI + luat xac nhan): TP/n, precision [Wilson] | `ai` (chi AI): TP/n, precision [Wilson] | `rule` (chi luat) |
|---|---|---|---|
| t_clean | 33/33 = 1.000 [0.896, 1.000] | 9/9 = 1.000 [0.701, 1.000] | - |
| t_hard | - | 0/1 = 0.000 [0.000, 0.793] | - |
| t_novel | 43/43 = 1.000 [0.918, 1.000] | 11/15 = 0.733 [0.480, 0.891] | - |
| gop 3 tap | 76/76 = 1.000 [0.952, 1.000] | 20/25 = 0.800 [0.609, 0.911] | - |

**Ham y van hanh:** canh bao co luat Sigma xac nhan (`both`) dung 76/76 tren test -> uu tien xu ly; canh bao chi-AI (`ai`) dung 20/25 - ca 5 canh bao nham deu thuoc nhom nay -> can nguoi phan tich xem lai (top-5 attention di kem). CI Wilson cua hai nhom khong chong nhau ([0.952, 1.000] vs [0.609, 0.911]), nhung day van la MO TA tren 101 canh bao (5 nham), khong phai kiem dinh dat truoc; nhom `both` gom cac cua so co lenh tan cong ro (de hon) nen khong suy ra quan he nhan qua.

**Vi du (chon tat dinh, chi tiet + top-5 attention: `reports/step8/m3_explain.md`):**

- **AI chan luat khop nham:** `20261014-150302-win10-01-a:w00224` (T-novel, LANH TINH) - luat `VTR-T1654-01` (`cmd~'system'`) khop lenh `auditpol /get /subcategory:"System Integrity"`; p_ai 0.738 + 0.1 = 0.838 < nguong 0.869 -> khong canh bao.
- **Canh bao nham tren T-hard (chi AI, khong luat xac nhan):** `20261015-122705-win10-01-h:w00015` (kich ban quan tri batch07) - p 0.934, TTP ['T1016']; top-5 attention: `cmd /c netsh interface show interface  ` (0.12); `netsh  interface show interface` (0.11); `cmd /c nbtstat -n  ` (0.10); `nbtstat  -n` (0.07). Lenh quan tri trung lenh kham pha T1016; khong luat nao xac nhan -> nhom `ai`, can xem lai.
- **AI + luat:** `20261014-043324-win10-01-a:w00000` (t_clean, doc hai ['T1016', 'T1087.002']) - score 1.097, luat: VTR-BIN-04; attention cao nhat `cmd /c ipconfig /all netsh interface show interface arp -a n`.
- **chi AI:** `20261014-043324-win10-01-a:w00032` (t_clean, doc hai ['T1016', 'T1087.002']) - score 0.997, luat: khong; attention cao nhat `cmd /c ipconfig /all netsh interface show interface arp -a n`.
- **Chi do luat:** khong co tren test.

**Pipeline `src/pipeline/infer.py`** (featurize vocab dong bang -> ONNX VT-Seq-ens -> Sigma -> F3-B): trung `fusion_<split>.jsonl` 0 lech quyet dinh tren 3 tap (diem lech <= 6e-7). Do tre host CPU (Intel64 Family 6 Model 158 Stepping 13, GenuineIntel, onnxruntime 1 thread), ms/cua so:

| Buoc | batch 1 TB | batch 1 p95 | batch 32 TB | batch 32 p95 |
|---|---|---|---|---|
| total | 2.77 | 5.97 | 2.12 | 3.06 |
| featurize | 0.86 | 3.44 | 0.78 | 1.41 |
| onnx | 1.46 | 1.88 | 0.95 | 1.02 |
| sigma | 0.40 | 0.87 | 0.37 | 0.67 |
| fusion | 0.03 | 0.03 | 0.00 | 0.01 |

## 5. Thao luan trung thuc

- **Fusion giup o dau:** (i) phan loai muc tin cay canh bao - nhom co luat xac nhan khong co canh bao nham tren test; (ii) moi canh bao co giai thich: 75% co luat Sigma (kem provenance ve cua so/phien Train), 100% co top-5 event attention; (iii) xep hang nhi phan tot hon (PR-AUC 0.986 -> 0.998) va T1018 nhinh hon - nho, khong co y nghia sau Holm; (iv) AI chan duoc luat khop nham (auditpol).
- **Fusion KHONG giup o dau:** khong tang recall (chi-AI da bat 96/96 cua so duong test), khong giam FPR T-hard (van 1/88, cung cua so voi chi-AI), khong co canh bao chi-do-luat, khong cai thien T1016 / T1087.002 (khong co luat theo TTP). Ve diem so, F3-B chi 'khong kem' chi-AI.
- Vi vay gia tri cua Buoc 8 nam o **giai thich duoc va xuat xu cua luat** cung voi phan loai muc tin cay canh bao, KHONG nam o diem so.

## 6. Han che

- **Luat fold de dai hon luat cuoi** (khong co OOF long trong fold): fusion hoc tren OOF co the tin luat khac luc test. Da xu ly bang bien the B (chi kenh luat theo TTP co trong bo luat cuoi); tham so con lai (beta, nguong) van hoc tren luat fold.
- **Muc giam FPR o OOF khong lap lai tren test** (hieu ung hoa nguong) - khong tuyen bo F3-B giam FPR.
- **T1003.003 test nho** (6 phien T-novel, 12 cua so T-clean); **2 host / 1 domain** (DC01 + WIN10-01, CORP.VTLAB.TEST).
- Precision theo decision_source la mo ta tren 101 canh bao (5 nham): CI Wilson rong, chua kiem dinh.
- Ke thua: crop do dai chua vung o tung seed (Buoc 6), token chung `create` / `system` cua luat va VTR-T1654-01 khop 1 cua so lanh tinh (Buoc 7, da dinh chinh), coverage gap va loi trung PID (dataset card muc 9), hat giong luat co canh bao scaffold (Buoc 6).

## 7. Tieu chi chap nhan Buoc 8 (brief muc 9)

| # | Tieu chi | Ket qua | Bang chung |
|---|---|---|---|
| 1 | Checksum dataset khop; fusion hoc/chon chi tren OOF; khong dung rules_train.jsonl | DAT | check_dataset True; test_fuse 1a-1c (khong doc rules_train / preds test) True; OOF AI = TB 5 seed True; F4 CV long True |
| 2 | final_fusion.json commit truoc khi chay test | DAT | commit 3fd9531 co final_fusion.json True, chua co ket qua test True, la to tien cua commit ket qua test bdf2adc True; final_fusion.json khong doi tu luc khoa True |
| 3 | Bang test du F0-F4; paired bootstrap + Holm | DAT | eval F0, F0', F1, F2, F3-B, F4-B True; Holm 6 so sanh True |
| 4 | alerts_<split>.jsonl du schema; co ti le canh bao duoc luat giai thich | DAT | 101 canh bao, du truong muc 6 True; co luat 75% |
| 5 | infer.py trung ket qua cham (0 lech) va co do tre | DAT | 0 lech quyet dinh tren 3 tap True; do tre batch 1 2.773 ms, batch 32 2.123 ms / cua so |
| 6 | reports/preds/fusion_<split>.jsonl cung dinh dang chung | DAT | fusion_{train (OOF), t_clean, t_hard, t_novel}.jsonl; khoa ban ghi trung Buoc 5 |

**Tong: 6/6 dat.** Unit test: 13/13 PASS trong 5.8s
