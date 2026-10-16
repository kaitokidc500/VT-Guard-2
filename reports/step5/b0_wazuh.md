### b0_wazuh (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.2667** (F1 OOF 0.862). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 0.977 [0.927, 1.000] | 1.000 [1.000, 1.000] | 0.988 [0.962, 1.000] | 0.021 [0.000, 0.068] | 0.987 [0.955, 1.000] | 0.994 [0.979, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.193 [0.114, 0.273], Wilson [0.124, 0.288] (17/88) | - | - |
| T-novel | 149 (54) | 0.828 [0.734, 0.910] | 0.982 [0.940, 1.000] | 0.898 [0.837, 0.948] | 0.116 [0.058, 0.186] | 0.820 [0.726, 0.903] | 0.933 [0.892, 0.968] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 0.119 [0.028, 0.229] | 0.213 [0.054, 0.372] | 0.000 [0.000, 0.000] | 0.987 [0.955, 1.000] | 0.994 [0.979, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.000 [0.000, 0.000], Wilson [0.000, 0.042] (0/88) | - | - |
| T-novel | 149 (54) | - | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.820 [0.726, 0.903] | 0.933 [0.892, 0.968] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 1/24 | 0.042 [0.000, 0.125] | 0.028 [-0.261, 0.372] |
| T-clean | 0.5 | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] |  |
| T-hard | khoa | 6/36 | 0.167 [0.056, 0.278] | 11/52 | 0.211 [0.115, 0.327] | 0.048 [-0.130, 0.228] |
| T-hard | 0.5 | 0/36 | 0.000 [0.000, 0.000] | 0/52 | 0.000 [0.000, 0.000] |  |
| T-novel | khoa | 11/54 | 0.204 [0.111, 0.315] | 0/41 | 0.000 [0.000, 0.000] | 0.244 [0.051, 0.416] |
| T-novel | 0.5 | 0/54 | 0.000 [0.000, 0.000] | 0/41 | 0.000 [0.000, 0.000] |  |

**T-hard - FPR theo chu ky cong cu (nguong da khoa)**

| Chu ky | n | FP | FPR [bootstrap] | Wilson 95% |
|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | 41 | 2 | 0.049 [0.000, 0.122] | [0.013, 0.161] |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | 12 | 1 | 0.083 [0.000, 0.250] | [0.015, 0.354] |
| `net.exe+net1.exe` | 5 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.434] |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | 5 | 3 | 0.600 [0.200, 1.000] | [0.231, 0.882] |
| `ntdsutil.exe+vssadmin.exe [revert_control]` | 4 | 3 | 0.750 [0.250, 1.000] | [0.301, 0.954] |
| `net.exe+nltest.exe+ping.exe` | 3 | 2 | 0.667 [0.000, 1.000] | [0.208, 0.939] |
| `net.exe+net1.exe+vssadmin.exe` | 2 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.658] |
| `net.exe+net1.exe+nltest.exe` | 2 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.658] |
| `ipconfig.exe+netsh.exe` | 2 | 2 | 1.000 [1.000, 1.000] | [0.342, 1.000] |
| `net.exe+nltest.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `vssadmin.exe+wevtutil.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `wevtutil.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `arp.exe+ipconfig.exe+net.exe+netstat.exe+nltest.exe+route.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `nltest.exe+wevtutil.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `nltest.exe+vssadmin.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `arp.exe+ipconfig.exe+netstat.exe+route.exe+wevtutil.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `ntdsutil.exe+vssadmin.exe+wevtutil.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| `arp.exe+net.exe+nltest.exe+ntdsutil.exe+ping.exe+vssadmin.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| `arp.exe+net.exe+nltest.exe+ping.exe+wevtutil.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| `nbtstat.exe+netsh.exe+nslookup.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `netsh.exe+nslookup.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| *khong cmd.exe trong cay tien trinh* | 69 | 3 | 0.043 [0.000, 0.101] | [0.015, 0.120] |
| *co cmd.exe trong cay tien trinh* | 19 | 14 | 0.737 [0.526, 0.895] | [0.512, 0.882] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.000 [0.000, 0.000] (n=21) | 0.000 [0.000, 0.000] (n=23) | 0.585 [0.441, 0.717] (n=24) | 0.000 [0.000, 0.000] (n=17) | 0.000 [0.000, 0.000] (n=12) | 0.117 [0.088, 0.143] |
| T-novel | 0.000 [0.000, 0.000] (n=37) | 0.000 [0.000, 0.000] (n=36) | 0.586 [0.468, 0.696] (n=33) | 0.000 [0.000, 0.000] (n=16) | 0.000 [0.000, 0.000] (n=6) | 0.117 [0.094, 0.139] |

**Phat hien som** - recall cua so duong khi chi giu k event dau tinh tu event malicious dau tien (nguong da khoa, khong chon lai); 'du' = cua so day du. T1003.003: so phien phat hien.

| Tap | k | Recall [CI] | Phat hien | T1003.003 phien |
|---|---|---|---|---|
| T-clean | 4 | 0.691 [0.548, 0.833] | 29/42 | 3/6 |
| T-clean | 8 | 0.714 [0.571, 0.857] | 30/42 | 4/6 |
| T-clean | 16 | 0.762 [0.643, 0.881] | 32/42 | 5/6 |
| T-clean | 32 | 0.952 [0.881, 1.000] | 40/42 | 6/6 |
| T-clean | du | 1.000 [1.000, 1.000] | 42/42 | 6/6 |
| T-novel | 4 | 0.870 [0.778, 0.944] | 47/54 | 0/6 |
| T-novel | 8 | 0.870 [0.778, 0.944] | 47/54 | 0/6 |
| T-novel | 16 | 0.870 [0.778, 0.944] | 47/54 | 0/6 |
| T-novel | 32 | 0.944 [0.888, 1.000] | 51/54 | 3/6 |
| T-novel | du | 0.982 [0.940, 1.000] | 53/54 | 5/6 |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 5/6 | 0.833 [0.500, 1.000] | [0.436, 0.970] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
| T-novel | 0.5 | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
| T-clean | 0.5 | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
