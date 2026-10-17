# VT-Guard Buoc 7 moc 2 - Sigma + bo phat hien chi-luat tren 3 tap test

Luat: 11 luat da duyet (RIPPER tren Train, `reports/step7/rules_provenance.json`), KHONG chinh theo test. Nguong co dinh 0.5 dat truoc (nhi phan = co luat khop; da nhan = hop TTP cua luat theo TTP khop). Diem p = max precision OOF cua luat khop (cho Buoc 8). Du doan Train la IN-SAMPLE.

## 1. Sigma

- 11 file `rules/sigma/<id>.yml` (10 luat don + 1 correlation `temporal` cho VTR-T1018-02 gom 2 luat con), logsource `process_creation` (Sysmon 1 / Security 4688), token -> `CommandLine|re` co bien token, image -> `Image|endswith`; custom field `vtguard_provenance` tro ve provenance.
- Validate: **pySigma 2.0.1 (SigmaCollection + 31 validator mac dinh)** -> 0 loi, 0 canh bao validator o ca 11 file.
- Matcher noi bo doc YAML Sigma (`src/rules/apply.py`) == vi tu luat tren Train: 0 lech o 11/11 luat, tap cua so khop trung provenance. (Chan doan them tren 3 tap test: 0 lech.) Ghi chu: log Wazuh giu dau nhay escape `\"`; regex token chap nhan `\"` lam bien phai (phat hien do kiem tra tren Train lech o token `controllers`).

## 2. Chi-luat canh B0 / B1 TF-IDF (b) / B2 (a) / VT-Seq-ens

Dataset: v1.2. Moi chi so o nguong khoa tren Train OOF (B0: L chon tren Train); CI bootstrap 95%, 1000 lan, seed 1337.
Mo hinh nhieu seed (ghi '(n seed)'): trung binh +- do lech chuan (ddof=1) cua gia tri diem qua cac seed; nguong khoa rieng moi seed.

**(1) Bang chinh**

| Mo hinh | T-clean F1 | T-clean PR-AUC | T-novel F1 | T-novel PR-AUC | macro-F1 TTP clean / novel | T1003.003 phien T-novel: nhi phan / nhan TTP (cua 6) |
|---|---|---|---|---|---|---|
| b0_wazuh | 0.988 [0.962, 1.000] | 0.987 [0.955, 1.000] | 0.898 [0.837, 0.948] | 0.820 [0.726, 0.903] | 0.12 [0.09, 0.14] / 0.12 [0.09, 0.14] | 5 / 0 |
| b1_tfidf_b | 0.988 [0.959, 1.000] | 0.998 [0.993, 1.000] | 0.946 [0.899, 0.984] | 0.979 [0.947, 0.998] | 0.84 [0.78, 0.89] / 0.73 [0.67, 0.79] | 6 / 6 |
| b2_lgbm_a | 0.976 [0.937, 1.000] | 0.999 [0.995, 1.000] | 0.936 [0.882, 0.979] | 0.990 [0.975, 0.999] | 0.88 [0.82, 0.92] / 0.80 [0.75, 0.85] | 4 / 6 |
| vtseq_M3_ens | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.964 [0.927, 0.992] | 0.986 [0.967, 0.998] | 0.87 [0.83, 0.92] / 0.82 [0.76, 0.87] | 6 / 6 |
| rules | 0.880 [0.789, 0.951] | 0.887 [0.809, 0.953] | 0.878 [0.796, 0.942] | 0.852 [0.763, 0.928] | 0.39 [0.32, 0.45] / 0.42 [0.35, 0.47] | 6 / 6 |

**(2) T-hard (88 cua so, 0 duong)**

| Mo hinh | FPR tong | FP (cua n) | Co cmd.exe: FP | Khong cmd.exe: FP | Du 64: FP | Ngan: FP | Spearman(diem, n_events) cua so am T-hard |
|---|---|---|---|---|---|---|---|
| b0_wazuh | 0.193 [0.114, 0.273] | 17/88 | 14/19 | 3/69 | 6/36 | 11/52 | 0.05 [-0.13, 0.23] |
| b1_tfidf_b | 0.000 [0.000, 0.000] | 0/88 | 0/19 | 0/69 | 0/36 | 0/52 | 0.78 [0.68, 0.84] |
| b2_lgbm_a | 0.011 [0.000, 0.034] | 1/88 | 1/19 | 0/69 | 1/36 | 0/52 | 0.02 [-0.20, 0.25] |
| vtseq_M3_ens | 0.011 [0.000, 0.045] | 1/88 | 1/19 | 0/69 | 1/36 | 0/52 | 0.01 [-0.20, 0.23] |
| rules | 0.000 [0.000, 0.000] | 0/88 | 0/19 | 0/69 | 0/36 | 0/52 | - |

**(3) T-hard - FP/n theo chu ky cong cu** (nhieu seed: FP trung binh)

| Chu ky | b0_wazuh | b1_tfidf_b | b2_lgbm_a | vtseq_M3_ens | rules |
|---|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | **2/41** | 0/41 | 0/41 | 0/41 | 0/41 |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | **1/12** | 0/12 | 0/12 | 0/12 | 0/12 |
| `net.exe+net1.exe` | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | **3/5** | 0/5 | 0/5 | **1/5** | 0/5 |
| `ntdsutil.exe+vssadmin.exe [revert_control]` | **3/4** | 0/4 | 0/4 | 0/4 | 0/4 |
| `net.exe+nltest.exe+ping.exe` | **2/3** | 0/3 | 0/3 | 0/3 | 0/3 |
| `net.exe+net1.exe+vssadmin.exe` | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| `net.exe+net1.exe+nltest.exe` | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| `ipconfig.exe+netsh.exe` | **2/2** | 0/2 | **1/2** | 0/2 | 0/2 |
| `net.exe+nltest.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `vssadmin.exe+wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `arp.exe+ipconfig.exe+net.exe+netstat.exe+nltest.exe+route.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `nltest.exe+wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `nltest.exe+vssadmin.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `arp.exe+ipconfig.exe+netstat.exe+route.exe+wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `ntdsutil.exe+vssadmin.exe+wevtutil.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 |
| `arp.exe+net.exe+nltest.exe+ntdsutil.exe+ping.exe+vssadmin.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 |
| `arp.exe+net.exe+nltest.exe+ping.exe+wevtutil.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 |
| `nbtstat.exe+netsh.exe+nslookup.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `netsh.exe+nslookup.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 |

**(4) Phan tang do dai tren T-clean / T-novel (cua so am, nguong khoa)**

| Mo hinh | T-clean du64 | T-clean ngan | Spearman T-clean | T-novel du64 | T-novel ngan | Spearman T-novel |
|---|---|---|---|---|---|---|
| b0_wazuh | 0/23 | 1/24 | 0.03 [-0.26, 0.37] | 11/54 | 0/41 | 0.24 [0.05, 0.42] |
| b1_tfidf_b | 0/23 | 0/24 | 0.33 [0.01, 0.60] | 4/54 | 0/41 | 0.68 [0.54, 0.79] |
| b2_lgbm_a | 0/23 | 0/24 | -0.09 [-0.38, 0.20] | 4/54 | 0/41 | 0.29 [0.10, 0.47] |
| vtseq_M3_ens | 0/23 | 0/24 | 0.03 [-0.25, 0.34] | 4/54 | 0/41 | 0.12 [-0.09, 0.34] |
| rules | 0/23 | 0/24 | - | 1/54 | 0/41 | 0.09 [0.07, 0.16] |

**(5) F1 theo TTP - T-clean** (nguong theo TTP khoa tren Train OOF; support = so cua so mang nhan)

| Mo hinh | T1016 (n=21) | T1018 (n=23) | T1087.002 (n=24) | T1654 (n=17) | T1003.003 (n=12) | macro-F1 |
|---|---|---|---|---|---|---|
| b0_wazuh | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.58 [0.44, 0.72] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.12 [0.09, 0.14] |
| b1_tfidf_b | 0.88 [0.75, 0.97] | 0.61 [0.38, 0.79] | 0.80 [0.65, 0.92] | 0.92 [0.80, 1.00] | 1.00 [1.00, 1.00] | 0.84 [0.78, 0.89] |
| b2_lgbm_a | 0.91 [0.81, 0.98] | 0.68 [0.50, 0.83] | 0.94 [0.86, 1.00] | 0.86 [0.71, 0.96] | 1.00 [1.00, 1.00] | 0.88 [0.82, 0.92] |
| vtseq_M3_ens | 0.82 [0.70, 0.93] | 0.71 [0.53, 0.86] | 0.89 [0.79, 0.97] | 0.94 [0.86, 1.00] | 1.00 [1.00, 1.00] | 0.87 [0.83, 0.92] |
| rules | 0.00 [0.00, 0.00] | 0.52 [0.29, 0.72] | 0.00 [0.00, 0.00] | 0.64 [0.38, 0.83] | 0.80 [0.57, 0.96] | 0.39 [0.32, 0.45] |

**(5) F1 theo TTP - T-novel** (nguong theo TTP khoa tren Train OOF; support = so cua so mang nhan)

| Mo hinh | T1016 (n=37) | T1018 (n=36) | T1087.002 (n=33) | T1654 (n=16) | T1003.003 (n=6) | macro-F1 |
|---|---|---|---|---|---|---|
| b0_wazuh | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.59 [0.47, 0.70] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.12 [0.09, 0.14] |
| b1_tfidf_b | 0.77 [0.65, 0.86] | 0.58 [0.41, 0.72] | 0.75 [0.62, 0.86] | 0.57 [0.38, 0.75] | 1.00 [1.00, 1.00] | 0.73 [0.67, 0.79] |
| b2_lgbm_a | 0.83 [0.73, 0.91] | 0.83 [0.73, 0.91] | 0.76 [0.64, 0.85] | 0.59 [0.42, 0.73] | 1.00 [1.00, 1.00] | 0.80 [0.75, 0.85] |
| vtseq_M3_ens | 0.81 [0.72, 0.89] | 0.83 [0.73, 0.91] | 0.76 [0.65, 0.85] | 0.68 [0.52, 0.82] | 1.00 [1.00, 1.00] | 0.82 [0.76, 0.87] |
| rules | 0.00 [0.00, 0.00] | 0.47 [0.27, 0.63] | 0.00 [0.00, 0.00] | 0.62 [0.35, 0.80] | 1.00 [1.00, 1.00] | 0.42 [0.35, 0.47] |

**(6) Phat hien som** - recall cua so duong khi chi giu k event dau tu event malicious dau tien (nguong khoa, khong chon lai)

| Mo hinh | T-clean k=4 | T-clean k=8 | T-clean k=16 | T-clean k=32 | T-clean du | T-novel k=4 | T-novel k=8 | T-novel k=16 | T-novel k=32 | T-novel du | T1003 phien T-novel k=4/8/16/32/du (cua 6) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| b0_wazuh | 0.69 [0.55, 0.83] | 0.71 [0.57, 0.86] | 0.76 [0.64, 0.88] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 0.87 [0.78, 0.94] | 0.87 [0.78, 0.94] | 0.87 [0.78, 0.94] | 0.94 [0.89, 1.00] | 0.98 [0.94, 1.00] | 0 / 0 / 0 / 3 / 5 |
| b1_tfidf_b | 0.86 [0.76, 0.95] | 0.88 [0.79, 0.98] | 0.90 [0.81, 0.98] | 0.93 [0.83, 1.00] | 0.98 [0.92, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.96 [0.91, 1.00] | 6 / 6 / 6 / 6 / 6 |
| b2_lgbm_a | 0.71 [0.57, 0.86] | 0.79 [0.67, 0.90] | 0.81 [0.69, 0.93] | 0.83 [0.71, 0.93] | 0.95 [0.88, 1.00] | 0.91 [0.83, 0.98] | 0.85 [0.76, 0.94] | 1.00 [1.00, 1.00] | 0.93 [0.85, 0.98] | 0.94 [0.88, 1.00] | 1 / 0 / 6 / 2 / 4 |
| vtseq_M3_ens | 0.88 [0.79, 0.98] | 0.95 [0.88, 1.00] | 0.95 [0.88, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.96 [0.91, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 6 / 6 / 6 / 6 / 6 |
| rules | 0.55 [0.40, 0.69] | 0.57 [0.43, 0.71] | 0.57 [0.43, 0.71] | 0.67 [0.52, 0.81] | 0.79 [0.65, 0.91] | 0.70 [0.59, 0.81] | 0.70 [0.59, 0.81] | 0.72 [0.61, 0.83] | 0.74 [0.63, 0.85] | 0.80 [0.68, 0.90] | 6 / 6 / 6 / 6 / 6 |

## 3. TP / FP theo tung luat (TP = cua so mang dung muc tieu cua luat; luat nhi phan: cua so doc hai)

| Luat | Muc tieu | Vi tu | Train TP/FP (in-sample) | T-clean TP/FP | T-hard FP/88 (chu ky) | T-novel TP/FP |
|---|---|---|---|---|---|---|
| VTR-BIN-01 | bin | `cmd~'userdnsdomain'` | 35/0 | 7/0 | 0 (-) | 21/0 |
| VTR-BIN-02 | bin | `cmd~'create'` | 26/0 | 8/0 | 0 (-) | 6/0 |
| VTR-BIN-03 | bin | `cmd~'enum-logs'` | 25/0 | 5/0 | 0 (-) | 8/0 |
| VTR-BIN-04 | bin | `cmd~'.findall'` | 19/0 | 10/0 | 0 (-) | 9/0 |
| VTR-BIN-05 | bin | `image=net.exe & cmd~'administrator'` | 18/0 | 2/0 | 0 (-) | 6/0 |
| VTR-BIN-06 | bin | `cmd~'controllers'` | 17/0 | 3/0 | 0 (-) | 2/0 |
| VTR-T1003003-01 | T1003.003 | `cmd~'create'` | 26/0 | 8/0 | 0 (-) | 6/0 |
| VTR-T1018-01 | T1018 | `cmd~'controllers'` | 17/0 | 3/0 | 0 (-) | 2/0 |
| VTR-T1018-02 | T1018 | `image=nltest.exe` AND `cmd~'userdnsdomain'` | 10/0 | 5/0 | 0 (-) | 9/0 |
| VTR-T1654-01 | T1654 | `cmd~'system'` | 25/0 | 3/0 | 0 (-) | 0/2 |
| VTR-T1654-02 | T1654 | `cmd~'enum-logs'` | 25/0 | 5/0 | 0 (-) | 8/0 |

## 4. So voi B0 (luat Wazuh co san) - F1 / recall theo TTP

| TTP | B0 F1 T-clean | Chi-luat F1 T-clean (recall) | B0 F1 T-novel | Chi-luat F1 T-novel (recall) | Luat theo TTP | B0 mu? |
|---|---|---|---|---|---|---|
| T1016 | 0.00 | 0.00 (0.00) | 0.00 | 0.00 (0.00) | - (khong co) | CO |
| T1018 | 0.00 | 0.52 (0.35) | 0.00 | 0.47 (0.31) | VTR-T1018-01, VTR-T1018-02 | CO |
| T1087.002 | 0.58 | 0.00 (0.00) | 0.59 | 0.00 (0.00) | - (khong co) | khong |
| T1654 | 0.00 | 0.64 (0.47) | 0.00 | 0.62 (0.50) | VTR-T1654-01, VTR-T1654-02 | CO |
| T1003.003 | 0.00 | 0.80 (0.67) | 0.00 | 1.00 (1.00) | VTR-T1003003-01 | CO |

**Tom tat:**
- Chi-luat: T-hard **0/88 FP** (B0 17/88); T-clean F1 0.880, T-novel F1 0.878 (recall 0.796); T1003.003 phien T-novel 6/6 nhi phan, 6/6 nhan TTP.
- B0 mu T1016 / T1018 / T1654 / T1003.003 (F1 = 0) -> luat tu sinh co luat theo TTP cho T1018, T1654, T1003.003; T1016 va T1087.002 chi phu o muc nhi phan (khong luat theo TTP qua cong - phien mixed).

**Han che (ghi lai, KHONG chinh luat):**
- VTR-T1654-01 (`cmd~'system'`) bao nham nhan TTP T1654 tren 2 cua so T-novel (cua so doc hai nhung khong mang T1654); token chung `system` (tu bo loc `*SYSTEM*` cua get-eventlog).
- VTR-T1003003-01 / VTR-BIN-02 (`cmd~'create'`) khop ca bien the vssadmin `create shadow` cua ntds2v (6 cua so T-novel) - nho token chung chung, khong phai luat duoc thiet ke cho bien the nay; ngoai lab co the khop `schtasks /create`, `sc create`.
- Luat quy nap tu 2 host / 1 domain; coverage gap da biet (dataset card muc 9); T1003.003 test nho (6 phien).
- Du doan Train cua chi-luat la in-sample: Buoc 8 khong duoc dung lam OOF.
