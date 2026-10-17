# VT-Guard Buoc 6 moc 2 - chuoi ablation kien truc: CHI OOF tren Train

Sinh boi `src/models/step6_m2_table.py` luc 2026-10-17T12:37:48+07:00. Huan luyen tren Colab bang `notebooks/step6_vtseq_colab.ipynb` (chi goi `vtseq.run_oof_experiment`, clone theo commit); bang dung tren host tu ket qua tai ve. KHONG doc / du doan tap test o moc nay.

CV 5 fold theo nhom chong thoi gian (`evaluate.cv_folds`), Train 483 cua so (165 duong, 59 hard_negative). Nguong nhi phan: FPR <= 1% tren cua so am OOF; nguong TTP: max-F1 OOF theo TTP; p_bin hay p_bin' = max(p_bin, max p_ttp) chon theo PR-AUC OOF. M0 = B3 Buoc 5 (3 seed, tran 60 epoch), tinh lai bang CUNG quy tac. Cac cau hinh khac 5 seed (1337, 7, 42, 2024, 99), tran 100 epoch, patience 10. Gia tri: trung binh +- do lech chuan (ddof=1) qua seed.

**(1) Bang OOF**

| Cau hinh | Thay doi | seed | macro-F1 TTP | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | PR-AUC bin | FPR hard_neg | FPR am | Recall | Spearman(diem, do dai) am | Nguong bin | p_bin / p_bin' |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M0a | B3 (a): GRU last-state, don nhiem, crop B3 (Buoc 5) | 3 | 0.774 +- 0.007 | 0.714 +- 0.008 | 0.719 +- 0.018 | 0.752 +- 0.005 | 0.705 +- 0.001 | 0.980 +- 0.007 | 0.993 +- 0.001 | 0.021 +- 0.011 | 0.010 +- 0.000 | 0.964 +- 0.013 | 0.12 +- 0.10 | 0.919 +- 0.018 | 3 / 0 |
| M0b | B3 (b): nhu M0a, bo image/parent (Buoc 5) | 3 | 0.787 +- 0.009 | 0.734 +- 0.011 | 0.698 +- 0.010 | 0.770 +- 0.009 | 0.739 +- 0.008 | 0.996 +- 0.007 | 0.989 +- 0.004 | 0.018 +- 0.000 | 0.010 +- 0.000 | 0.879 +- 0.082 | 0.16 +- 0.13 | 0.942 +- 0.043 | 1 / 2 |
| M1 | + attention pooling (don nhiem) | 5 | 0.822 +- 0.008 | 0.762 +- 0.012 | 0.775 +- 0.021 | 0.779 +- 0.009 | 0.801 +- 0.011 | 0.995 +- 0.007 | 0.998 +- 0.002 | 0.024 +- 0.005 | 0.012 +- 0.002 | 0.974 +- 0.026 | 0.04 +- 0.03 | 0.622 +- 0.263 | 4 / 1 |
| M2 | + da nhiem | 5 | 0.831 +- 0.007 | 0.774 +- 0.015 | 0.762 +- 0.007 | 0.802 +- 0.016 | 0.827 +- 0.012 | 0.988 +- 0.012 | 0.996 +- 0.001 | 0.029 +- 0.008 | 0.012 +- 0.001 | 0.977 +- 0.030 | -0.01 +- 0.06 | 0.772 +- 0.132 | 1 / 4 |
| M3 | + crop U[4,n] moi lop | 5 | 0.825 +- 0.018 | 0.769 +- 0.035 | 0.740 +- 0.017 | 0.800 +- 0.021 | 0.826 +- 0.028 | 0.988 +- 0.009 | 0.996 +- 0.001 | 0.028 +- 0.000 | 0.010 +- 0.001 | 0.952 +- 0.043 | -0.02 +- 0.08 | 0.877 +- 0.060 | 1 / 4 |
| M4 | + name dropout p=0.5 | 5 | 0.820 +- 0.012 | 0.758 +- 0.012 | 0.750 +- 0.021 | 0.794 +- 0.013 | 0.816 +- 0.033 | 0.983 +- 0.007 | 0.995 +- 0.002 | 0.026 +- 0.004 | 0.010 +- 0.001 | 0.957 +- 0.044 | 0.03 +- 0.04 | 0.788 +- 0.135 | 0 / 5 |
| M4b | M3 + bo han image/parent | 5 | 0.820 +- 0.009 | 0.754 +- 0.015 | 0.730 +- 0.014 | 0.801 +- 0.014 | 0.823 +- 0.024 | 0.990 +- 0.010 | 0.994 +- 0.003 | 0.020 +- 0.012 | 0.011 +- 0.002 | 0.947 +- 0.045 | -0.02 +- 0.07 | 0.762 +- 0.249 | 1 / 4 |

**(2) Epoch moi fold** - `tot nhat/dung` (M0: chi co epoch tot nhat; dau bin|ttp). Tran: M0 60, M1-M4b 100.

| Cau hinh | seed | fold 1 | fold 2 | fold 3 | fold 4 | fold 5 | fold cham tran (epoch tot nhat = tran) | fold chay toi tran |
|---|---|---|---|---|---|---|---|---|
| M0a | 1337 | bin:37 ; ttp:18 | bin:36 ; ttp:49 | bin:41 ; ttp:15 | bin:20 ; ttp:35 | bin:21 ; ttp:13 | 0 | - |
| M0a | 7 | bin:39 ; ttp:17 | bin:46 ; ttp:33 | bin:27 ; ttp:60 | bin:24 ; ttp:38 | bin:13 ; ttp:17 | 1 | - |
| M0a | 42 | bin:31 ; ttp:16 | bin:30 ; ttp:49 | bin:28 ; ttp:28 | bin:26 ; ttp:60 | bin:22 ; ttp:14 | 1 | - |
| M0b | 1337 | bin:27 ; ttp:16 | bin:40 ; ttp:40 | bin:41 ; ttp:27 | bin:42 ; ttp:54 | bin:35 ; ttp:13 | 0 | - |
| M0b | 7 | bin:18 ; ttp:22 | bin:31 ; ttp:43 | bin:29 ; ttp:27 | bin:24 ; ttp:45 | bin:32 ; ttp:14 | 0 | - |
| M0b | 42 | bin:28 ; ttp:27 | bin:20 ; ttp:37 | bin:31 ; ttp:19 | bin:44 ; ttp:30 | bin:18 ; ttp:18 | 0 | - |
| M1 | 1337 | bin:41/51 ; ttp:19/29 | bin:23/33 ; ttp:12/22 | bin:37/47 ; ttp:48/58 | bin:22/32 ; ttp:29/39 | bin:26/36 ; ttp:4/14 | 0 | 0 |
| M1 | 7 | bin:43/53 ; ttp:20/30 | bin:55/65 ; ttp:21/31 | bin:17/27 ; ttp:40/50 | bin:20/30 ; ttp:47/57 | bin:6/16 ; ttp:5/15 | 0 | 0 |
| M1 | 42 | bin:24/34 ; ttp:51/61 | bin:37/47 ; ttp:31/41 | bin:58/68 ; ttp:26/36 | bin:10/20 ; ttp:26/36 | bin:9/19 ; ttp:7/17 | 0 | 0 |
| M1 | 2024 | bin:49/59 ; ttp:27/37 | bin:34/44 ; ttp:34/44 | bin:52/62 ; ttp:15/25 | bin:36/46 ; ttp:37/47 | bin:9/19 ; ttp:7/17 | 0 | 0 |
| M1 | 99 | bin:27/37 ; ttp:21/31 | bin:50/60 ; ttp:46/56 | bin:17/27 ; ttp:46/56 | bin:31/41 ; ttp:40/50 | bin:5/15 ; ttp:5/15 | 0 | 0 |
| M2 | 1337 | 32/42 | 56/66 | 49/59 | 37/47 | 7/17 | 0 | 0 |
| M2 | 7 | 46/56 | 28/38 | 30/40 | 28/38 | 5/15 | 0 | 0 |
| M2 | 42 | 41/51 | 45/55 | 39/49 | 41/51 | 8/18 | 0 | 0 |
| M2 | 2024 | 28/38 | 38/48 | 39/49 | 16/26 | 6/16 | 0 | 0 |
| M2 | 99 | 26/36 | 35/45 | 34/44 | 30/40 | 5/15 | 0 | 0 |
| M3 | 1337 | 44/54 | 39/49 | 37/47 | 42/52 | 4/14 | 0 | 0 |
| M3 | 7 | 28/38 | 45/55 | 80/90 | 31/41 | 5/15 | 0 | 0 |
| M3 | 42 | 28/38 | 36/46 | 33/43 | 34/44 | 8/18 | 0 | 0 |
| M3 | 2024 | 52/62 | 59/69 | 70/80 | 30/40 | 8/18 | 0 | 0 |
| M3 | 99 | 38/48 | 72/82 | 41/51 | 19/29 | 10/20 | 0 | 0 |
| M4 | 1337 | 34/44 | 33/43 | 35/45 | 57/67 | 14/24 | 0 | 0 |
| M4 | 7 | 38/48 | 48/58 | 49/59 | 78/88 | 7/17 | 0 | 0 |
| M4 | 42 | 36/46 | 61/71 | 42/52 | 45/55 | 14/24 | 0 | 0 |
| M4 | 2024 | 49/59 | 46/56 | 19/29 | 33/43 | 7/17 | 0 | 0 |
| M4 | 99 | 44/54 | 71/81 | 29/39 | 37/47 | 11/21 | 0 | 0 |
| M4b | 1337 | 17/27 | 42/52 | 53/63 | 41/51 | 12/22 | 0 | 0 |
| M4b | 7 | 27/37 | 68/78 | 55/65 | 26/36 | 8/18 | 0 | 0 |
| M4b | 42 | 38/48 | 48/58 | 25/35 | 64/74 | 6/16 | 0 | 0 |
| M4b | 2024 | 39/49 | 62/72 | 49/59 | 13/23 | 20/30 | 0 | 0 |
| M4b | 99 | 34/44 | 26/36 | 48/58 | 24/34 | 7/17 | 0 | 0 |

Tong fold cham tran: M0a 2/30, M0b 0/30, M1 0/50, M2 0/25, M3 0/25, M4 0/25, M4b 0/25.

**(3) De xuat cau hinh cuoi theo quy tac 4.3 (chi OOF)**

Ung vien: M3, M4, M4b. Nguong ngang nhau: |chenh trung binh| <= do lech chuan gop qua seed.

- Tieu chi `macro_f1_ttp`: tot nhat M3 (0.8246); ngang nhau voi no: M3, M4, M4b -> con lai M3, M4, M4b
- Tieu chi `pr_auc_bin`: tot nhat M3 (0.9959); ngang nhau voi no: M3, M4, M4b -> con lai M3, M4, M4b
- Tieu chi `fpr_hard_negative`: tot nhat M4b (0.0202); ngang nhau voi no: M3, M4, M4b -> con lai M3, M4, M4b
- Van ngang nhau sau ca 3 tieu chi: M3, M4, M4b (can quyet dinh them).

