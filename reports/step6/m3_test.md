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
