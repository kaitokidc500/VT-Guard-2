# VT-Guard Buoc 6 moc 3 - VT-Seq tren test (cham bang evaluate.py tren host)

Huan luyen chinh tren Colab (CUDA) bang `notebooks/step6_vtseq_colab.ipynb` (commit 44f8948), cau hinh KHOA truoc test (`reports/step6/final_config.json`: VT-Seq = M3). Test chay MOT lan; nguong, p_bin/p_bin', so epoch lay tu OOF Train. Bang day du (bang chinh, T-hard theo chu ky / cmd / do dai, F1 theo TTP, phat hien som) o `reports/step6/m3_summary.md`.

**Paired bootstrap** (1000 lan, seed 1337, cung mau cua so; hieu so = VT-Seq-ens - baseline; FPR: am = tot hon). Chi tuyen bo 'hon' khi CI 95% khong chua 0.

| So sanh | macro-F1 TTP T-novel: a / b / hieu [CI] | PR-AUC T-novel: a / b / hieu [CI] | FPR T-hard: a / b / hieu [CI] |
|---|---|---|---|
| vtseq_M3_ens - b1_tfidf_b | 0.817 / 0.735 / **+0.082** [+0.009, +0.156] a hon | 0.986 / 0.979 / **+0.007** [-0.007, +0.029] khong khac co y nghia | 0.011 / 0.000 / **+0.011** [+0.000, +0.034] khong khac co y nghia |
| vtseq_M3_ens - b2_lgbm_a | 0.817 / 0.802 / **+0.015** [-0.026, +0.050] khong khac co y nghia | 0.986 / 0.990 / **-0.004** [-0.015, +0.003] khong khac co y nghia | 0.011 / 0.011 / **+0.000** [-0.023, +0.034] khong khac co y nghia |
| vtseq_M3_ens - b3_gru_b_s1337 | 0.817 / 0.725 / **+0.092** [+0.039, +0.183] a hon | 0.986 / 0.918 / **+0.068** [+0.007, +0.158] a hon | 0.011 / 0.011 / **+0.000** [+0.000, +0.000] khong khac co y nghia |
| vtseq_M3_ens - b3_gru_b_s7 | 0.817 / 0.749 / **+0.068** [+0.039, +0.102] a hon | 0.986 / 0.930 / **+0.056** [+0.001, +0.129] a hon | 0.011 / 0.023 / **-0.011** [-0.045, +0.023] khong khac co y nghia |
| vtseq_M3_ens - b3_gru_b_s42 | 0.817 / 0.777 / **+0.040** [+0.018, +0.062] a hon | 0.986 / 0.945 / **+0.041** [+0.001, +0.094] a hon | 0.011 / 0.023 / **-0.011** [-0.045, +0.023] khong khac co y nghia |
| vtseq_M4b_ens - b1_tfidf_b | 0.831 / 0.735 / **+0.096** [+0.026, +0.166] a hon | 0.988 / 0.979 / **+0.009** [-0.007, +0.035] khong khac co y nghia | 0.000 / 0.000 / **+0.000** [+0.000, +0.000] khong khac co y nghia |
| vtseq_M4b_ens - b2_lgbm_a | 0.831 / 0.802 / **+0.029** [-0.011, +0.065] khong khac co y nghia | 0.988 / 0.990 / **-0.002** [-0.013, +0.006] khong khac co y nghia | 0.000 / 0.011 / **-0.011** [-0.034, +0.000] khong khac co y nghia |
| vtseq_M4b_ens - b3_gru_b_s1337 | 0.831 / 0.725 / **+0.106** [+0.053, +0.202] a hon | 0.988 / 0.918 / **+0.070** [+0.012, +0.158] a hon | 0.000 / 0.011 / **-0.011** [-0.034, +0.000] khong khac co y nghia |
| vtseq_M4b_ens - b3_gru_b_s7 | 0.831 / 0.749 / **+0.082** [+0.051, +0.117] a hon | 0.988 / 0.930 / **+0.058** [+0.007, +0.129] a hon | 0.000 / 0.023 / **-0.023** [-0.057, +0.000] khong khac co y nghia |
| vtseq_M4b_ens - b3_gru_b_s42 | 0.831 / 0.777 / **+0.053** [+0.031, +0.078] a hon | 0.988 / 0.945 / **+0.043** [+0.006, +0.093] a hon | 0.000 / 0.023 / **-0.023** [-0.057, +0.000] khong khac co y nghia |

**Hieu chinh so sanh boi (Holm, 9 so sanh: VT-Seq-ens M3 vs 3 baseline x 3 chi so).** p-value hai phia tu phan bo bootstrap (san 1/1000). B3 (b): lay seed co p lon nhat (bao thu). Cac dong khac (M4b-ens, tung seed B3) o bang tren la tham khao, CHUA hieu chinh so sanh boi.

| Baseline | Chi so | Hieu (VT-Seq-ens - baseline) [CI 95%] | p | p Holm | Ket luan sau Holm (alpha 0.05) |
|---|---|---|---|---|---|
| B1 TF-IDF (b) | macro-F1 TTP T-novel | +0.082 [+0.009, +0.156] | 0.032 | 0.256 | khong khac co y nghia |
| B1 TF-IDF (b) | PR-AUC T-novel | +0.007 [-0.007, +0.029] | 0.454 | 1.000 | khong khac co y nghia |
| B1 TF-IDF (b) | FPR T-hard | +0.011 [+0.000, +0.034] | 0.722 | 1.000 | khong khac co y nghia |
| B2 (a) | macro-F1 TTP T-novel | +0.015 [-0.026, +0.050] | 0.462 | 1.000 | khong khac co y nghia |
| B2 (a) | PR-AUC T-novel | -0.004 [-0.015, +0.003] | 0.276 | 1.000 | khong khac co y nghia |
| B2 (a) | FPR T-hard | +0.000 [-0.023, +0.034] | 1.000 | 1.000 | khong khac co y nghia |
| B3 (b) (3 seed, p lon nhat) | macro-F1 TTP T-novel | +0.092 [+0.039, +0.183] | 0.001 | 0.009 | VT-Seq-ens hon |
| B3 (b) (3 seed, p lon nhat) | PR-AUC T-novel | +0.056 [+0.001, +0.129] | 0.042 | 0.294 | khong khac co y nghia |
| B3 (b) (3 seed, p lon nhat) | FPR T-hard | +0.000 [+0.000, +0.000] | 1.000 | 1.000 | khong khac co y nghia |

**Ghi chu**

- **Mo hinh trien khai = VT-Seq-ens (M3, trung binh xac suat 5 seed)**, nguong chon tren OOF trung binh. Seed le KHONG on dinh voi T1003.003 (bang cuoi: M3 seed 42 bat 5/6 phien, seed 7 chi 4/6 o nhan TTP; M4b va M3cp seed 99 bo sot 0/6), ens bat 6/6.
- **Crop do dai (M2 -> M3), trung thuc:** Spearman trung binh giam (T-hard +0.32 -> +0.11, T-novel +0.29 -> +0.14) CHU YEU nho seed 7 (-0.44 / -0.61); trung vi chi giam nhe (+0.40 -> +0.29, +0.40 -> +0.33) va 3/5 seed M3 van > +0.2 tren T-novel (+0.35, +0.33, +0.43). VT-Seq-ens dat |rho| <= 0.2 (T-hard +0.01, T-novel +0.12) mot phan do TRIET TIEU tuong quan trai dau giua cac seed, khong chung minh tung mo hinh trung lap voi do dai. Kiem soat do dai van la han che mo.


**Spearman(diem, n_events) tren cua so am - tung seed (hieu qua crop: M2 -> M3)**

| Cau hinh | s1337 | s7 | s42 | s2024 | s99 | trung binh | trung vi |
|---|---|---|---|---|---|---|---|
| M2 T-hard | +0.24 | -0.06 | +0.61 | +0.44 | +0.40 | +0.32 +- 0.25 | +0.40 |
| M2 T-novel | +0.38 | -0.23 | +0.49 | +0.40 | +0.40 | +0.29 +- 0.29 | +0.40 |
| M3 T-hard | +0.29 | -0.44 | +0.30 | +0.30 | +0.08 | +0.11 +- 0.32 | +0.29 |
| M3 T-novel | +0.35 | -0.61 | +0.33 | +0.43 | +0.18 | +0.14 +- 0.43 | +0.33 |
| M4 T-hard | +0.15 | +0.42 | +0.49 | +0.52 | -0.10 | +0.30 +- 0.26 | +0.42 |
| M4 T-novel | +0.24 | +0.45 | +0.37 | +0.50 | -0.24 | +0.26 +- 0.30 | +0.37 |
| M4b T-hard | +0.41 | +0.55 | +0.52 | +0.19 | +0.08 | +0.35 +- 0.21 | +0.41 |
| M4b T-novel | +0.34 | +0.27 | +0.37 | +0.49 | -0.00 | +0.29 +- 0.18 | +0.34 |
| vtseq_M3_ens | T-hard +0.01, T-novel +0.12 | | | | | | |
| vtseq_M4b_ens | T-hard +0.50, T-novel +0.48 | | | | | | |

**T1003.003 theo phien T-novel tung seed** (nhi phan / nhan TTP, cua 6)

| Cau hinh | s1337 | s7 | s42 | s2024 | s99 |
|---|---|---|---|---|---|
| M1 | 6 / 6 | 4 / 6 | 6 / 3 | 6 / 1 | 6 / 6 |
| M2 | 6 / 6 | 6 / 4 | 6 / 6 | 6 / 6 | 6 / 6 |
| M3 | 6 / 6 | 6 / 4 | 5 / 6 | 6 / 6 | 6 / 6 |
| M4 | 6 / 6 | 6 / 6 | 6 / 6 | 6 / 6 | 6 / 6 |
| M4b | 6 / 6 | 6 / 6 | 6 / 6 | 6 / 6 | 0 / 0 |
| M3cp | 6 / 6 | 6 / 6 | 6 / 6 | 6 / 6 | 0 / 0 |
