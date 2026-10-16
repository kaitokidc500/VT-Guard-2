### b1_raw_b (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.4768** (F1 OOF 0.971). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 0.976 [0.921, 1.000] | 0.988 [0.959, 1.000] | 0.000 [0.000, 0.000] | 0.999 [0.997, 1.000] | 1.000 [0.997, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.000 [0.000, 0.000], Wilson [0.000, 0.042] (0/88) | - | - |
| T-novel | 149 (54) | 0.930 [0.862, 0.983] | 0.982 [0.939, 1.000] | 0.955 [0.913, 0.990] | 0.042 [0.010, 0.087] | 0.953 [0.894, 0.999] | 0.981 [0.955, 1.000] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 0.976 [0.921, 1.000] | 0.988 [0.959, 1.000] | 0.000 [0.000, 0.000] | 0.999 [0.997, 1.000] | 1.000 [0.997, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.000 [0.000, 0.000], Wilson [0.000, 0.042] (0/88) | - | - |
| T-novel | 149 (54) | 0.930 [0.862, 0.983] | 0.982 [0.939, 1.000] | 0.955 [0.913, 0.990] | 0.042 [0.010, 0.087] | 0.953 [0.894, 0.999] | 0.981 [0.955, 1.000] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] | -0.209 [-0.469, 0.080] |
| T-clean | 0.5 | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] |  |
| T-hard | khoa | 0/36 | 0.000 [0.000, 0.000] | 0/52 | 0.000 [0.000, 0.000] | 0.043 [-0.182, 0.280] |
| T-hard | 0.5 | 0/36 | 0.000 [0.000, 0.000] | 0/52 | 0.000 [0.000, 0.000] |  |
| T-novel | khoa | 4/54 | 0.074 [0.018, 0.148] | 0/41 | 0.000 [0.000, 0.000] | 0.157 [-0.034, 0.350] |
| T-novel | 0.5 | 4/54 | 0.074 [0.018, 0.148] | 0/41 | 0.000 [0.000, 0.000] |  |

**T-hard - FPR theo chu ky cong cu (nguong da khoa)**

| Chu ky | n | FP | FPR [bootstrap] | Wilson 95% |
|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | 41 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.086] |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | 12 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.242] |
| `net.exe+net1.exe` | 5 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.434] |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | 5 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.434] |
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
| *co cmd.exe trong cay tien trinh* | 19 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.168] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.800 [0.629, 0.933] (n=21) | 0.562 [0.320, 0.750] (n=23) | 0.703 [0.500, 0.850] (n=24) | 0.741 [0.526, 0.903] (n=17) | 1.000 [1.000, 1.000] (n=12) | 0.761 [0.685, 0.824] |
| T-novel | 0.774 [0.636, 0.882] (n=37) | 0.520 [0.327, 0.667] (n=36) | 0.746 [0.603, 0.857] (n=33) | 0.500 [0.261, 0.692] (n=16) | 1.000 [1.000, 1.000] (n=6) | 0.708 [0.630, 0.774] |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-novel | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
