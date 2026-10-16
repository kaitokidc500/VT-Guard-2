### b3_gru_a_s1337 (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.9451** (F1 OOF 0.977). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 0.976 [0.919, 1.000] | 0.988 [0.958, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.057 [0.011, 0.114], Wilson [0.025, 0.126] (5/88) | - | - |
| T-novel | 149 (54) | 0.897 [0.815, 0.966] | 0.963 [0.904, 1.000] | 0.929 [0.875, 0.971] | 0.063 [0.020, 0.120] | 0.956 [0.909, 0.989] | 0.978 [0.954, 0.994] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 0.977 [0.923, 1.000] | 1.000 [1.000, 1.000] | 0.988 [0.960, 1.000] | 0.021 [0.000, 0.068] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.091 [0.034, 0.159], Wilson [0.047, 0.169] (8/88) | - | - |
| T-novel | 149 (54) | 0.900 [0.821, 0.968] | 1.000 [1.000, 1.000] | 0.947 [0.902, 0.984] | 0.063 [0.020, 0.120] | 0.956 [0.909, 0.989] | 0.978 [0.954, 0.994] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] | 0.342 [-0.008, 0.641] |
| T-clean | 0.5 | 0/23 | 0.000 [0.000, 0.000] | 1/24 | 0.042 [0.000, 0.125] |  |
| T-hard | khoa | 4/36 | 0.111 [0.028, 0.222] | 1/52 | 0.019 [0.000, 0.058] | 0.696 [0.553, 0.815] |
| T-hard | 0.5 | 6/36 | 0.167 [0.056, 0.278] | 2/52 | 0.038 [0.000, 0.096] |  |
| T-novel | khoa | 6/54 | 0.111 [0.037, 0.186] | 0/41 | 0.000 [0.000, 0.000] | 0.602 [0.399, 0.759] |
| T-novel | 0.5 | 6/54 | 0.111 [0.037, 0.186] | 0/41 | 0.000 [0.000, 0.000] |  |

**T-hard - FPR theo chu ky cong cu (nguong da khoa)**

| Chu ky | n | FP | FPR [bootstrap] | Wilson 95% |
|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | 41 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.086] |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | 12 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.242] |
| `net.exe+net1.exe` | 5 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.434] |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | 5 | 3 | 0.600 [0.200, 1.000] | [0.231, 0.882] |
| `ntdsutil.exe+vssadmin.exe [revert_control]` | 4 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.490] |
| `net.exe+nltest.exe+ping.exe` | 3 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.561] |
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
| `ntdsutil.exe+vssadmin.exe+wevtutil.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `arp.exe+net.exe+nltest.exe+ntdsutil.exe+ping.exe+vssadmin.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `arp.exe+net.exe+nltest.exe+ping.exe+wevtutil.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `nbtstat.exe+netsh.exe+nslookup.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `netsh.exe+nslookup.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| *khong cmd.exe trong cay tien trinh* | 69 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.053] |
| *co cmd.exe trong cay tien trinh* | 19 | 5 | 0.263 [0.105, 0.474] | [0.118, 0.488] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.745 [0.605, 0.866] (n=21) | 0.651 [0.468, 0.808] (n=23) | 0.815 [0.692, 0.915] (n=24) | 0.739 [0.571, 0.870] (n=17) | 0.909 [0.727, 1.000] (n=12) | 0.772 [0.677, 0.851] |
| T-novel | 0.805 [0.710, 0.889] (n=37) | 0.735 [0.597, 0.846] (n=36) | 0.747 [0.639, 0.842] (n=33) | 0.485 [0.345, 0.617] (n=16) | 0.909 [0.667, 1.000] (n=6) | 0.736 [0.656, 0.795] |

**Phat hien som** - recall cua so duong khi chi giu k event dau tinh tu event malicious dau tien (nguong da khoa, khong chon lai); 'du' = cua so day du. T1003.003: so phien phat hien.

| Tap | k | Recall [CI] | Phat hien | T1003.003 phien |
|---|---|---|---|---|
| T-clean | 4 | 0.452 [0.309, 0.596] | 19/42 | 5/6 |
| T-clean | 8 | 0.809 [0.691, 0.929] | 34/42 | 6/6 |
| T-clean | 16 | 0.833 [0.714, 0.929] | 35/42 | 6/6 |
| T-clean | 32 | 0.952 [0.881, 1.000] | 40/42 | 6/6 |
| T-clean | du | 0.976 [0.919, 1.000] | 41/42 | 6/6 |
| T-novel | 4 | 0.741 [0.630, 0.852] | 40/54 | 6/6 |
| T-novel | 8 | 0.944 [0.870, 1.000] | 51/54 | 6/6 |
| T-novel | 16 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
| T-novel | 32 | 0.982 [0.944, 1.000] | 53/54 | 6/6 |
| T-novel | du | 0.963 [0.904, 1.000] | 52/54 | 6/6 |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 5/6 | 0.833 [0.500, 1.000] | [0.436, 0.970] |
| T-novel | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 5/6 | 0.833 [0.500, 1.000] | [0.436, 0.970] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
