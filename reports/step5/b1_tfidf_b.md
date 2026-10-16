### b1_tfidf_b (dataset-v1.1)

Nguong nhi phan chon tren Train OOF: **0.5774** (F1 OOF 0.97). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 87 (41) | 1.000 [1.000, 1.000] | 0.976 [0.917, 1.000] | 0.988 [0.957, 1.000] | 0.000 [0.000, 0.000] | 0.997 [0.990, 1.000] | 0.997 [0.989, 1.000] |
| T-hard | 87 (0) | - | - | - | 0.000 [0.000, 0.000], Wilson [0.000, 0.042] (0/87) | - | - |
| T-novel | 148 (53) | 0.893 [0.807, 0.966] | 0.943 [0.877, 1.000] | 0.917 [0.855, 0.966] | 0.063 [0.020, 0.120] | 0.903 [0.817, 0.972] | 0.962 [0.925, 0.988] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 87 (41) | 1.000 [1.000, 1.000] | 0.976 [0.917, 1.000] | 0.988 [0.957, 1.000] | 0.000 [0.000, 0.000] | 0.997 [0.990, 1.000] | 0.997 [0.989, 1.000] |
| T-hard | 87 (0) | - | - | - | 0.000 [0.000, 0.000], Wilson [0.000, 0.042] (0/87) | - | - |
| T-novel | 148 (53) | 0.897 [0.810, 0.967] | 0.981 [0.938, 1.000] | 0.937 [0.883, 0.977] | 0.063 [0.020, 0.120] | 0.903 [0.817, 0.972] | 0.962 [0.925, 0.988] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/21 | 0.000 [0.000, 0.000] | 0/25 | 0.000 [0.000, 0.000] | 0.306 [-0.054, 0.580] |
| T-clean | 0.5 | 0/21 | 0.000 [0.000, 0.000] | 0/25 | 0.000 [0.000, 0.000] |  |
| T-hard | khoa | 0/34 | 0.000 [0.000, 0.000] | 0/53 | 0.000 [0.000, 0.000] | 0.791 [0.684, 0.863] |
| T-hard | 0.5 | 0/34 | 0.000 [0.000, 0.000] | 0/53 | 0.000 [0.000, 0.000] |  |
| T-novel | khoa | 6/53 | 0.113 [0.038, 0.207] | 0/42 | 0.000 [0.000, 0.000] | 0.716 [0.582, 0.822] |
| T-novel | 0.5 | 6/53 | 0.113 [0.038, 0.207] | 0/42 | 0.000 [0.000, 0.000] |  |

**T-hard - FPR theo chu ky cong cu (nguong da khoa)**

| Chu ky | n | FP | FPR [bootstrap] | Wilson 95% |
|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | 41 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.086] |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | 12 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.242] |
| `net.exe+net1.exe` | 5 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.434] |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | 4 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.490] |
| `ntdsutil.exe+vssadmin.exe [revert_control]` | 4 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.490] |
| `net.exe+nltest.exe+ping.exe` | 3 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.561] |
| `net.exe+net1.exe+vssadmin.exe` | 2 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.658] |
| `net.exe+net1.exe+nltest.exe` | 2 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.658] |
| `ipconfig.exe+netsh.exe` | 2 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.658] |
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
| *co cmd.exe trong cay tien trinh* | 18 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.176] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.895 [0.773, 0.980] (n=21) | 0.625 [0.385, 0.800] (n=22) | 0.821 [0.651, 0.936] (n=23) | 0.914 [0.800, 1.000] (n=16) | 1.000 [1.000, 1.000] (n=12) | 0.851 [0.787, 0.901] |
| T-novel | 0.771 [0.654, 0.877] (n=36) | 0.597 [0.432, 0.741] (n=35) | 0.730 [0.593, 0.846] (n=32) | 0.591 [0.400, 0.737] (n=16) | 1.000 [1.000, 1.000] (n=6) | 0.738 [0.678, 0.788] |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-novel | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
