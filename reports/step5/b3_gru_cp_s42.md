### b3_gru_cp_s42 (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.6520** (F1 OOF 0.972). CI bootstrap 95%, 1000 lan, seed 42.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 0.976 [0.919, 1.000] | 0.988 [0.958, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.057 [0.011, 0.114], Wilson [0.025, 0.126] (5/88) | - | - |
| T-novel | 149 (54) | 0.885 [0.803, 0.961] | 1.000 [1.000, 1.000] | 0.939 [0.891, 0.980] | 0.074 [0.022, 0.134] | 0.945 [0.890, 0.987] | 0.974 [0.948, 0.993] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 0.976 [0.919, 1.000] | 0.988 [0.958, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.057 [0.011, 0.114], Wilson [0.025, 0.126] (5/88) | - | - |
| T-novel | 149 (54) | 0.885 [0.803, 0.961] | 1.000 [1.000, 1.000] | 0.939 [0.891, 0.980] | 0.074 [0.022, 0.134] | 0.945 [0.890, 0.987] | 0.974 [0.948, 0.993] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] | 0.430 [0.124, 0.686] |
| T-clean | 0.5 | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] |  |
| T-hard | khoa | 4/36 | 0.111 [0.028, 0.222] | 1/52 | 0.019 [0.000, 0.058] | 0.486 [0.309, 0.643] |
| T-hard | 0.5 | 4/36 | 0.111 [0.028, 0.222] | 1/52 | 0.019 [0.000, 0.058] |  |
| T-novel | khoa | 7/54 | 0.130 [0.056, 0.222] | 0/41 | 0.000 [0.000, 0.000] | 0.527 [0.342, 0.682] |
| T-novel | 0.5 | 7/54 | 0.130 [0.056, 0.222] | 0/41 | 0.000 [0.000, 0.000] |  |

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
| T-clean | 0.824 [0.700, 0.925] (n=21) | 0.773 [0.609, 0.897] (n=23) | 0.889 [0.791, 0.967] (n=24) | 0.723 [0.545, 0.852] (n=17) | 1.000 [1.000, 1.000] (n=12) | 0.842 [0.781, 0.894] |
| T-novel | 0.813 [0.725, 0.893] (n=37) | 0.732 [0.607, 0.831] (n=36) | 0.759 [0.651, 0.849] (n=33) | 0.464 [0.327, 0.595] (n=16) | 1.000 [1.000, 1.000] (n=6) | 0.754 [0.695, 0.803] |

**Phat hien som** - recall cua so duong khi chi giu k event dau tinh tu event malicious dau tien (nguong da khoa, khong chon lai); 'du' = cua so day du. T1003.003: so phien phat hien.

| Tap | k | Recall [CI] | Phat hien | T1003.003 phien |
|---|---|---|---|---|
| T-clean | 4 | 0.881 [0.762, 0.976] | 37/42 | 6/6 |
| T-clean | 8 | 0.857 [0.762, 0.952] | 36/42 | 6/6 |
| T-clean | 16 | 0.905 [0.809, 0.976] | 38/42 | 6/6 |
| T-clean | 32 | 0.976 [0.929, 1.000] | 41/42 | 6/6 |
| T-clean | du | 0.976 [0.919, 1.000] | 41/42 | 6/6 |
| T-novel | 4 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
| T-novel | 8 | 0.944 [0.889, 1.000] | 51/54 | 5/6 |
| T-novel | 16 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
| T-novel | 32 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
| T-novel | du | 1.000 [1.000, 1.000] | 54/54 | 6/6 |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-novel | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
