# VT-Guard - Bao cao Buoc 5 (baseline B0-B3 tren dataset-v1.2)

Sinh tu dong boi `src/baselines/step5_report.py` luc 2026-10-17T00:52:38+07:00. So lieu: `reports/step5_results.json`, chi tiet moi mo hinh: `reports/step5/<model>.json`, du doan: `reports/preds/<model>_<split>.jsonl` (giu cho Buoc 8 fusion).

Dataset `dataset-v1.2` dong bang (809 cua so; Train 483 / T-clean 89 / T-hard 88 / T-novel 149; 272 duong). Khung danh gia `src/eval/evaluate.py`: nguong chon tren Train OOF (CV theo nhom chong thoi gian) roi KHOA, ap nguyen cho 3 tap test; CI bootstrap 95% (1000 lan, seed 1337). T-clean = tool cung ho tro da thay; T-hard = hard-negative (hoat dong quan tri lanh tinh, 0 duong); T-novel = batch05 + ntds2v (bien the/cong cu chua thay khi train).

Ablation: **(a)** du; **(b)** bo `image_name` + `parent_image_name`; **(c)** chi event trong cay tien trinh (mat na = co che gan nhan -> ro nhan theo cau truc, CHI bao T-hard); **(c')** che event nen mot-phia da biet (ESENT/Directory Service cua ntdsutil, svchost->rundll32 COM). B3 (GRU) chay 3 seed (1337, 7, 42), bao trung binh +- do lech chuan; nguong khoa rieng moi seed.

Mo hinh: **B0** luat Wazuh (nguong muc do L chon tren Train); **B1** TF-IDF / dem tho (raw) + Logistic Regression tren token event (img/eid/dong lenh chuan hoa); **B2** LightGBM tren dac trung ti le theo cua so (khong n_events); **B3** GRU 1 lop (hidden 96, khong attention, don nhiem) tren chuoi event. B3 co hai bien the huan luyen RIENG: B3-bin (nhi phan) va B3-ttp (5 dau da nhan); bang duoi lay cot nhi phan tu B3-bin, cot TTP tu B3-ttp.

**(1) Bang chinh** - moi chi so o nguong khoa tren Train OOF; CI 95%; B3 = trung binh +- do lech chuan qua 3 seed

| Mo hinh | T-clean F1 | T-novel F1 | T-novel PR-AUC | T-hard FPR | FP/88 | cmd/khong-cmd | du64/ngan | Spearman(T-hard) | macro-F1 TTP clean / novel |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.988 [0.962, 1.000] | 0.898 [0.837, 0.948] | 0.820 [0.726, 0.903] | 0.193 [0.114, 0.273] | 17 | 14/3 | 6/11 | 0.05 [-0.13, 0.23] | 0.12 [0.09, 0.14] / 0.12 [0.09, 0.14] |
| B1 TF-IDF (a) | 0.976 [0.935, 1.000] | 0.938 [0.889, 0.975] | 0.946 [0.886, 0.988] | 0.011 [0.000, 0.034] | 1 | 1/0 | 1/0 | 0.83 [0.74, 0.88] | 0.83 [0.75, 0.90] / 0.72 [0.65, 0.78] |
| B1 TF-IDF (b) | 0.988 [0.959, 1.000] | 0.946 [0.899, 0.984] | 0.979 [0.947, 0.998] | 0.000 [0.000, 0.000] | 0 | 0/0 | 0/0 | 0.78 [0.68, 0.84] | 0.84 [0.78, 0.89] / 0.73 [0.67, 0.79] |
| B1 TF-IDF (c') | 0.976 [0.935, 1.000] | 0.938 [0.889, 0.975] | 0.950 [0.894, 0.990] | 0.011 [0.000, 0.034] | 1 | 1/0 | 1/0 | 0.83 [0.74, 0.88] | 0.83 [0.75, 0.90] / 0.72 [0.65, 0.78] |
| B1-raw (a) | 1.000 [1.000, 1.000] | 0.955 [0.911, 0.990] | 0.933 [0.856, 0.995] | 0.023 [0.000, 0.057] | 2 | 2/0 | 2/0 | 0.07 [-0.17, 0.30] | 0.78 [0.71, 0.84] / 0.69 [0.61, 0.76] |
| B1-raw (b) | 0.988 [0.959, 1.000] | 0.955 [0.913, 0.990] | 0.953 [0.894, 0.999] | 0.000 [0.000, 0.000] | 0 | 0/0 | 0/0 | 0.04 [-0.18, 0.28] | 0.76 [0.69, 0.82] / 0.71 [0.63, 0.77] |
| B1-raw (c') | 0.988 [0.960, 1.000] | 0.938 [0.889, 0.974] | 0.935 [0.859, 0.995] | 0.023 [0.000, 0.057] | 2 | 2/0 | 2/0 | 0.09 [-0.15, 0.31] | 0.78 [0.71, 0.84] / 0.71 [0.65, 0.78] |
| B2 (a) | 0.976 [0.937, 1.000] | 0.936 [0.882, 0.979] | 0.990 [0.975, 0.999] | 0.011 [0.000, 0.034] | 1 | 1/0 | 1/0 | 0.02 [-0.20, 0.25] | 0.88 [0.82, 0.92] / 0.80 [0.75, 0.85] |
| B2 (b) | 0.730 [0.594, 0.829] | 0.478 [0.348, 0.604] | 0.642 [0.526, 0.763] | 0.159 [0.091, 0.239] | 14 | 1/13 | 3/11 | -0.25 [-0.46, -0.02] | 0.52 [0.42, 0.60] / 0.45 [0.31, 0.55] |
| B2 (c') | 0.976 [0.937, 1.000] | 0.935 [0.878, 0.979] | 0.994 [0.983, 1.000] | 0.023 [0.000, 0.057] | 2 | 2/0 | 0/2 | -0.05 [-0.26, 0.18] | 0.87 [0.80, 0.91] / 0.81 [0.77, 0.86] |
| B3 (a) | 0.988 +- 0.000 | 0.929 +- 0.001 | 0.918 +- 0.042 | 0.053 +- 0.007 | 4.7 +- 0.6 | 4.7 +- 0.6/0.0 +- 0.0 | 4.0 +- 0.0/0.7 +- 0.6 | 0.61 +- 0.13 | 0.82 +- 0.04 / 0.74 +- 0.01 |
| B3 (b) | 1.000 +- 0.000 | 0.938 +- 0.009 | 0.931 +- 0.014 | 0.019 +- 0.007 | 1.7 +- 0.6 | 1.7 +- 0.6/0.0 +- 0.0 | 1.7 +- 0.6/0.0 +- 0.0 | 0.72 +- 0.03 | 0.86 +- 0.02 / 0.75 +- 0.03 |
| B3 (c') | 0.992 +- 0.007 | 0.939 +- 0.017 | 0.935 +- 0.039 | 0.076 +- 0.024 | 6.7 +- 2.1 | 6.3 +- 2.3/0.3 +- 0.6 | 5.0 +- 1.0/1.7 +- 1.2 | 0.53 +- 0.05 | 0.86 +- 0.01 / 0.76 +- 0.01 |

T-hard: 88 cua so, 0 duong. 'du64/ngan' = so FP o cua so du 64 event / cua so ngan.

**(1b) Ablation (c) - CHI bao T-hard** (mat na cay tien trinh = co che gan nhan -> ro nhan theo cau truc)

| Mo hinh | T-hard FPR | FP/88 | so voi (a) FP/88 |
|---|---|---|---|
| B1 TF-IDF (c) | 0.000 [0.000, 0.000] | 0 | 1 |
| B1-raw (c) | 0.000 [0.000, 0.000] | 0 | 2 |
| B2 (c) | 0.011 [0.000, 0.045] | 1 | 1 |
| B3 (c) | 0.004 +- 0.007 | 0.3 +- 0.6 | 4.7 +- 0.6 |


**(2) F1 theo TTP - T-clean** (nguong theo TTP khoa tren Train OOF; support = so cua so mang nhan)

| Mo hinh | T1016 (n=21) | T1018 (n=23) | T1087.002 (n=24) | T1654 (n=17) | T1003.003 (n=12) | macro-F1 |
|---|---|---|---|---|---|---|
| B0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.58 [0.44, 0.72] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.12 [0.09, 0.14] |
| B1 TF-IDF (a) | 0.83 [0.67, 0.94] | 0.63 [0.40, 0.80] | 0.91 [0.80, 0.98] | 0.80 [0.62, 0.93] | 1.00 [1.00, 1.00] | 0.83 [0.75, 0.90] |
| B1 TF-IDF (b) | 0.88 [0.75, 0.97] | 0.61 [0.38, 0.79] | 0.80 [0.65, 0.92] | 0.92 [0.80, 1.00] | 1.00 [1.00, 1.00] | 0.84 [0.78, 0.89] |
| B1 TF-IDF (c') | 0.83 [0.67, 0.94] | 0.63 [0.40, 0.80] | 0.91 [0.80, 0.98] | 0.80 [0.62, 0.93] | 1.00 [1.00, 1.00] | 0.83 [0.75, 0.90] |
| B1-raw (a) | 0.83 [0.67, 0.94] | 0.61 [0.36, 0.79] | 0.67 [0.44, 0.81] | 0.81 [0.64, 0.94] | 1.00 [1.00, 1.00] | 0.78 [0.71, 0.84] |
| B1-raw (b) | 0.80 [0.63, 0.93] | 0.56 [0.32, 0.75] | 0.70 [0.50, 0.85] | 0.74 [0.53, 0.90] | 1.00 [1.00, 1.00] | 0.76 [0.69, 0.82] |
| B1-raw (c') | 0.83 [0.67, 0.94] | 0.61 [0.36, 0.79] | 0.67 [0.44, 0.81] | 0.81 [0.64, 0.94] | 1.00 [1.00, 1.00] | 0.78 [0.71, 0.84] |
| B2 (a) | 0.91 [0.81, 0.98] | 0.68 [0.50, 0.83] | 0.94 [0.86, 1.00] | 0.86 [0.71, 0.96] | 1.00 [1.00, 1.00] | 0.88 [0.82, 0.92] |
| B2 (b) | 0.52 [0.33, 0.67] | 0.08 [0.00, 0.24] | 0.57 [0.38, 0.73] | 0.46 [0.25, 0.65] | 0.96 [0.83, 1.00] | 0.52 [0.42, 0.60] |
| B2 (c') | 0.89 [0.78, 0.97] | 0.65 [0.46, 0.81] | 0.92 [0.83, 0.98] | 0.88 [0.75, 0.98] | 1.00 [1.00, 1.00] | 0.87 [0.80, 0.91] |
| B3 (a) | 0.80 +- 0.05 | 0.74 +- 0.08 | 0.86 +- 0.04 | 0.73 +- 0.01 | 0.97 +- 0.05 | 0.82 +- 0.04 |
| B3 (b) | 0.80 +- 0.03 | 0.84 +- 0.03 | 0.87 +- 0.02 | 0.79 +- 0.04 | 1.00 +- 0.00 | 0.86 +- 0.02 |
| B3 (c') | 0.81 +- 0.03 | 0.81 +- 0.04 | 0.88 +- 0.01 | 0.78 +- 0.05 | 1.00 +- 0.00 | 0.86 +- 0.01 |

**(2) F1 theo TTP - T-novel** (nguong theo TTP khoa tren Train OOF; support = so cua so mang nhan)

| Mo hinh | T1016 (n=37) | T1018 (n=36) | T1087.002 (n=33) | T1654 (n=16) | T1003.003 (n=6) | macro-F1 |
|---|---|---|---|---|---|---|
| B0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.59 [0.47, 0.70] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.12 [0.09, 0.14] |
| B1 TF-IDF (a) | 0.79 [0.67, 0.89] | 0.61 [0.45, 0.74] | 0.72 [0.58, 0.82] | 0.48 [0.29, 0.64] | 1.00 [1.00, 1.00] | 0.72 [0.65, 0.78] |
| B1 TF-IDF (b) | 0.77 [0.65, 0.86] | 0.58 [0.41, 0.72] | 0.75 [0.62, 0.86] | 0.57 [0.38, 0.75] | 1.00 [1.00, 1.00] | 0.73 [0.67, 0.79] |
| B1 TF-IDF (c') | 0.79 [0.67, 0.89] | 0.61 [0.45, 0.74] | 0.72 [0.58, 0.82] | 0.48 [0.29, 0.64] | 1.00 [1.00, 1.00] | 0.72 [0.65, 0.78] |
| B1-raw (a) | 0.81 [0.69, 0.91] | 0.52 [0.33, 0.68] | 0.72 [0.58, 0.84] | 0.41 [0.20, 0.60] | 1.00 [1.00, 1.00] | 0.69 [0.61, 0.76] |
| B1-raw (b) | 0.77 [0.64, 0.88] | 0.52 [0.33, 0.67] | 0.75 [0.60, 0.86] | 0.50 [0.26, 0.69] | 1.00 [1.00, 1.00] | 0.71 [0.63, 0.77] |
| B1-raw (c') | 0.83 [0.72, 0.92] | 0.62 [0.45, 0.76] | 0.72 [0.58, 0.84] | 0.40 [0.19, 0.59] | 1.00 [1.00, 1.00] | 0.71 [0.65, 0.78] |
| B2 (a) | 0.83 [0.73, 0.91] | 0.83 [0.73, 0.91] | 0.76 [0.64, 0.85] | 0.59 [0.42, 0.73] | 1.00 [1.00, 1.00] | 0.80 [0.75, 0.85] |
| B2 (b) | 0.45 [0.32, 0.58] | 0.20 [0.05, 0.35] | 0.47 [0.33, 0.60] | 0.33 [0.15, 0.50] | 0.80 [0.33, 1.00] | 0.45 [0.31, 0.55] |
| B2 (c') | 0.88 [0.79, 0.95] | 0.79 [0.68, 0.88] | 0.79 [0.69, 0.87] | 0.61 [0.44, 0.76] | 1.00 [1.00, 1.00] | 0.81 [0.77, 0.86] |
| B3 (a) | 0.80 +- 0.00 | 0.74 +- 0.01 | 0.74 +- 0.00 | 0.46 +- 0.02 | 0.97 +- 0.05 | 0.74 +- 0.01 |
| B3 (b) | 0.78 +- 0.03 | 0.79 +- 0.03 | 0.74 +- 0.01 | 0.50 +- 0.03 | 0.93 +- 0.12 | 0.75 +- 0.03 |
| B3 (c') | 0.78 +- 0.04 | 0.76 +- 0.03 | 0.74 +- 0.01 | 0.51 +- 0.04 | 1.00 +- 0.00 | 0.76 +- 0.01 |


**(3) Phat hien som** - recall cua so duong khi chi giu k event dau tu event malicious dau tien (nguong khoa, khong chon lai)

| Mo hinh | T-clean k=4 | T-clean k=8 | T-clean k=16 | T-clean k=32 | T-clean du | T-novel k=4 | T-novel k=8 | T-novel k=16 | T-novel k=32 | T-novel du | T1003 phien T-novel k=4/8/16/32/du (cua 6) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.69 [0.55, 0.83] | 0.71 [0.57, 0.86] | 0.76 [0.64, 0.88] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 0.87 [0.78, 0.94] | 0.87 [0.78, 0.94] | 0.87 [0.78, 0.94] | 0.94 [0.89, 1.00] | 0.98 [0.94, 1.00] | 0 / 0 / 0 / 3 / 5 |
| B1 TF-IDF (a) | 0.88 [0.79, 0.98] | 0.93 [0.86, 1.00] | 0.93 [0.86, 1.00] | 0.95 [0.88, 1.00] | 0.98 [0.92, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.98 [0.94, 1.00] | 6 / 6 / 6 / 6 / 6 |
| B1 TF-IDF (b) | 0.86 [0.76, 0.95] | 0.88 [0.79, 0.98] | 0.90 [0.81, 0.98] | 0.93 [0.83, 1.00] | 0.98 [0.92, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.96 [0.91, 1.00] | 6 / 6 / 6 / 6 / 6 |
| B1 TF-IDF (c') | 1.00 [1.00, 1.00] | 0.95 [0.88, 1.00] | 0.95 [0.88, 1.00] | 0.95 [0.88, 1.00] | 0.98 [0.92, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.98 [0.94, 1.00] | 6 / 6 / 6 / 6 / 6 |
| B1-raw (a) | 0.71 [0.60, 0.86] | 0.86 [0.76, 0.95] | 0.90 [0.81, 0.98] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.98 [0.94, 1.00] | 6 / 6 / 6 / 6 / 6 |
| B1-raw (b) | 0.83 [0.71, 0.93] | 0.88 [0.79, 0.98] | 0.90 [0.81, 0.98] | 0.95 [0.88, 1.00] | 0.98 [0.92, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.98 [0.94, 1.00] | 6 / 6 / 6 / 6 / 6 |
| B1-raw (c') | 0.93 [0.83, 1.00] | 0.90 [0.81, 0.98] | 0.90 [0.81, 0.98] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.98 [0.94, 1.00] | 6 / 6 / 6 / 6 / 6 |
| B2 (a) | 0.71 [0.57, 0.86] | 0.79 [0.67, 0.90] | 0.81 [0.69, 0.93] | 0.83 [0.71, 0.93] | 0.95 [0.88, 1.00] | 0.91 [0.83, 0.98] | 0.85 [0.76, 0.94] | 1.00 [1.00, 1.00] | 0.93 [0.85, 0.98] | 0.94 [0.88, 1.00] | 1 / 0 / 6 / 2 / 4 |
| B2 (b) | 0.17 [0.07, 0.29] | 0.52 [0.38, 0.69] | 0.48 [0.33, 0.64] | 0.67 [0.52, 0.81] | 0.64 [0.49, 0.79] | 0.09 [0.02, 0.19] | 0.44 [0.31, 0.57] | 0.33 [0.20, 0.46] | 0.44 [0.31, 0.57] | 0.41 [0.28, 0.54] | 0 / 0 / 0 / 5 / 4 |
| B2 (c') | 0.71 [0.57, 0.86] | 0.79 [0.67, 0.90] | 0.81 [0.69, 0.93] | 0.83 [0.71, 0.93] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 0.98 [0.94, 1.00] | 1.00 [1.00, 1.00] | 0.96 [0.91, 1.00] | 0.93 [0.85, 0.98] | 6 / 5 / 6 / 4 / 3 |
| B3 (a) | 0.55 +- 0.13 | 0.75 +- 0.05 | 0.84 +- 0.01 | 0.97 +- 0.01 | 0.98 +- 0.00 | 0.78 +- 0.13 | 0.88 +- 0.07 | 0.97 +- 0.03 | 0.98 +- 0.01 | 0.97 +- 0.01 | 4.0 +- 3.5 / 4.0 +- 3.5 / 6.0 +- 0.0 / 6.0 +- 0.0 / 6.0 +- 0.0 |
| B3 (b) | 0.76 +- 0.12 | 0.79 +- 0.07 | 0.86 +- 0.06 | 0.95 +- 0.02 | 1.00 +- 0.00 | 0.97 +- 0.05 | 0.98 +- 0.03 | 0.99 +- 0.02 | 1.00 +- 0.00 | 0.98 +- 0.02 | 5.7 +- 0.6 / 6.0 +- 0.0 / 6.0 +- 0.0 / 6.0 +- 0.0 / 6.0 +- 0.0 |
| B3 (c') | 0.87 +- 0.05 | 0.86 +- 0.07 | 0.91 +- 0.01 | 0.98 +- 0.01 | 0.98 +- 0.01 | 0.93 +- 0.06 | 0.86 +- 0.09 | 0.92 +- 0.07 | 0.99 +- 0.01 | 0.99 +- 0.01 | 2.3 +- 3.2 / 1.7 +- 2.9 / 2.3 +- 3.2 / 6.0 +- 0.0 / 6.0 +- 0.0 |

## Phat hien chinh

1. **Hoc may cat manh bao dong gia tren T-hard.** B0 (luat Wazuh) bao nham 17/88 cua so hard-negative (chu yeu khi co `cmd.exe` trong cay tien trinh: 14/19); moi mo hinh hoc may ha xuong 0-5/88. B1 (TF-IDF/raw) o (b) dat 0/88; B2 (a) va B3 (b) deu <= 2/88.
2. **B2 phu thuoc ten cong cu, B1 va B3 thi khong.** Bo `image_name`/`parent_image_name` (ablation b), B2 sup: T-novel F1 0.94 -> 0.48, FPR T-hard tang len 14/88 (13 trong so o phien khong cmd.exe). Nguoc lai B3 giu macro-F1 T-novel 0.74 -> 0.75 va B1 giu ~0.95, nho token dong lenh + chuoi event.
3. **O B1 va B3, (b) bang hoac tot hon (a).** Bo `image_name` khong lam giam (tham chi tang nhe T-clean F1 va giam FPR T-hard): ten anh dua mo hinh vao duong tat `ping/wevtutil/ntdsutil` thay vi hanh vi, lam giam kha nang tong quat hoa sang T-novel. Day la bang chung chinh ung ho cau hinh (b) cho Buoc 6.
4. **(c') ~ (a) o moi mo hinh.** Che event nen mot-phia da biet (ESENT/DS, COM nen) gan nhu khong doi ket qua -> khong mo hinh nao song nho tac dong phu nen cua T1003.003; tin hieu den tu hanh vi trong cay tien trinh.
5. **T1654 (Log Enumeration) la TTP kho nhat**, nhat la tren T-novel (F1 ~0.46-0.61 o moi mo hinh). **T1003.003** chi co 6 phien tren T-novel nen F1 muc cua so bao hoa 1.0 khong co y nghia thong ke; bao theo PHIEN: B1 va B3 bat 6/6 o muc nhi phan, B2 (a) 4/6.
6. **Phat hien som**: B1 nhanh va on dinh nhat (recall >= 0.86 tu k=4 tren T-clean, 1.00 tren T-novel, 6/6 phien T1003 o moi k). B3 can k>=16 de bat du 6/6 phien T1003 va dao dong theo seed o k nho. B0 phai toi k=32 moi bat phien T1003 dau tien.

## Han che

- **Confounder do dai cua so.** Spearman diem~n_events tren cua so am duong ro o B1 TF-IDF (T-novel ~0.73) va B3 (T-hard ~0.61): cua so dai bi cham diem cao hon. Tap am T-hard phan lon ngan nen chua gay FP, nhung la rui ro khi trien khai; B1-raw va B2 (a) trung lap hon (Spearman ~0). Buoc 6 phai kiem soat (xem duoi).
- **Nguong B3 khong on dinh giua seed.** Nguong nhi phan khoa dao dong 0.51-0.95 giua 3 seed, keo theo phat hien som T1003 o k nho lech manh (vd (a): seed 1337/42 bat 6/6 tu k=4, seed 7 bat 0 toi k=16). Can bao trung binh +- do lech chuan, khong dua vao 1 seed.
- **Tran epoch.** B3 gioi han 60 epoch/fold; 3/120 fold CV cham tran (a_s7, a_s42 o dau TTP; c_s1337 o dau nhi phan). Mo hinh CUOI cua moi luot fit lai voi so epoch = trung vi cac fold (18-49, deu duoi tran), nen anh huong nho; Buoc 6 nang tran 100, patience 10.
- **T1003.003 test nho (6 phien T-novel, 12 cua so T-clean)**: moi chi so T1003 bao kem khoang tin cay / theo phien.
- **Coverage gap (gioi han sinh du lieu, khong phai mo hinh).** `route.exe`/`netstat.exe` chi o phia am; mot so hoat dong Domain Admins chi o phia duong. Da do bang ablation va bao trong dataset card muc 5b/7a.
- **Loi trung PID khi loai orchestrator** (labeler): 7 tien trinh / 23 event (gom ntdsutil malicious) co the bi loai/giu sai do PID bi tai su dung sau khoi phuc snapshot. Ghi trong dataset card muc 9.
- **Ro ri da phat hien va xu ly:** dau vet bo sinh (duong dan cmd, `conhost.exe`, launcher cha, duoi `.exe`) trung hoa o v1.1; bat doi xung 4688/EID1 sua o v1.2; cau hinh orchestrator `variant`/`tempo`/`user_role` (variant != mixed chi o attack -> ro nhan) cam lam feature o Buoc 5, quet tinh moi mo hinh (acceptance #2).

## He qua cho Buoc 6 (VT-Seq: GRU-Attention da nhiem)

- **Muc tieu chi so**: nang T1654 va macro-F1 TTP tren T-novel > 0.80 (tran hien tai B2/B3 ~0.74-0.81); giu FPR T-hard <= muc B1 (0/88) va PR-AUC T-novel cao.
- **Chon nguong theo FPR muc tieu** (vd FPR T-hard <= 1%) thay vi chi max-F1, kem PR-AUC; bao trung binh nhieu seed.
- **Kiem soat confounder do dai**: ep Spearman diem~do dai ~ 0 (random length crop manh hon, phat trong luong theo do dai, hoac chuan hoa); danh gia lai bang bang phan tang do dai.
- **Can nhac lay cau hinh (b) lam chinh** (bo `image_name`): (b) tong quat hoa tot hon va giam phu thuoc ten cong cu.
- **Attention** them o Buoc 6 phuc vu giai thich (trong so event) va sinh luat Sigma o Buoc 7, khong chi de tang diem.
- **Huan luyen**: tran epoch 100, patience 10, nhieu seed (>=3), bao trung binh +- do lech chuan; giu reports/preds/ de Buoc 8 fusion dung lai.
