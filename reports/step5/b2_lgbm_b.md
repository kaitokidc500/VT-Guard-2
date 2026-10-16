### b2_lgbm_b (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.5937** (F1 OOF 0.718). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 0.844 [0.706, 0.966] | 0.643 [0.486, 0.786] | 0.730 [0.594, 0.829] | 0.106 [0.024, 0.197] | 0.871 [0.778, 0.933] | 0.846 [0.748, 0.919] |
| T-hard | 88 (0) | - | - | - | 0.159 [0.091, 0.239], Wilson [0.097, 0.249] (14/88) | - | - |
| T-novel | 149 (54) | 0.579 [0.419, 0.739] | 0.407 [0.279, 0.542] | 0.478 [0.348, 0.604] | 0.168 [0.092, 0.248] | 0.642 [0.526, 0.763] | 0.745 [0.656, 0.822] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 0.794 [0.645, 0.923] | 0.643 [0.486, 0.786] | 0.711 [0.575, 0.815] | 0.149 [0.053, 0.250] | 0.871 [0.778, 0.933] | 0.846 [0.748, 0.919] |
| T-hard | 88 (0) | - | - | - | 0.193 [0.114, 0.273], Wilson [0.124, 0.288] (17/88) | - | - |
| T-novel | 149 (54) | 0.595 [0.450, 0.742] | 0.463 [0.327, 0.600] | 0.521 [0.395, 0.636] | 0.179 [0.105, 0.264] | 0.642 [0.526, 0.763] | 0.745 [0.656, 0.822] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 5/24 | 0.208 [0.042, 0.417] | -0.337 [-0.593, -0.035] |
| T-clean | 0.5 | 2/23 | 0.087 [0.000, 0.217] | 5/24 | 0.208 [0.042, 0.417] |  |
| T-hard | khoa | 3/36 | 0.083 [0.000, 0.194] | 11/52 | 0.211 [0.115, 0.327] | -0.251 [-0.457, -0.023] |
| T-hard | 0.5 | 4/36 | 0.111 [0.028, 0.222] | 13/52 | 0.250 [0.135, 0.365] |  |
| T-novel | khoa | 11/54 | 0.204 [0.111, 0.333] | 5/41 | 0.122 [0.049, 0.220] | 0.120 [-0.070, 0.329] |
| T-novel | 0.5 | 11/54 | 0.204 [0.111, 0.333] | 6/41 | 0.146 [0.049, 0.268] |  |

**T-hard - FPR theo chu ky cong cu (nguong da khoa)**

| Chu ky | n | FP | FPR [bootstrap] | Wilson 95% |
|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | 41 | 5 | 0.122 [0.024, 0.244] | [0.053, 0.255] |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | 12 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.242] |
| `net.exe+net1.exe` | 5 | 3 | 0.600 [0.200, 1.000] | [0.231, 0.882] |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | 5 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.434] |
| `ntdsutil.exe+vssadmin.exe [revert_control]` | 4 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.490] |
| `net.exe+nltest.exe+ping.exe` | 3 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.561] |
| `net.exe+net1.exe+vssadmin.exe` | 2 | 2 | 1.000 [1.000, 1.000] | [0.342, 1.000] |
| `net.exe+net1.exe+nltest.exe` | 2 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.658] |
| `ipconfig.exe+netsh.exe` | 2 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.658] |
| `net.exe+nltest.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| `vssadmin.exe+wevtutil.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `wevtutil.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| `arp.exe+ipconfig.exe+net.exe+netstat.exe+nltest.exe+route.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| `nltest.exe+wevtutil.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `nltest.exe+vssadmin.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `arp.exe+ipconfig.exe+netstat.exe+route.exe+wevtutil.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `ntdsutil.exe+vssadmin.exe+wevtutil.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| `arp.exe+net.exe+nltest.exe+ntdsutil.exe+ping.exe+vssadmin.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `arp.exe+net.exe+nltest.exe+ping.exe+wevtutil.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `nbtstat.exe+netsh.exe+nslookup.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `netsh.exe+nslookup.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| *khong cmd.exe trong cay tien trinh* | 69 | 13 | 0.188 [0.101, 0.290] | [0.114, 0.296] |
| *co cmd.exe trong cay tien trinh* | 19 | 1 | 0.053 [0.000, 0.158] | [0.009, 0.246] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.520 [0.333, 0.667] (n=21) | 0.080 [0.000, 0.243] (n=23) | 0.571 [0.381, 0.727] (n=24) | 0.457 [0.250, 0.649] (n=17) | 0.957 [0.828, 1.000] (n=12) | 0.517 [0.418, 0.596] |
| T-novel | 0.449 [0.318, 0.577] (n=37) | 0.204 [0.051, 0.351] (n=36) | 0.469 [0.328, 0.600] (n=33) | 0.333 [0.154, 0.500] (n=16) | 0.800 [0.330, 1.000] (n=6) | 0.451 [0.313, 0.546] |

**Phat hien som** - recall cua so duong khi chi giu k event dau tinh tu event malicious dau tien (nguong da khoa, khong chon lai); 'du' = cua so day du. T1003.003: so phien phat hien.

| Tap | k | Recall [CI] | Phat hien | T1003.003 phien |
|---|---|---|---|---|
| T-clean | 4 | 0.167 [0.071, 0.286] | 7/42 | 0/6 |
| T-clean | 8 | 0.524 [0.381, 0.691] | 22/42 | 2/6 |
| T-clean | 16 | 0.476 [0.333, 0.643] | 20/42 | 3/6 |
| T-clean | 32 | 0.667 [0.524, 0.809] | 28/42 | 6/6 |
| T-clean | du | 0.643 [0.486, 0.786] | 27/42 | 6/6 |
| T-novel | 4 | 0.093 [0.018, 0.185] | 5/54 | 0/6 |
| T-novel | 8 | 0.444 [0.315, 0.574] | 24/54 | 0/6 |
| T-novel | 16 | 0.333 [0.204, 0.463] | 18/54 | 0/6 |
| T-novel | 32 | 0.444 [0.314, 0.574] | 24/54 | 5/6 |
| T-novel | du | 0.407 [0.279, 0.542] | 22/54 | 4/6 |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 4/6 | 0.667 [0.333, 1.000] | [0.300, 0.903] | 4/6 | 0.667 [0.333, 1.000] | [0.300, 0.903] |
| T-novel | 0.5 | 4/6 | 0.667 [0.333, 1.000] | [0.300, 0.903] | 5/6 | 0.833 [0.500, 1.000] | [0.436, 0.970] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
