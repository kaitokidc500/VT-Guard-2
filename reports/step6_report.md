# VT-Guard - Bao cao Buoc 6: VT-Seq (GRU-Attention da nhiem) tren dataset-v1.2

Sinh tu dong boi `src/models/step6_report.py` luc 2026-10-17T13:56:02+07:00. So lieu: `reports/step6_results.json`; chi tiet: `reports/step6/` (m2_oof.md, m3_test.md, m3_summary.md, m4_explain.md, eval/*.json); du doan cho Buoc 8: `reports/preds/vtseq*`.

## 0. Tom tat va moi truong

- **Mo hinh trien khai: VT-Seq-ens** = trung binh xac suat 5 seed (1337, 7, 42, 2024, 99) cua cau hinh **M3** (embedding event + GRU 1 lop hidden 96 + attention pooling + da nhiem bin/TTP + crop do dai U[4,n]); nguong nhi phan FPR <= 1% tren OOF Train trung binh; p_bin' = max(p_bin, max p_ttp). Seed le KHONG duoc dung de trien khai (khong on dinh voi T1003.003, muc 6).
- **Moi truong:** moc 2 (OOF chuoi ablation) va moc 3 (fit cuoi + du doan test MOT lan) huan luyen tren **Colab CUDA** (torch 2.11.0+cu130, commit `44f8948d`) bang `notebooks/step6_vtseq_colab.ipynb` (di kem de tai lap); cham diem bang `src/eval/evaluate.py` tren host. Hat giong luat (attention OOF) va ONNX chay tren **host CPU**; 25 mo hinh fold huan luyen lai tren host co diem OOF tuong quan 0.991-0.999 voi Colab.
- **Khoa truoc test:** cau hinh M3, nguong, p_bin/p_bin', so epoch cuoi ghi o `reports/step6/final_config.json` (commit 3ebc94b) truoc khi co bat ky du doan test nao. Quy tac 4.3 cho M3/M4/M4b ngang nhau; pha hoa bang do on dinh nguong OOF (them sau khi xem OOF, van chi dua tren Train).

## 1. Ket luan chinh

1. **Sau hieu chinh Holm (9 so sanh), VT-Seq-ens hon B3 (GRU thuan, cung ho) o macro-F1 TTP T-novel**: hieu +0.092 [CI +0.039, +0.183], p Holm 0.009 (B3 lay seed bao thu nhat).
2. **Chuoi ablation M0 -> M4(b): attention pooling la nguon cai thien chinh.** OOF macro-F1 TTP 0.774 +- 0.007 (M0a) -> 0.822 +- 0.007 (M1); tren test T1654 T-novel 0.46 +- 0.02 -> 0.73 +- 0.08 (moi seed M1 0.61-0.82 > moi seed B3 0.44-0.53). Macro-F1 test cua M1 0.78 +- 0.08 dao dong vi T1003.003 chi 6 cua so; M2-M3 on dinh hon. Da nhiem / crop / name dropout / bo ten cong cu: thay doi nho, trong do lech chuan giua seed (mo ta trung binh +- do lech chuan, khong them kiem dinh).
3. **So voi B1 TF-IDF (b) va B2 (a): KHONG khac biet co y nghia sau Holm** (macro-F1 TTP T-novel: vs B1 +0.082, p 0.032 -> p Holm 0.256; vs B2 +0.015, p Holm 1.000; PR-AUC va FPR T-hard deu khong khac). Nhi phan va FPR T-hard da gan tran o baseline nhu brief du doan; VT-Seq khong kem B1 o day. **Khong tuyen bo VT-Seq tot hon moi baseline.**
4. **Uu the con lai cua VT-Seq (mo ta, khong phai kiem dinh 'hon'):**
   - T1654 (TTP kho nhat): VT-Seq-ens 0.68 vs B2 (a) 0.59, B1 (b) 0.57, B3 0.46-0.50.
   - Ben khi bo ten cong cu: VT-Seq-ens (M4b) macro-F1 TTP T-novel 0.83, T-hard FP 0/88 vs B2 (b) 0.45, 14/88.
   - Trung lap do dai (ens): Spearman diem~n_events am T-hard +0.01, T-novel +0.12 (B1 TF-IDF (b) +0.78 / +0.68) - xem han che ve crop.
   - Nguong on dinh: do lech chuan nguong nhi phan OOF cua M3 0.060 (nho nhat trong M1-M4b); so voi B3 Buoc 5 (max-F1: 0.51-0.90 o B3 (b)). Luu y: khi ap CUNG quy tac FPR <= 1%, nguong B3 cung on dinh (0.018 / 0.043) -> cai thien nay den tu QUY TAC NGUONG, khong tu kien truc.
   - Attention trung thuc (faithfulness dat o moi k cho ens, muc 7) va xuat ONNX: ens 5 mang ~1.4 ms/cua so (1 thread CPU).

## 2. Chuoi ablation M0 -> M4(b) (OOF Train va test; trung binh +- do lech chuan qua seed)

| Ma | Cau hinh | seed | OOF macro-F1 TTP | OOF PR-AUC | OOF FPR hard_neg | OOF nguong bin | Test T-novel F1 | Test T-novel PR-AUC | Test macro-F1 clean / novel | Test T1654 novel | T-hard FP/88 | Spearman T-hard / T-novel | T1003 phien bin / TTP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M0a | B3 (a): GRU last-state, don nhiem (Buoc 5) | 3 | 0.774 +- 0.007 | 0.993 +- 0.001 | 0.021 +- 0.011 | 0.919 +- 0.018 | 0.929 +- 0.001 | 0.918 +- 0.042 | 0.82 +- 0.04 / 0.74 +- 0.01 | 0.46 +- 0.02 | 4.7 +- 0.6 | 0.61 +- 0.13 / 0.60 +- 0.05 | 6.0 +- 0.0 / 5.7 +- 0.6 |
| M0b | B3 (b): nhu M0a, bo image/parent | 3 | 0.787 +- 0.009 | 0.989 +- 0.004 | 0.018 +- 0.000 | 0.942 +- 0.043 | 0.938 +- 0.009 | 0.931 +- 0.014 | 0.86 +- 0.02 / 0.75 +- 0.03 | 0.50 +- 0.03 | 1.7 +- 0.6 | 0.72 +- 0.03 / 0.59 +- 0.03 | 6.0 +- 0.0 / 5.3 +- 1.2 |
| M1 | + attention pooling (don nhiem) | 5 | 0.822 +- 0.007 | 0.998 +- 0.002 | 0.024 +- 0.005 | 0.622 +- 0.263 | 0.954 +- 0.008 | 0.958 +- 0.034 | 0.88 +- 0.01 / 0.78 +- 0.08 | 0.73 +- 0.08 | 0.8 +- 0.8 | 0.30 +- 0.06 / 0.43 +- 0.09 | 5.6 +- 0.9 / 4.4 +- 2.3 |
| M2 | + da nhiem | 5 | 0.831 +- 0.006 | 0.996 +- 0.001 | 0.029 +- 0.008 | 0.772 +- 0.132 | 0.954 +- 0.009 | 0.971 +- 0.025 | 0.88 +- 0.02 / 0.80 +- 0.03 | 0.69 +- 0.07 | 1.6 +- 2.1 | 0.32 +- 0.25 / 0.29 +- 0.29 | 6.0 +- 0.0 / 5.6 +- 0.9 |
| M3 | + crop U[4,n] moi lop = VT-Seq | 5 | 0.825 +- 0.018 | 0.996 +- 0.001 | 0.028 +- 0.000 | 0.877 +- 0.060 | 0.945 +- 0.004 | 0.986 +- 0.009 | 0.88 +- 0.02 / 0.81 +- 0.01 | 0.69 +- 0.04 | 1.8 +- 1.3 | 0.11 +- 0.32 / 0.14 +- 0.43 | 5.8 +- 0.4 / 5.6 +- 0.9 |
| M4 | + name dropout 0.5 | 5 | 0.820 +- 0.012 | 0.995 +- 0.002 | 0.026 +- 0.004 | 0.788 +- 0.135 | 0.947 +- 0.000 | 0.970 +- 0.030 | 0.89 +- 0.02 / 0.82 +- 0.02 | 0.69 +- 0.04 | 1.8 +- 1.9 | 0.30 +- 0.26 / 0.26 +- 0.30 | 6.0 +- 0.0 / 6.0 +- 0.0 |
| M4b | M3 + bo han image/parent | 5 | 0.820 +- 0.009 | 0.994 +- 0.003 | 0.020 +- 0.012 | 0.762 +- 0.249 | 0.943 +- 0.016 | 0.978 +- 0.018 | 0.89 +- 0.01 / 0.78 +- 0.09 | 0.69 +- 0.04 | 0.8 +- 1.8 | 0.35 +- 0.21 / 0.29 +- 0.18 | 4.8 +- 2.7 / 4.8 +- 2.7 |

M0 (B3) 3 seed, tran 60 epoch; M1-M4b 5 seed, tran 100, patience 10, 0/150 fold cham tran. OOF M0 tinh lai bang cung quy tac nguong 4.3 tu OOF Buoc 5. Bang OOF day du + epoch tung fold: `reports/step6/m2_oof.md`.

## 3. VT-Seq cuoi + VT-Seq-ens canh B0 / B1 / B2 / B3 (cot giong Buoc 5)

Dataset: v1.2. Moi chi so o nguong khoa tren Train OOF (B0: L chon tren Train); CI bootstrap 95%, 1000 lan, seed 1337.
Mo hinh nhieu seed (ghi '(n seed)'): trung binh +- do lech chuan (ddof=1) cua gia tri diem qua cac seed; nguong khoa rieng moi seed.

**(1) Bang chinh**

| Mo hinh | T-clean F1 | T-clean PR-AUC | T-novel F1 | T-novel PR-AUC | macro-F1 TTP clean / novel | T1003.003 phien T-novel: nhi phan / nhan TTP (cua 6) |
|---|---|---|---|---|---|---|
| b0_wazuh | 0.988 [0.962, 1.000] | 0.987 [0.955, 1.000] | 0.898 [0.837, 0.948] | 0.820 [0.726, 0.903] | 0.12 [0.09, 0.14] / 0.12 [0.09, 0.14] | 5 / 0 |
| b1_tfidf_b | 0.988 [0.959, 1.000] | 0.998 [0.993, 1.000] | 0.946 [0.899, 0.984] | 0.979 [0.947, 0.998] | 0.84 [0.78, 0.89] / 0.73 [0.67, 0.79] | 6 / 6 |
| b1_raw_b | 0.988 [0.959, 1.000] | 0.999 [0.997, 1.000] | 0.955 [0.913, 0.990] | 0.953 [0.894, 0.999] | 0.76 [0.69, 0.82] / 0.71 [0.63, 0.77] | 6 / 6 |
| b2_lgbm_a | 0.976 [0.937, 1.000] | 0.999 [0.995, 1.000] | 0.936 [0.882, 0.979] | 0.990 [0.975, 0.999] | 0.88 [0.82, 0.92] / 0.80 [0.75, 0.85] | 4 / 6 |
| b2_lgbm_b | 0.730 [0.594, 0.829] | 0.871 [0.778, 0.933] | 0.478 [0.348, 0.604] | 0.642 [0.526, 0.763] | 0.52 [0.42, 0.60] / 0.45 [0.31, 0.55] | 4 / 4 |
| b3_gru_a (3 seed) | 0.988 +- 0.000 | 1.000 +- 0.000 | 0.929 +- 0.001 | 0.918 +- 0.042 | 0.82 +- 0.04 / 0.74 +- 0.01 | 6.0 +- 0.0 / 5.7 +- 0.6 |
| b3_gru_b (3 seed) | 1.000 +- 0.000 | 1.000 +- 0.000 | 0.938 +- 0.009 | 0.931 +- 0.014 | 0.86 +- 0.02 / 0.75 +- 0.03 | 6.0 +- 0.0 / 5.3 +- 1.2 |
| vtseq_M3 (5 seed) | 1.000 +- 0.000 | 1.000 +- 0.000 | 0.945 +- 0.004 | 0.986 +- 0.009 | 0.88 +- 0.02 / 0.81 +- 0.01 | 5.8 +- 0.4 / 5.6 +- 0.9 |
| vtseq_M3_ens | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.964 [0.927, 0.992] | 0.986 [0.967, 0.998] | 0.87 [0.83, 0.92] / 0.82 [0.76, 0.87] | 6 / 6 |
| vtseq_M4b (5 seed) | 1.000 +- 0.000 | 1.000 +- 0.000 | 0.942 +- 0.016 | 0.978 +- 0.018 | 0.89 +- 0.01 / 0.78 +- 0.09 | 4.8 +- 2.7 / 4.8 +- 2.7 |
| vtseq_M4b_ens | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.947 [0.902, 0.984] | 0.988 [0.972, 0.998] | 0.89 [0.84, 0.93] / 0.83 [0.78, 0.88] | 6 / 6 |
| vtseq_M3cp (5 seed) | 1.000 +- 0.000 | 1.000 +- 0.000 | 0.935 +- 0.026 | 0.983 +- 0.023 | 0.86 +- 0.05 / 0.77 +- 0.10 | 4.8 +- 2.7 / 4.8 +- 2.7 |

**(2) T-hard (88 cua so, 0 duong)**

| Mo hinh | FPR tong | FP (cua n) | Co cmd.exe: FP | Khong cmd.exe: FP | Du 64: FP | Ngan: FP | Spearman(diem, n_events) cua so am T-hard |
|---|---|---|---|---|---|---|---|
| b0_wazuh | 0.193 [0.114, 0.273] | 17/88 | 14/19 | 3/69 | 6/36 | 11/52 | 0.05 [-0.13, 0.23] |
| b1_tfidf_b | 0.000 [0.000, 0.000] | 0/88 | 0/19 | 0/69 | 0/36 | 0/52 | 0.78 [0.68, 0.84] |
| b1_raw_b | 0.000 [0.000, 0.000] | 0/88 | 0/19 | 0/69 | 0/36 | 0/52 | 0.04 [-0.18, 0.28] |
| b2_lgbm_a | 0.011 [0.000, 0.034] | 1/88 | 1/19 | 0/69 | 1/36 | 0/52 | 0.02 [-0.20, 0.25] |
| b2_lgbm_b | 0.159 [0.091, 0.239] | 14/88 | 1/19 | 13/69 | 3/36 | 11/52 | -0.25 [-0.46, -0.02] |
| b3_gru_a (3 seed) | 0.053 +- 0.007 | 4.7 +- 0.6/88 | 4.7 +- 0.6/19 | 0.0 +- 0.0/69 | 4.0 +- 0.0/36 | 0.7 +- 0.6/52 | 0.61 +- 0.13 |
| b3_gru_b (3 seed) | 0.019 +- 0.007 | 1.7 +- 0.6/88 | 1.7 +- 0.6/19 | 0.0 +- 0.0/69 | 1.7 +- 0.6/36 | 0.0 +- 0.0/52 | 0.72 +- 0.03 |
| vtseq_M3 (5 seed) | 0.020 +- 0.015 | 1.8 +- 1.3/88 | 1.8 +- 1.3/19 | 0.0 +- 0.0/69 | 1.2 +- 0.8/36 | 0.6 +- 0.5/52 | 0.11 +- 0.32 |
| vtseq_M3_ens | 0.011 [0.000, 0.045] | 1/88 | 1/19 | 0/69 | 1/36 | 0/52 | 0.01 [-0.20, 0.23] |
| vtseq_M4b (5 seed) | 0.009 +- 0.020 | 0.8 +- 1.8/88 | 0.6 +- 1.3/19 | 0.2 +- 0.4/69 | 0.6 +- 1.3/36 | 0.2 +- 0.4/52 | 0.35 +- 0.21 |
| vtseq_M4b_ens | 0.000 [0.000, 0.000] | 0/88 | 0/19 | 0/69 | 0/36 | 0/52 | 0.50 [0.32, 0.66] |
| vtseq_M3cp (5 seed) | 0.020 +- 0.023 | 1.8 +- 2.0/88 | 1.8 +- 2.0/19 | 0.0 +- 0.0/69 | 1.6 +- 1.7/36 | 0.2 +- 0.4/52 | 0.17 +- 0.25 |
| vtseq_M3c (5 seed) (chi T-hard, so voi (a)) | 0.007 +- 0.006 | 0.6 +- 0.5/88 | 0.6 +- 0.5/19 | 0.0 +- 0.0/69 | 0.6 +- 0.5/36 | 0.0 +- 0.0/52 | 0.03 +- 0.21 |

**(3) T-hard - FP/n theo chu ky cong cu** (nhieu seed: FP trung binh)

| Chu ky | b0_wazuh | b1_tfidf_b | b1_raw_b | b2_lgbm_a | b2_lgbm_b | b3_gru_a (3 seed) | b3_gru_b (3 seed) | vtseq_M3 (5 seed) | vtseq_M3_ens | vtseq_M4b (5 seed) | vtseq_M4b_ens | vtseq_M3cp (5 seed) | vtseq_M3c (5 seed) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | **2/41** | 0/41 | 0/41 | 0/41 | **5/41** | 0.0/41 | 0.0/41 | 0.0/41 | 0/41 | **0.2/41** | 0/41 | 0.0/41 | 0.0/41 |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | **1/12** | 0/12 | 0/12 | 0/12 | 0/12 | 0.0/12 | 0.0/12 | 0.0/12 | 0/12 | 0.0/12 | 0/12 | 0.0/12 | 0.0/12 |
| `net.exe+net1.exe` | 0/5 | 0/5 | 0/5 | 0/5 | **3/5** | 0.0/5 | 0.0/5 | 0.0/5 | 0/5 | 0.0/5 | 0/5 | 0.0/5 | 0.0/5 |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | **3/5** | 0/5 | 0/5 | 0/5 | 0/5 | **2.7/5** | **0.3/5** | **1.2/5** | **1/5** | **0.4/5** | 0/5 | **1.2/5** | **0.6/5** |
| `ntdsutil.exe+vssadmin.exe [revert_control]` | **3/4** | 0/4 | 0/4 | 0/4 | 0/4 | 0.0/4 | 0.0/4 | 0.0/4 | 0/4 | 0.0/4 | 0/4 | 0.0/4 | 0.0/4 |
| `net.exe+nltest.exe+ping.exe` | **2/3** | 0/3 | 0/3 | 0/3 | 0/3 | 0.0/3 | 0.0/3 | 0.0/3 | 0/3 | 0.0/3 | 0/3 | 0.0/3 | 0.0/3 |
| `net.exe+net1.exe+vssadmin.exe` | 0/2 | 0/2 | 0/2 | 0/2 | **2/2** | 0.0/2 | 0.0/2 | 0.0/2 | 0/2 | 0.0/2 | 0/2 | 0.0/2 | 0.0/2 |
| `net.exe+net1.exe+nltest.exe` | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0.0/2 | 0.0/2 | 0.0/2 | 0/2 | 0.0/2 | 0/2 | 0.0/2 | 0.0/2 |
| `ipconfig.exe+netsh.exe` | **2/2** | 0/2 | 0/2 | **1/2** | 0/2 | **2.0/2** | **1.3/2** | 0.0/2 | 0/2 | 0.0/2 | 0/2 | **0.4/2** | 0.0/2 |
| `net.exe+nltest.exe` | 0/1 | 0/1 | 0/1 | 0/1 | **1/1** | 0.0/1 | 0.0/1 | 0.0/1 | 0/1 | 0.0/1 | 0/1 | 0.0/1 | 0.0/1 |
| `vssadmin.exe+wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0.0/1 | 0.0/1 | 0.0/1 | 0/1 | 0.0/1 | 0/1 | 0.0/1 | 0.0/1 |
| `wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | **1/1** | 0.0/1 | 0.0/1 | 0.0/1 | 0/1 | 0.0/1 | 0/1 | 0.0/1 | 0.0/1 |
| `arp.exe+ipconfig.exe+net.exe+netstat.exe+nltest.exe+route.exe` | 0/1 | 0/1 | 0/1 | 0/1 | **1/1** | 0.0/1 | 0.0/1 | 0.0/1 | 0/1 | 0.0/1 | 0/1 | 0.0/1 | 0.0/1 |
| `nltest.exe+wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0.0/1 | 0.0/1 | 0.0/1 | 0/1 | 0.0/1 | 0/1 | 0.0/1 | 0.0/1 |
| `nltest.exe+vssadmin.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0.0/1 | 0.0/1 | 0.0/1 | 0/1 | 0.0/1 | 0/1 | 0.0/1 | 0.0/1 |
| `arp.exe+ipconfig.exe+netstat.exe+route.exe+wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0.0/1 | 0.0/1 | 0.0/1 | 0/1 | 0.0/1 | 0/1 | 0.0/1 | 0.0/1 |
| `ntdsutil.exe+vssadmin.exe+wevtutil.exe` | **1/1** | 0/1 | 0/1 | 0/1 | **1/1** | 0.0/1 | 0.0/1 | 0.0/1 | 0/1 | 0.0/1 | 0/1 | 0.0/1 | 0.0/1 |
| `arp.exe+net.exe+nltest.exe+ntdsutil.exe+ping.exe+vssadmin.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 | 0.0/1 | 0.0/1 | 0.0/1 | 0/1 | 0.0/1 | 0/1 | 0.0/1 | 0.0/1 |
| `arp.exe+net.exe+nltest.exe+ping.exe+wevtutil.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 | 0.0/1 | 0.0/1 | 0.0/1 | 0/1 | 0.0/1 | 0/1 | 0.0/1 | 0.0/1 |
| `nbtstat.exe+netsh.exe+nslookup.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0.0/1 | 0.0/1 | 0.0/1 | 0/1 | 0.0/1 | 0/1 | 0.0/1 | 0.0/1 |
| `netsh.exe+nslookup.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 | 0.0/1 | 0.0/1 | **0.6/1** | 0/1 | **0.2/1** | 0/1 | **0.2/1** | 0.0/1 |

**(4) Phan tang do dai tren T-clean / T-novel (cua so am, nguong khoa)**

| Mo hinh | T-clean du64 | T-clean ngan | Spearman T-clean | T-novel du64 | T-novel ngan | Spearman T-novel |
|---|---|---|---|---|---|---|
| b0_wazuh | 0/23 | 1/24 | 0.03 [-0.26, 0.37] | 11/54 | 0/41 | 0.24 [0.05, 0.42] |
| b1_tfidf_b | 0/23 | 0/24 | 0.33 [0.01, 0.60] | 4/54 | 0/41 | 0.68 [0.54, 0.79] |
| b1_raw_b | 0/23 | 0/24 | -0.21 [-0.47, 0.08] | 4/54 | 0/41 | 0.16 [-0.03, 0.35] |
| b2_lgbm_a | 0/23 | 0/24 | -0.09 [-0.38, 0.20] | 4/54 | 0/41 | 0.29 [0.10, 0.47] |
| b2_lgbm_b | 0/23 | 5/24 | -0.34 [-0.59, -0.03] | 11/54 | 5/41 | 0.12 [-0.07, 0.33] |
| b3_gru_a (3 seed) | 0.0 +- 0.0/23 | 0.0 +- 0.0/24 | 0.35 +- 0.14 | 6.3 +- 0.6/54 | 0.0 +- 0.0/41 | 0.60 +- 0.05 |
| b3_gru_b (3 seed) | 0.0 +- 0.0/23 | 0.0 +- 0.0/24 | 0.29 +- 0.10 | 6.0 +- 0.0/54 | 0.0 +- 0.0/41 | 0.59 +- 0.03 |
| vtseq_M3 (5 seed) | 0.0 +- 0.0/23 | 0.0 +- 0.0/24 | 0.02 +- 0.38 | 5.6 +- 0.9/54 | 0.0 +- 0.0/41 | 0.14 +- 0.43 |
| vtseq_M3_ens | 0/23 | 0/24 | 0.03 [-0.25, 0.34] | 4/54 | 0/41 | 0.12 [-0.09, 0.34] |
| vtseq_M4b (5 seed) | 0.0 +- 0.0/23 | 0.0 +- 0.0/24 | 0.19 +- 0.17 | 5.2 +- 1.3/54 | 0.0 +- 0.0/41 | 0.29 +- 0.18 |
| vtseq_M4b_ens | 0/23 | 0/24 | 0.33 [0.02, 0.62] | 6/54 | 0/41 | 0.48 [0.28, 0.64] |
| vtseq_M3cp (5 seed) | 0.0 +- 0.0/23 | 0.0 +- 0.0/24 | -0.02 +- 0.35 | 5.6 +- 0.9/54 | 0.0 +- 0.0/41 | 0.12 +- 0.34 |

**(5) F1 theo TTP - T-clean** (nguong theo TTP khoa tren Train OOF; support = so cua so mang nhan)

| Mo hinh | T1016 (n=21) | T1018 (n=23) | T1087.002 (n=24) | T1654 (n=17) | T1003.003 (n=12) | macro-F1 |
|---|---|---|---|---|---|---|
| b0_wazuh | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.58 [0.44, 0.72] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.12 [0.09, 0.14] |
| b1_tfidf_b | 0.88 [0.75, 0.97] | 0.61 [0.38, 0.79] | 0.80 [0.65, 0.92] | 0.92 [0.80, 1.00] | 1.00 [1.00, 1.00] | 0.84 [0.78, 0.89] |
| b1_raw_b | 0.80 [0.63, 0.93] | 0.56 [0.32, 0.75] | 0.70 [0.50, 0.85] | 0.74 [0.53, 0.90] | 1.00 [1.00, 1.00] | 0.76 [0.69, 0.82] |
| b2_lgbm_a | 0.91 [0.81, 0.98] | 0.68 [0.50, 0.83] | 0.94 [0.86, 1.00] | 0.86 [0.71, 0.96] | 1.00 [1.00, 1.00] | 0.88 [0.82, 0.92] |
| b2_lgbm_b | 0.52 [0.33, 0.67] | 0.08 [0.00, 0.24] | 0.57 [0.38, 0.73] | 0.46 [0.25, 0.65] | 0.96 [0.83, 1.00] | 0.52 [0.42, 0.60] |
| b3_gru_a (3 seed) | 0.80 +- 0.05 | 0.74 +- 0.08 | 0.86 +- 0.04 | 0.73 +- 0.01 | 0.97 +- 0.05 | 0.82 +- 0.04 |
| b3_gru_b (3 seed) | 0.80 +- 0.03 | 0.84 +- 0.03 | 0.87 +- 0.02 | 0.79 +- 0.04 | 1.00 +- 0.00 | 0.86 +- 0.02 |
| vtseq_M3 (5 seed) | 0.81 +- 0.05 | 0.77 +- 0.06 | 0.89 +- 0.02 | 0.94 +- 0.01 | 1.00 +- 0.00 | 0.88 +- 0.02 |
| vtseq_M3_ens | 0.82 [0.70, 0.93] | 0.71 [0.53, 0.86] | 0.89 [0.79, 0.97] | 0.94 [0.86, 1.00] | 1.00 [1.00, 1.00] | 0.87 [0.83, 0.92] |
| vtseq_M4b (5 seed) | 0.81 +- 0.03 | 0.83 +- 0.04 | 0.87 +- 0.04 | 0.92 +- 0.04 | 1.00 +- 0.00 | 0.89 +- 0.01 |
| vtseq_M4b_ens | 0.82 [0.70, 0.93] | 0.79 [0.65, 0.90] | 0.89 [0.79, 0.97] | 0.94 [0.86, 1.00] | 1.00 [1.00, 1.00] | 0.89 [0.84, 0.93] |
| vtseq_M3cp (5 seed) | 0.83 +- 0.03 | 0.68 +- 0.20 | 0.87 +- 0.03 | 0.90 +- 0.04 | 1.00 +- 0.00 | 0.86 +- 0.05 |

**(5) F1 theo TTP - T-novel** (nguong theo TTP khoa tren Train OOF; support = so cua so mang nhan)

| Mo hinh | T1016 (n=37) | T1018 (n=36) | T1087.002 (n=33) | T1654 (n=16) | T1003.003 (n=6) | macro-F1 |
|---|---|---|---|---|---|---|
| b0_wazuh | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.59 [0.47, 0.70] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.12 [0.09, 0.14] |
| b1_tfidf_b | 0.77 [0.65, 0.86] | 0.58 [0.41, 0.72] | 0.75 [0.62, 0.86] | 0.57 [0.38, 0.75] | 1.00 [1.00, 1.00] | 0.73 [0.67, 0.79] |
| b1_raw_b | 0.77 [0.64, 0.88] | 0.52 [0.33, 0.67] | 0.75 [0.60, 0.86] | 0.50 [0.26, 0.69] | 1.00 [1.00, 1.00] | 0.71 [0.63, 0.77] |
| b2_lgbm_a | 0.83 [0.73, 0.91] | 0.83 [0.73, 0.91] | 0.76 [0.64, 0.85] | 0.59 [0.42, 0.73] | 1.00 [1.00, 1.00] | 0.80 [0.75, 0.85] |
| b2_lgbm_b | 0.45 [0.32, 0.58] | 0.20 [0.05, 0.35] | 0.47 [0.33, 0.60] | 0.33 [0.15, 0.50] | 0.80 [0.33, 1.00] | 0.45 [0.31, 0.55] |
| b3_gru_a (3 seed) | 0.80 +- 0.00 | 0.74 +- 0.01 | 0.74 +- 0.00 | 0.46 +- 0.02 | 0.97 +- 0.05 | 0.74 +- 0.01 |
| b3_gru_b (3 seed) | 0.78 +- 0.03 | 0.79 +- 0.03 | 0.74 +- 0.01 | 0.50 +- 0.03 | 0.93 +- 0.12 | 0.75 +- 0.03 |
| vtseq_M3 (5 seed) | 0.80 +- 0.02 | 0.83 +- 0.02 | 0.76 +- 0.02 | 0.69 +- 0.04 | 0.96 +- 0.09 | 0.81 +- 0.01 |
| vtseq_M3_ens | 0.81 [0.72, 0.89] | 0.83 [0.73, 0.91] | 0.76 [0.65, 0.85] | 0.68 [0.52, 0.82] | 1.00 [1.00, 1.00] | 0.82 [0.76, 0.87] |
| vtseq_M4b (5 seed) | 0.83 +- 0.02 | 0.83 +- 0.03 | 0.74 +- 0.03 | 0.69 +- 0.04 | 0.80 +- 0.45 | 0.78 +- 0.09 |
| vtseq_M4b_ens | 0.84 [0.75, 0.91] | 0.85 [0.76, 0.92] | 0.77 [0.67, 0.85] | 0.70 [0.53, 0.83] | 1.00 [1.00, 1.00] | 0.83 [0.78, 0.88] |
| vtseq_M3cp (5 seed) | 0.83 +- 0.02 | 0.77 +- 0.10 | 0.75 +- 0.02 | 0.72 +- 0.04 | 0.80 +- 0.45 | 0.77 +- 0.10 |

**(6) Phat hien som** - recall cua so duong khi chi giu k event dau tu event malicious dau tien (nguong khoa, khong chon lai)

| Mo hinh | T-clean k=4 | T-clean k=8 | T-clean k=16 | T-clean k=32 | T-clean du | T-novel k=4 | T-novel k=8 | T-novel k=16 | T-novel k=32 | T-novel du | T1003 phien T-novel k=4/8/16/32/du (cua 6) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| b0_wazuh | 0.69 [0.55, 0.83] | 0.71 [0.57, 0.86] | 0.76 [0.64, 0.88] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 0.87 [0.78, 0.94] | 0.87 [0.78, 0.94] | 0.87 [0.78, 0.94] | 0.94 [0.89, 1.00] | 0.98 [0.94, 1.00] | 0 / 0 / 0 / 3 / 5 |
| b1_tfidf_b | 0.86 [0.76, 0.95] | 0.88 [0.79, 0.98] | 0.90 [0.81, 0.98] | 0.93 [0.83, 1.00] | 0.98 [0.92, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.96 [0.91, 1.00] | 6 / 6 / 6 / 6 / 6 |
| b1_raw_b | 0.83 [0.71, 0.93] | 0.88 [0.79, 0.98] | 0.90 [0.81, 0.98] | 0.95 [0.88, 1.00] | 0.98 [0.92, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.98 [0.94, 1.00] | 6 / 6 / 6 / 6 / 6 |
| b2_lgbm_a | 0.71 [0.57, 0.86] | 0.79 [0.67, 0.90] | 0.81 [0.69, 0.93] | 0.83 [0.71, 0.93] | 0.95 [0.88, 1.00] | 0.91 [0.83, 0.98] | 0.85 [0.76, 0.94] | 1.00 [1.00, 1.00] | 0.93 [0.85, 0.98] | 0.94 [0.88, 1.00] | 1 / 0 / 6 / 2 / 4 |
| b2_lgbm_b | 0.17 [0.07, 0.29] | 0.52 [0.38, 0.69] | 0.48 [0.33, 0.64] | 0.67 [0.52, 0.81] | 0.64 [0.49, 0.79] | 0.09 [0.02, 0.19] | 0.44 [0.31, 0.57] | 0.33 [0.20, 0.46] | 0.44 [0.31, 0.57] | 0.41 [0.28, 0.54] | 0 / 0 / 0 / 5 / 4 |
| b3_gru_a (3 seed) | 0.55 +- 0.13 | 0.75 +- 0.05 | 0.84 +- 0.01 | 0.97 +- 0.01 | 0.98 +- 0.00 | 0.78 +- 0.13 | 0.88 +- 0.07 | 0.97 +- 0.03 | 0.98 +- 0.01 | 0.97 +- 0.01 | 4.0 +- 3.5 / 4.0 +- 3.5 / 6.0 +- 0.0 / 6.0 +- 0.0 / 6.0 +- 0.0 |
| b3_gru_b (3 seed) | 0.76 +- 0.12 | 0.79 +- 0.07 | 0.86 +- 0.06 | 0.95 +- 0.02 | 1.00 +- 0.00 | 0.97 +- 0.05 | 0.98 +- 0.03 | 0.99 +- 0.02 | 1.00 +- 0.00 | 0.98 +- 0.02 | 5.7 +- 0.6 / 6.0 +- 0.0 / 6.0 +- 0.0 / 6.0 +- 0.0 / 6.0 +- 0.0 |
| vtseq_M3 (5 seed) | 0.95 +- 0.04 | 0.94 +- 0.05 | 0.94 +- 0.05 | 0.99 +- 0.02 | 1.00 +- 0.00 | 0.99 +- 0.02 | 0.98 +- 0.03 | 0.97 +- 0.04 | 0.98 +- 0.03 | 0.99 +- 0.02 | 5.8 +- 0.4 / 5.8 +- 0.4 / 5.8 +- 0.4 / 5.4 +- 0.9 / 5.8 +- 0.4 |
| vtseq_M3_ens | 0.88 [0.79, 0.98] | 0.95 [0.88, 1.00] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.96 [0.91, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 6 / 6 / 6 / 6 / 6 |
| vtseq_M4b (5 seed) | 0.86 +- 0.05 | 0.92 +- 0.04 | 0.93 +- 0.03 | 0.98 +- 0.00 | 1.00 +- 0.00 | 0.98 +- 0.05 | 0.98 +- 0.05 | 0.98 +- 0.05 | 0.98 +- 0.05 | 0.98 +- 0.05 | 4.8 +- 2.7 / 4.8 +- 2.7 / 4.8 +- 2.7 / 4.8 +- 2.7 / 4.8 +- 2.7 |
| vtseq_M4b_ens | 0.88 [0.79, 0.98] | 0.93 [0.86, 1.00] | 0.93 [0.86, 1.00] | 0.98 [0.93, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 6 / 6 / 6 / 6 / 6 |
| vtseq_M3cp (5 seed) | 0.98 +- 0.04 | 0.98 +- 0.04 | 0.97 +- 0.04 | 1.00 +- 0.01 | 1.00 +- 0.00 | 0.98 +- 0.05 | 0.98 +- 0.05 | 0.98 +- 0.05 | 0.98 +- 0.05 | 0.97 +- 0.05 | 4.8 +- 2.7 / 4.8 +- 2.7 / 4.8 +- 2.7 / 4.8 +- 2.7 / 4.8 +- 2.7 |

vtseq_M3 = VT-Seq (a); vtseq_M4b = (b) bo ten cong cu; vtseq_M3c = (c) chi cay tien trinh (ro nhan theo cau truc, CHI bao T-hard); vtseq_M3cp = (c') che event nen mot-phia. (c') ~ (a): khong song nho event nen mot-phia.

## 4. Paired bootstrap so voi baseline + Holm

1000 lan, seed 1337, cung mau cua so cho hai mo hinh; p-value hai phia tu phan bo bootstrap; Holm tren ho 9 so sanh cua mo hinh trien khai (VT-Seq-ens M3 vs B1 TF-IDF (b) / B2 (a) / B3 (b) x 3 chi so; B3 lay seed co p lon nhat).

| Baseline | Chi so | Hieu [CI 95%] | p | p Holm | Ket luan (alpha 0.05 sau Holm) |
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

So sanh tham khao (M4b-ens, tung seed B3; CHUA hieu chinh so sanh boi): `reports/step6/m3_test.md`.

## 5. On dinh giua seed

| Mo hinh | Quy tac nguong | Nguong nhi phan (tung seed / TB +- DLC) | macro-F1 TTP T-novel | T1003 phien T-novel bin / TTP |
|---|---|---|---|---|
| B3 (a) | max-F1 OOF (Buoc 5) | 0.945, 0.899, 0.894 (0.913 +- 0.028) | 0.744 +- 0.007 | [6, 6, 6] / [5, 6, 6] |
| B3 (b) | max-F1 OOF (Buoc 5) | 0.743, 0.901, 0.510 (0.718 +- 0.197) | 0.750 +- 0.026 | [6, 6, 6] / [4, 6, 6] |
| VT-Seq M3 | FPR <= 1% OOF | 0.910, 0.912, 0.920, 0.864, 0.777 (0.877 +- 0.060) | 0.807 +- 0.013 | [6, 6, 5, 6, 6] / [6, 4, 6, 6, 6] |
| B3 (a) / (b) | FPR <= 1% OOF (tinh lai, chi OOF) | 0.919 +- 0.018 / 0.942 +- 0.043 | - | - |
| VT-Seq-ens (M3) | FPR <= 1% OOF trung binh | 0.869 | 0.817 | 6 / 6 |

Macro-F1 TTP T-novel: VT-Seq M3 cao hon B3 o moi seed (0.79-0.82 vs 0.73-0.78) voi do lech chuan tuong duong; T1003 theo phien van dao dong theo seed o ca hai ho; VT-Seq-ens xoa dao dong nay (6/6). Nguong: xem muc 1.4 (on dinh nho quy tac FPR <= 1%).

## 6. Han che

- **Kiem soat do dai (crop) chua vung.** M2 -> M3: Spearman trung binh T-hard +0.32 -> +0.11, T-novel +0.29 -> +0.14, nhung chu yeu nho seed 7 (-0.44 / -0.61); trung vi chi +0.40 -> +0.29 va +0.40 -> +0.33; 3/5 seed M3 van > +0.2 tren T-novel. VT-Seq-ens dat |rho| <= 0.2 mot phan do triet tieu tuong quan trai dau giua seed.
- **Seed le khong on dinh voi T1003.003** (M3 seed 42 bat 5/6 phien; seed 7 4/6 o nhan TTP; M4b va M3cp seed 99 bo sot 0/6) -> trien khai bang ens (6/6).
- **T1003.003 test nho:** 6 phien / 6 cua so T-novel (12 cua so T-clean); F1 cua so bao hoa, bao theo phien.
- **Hat giong luat (Train, attention OOF) co 4 canh bao** (`reports/step6/m4_explain.md`): (1) `\windows\temp\ntds_t0` = duong dan ART chua ma ky thuat; (2) `cmd.exe` / `cmd /c` dung dau moi TTP (ART chay qua cmd, bat doi xung da biet); (3) attention dung chung cho moi TTP (phien mixed lam lan token) va T1003.003 co 34% top-5 la event NEN (ESENT 216/103, vssvc); (4) T1087.002: `powershell.exe` (lift ~81) + EID 40961/4104 la dau vet bo sinh (`<launcher>`->powershell.exe) - luat phai dua tren lenh that (`net user /domain`, `adsisearcher`, `objectcategory`).
- **Ablation (c)** dung mat na cay tien trinh = co che gan nhan -> chi bao T-hard.
- Dataset: cac han che cua `reports/dataset_card.md` muc 9 van ap dung (coverage route/netstat/Domain Admins chi o phia am, loi trung PID 23 event).

## 7. Giai thich bang attention (dau vao Buoc 7)

Faithfulness (cua so duong duoc ens phat hien: 42 T-clean + 54 T-novel): xoa top-k theo alpha vs xoa k event ngau nhien (10 lan, cung k).

| Mo hinh | k | p_bin: giam top-k / ngau nhien / hieu [CI] | p_ttp dung TTP: hieu [CI] |
|---|---|---|---|
| ens | 1 | 0.025 / 0.001 / +0.023 [+0.011, +0.041] | +0.038 [+0.025, +0.055] |
| ens | 3 | 0.111 / 0.002 / +0.109 [+0.059, +0.166] | +0.119 [+0.075, +0.170] |
| ens | 5 | 0.230 / 0.003 / +0.227 [+0.157, +0.304] | +0.228 [+0.165, +0.298] |
| s1337 | 1 | 0.006 / 0.000 / +0.006 [+0.001, +0.014] | +0.018 [+0.012, +0.025] |
| s1337 | 3 | 0.108 / 0.001 / +0.108 [+0.050, +0.177] | +0.113 [+0.061, +0.176] |
| s1337 | 5 | 0.206 / 0.001 / +0.206 [+0.133, +0.287] | +0.219 [+0.151, +0.292] |
| s7 | 1 | 0.017 / 0.001 / +0.016 [-0.006, +0.048] KHONG dat | +0.025 [+0.004, +0.052] |
| s7 | 3 | 0.174 / 0.002 / +0.172 [+0.106, +0.246] | +0.162 [+0.106, +0.224] |
| s7 | 5 | 0.295 / 0.004 / +0.291 [+0.212, +0.376] | +0.279 [+0.211, +0.357] |
| s42 | 1 | 0.018 / 0.000 / +0.017 [+0.005, +0.039] | +0.035 [+0.018, +0.057] |
| s42 | 3 | 0.082 / 0.001 / +0.081 [+0.036, +0.132] | +0.092 [+0.051, +0.139] |
| s42 | 5 | 0.299 / 0.002 / +0.297 [+0.211, +0.386] | +0.289 [+0.212, +0.367] |
| s2024 | 1 | 0.021 / 0.001 / +0.021 [+0.004, +0.043] | +0.032 [+0.013, +0.054] |
| s2024 | 3 | 0.098 / 0.002 / +0.095 [+0.048, +0.149] | +0.119 [+0.079, +0.169] |
| s2024 | 5 | 0.212 / 0.002 / +0.210 [+0.141, +0.287] | +0.208 [+0.153, +0.270] |
| s99 | 1 | 0.042 / 0.003 / +0.039 [+0.014, +0.072] | +0.061 [+0.033, +0.096] |
| s99 | 3 | 0.144 / 0.004 / +0.140 [+0.080, +0.210] | +0.158 [+0.105, +0.219] |
| s99 | 5 | 0.395 / 0.005 / +0.390 [+0.302, +0.481] | +0.377 [+0.302, +0.455] |

Ens dat o moi k; trong 30 o cua seed le chi seed 7 k=1 p_bin co CI chua 0. Hat giong theo TTP (CHI Train, attention OOF; bang day du + canh bao: `reports/step6/m4_explain.md`, `reports/step6/rule_seeds_train.json`):

- T1016 (85 cua so; top-5 event nen 3%): `-querytype` lift 101.13; `-timeout` lift 101.13; `config` lift 75.85; `enum-logs` lift 72.24
- T1018 (78 cua so; top-5 event nen 4%): `userdnsdomain` lift 74.78; `controllers` lift 66.91; `-querytype` lift 62.97; `-timeout` lift 62.97
- T1087.002 (95 cua so; top-5 event nen 4%): `powershell.exe` lift 80.79; `powershell` lift 80.79; `-querytype` lift 61.4; `-timeout` lift 61.4
- T1654 (83 cua so; top-5 event nen 3%): `enum-logs` lift 92.47; `powershell.exe` lift 66.58; `powershell` lift 66.58; `wevtutil` lift 30.82
- T1003.003 (42 cua so; top-5 event nen 34%): `ntdsutil.exe` lift 248.52; `create` lift 182.74; `\windows\temp\ntds_t0` lift 160.81; `full` lift 160.81

## 8. ONNX

| Mo hinh | max abs diff p_bin / p_ttp / alpha (toan T-novel) | batch 1 ms/cua so TB / p95 | batch 32 ms/cua so TB / p95 | sha256 |
|---|---|---|---|---|
| vtseq_M3_s1337 (1 mang) | 1.2e-07 / 1.8e-07 / 6.6e-07 | 0.33 / 0.44 | 0.20 / 0.20 | `0023d63e9200ff12` |
| vtseq_M3_ens (5 mang) | 1.8e-07 / 1.8e-07 / 3.3e-07 | 1.44 / 1.85 | 0.99 / 1.01 | `488419e2887bc968` |

Opset 17, truc dong batch + time, dau ra p_bin / p_ttp / alpha; onnxruntime 1.31.0, CPU 1 thread tren host. File .onnx va checkpoint .pt khong vao git (.gitignore); sha256 o `reports/step6/onnx_report.json`, `checkpoints_sha256.json`.

## 9. Tieu chi chap nhan Buoc 6 (brief muc 9)

| # | Tieu chi | Ket qua | Bang chung |
|---|---|---|---|
| 1 | Checksum dataset-v1.2 khop (host + Colab); acceptance #2 (truong cam) dat cho VT-Seq | DAT | check_dataset True; check_model_sources sach; sha Colab khop; unit test 38/38 PASS trong 11.3s |
| 2 | Cau hinh, nguong, lambda, p_bin vs p_bin' chon tren Train OOF; test chay mot lan | DAT | khoa o commit 3ebc94b (final_config.json) TRUOC moi ket qua test, la to tien cua commit Colab 44f8948d: True; khong co file test nao o 3ebc94b: True; nguong M3 trung ban khoa: True; lambda = 1 co dinh (brief), khong chon. Ghi chu: lan chay Colab dau dung giua chung o M3c (loi kiem nguong), khong cham/xem du doan nao; chay lai cung cau hinh khoa. |
| 3 | >= 5 seed; trung binh +- do lech chuan; co VT-Seq-ens | DAT | so seed {'M1': 5, 'M2': 5, 'M3': 5, 'M4': 5, 'M4b': 5, 'M3c': 5, 'M3cp': 5}; ens M3/M4b [True, True] |
| 4 | Du chuoi ablation M0->M4(b) va ablation dac trung (a)(b)(c)(c') | DAT | M0 = B3 (Buoc 5), M1-M4b; (a) = M3, (b) = M4b, (c) = M3c (chi bao T-hard), (c') = M3cp |
| 5 | Paired bootstrap cho moi tuyen bo 'hon baseline' | DAT | 1000 lan, cung mau cua so; p-value hai phia + Holm cho 9 so sanh; chi tuyen bo 'hon' khi p Holm < 0.05 |
| 6 | Faithfulness attention co so lieu | DAT | ens + 5 seed, k = 1/3/5, CI bootstrap |
| 7 | ONNX parity < 1e-4; co do tre CPU | DAT | vtseq_M3_s1337: max 6.6e-07, b1 0.326 ms; vtseq_M3_ens: max 3.3e-07, b1 1.435 ms |
| 8 | reports/preds/vtseq*_<split>.jsonl (cung dinh dang Buoc 5) cho Buoc 8 | DAT | 37 mo hinh x 4 tap, thieu 0; khoa ban ghi trung Buoc 5: True |

**Tong: 8/8 dat.**
