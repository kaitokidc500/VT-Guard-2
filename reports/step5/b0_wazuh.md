### b0_wazuh (dataset-v1.1)

Nguong nhi phan chon tren Train OOF: **0.2667** (F1 OOF 0.867). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 87 (41) | 0.976 [0.923, 1.000] | 1.000 [1.000, 1.000] | 0.988 [0.960, 1.000] | 0.022 [0.000, 0.071] | 0.986 [0.952, 1.000] | 0.994 [0.978, 1.000] |
| T-hard | 87 (0) | - | - | - | 0.195 [0.126, 0.276], Wilson [0.126, 0.291] (17/87) | - | - |
| T-novel | 148 (53) | 0.825 [0.738, 0.918] | 0.981 [0.939, 1.000] | 0.897 [0.835, 0.952] | 0.116 [0.051, 0.184] | 0.818 [0.724, 0.909] | 0.934 [0.898, 0.971] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 87 (41) | 1.000 [1.000, 1.000] | 0.098 [0.023, 0.200] | 0.178 [0.045, 0.334] | 0.000 [0.000, 0.000] | 0.986 [0.952, 1.000] | 0.994 [0.978, 1.000] |
| T-hard | 87 (0) | - | - | - | 0.000 [0.000, 0.000], Wilson [0.000, 0.042] (0/87) | - | - |
| T-novel | 148 (53) | - | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.818 [0.724, 0.909] | 0.934 [0.898, 0.971] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/21 | 0.000 [0.000, 0.000] | 1/25 | 0.040 [0.000, 0.120] | 0.528 [0.172, 0.751] |
| T-clean | 0.5 | 0/21 | 0.000 [0.000, 0.000] | 0/25 | 0.000 [0.000, 0.000] |  |
| T-hard | khoa | 6/34 | 0.176 [0.059, 0.294] | 11/53 | 0.207 [0.113, 0.321] | 0.458 [0.223, 0.635] |
| T-hard | 0.5 | 0/34 | 0.000 [0.000, 0.000] | 0/53 | 0.000 [0.000, 0.000] |  |
| T-novel | khoa | 11/53 | 0.207 [0.113, 0.340] | 0/42 | 0.000 [0.000, 0.000] | 0.563 [0.396, 0.699] |
| T-novel | 0.5 | 0/53 | 0.000 [0.000, 0.000] | 0/42 | 0.000 [0.000, 0.000] |  |

**T-hard - FPR theo chu ky cong cu (nguong da khoa)**

| Chu ky | n | FP | FPR [bootstrap] | Wilson 95% |
|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | 41 | 2 | 0.049 [0.000, 0.122] | [0.013, 0.161] |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | 12 | 1 | 0.083 [0.000, 0.250] | [0.015, 0.354] |
| `net.exe+net1.exe` | 5 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.434] |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | 4 | 3 | 0.750 [0.250, 1.000] | [0.301, 0.954] |
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
| *co cmd.exe trong cay tien trinh* | 18 | 14 | 0.778 [0.611, 0.944] | [0.548, 0.910] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.000 [0.000, 0.000] (n=21) | 0.000 [0.000, 0.000] (n=22) | 0.581 [0.426, 0.708] (n=23) | 0.000 [0.000, 0.000] (n=16) | 0.000 [0.000, 0.000] (n=12) | 0.116 [0.085, 0.141] |
| T-novel | 0.000 [0.000, 0.000] (n=36) | 0.000 [0.000, 0.000] (n=35) | 0.571 [0.449, 0.686] (n=32) | 0.000 [0.000, 0.000] (n=16) | 0.000 [0.000, 0.000] (n=6) | 0.114 [0.090, 0.137] |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 5/6 | 0.833 [0.500, 1.000] | [0.436, 0.970] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
| T-novel | 0.5 | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
| T-clean | 0.5 | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
