Dataset: v1.1. Moi chi so o nguong khoa tren Train OOF (B0: L chon tren Train); CI bootstrap 95%, 1000 lan, seed 1337.

**(1) Bang chinh**

| Mo hinh | T-clean F1 | T-clean PR-AUC | T-novel F1 | T-novel PR-AUC | macro-F1 TTP clean / novel | T1003.003 phien T-novel: nhi phan / nhan TTP |
|---|---|---|---|---|---|---|
| b0_wazuh | 0.988 [0.960, 1.000] | 0.986 [0.952, 1.000] | 0.897 [0.835, 0.952] | 0.818 [0.724, 0.909] | 0.12 [0.09, 0.14] / 0.11 [0.09, 0.14] | 5/6 / 0/6 |
| b1_tfidf_a | 0.976 [0.935, 1.000] | 0.999 [0.997, 1.000] | 0.929 [0.875, 0.973] | 0.926 [0.849, 0.985] | 0.82 [0.74, 0.88] / 0.72 [0.65, 0.78] | 6/6 / 6/6 |
| b1_tfidf_b | 0.988 [0.957, 1.000] | 0.997 [0.990, 1.000] | 0.917 [0.855, 0.966] | 0.903 [0.817, 0.972] | 0.85 [0.79, 0.90] / 0.74 [0.68, 0.79] | 6/6 / 6/6 |
| b1_tfidf_c | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.78 [0.71, 0.85] / 0.78 [0.72, 0.83] | 6/6 / 6/6 |
| b1_raw_a | 0.988 [0.957, 1.000] | 1.000 [1.000, 1.000] | 0.930 [0.881, 0.970] | 0.894 [0.790, 0.979] | 0.82 [0.75, 0.88] / 0.69 [0.59, 0.76] | 6/6 / 5/6 |
| b1_raw_b | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.946 [0.898, 0.983] | 0.858 [0.751, 0.956] | 0.83 [0.77, 0.89] / 0.66 [0.57, 0.73] | 6/6 / 5/6 |
| b1_raw_c | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.82 [0.75, 0.87] / 0.75 [0.71, 0.79] | 6/6 / 6/6 |

**(2) T-hard (87 cua so, 0 duong)**

| Mo hinh | FPR tong (FP/87) | Co cmd.exe: FP/n | Khong cmd.exe: FP/n | Du 64: FP/n | Ngan: FP/n | Spearman(diem, n_events) cua so am T-hard |
|---|---|---|---|---|---|---|
| b0_wazuh | 0.195 [0.126, 0.276] (17) | 14/18 | 3/69 | 6/34 | 11/53 | 0.46 [0.22, 0.64] |
| b1_tfidf_a | 0.023 [0.000, 0.058] (2) | 2/18 | 0/69 | 2/34 | 0/53 | 0.81 [0.70, 0.88] |
| b1_tfidf_b | 0.000 [0.000, 0.000] (0) | 0/18 | 0/69 | 0/34 | 0/53 | 0.79 [0.68, 0.86] |
| b1_tfidf_c | 0.000 [0.000, 0.000] (0) | 0/18 | 0/69 | 0/34 | 0/53 | 0.44 [0.23, 0.61] |
| b1_raw_a | 0.023 [0.000, 0.058] (2) | 2/18 | 0/69 | 2/34 | 0/53 | 0.05 [-0.16, 0.27] |
| b1_raw_b | 0.000 [0.000, 0.000] (0) | 0/18 | 0/69 | 0/34 | 0/53 | 0.07 [-0.16, 0.28] |
| b1_raw_c | 0.011 [0.000, 0.035] (1) | 1/18 | 0/69 | 1/34 | 0/53 | 0.55 [0.37, 0.69] |

**(3) T-hard - FP/n theo chu ky cong cu**

| Chu ky | b0_wazuh | b1_tfidf_a | b1_tfidf_b | b1_tfidf_c | b1_raw_a | b1_raw_b | b1_raw_c |
|---|---|---|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | **2/41** | 0/41 | 0/41 | 0/41 | 0/41 | 0/41 | 0/41 |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | **1/12** | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 | 0/12 |
| `net.exe+net1.exe` | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | **3/4** | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | **1/4** |
| `ntdsutil.exe+vssadmin.exe [revert_control]` | **3/4** | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| `net.exe+nltest.exe+ping.exe` | **2/3** | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| `net.exe+net1.exe+vssadmin.exe` | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| `net.exe+net1.exe+nltest.exe` | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| `ipconfig.exe+netsh.exe` | **2/2** | **2/2** | 0/2 | 0/2 | **2/2** | 0/2 | 0/2 |
| `net.exe+nltest.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `vssadmin.exe+wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `arp.exe+ipconfig.exe+net.exe+netstat.exe+nltest.exe+route.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `nltest.exe+wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `nltest.exe+vssadmin.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `arp.exe+ipconfig.exe+netstat.exe+route.exe+wevtutil.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `ntdsutil.exe+vssadmin.exe+wevtutil.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `arp.exe+net.exe+nltest.exe+ntdsutil.exe+ping.exe+vssadmin.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `arp.exe+net.exe+nltest.exe+ping.exe+wevtutil.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `nbtstat.exe+netsh.exe+nslookup.exe` | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| `netsh.exe+nslookup.exe` | **1/1** | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |

**(4) Phan tang do dai tren T-clean / T-novel (cua so am, nguong khoa)**

| Mo hinh | T-clean du64 | T-clean ngan | Spearman T-clean | T-novel du64 | T-novel ngan | Spearman T-novel |
|---|---|---|---|---|---|---|
| b0_wazuh | 0/21 | 1/25 | 0.53 [0.17, 0.75] | 11/53 | 0/42 | 0.56 [0.40, 0.70] |
| b1_tfidf_a | 0/21 | 1/25 | 0.40 [0.07, 0.65] | 7/53 | 0/42 | 0.72 [0.58, 0.83] |
| b1_tfidf_b | 0/21 | 0/25 | 0.31 [-0.05, 0.58] | 6/53 | 0/42 | 0.72 [0.58, 0.82] |
| b1_tfidf_c | 0/21 | 0/25 | 0.43 [0.17, 0.65] | 0/53 | 0/42 | 0.70 [0.55, 0.83] |
| b1_raw_a | 0/21 | 1/25 | -0.43 [-0.64, -0.18] | 8/53 | 0/42 | 0.12 [-0.06, 0.31] |
| b1_raw_b | 0/21 | 0/25 | -0.02 [-0.31, 0.28] | 6/53 | 0/42 | 0.37 [0.17, 0.55] |
| b1_raw_c | 0/21 | 0/25 | 0.49 [0.22, 0.70] | 0/53 | 0/42 | 0.68 [0.52, 0.81] |

**Top trong so - b1_tfidf_a** (du; C=100.0)

| # | Duong (huong attack) | w | Am (huong benign) | w |
|---|---|---|---|---|
| 1 | `eid=5 img=ping.exe` | 10.014 | `c:/c c:ping` | -7.667 |
| 2 | `c:enum-logs` | 9.639 | `c:domain c:admins` | -4.991 |
| 3 | `c:wevtutil c:enum-logs` | 9.639 | `c:group c:domain` | -4.991 |
| 4 | `img=ping.exe` | 9.156 | `c:admins` | -4.991 |
| 5 | `c:enum-logs img=wevtutil.exe` | 8.616 | `c:admins c:/domain` | -4.991 |
| 6 | `c:group c:/domain` | 7.949 | `img=netstat.exe` | -4.826 |
| 7 | `img=none` | 7.486 | `img=route.exe` | -4.353 |
| 8 | `c:wevtutil` | 7.037 | `eid=5 img=cmd.exe` | -3.511 |
| 9 | `img=powershell.exe` | 6.221 | `eid=4634 img=none` | -3.269 |
| 10 | `img=none eid=4104` | 5.998 | `c:corp.vtlab.test` | -3.171 |

**Top trong so - b1_tfidf_b** (bo image_name + parent_image_name; C=100.0)

| # | Duong (huong attack) | w | Am (huong benign) | w |
|---|---|---|---|---|
| 1 | `eid=5 eid=4688` | 9.558 | `eid=5 eid=1` | -12.914 |
| 2 | `c:enum-logs` | 9.534 | `c:/c c:ping` | -7.539 |
| 3 | `c:wevtutil c:enum-logs` | 9.534 | `c:0.0.0.0 eid=4688` | -7.539 |
| 4 | `eid=4104` | 9.361 | `c:admins` | -4.693 |
| 5 | `eid=4624 eid=4624` | 7.799 | `c:admins c:/domain` | -4.693 |
| 6 | `c:wevtutil` | 7.353 | `c:group c:domain` | -4.693 |
| 7 | `c:group c:/domain` | 7.176 | `c:domain c:admins` | -4.693 |
| 8 | `c:/dclist` | 6.488 | `c:view` | -3.174 |
| 9 | `c:nltest c:/dclist` | 6.488 | `c:\dc0` | -3.174 |
| 10 | `eid=216` | 5.43 | `c:view c:\dc0` | -3.174 |

**Top trong so - b1_raw_a** (du; C=1.0)

| # | Duong (huong attack) | w | Am (huong benign) | w |
|---|---|---|---|---|
| 1 | `c:wevtutil c:enum-logs` | 0.613 | `eid=1` | -0.374 |
| 2 | `c:enum-logs` | 0.613 | `c:admins` | -0.327 |
| 3 | `c:enum-logs img=wevtutil.exe` | 0.535 | `c:admins c:/domain` | -0.327 |
| 4 | `eid=4688` | 0.441 | `c:domain c:admins` | -0.327 |
| 5 | `c:wevtutil` | 0.435 | `c:group c:domain` | -0.327 |
| 6 | `img=cmd.exe` | 0.393 | `img=netstat.exe` | -0.313 |
| 7 | `c:arp c:-a` | 0.388 | `c:/domain img=net1.exe` | -0.3 |
| 8 | `c:arp` | 0.388 | `img=route.exe` | -0.279 |
| 9 | `c:-a` | 0.388 | `eid=5 img=cmd.exe` | -0.262 |
| 10 | `c:group c:/domain` | 0.375 | `eid=4672` | -0.239 |
