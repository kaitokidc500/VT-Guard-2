# VT-Guard - Bao cao Buoc 7: Auto Rule Engine (luat tu sinh -> Sigma)

Sinh tu dong boi `src/rules/step7_report.py` luc 2026-10-17T16:37:25+07:00. So lieu: `reports/step7_results.json`; chi tiet: `reports/step7/` (m1_rules.md, rules_provenance.json, m2_eval.md, per_rule.json, sigma_validation.json, rules_oof.json, eval/rules.json); Sigma: `rules/sigma/*.yml`; du doan cho Buoc 8: `reports/preds/rules_*.jsonl`.

## 0. Tom tat

- **11 luat** quy nap tu dong CHI tu Train (RIPPER, dataset-v1.2), moi luat co provenance va file Sigma hop le (pySigma). Nhanh chi-luat: **T-hard 0/88 FP** (B0 17/88), T-clean F1 0.880, T-novel F1 0.878 (recall 0.796); kem AI ve recall va da nhan (macro-F1 TTP T-novel 0.42 vs VT-Seq-ens 0.82) - nhu brief du kien; gia tri: minh bach + FPR thap.
- B0 (luat Wazuh) mu hoan toan 4 TTP (T1016, T1018, T1654, T1003.003); luat tu sinh phu 3 trong so do: T1018, T1654, T1003.003. T1016 va T1087.002 khong co luat theo TTP (phien mixed) -> hai TTP nay dua vao AI.
- Luat KHONG duoc chinh sau khi cham test (luat + code quy nap khong doi tu commit duyet 6b56a7a).

## 1. Phuong phap va sai khac so voi brief

Atom = 'cua so co >= 1 event thoa ...' tren telemetry quan sat duoc (image, parent, event_id, token lenh norm_cmd, image + token cung event). Hai luot: khong rang buoc (moi atom - de do cong vi tu cam) va rang buoc (bo atom cam). Engine chon bang macro-F1 TTP OOF (CV 5 fold theo nhom): tree3 0.6584; tree4 0.6751; ripper 0.7558 -> **ripper**. Luat = literal co mat cua tung luat RIPPER (rut gon); OOF = luat duoc quy nap lai tren 4/5 Train va do tren 1/5 con lai. Cong: G0 khong literal co mat, G1 vi tu cam, G2 Sigma, G3 support >= 10 + precision OOF >= 0.9 tren >= 10 cua so OOF, G4 khu trung.

**Sai khac so voi brief (ly do):**

1. **vi tu CO MAT (cua so co >= 1 event thoa atom) thay cho nguong ti le dac trung B2 (brief 4.1/4.2)** - chi dang nay anh xa CHINH XAC sang Sigma ('co >= 1 event thoa ...'); nguong ti le > 0 cua B2 tuong duong co mat, nguong ti le khac 0 khong bieu dien duoc trong Sigma -> matcher Sigma se lech dieu kien luat.
2. **engine = RIPPER (wittgenstein), khong phai cay** - brief 4.1 yeu cau chon bang macro-F1 TTP OOF; RIPPER 0.756 > cay sau 4 0.675 > cay sau 3 0.658 (du doan cua chinh engine, literal day du, luot rang buoc). Cay van duoc chay va bao cao.
3. **them cong S5 (ten mien lab vtlab) va S4-auto (atom co < 50% lan khop tren cua so duong Train nam trong cay tien trinh)** - S5: token ten mien lab khong khai quat ra moi truong khac. S4-auto: tong quat hoa canh bao 4 (event nen mot-phia) - bat duoc svchost dsmsvc / rundll32 -embedding (tac dong phu nen cua T1003, 0% trong cay tien trinh) ma danh sach tay bo sot; event_origin chi dung cho cong nay tren Train, khong bao gio la dac trung.
4. **cong phu: precision OOF phai tinh tren >= 10 cua so OOF khop (them vao G3)** - precision OOF tren 3-9 cua so khong co y nghia thong ke (vd cmd~'system' cho T1087.002: 3 cua so, precision Train 0.72). Cong dat TRUOC khi cham test, CHI dua tren Train; nguoi dung duyet giu nguong 10 (khong ha de lay them luat).

## 2. Danh sach 11 luat va provenance tom tat

| id | Muc tieu | Vi tu | Support Train (TP/FP) | Prec OOF (TP/FP) | Fold tai lap | Phien Train khop | Luat RIPPER goc | Hat giong attention | Sigma |
|---|---|---|---|---|---|---|---|---|---|
| VTR-BIN-01 | bin | `cmd~'userdnsdomain'` | 35 (35/0) | 1.00 (24/0) | 4/5 | 26 | 1 (rang_buoc) | cmd~'userdnsdomain': T1018 74.78 | `rules/sigma/VTR-BIN-01.yml` |
| VTR-BIN-02 | bin | `cmd~'create'` | 26 (26/0) | 1.00 (18/0) | 4/5 | 23 | 1 (rang_buoc) | cmd~'create': T1003.003 182.74 | `rules/sigma/VTR-BIN-02.yml` |
| VTR-BIN-03 | bin | `cmd~'enum-logs'` | 25 (25/0) | 1.00 (25/0) | 5/5 | 20 | 1 (rang_buoc) | cmd~'enum-logs': T1016 72.24, T1087.002 42.01, T1654 92.47 | `rules/sigma/VTR-BIN-03.yml` |
| VTR-BIN-04 | bin | `cmd~'.findall'` | 19 (19/0) | 1.00 (15/0) | 4/5 | 16 | 1 (rang_buoc) | - | `rules/sigma/VTR-BIN-04.yml` |
| VTR-BIN-05 | bin | `image=net.exe & cmd~'administrator'` | 18 (18/0) | 1.00 (10/0) | 3/5 | 15 | 1 (rang_buoc) | - | `rules/sigma/VTR-BIN-05.yml` |
| VTR-BIN-06 | bin | `cmd~'controllers'` | 17 (17/0) | 1.00 (10/0) | 4/5 | 13 | 1 (rang_buoc) | cmd~'controllers': T1018 66.91 | `rules/sigma/VTR-BIN-06.yml` |
| VTR-T1018-01 | T1018 | `cmd~'controllers'` | 17 (17/0) | 1.00 (13/0) | 4/5 | 13 | 1 (rang_buoc) | cmd~'controllers': T1018 66.91 | `rules/sigma/VTR-T1018-01.yml` |
| VTR-T1018-02 | T1018 | `image=nltest.exe` AND `cmd~'userdnsdomain'` | 10 (10/0) | 1.00 (10/0) | 4/5 | 8 | 1 (rang_buoc) | cmd~'userdnsdomain': T1018 74.78 | `rules/sigma/VTR-T1018-02.yml` |
| VTR-T1654-01 | T1654 | `cmd~'system'` | 25 (25/0) | 1.00 (11/0) | 3/5 | 16 | 1 (khong_rang_buoc) | - | `rules/sigma/VTR-T1654-01.yml` |
| VTR-T1654-02 | T1654 | `cmd~'enum-logs'` | 25 (25/0) | 1.00 (25/0) | 5/5 | 20 | 1 (rang_buoc) | cmd~'enum-logs': T1016 72.24, T1087.002 42.01, T1654 92.47 | `rules/sigma/VTR-T1654-02.yml` |
| VTR-T1003003-01 | T1003.003 | `cmd~'create'` | 26 (26/0) | 1.00 (18/0) | 4/5 | 23 | 1 (rang_buoc) | cmd~'create': T1003.003 182.74 | `rules/sigma/VTR-T1003003-01.yml` |

Provenance day du (cua so / phien Train khop, luat RIPPER goc voi moi literal ke ca vang mat, engine, tham so, seed): `reports/step7/rules_provenance.json`. Moi file Sigma co custom field `vtguard_provenance` tro ve day.

## 3. Luat bi loai theo cong

| Cong | So luat | Mo ta |
|---|---|---|
| G0 | 0 | luat khong co literal duong |
| G1 | 18 | vi tu cam (scaffold S1-S5 / nen mot-phia S4-auto) |
| G2 | 0 | khong anh xa Sigma nguyen van |
| G3 | 24 | support Train >= 10, precision OOF >= 0.9 tren >= 10 cua so OOF (can tai lap tren fold) |
| G4 | 1 | khu trung (Jaccard >= 0.8, cung TTP) |

Them: 446/706 atom bi chan o tang dac trung cua luot rang buoc (S4 nen T1003 (ESENT/Directory Service): 16, S3 kenh PowerShell: 5, S2 vo cmd: 70, S3 powershell: 24, S4 nen T1003 (VSS service): 2, S1 duong dan/ma ky thuat ART: 3, S5 ten mien lab: 4, S4 nen COM (svchost->rundll32): 2, S2/S3 launcher (cmd|powershell): 1; S4-auto: 319). 18 luat cua luot khong rang buoc bi cong G1 loai, vd `image=cmd.exe` (S2), `event_id=40961` (S3), `event_id=103` ESENT (S4), `svchost & dsmsvc` (S4-auto, precision Train 1.00 cho T1003 nhung 0% trong cay tien trinh). Danh sach: `reports/step7/m1_rules.md`.

## 4. Sigma

- 11 file: 10 luat don + 1 correlation `temporal` (VTR-T1018-02: `nltest.exe` va `%USERDNSDOMAIN%` o hai event khac nhau, Train cach nhau <= 0.07 s; timespan 1m, group-by Computer). logsource `process_creation` (moi token cua luat chi khop Sysmon 1 / Security 4688 tren Train); token -> `CommandLine|re` co bien token (khong khop `System32`), image -> `Image|endswith`.
- Correlation dat `generate: false` (spec Sigma correlation): hai luat con KHONG sinh truy van / canh bao rieng (pySigma: output cua luat con = False).
- Validate: pySigma 2.0.1 (SigmaCollection + 31 validator mac dinh) -> 0 loi, 0 canh bao validator o ca 11 file.
- Matcher noi bo `src/rules/apply.py` doc YAML Sigma (khong doc provenance): == vi tu luat tren Train 0 lech o 11/11 luat (tap cua so khop trung provenance); chan doan tren 3 tap test: 0 lech. Log Wazuh giu nhay escape `\"`, regex chap nhan lam bien.

## 5. Chi-luat canh B0 / B1 TF-IDF (b) / B2 (a) / VT-Seq-ens

Nguong co dinh 0.5 dat truoc (nhi phan = co luat khop; da nhan = hop TTP cua luat theo TTP). Diem = max precision OOF cua luat khop.

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

## 6. TP / FP theo tung luat

| Luat | Muc tieu | Vi tu | Train (in-sample) TP/FP | T-clean TP/FP | T-hard FP/88 | T-novel TP/FP |
|---|---|---|---|---|---|---|
| VTR-BIN-01 | bin | `cmd~'userdnsdomain'` | 35/0 | 7/0 | 0 | 21/0 |
| VTR-BIN-02 | bin | `cmd~'create'` | 26/0 | 8/0 | 0 | 6/0 |
| VTR-BIN-03 | bin | `cmd~'enum-logs'` | 25/0 | 5/0 | 0 | 8/0 |
| VTR-BIN-04 | bin | `cmd~'.findall'` | 19/0 | 10/0 | 0 | 9/0 |
| VTR-BIN-05 | bin | `image=net.exe & cmd~'administrator'` | 18/0 | 2/0 | 0 | 6/0 |
| VTR-BIN-06 | bin | `cmd~'controllers'` | 17/0 | 3/0 | 0 | 2/0 |
| VTR-T1003003-01 | T1003.003 | `cmd~'create'` | 26/0 | 8/0 | 0 | 6/0 |
| VTR-T1018-01 | T1018 | `cmd~'controllers'` | 17/0 | 3/0 | 0 | 2/0 |
| VTR-T1018-02 | T1018 | `image=nltest.exe` AND `cmd~'userdnsdomain'` | 10/0 | 5/0 | 0 | 9/0 |
| VTR-T1654-01 | T1654 | `cmd~'system'` | 25/0 | 3/0 | 0 | 0/2 |
| VTR-T1654-02 | T1654 | `cmd~'enum-logs'` | 25/0 | 5/0 | 0 | 8/0 |

## 7. So voi B0 (luat Wazuh co san)

| TTP | B0 F1 T-clean / T-novel | Chi-luat F1 T-clean / T-novel | Luat theo TTP | B0 mu? |
|---|---|---|---|---|
| T1016 | 0.00 / 0.00 | 0.00 / 0.00 | - (dua vao AI) | CO |
| T1018 | 0.00 / 0.00 | 0.52 / 0.47 | VTR-T1018-01, VTR-T1018-02 | CO |
| T1087.002 | 0.58 / 0.59 | 0.00 / 0.00 | - (dua vao AI) | khong |
| T1654 | 0.00 / 0.00 | 0.64 / 0.62 | VTR-T1654-01, VTR-T1654-02 | CO |
| T1003.003 | 0.00 / 0.00 | 0.80 / 1.00 | VTR-T1003003-01 | CO |

B0 mu hoan toan 4 TTP (F1 = 0: T1016, T1018, T1654, T1003.003); luat tu sinh phu **T1018, T1654, T1003.003** (3/4). T1016 khong nhanh nao phu bang luat (dua vao AI). B0 tot hon o T1087.002 (F1 0.58 / 0.59), noi luat tu sinh khong co luat theo TTP. Nhi phan: chi-luat 0/88 FP tren T-hard so voi 17/88 cua B0.

## 8. Du doan OOF cho Buoc 8

- `reports/preds/rules_train.jsonl` la **IN-SAMPLE** (11 luat quy nap tu toan Train). **Buoc 8 CHI duoc dung `reports/preds/rules_oof_train.jsonl` de hoc fusion.**
- OOF: voi moi fold, chay LAI quy trinh moc 1 chi tren 4/5 Train (tu vung, danh sach chan S1-S5 + S4-auto tinh tren 4/5 Train, RIPPER 2 luot, cong G0-G2, G4) va ap len 1/5 con lai. Trong fold khong co OOF long nen G3 xap xi bang support >= 10 + precision >= 0.9 tren 4/5 Train (khong co cong >= 10 cua so OOF) -> bo luat fold de dai hon bo luat cuoi (vd co luat T1016).
- Ket qua OOF (nguong 0.5): nhi phan precision 0.9841, recall 0.7045, F1 0.8212; F1 TTP {'T1016': 0.7068, 'T1018': 0.2857, 'T1087.002': 0.2569, 'T1654': 0.7121, 'T1003.003': 0.7647} (macro 0.5452). So luat moi fold: [13, 13, 12, 13, 14]; trung voi 11 luat cuoi: [8, 8, 7, 9, 11].

## 9. Han che

- **KHONG tuyen bo tong quat hoa sang ntds2v.** VTR-T1003003-01 / VTR-BIN-02 (`cmd~'create'`) bat 6/6 cua so T-novel cua ntds2v (bien the `vssadmin create shadow`) chi nho token chung `create` - trung khop, khong phai luat duoc thiet ke cho bien the nay.
- **Token chung co rui ro FP ngoai lab:** `create` (vd `schtasks /create`, `sc create`) va `system` (VTR-T1654-01, tu bo loc `*SYSTEM*` cua get-eventlog). Trong lab 0/88 FP tren T-hard, nhung khong bao dam o moi truong khac.
- **VTR-T1654-01 (`cmd~'system'`) khop nham 2 cua so T-novel** (DINH CHINH Buoc 8: ban truoc ghi sai la ca hai deu doc hai): 1 cua so LANH TINH (`auditpol /get /subcategory:"System Integrity"`, event nen trong phien attack) - day la FP nhi phan duy nhat cua chi-luat tren T-novel (FPR 1/95) - va 1 cua so doc hai khong mang T1654. Token chung `system` (tu bo loc `*SYSTEM*` cua get-eventlog) khop ca lenh quan tri. Ghi lai, khong chinh luat.
- **Khong co luat theo TTP cho T1016 va T1087.002** (phien mixed lam token cua TTP khac xuat hien; cac luat chinh xac khong qua cong); hai TTP nay dua vao AI (VT-Seq-ens). T1087.002 chi duoc phu o muc nhi phan (VTR-BIN-04 `.findall`, VTR-BIN-05).
- **Luat quy nap tu 2 host / 1 domain** (DC01 + WIN10-01, CORP.VTLAB.TEST); coverage gap da biet (dataset card muc 9); T1003.003 test nho (6 phien T-novel).
- Chi-luat kem AI ve recall va phat hien som (T-novel k=4: 0.70 vs VT-Seq-ens 1.00) - binh thuong voi luat don gian.
- Correlation VTR-T1018-02: matcher danh gia o muc cua so (timespan khong mo phong); timespan 1m chon tu khoang cach tren Train.
- G3 trong OOF fold la xap xi (muc 8).

## 10. Tieu chi chap nhan Buoc 7 (brief muc 8)

| # | Tieu chi | Ket qua | Bang chung |
|---|---|---|---|
| 1 | Checksum dataset-v1.2 khop; luat chi quy nap tu Train; test chi de do | DAT | check_dataset True; test 1a-1c (split test chi bam sha, windows.jsonl chi parse dong Train) True; luat + code quy nap khong doi tu commit duyet 6b56a7a: True; nguong chi-luat co dinh 0.5 dat truoc test |
| 2 | Moi luat co provenance day du va KHONG chua vi tu cam (assert tu dong, 0 vi pham) | DAT | provenance day du True; vi pham danh sach cam 0; test 3e (S1-S5 + S4-auto, 0 vi pham) True; test 5 True |
| 3 | Sigma hop le cu phap; matcher noi bo == dieu kien luat/engine tren Train | DAT | pySigma 2.0.1 (SigmaCollection + 31 validator mac dinh): 11/11 file 0 loi 0 canh bao True; matcher doc YAML Sigma == vi tu luat tren Train (0 lech, support trung) True; test 4a-4c (matcher == RIPPER, ruleset doc lai == wittgenstein.predict) True |
| 4 | Bang chi-luat tren ca 3 tap test + so voi B0 + so voi AI | DAT | muc 3-5 bao cao nay (B0, B1 TF-IDF (b), B2 (a), VT-Seq-ens) |
| 5 | reports/preds/rules_<split>.jsonl san cho Buoc 8 | DAT | rules_{train,t_clean,t_hard,t_novel}.jsonl + rules_oof_train.jsonl (OOF theo fold; rules_train la in-sample) |
| 6 | Bao so luat loai theo tung cong, gom cong vi tu cam | DAT | {'G1': 18, 'G3': 24, 'G4': 1}; atom bi chan o tang dac trung 446 |

**Tong: 6/6 dat.** Unit test: 15/15 PASS trong 12.5s
