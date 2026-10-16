### b1_tfidf_a (dataset-v1.1)

Nguong nhi phan chon tren Train OOF: **0.4518** (F1 OOF 0.962). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 87 (41) | 0.976 [0.913, 1.000] | 0.976 [0.917, 1.000] | 0.976 [0.935, 1.000] | 0.022 [0.000, 0.077] | 0.999 [0.997, 1.000] | 1.000 [0.997, 1.000] |
| T-hard | 87 (0) | - | - | - | 0.023 [0.000, 0.058], Wilson [0.006, 0.080] (2/87) | - | - |
| T-novel | 148 (53) | 0.881 [0.797, 0.955] | 0.981 [0.938, 1.000] | 0.929 [0.875, 0.973] | 0.074 [0.029, 0.133] | 0.926 [0.849, 0.985] | 0.971 [0.940, 0.993] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 87 (41) | 0.976 [0.913, 1.000] | 0.976 [0.917, 1.000] | 0.976 [0.935, 1.000] | 0.022 [0.000, 0.077] | 0.999 [0.997, 1.000] | 1.000 [0.997, 1.000] |
| T-hard | 87 (0) | - | - | - | 0.011 [0.000, 0.035], Wilson [0.002, 0.062] (1/87) | - | - |
| T-novel | 148 (53) | 0.879 [0.794, 0.954] | 0.962 [0.900, 1.000] | 0.919 [0.860, 0.967] | 0.074 [0.029, 0.133] | 0.926 [0.849, 0.985] | 0.971 [0.940, 0.993] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/21 | 0.000 [0.000, 0.000] | 1/25 | 0.040 [0.000, 0.120] | 0.404 [0.066, 0.648] |
| T-clean | 0.5 | 0/21 | 0.000 [0.000, 0.000] | 1/25 | 0.040 [0.000, 0.120] |  |
| T-hard | khoa | 2/34 | 0.059 [0.000, 0.147] | 0/53 | 0.000 [0.000, 0.000] | 0.808 [0.704, 0.876] |
| T-hard | 0.5 | 1/34 | 0.029 [0.000, 0.088] | 0/53 | 0.000 [0.000, 0.000] |  |
| T-novel | khoa | 7/53 | 0.132 [0.057, 0.226] | 0/42 | 0.000 [0.000, 0.000] | 0.719 [0.584, 0.830] |
| T-novel | 0.5 | 7/53 | 0.132 [0.057, 0.226] | 0/42 | 0.000 [0.000, 0.000] |  |

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
| *co cmd.exe trong cay tien trinh* | 18 | 2 | 0.111 [0.000, 0.278] | [0.031, 0.328] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.800 [0.640, 0.930] (n=21) | 0.606 [0.375, 0.783] (n=22) | 0.889 [0.773, 0.969] (n=23) | 0.800 [0.629, 0.923] (n=16) | 1.000 [1.000, 1.000] (n=12) | 0.819 [0.741, 0.880] |
| T-novel | 0.806 [0.692, 0.907] (n=36) | 0.607 [0.444, 0.755] (n=35) | 0.696 [0.561, 0.800] (n=32) | 0.500 [0.312, 0.667] (n=16) | 1.000 [1.000, 1.000] (n=6) | 0.722 [0.652, 0.780] |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-novel | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
