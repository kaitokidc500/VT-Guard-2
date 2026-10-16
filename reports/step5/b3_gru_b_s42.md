### b3_gru_b_s42 (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.5097** (F1 OOF 0.963). CI bootstrap 95%, 1000 lan, seed 42.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.023 [0.000, 0.057], Wilson [0.006, 0.079] (2/88) | - | - |
| T-novel | 149 (54) | 0.898 [0.818, 0.967] | 0.982 [0.940, 1.000] | 0.938 [0.889, 0.980] | 0.063 [0.020, 0.120] | 0.945 [0.890, 0.988] | 0.975 [0.949, 0.995] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.023 [0.000, 0.057], Wilson [0.006, 0.079] (2/88) | - | - |
| T-novel | 149 (54) | 0.898 [0.818, 0.967] | 0.982 [0.940, 1.000] | 0.938 [0.889, 0.980] | 0.063 [0.020, 0.120] | 0.945 [0.890, 0.988] | 0.975 [0.949, 0.995] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] | 0.219 [-0.161, 0.542] |
| T-clean | 0.5 | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] |  |
| T-hard | khoa | 2/36 | 0.056 [0.000, 0.139] | 0/52 | 0.000 [0.000, 0.000] | 0.750 [0.634, 0.832] |
| T-hard | 0.5 | 2/36 | 0.056 [0.000, 0.139] | 0/52 | 0.000 [0.000, 0.000] |  |
| T-novel | khoa | 6/54 | 0.111 [0.037, 0.186] | 0/41 | 0.000 [0.000, 0.000] | 0.610 [0.416, 0.770] |
| T-novel | 0.5 | 6/54 | 0.111 [0.037, 0.186] | 0/41 | 0.000 [0.000, 0.000] |  |

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
| *co cmd.exe trong cay tien trinh* | 19 | 2 | 0.105 [0.000, 0.263] | [0.029, 0.314] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.824 [0.700, 0.925] (n=21) | 0.868 [0.755, 0.955] (n=23) | 0.889 [0.791, 0.967] (n=24) | 0.829 [0.683, 0.945] (n=17) | 1.000 [1.000, 1.000] (n=12) | 0.882 [0.821, 0.933] |
| T-novel | 0.800 [0.705, 0.882] (n=37) | 0.809 [0.713, 0.891] (n=36) | 0.744 [0.635, 0.840] (n=33) | 0.533 [0.385, 0.676] (n=16) | 1.000 [1.000, 1.000] (n=6) | 0.777 [0.718, 0.827] |

**Phat hien som** - recall cua so duong khi chi giu k event dau tinh tu event malicious dau tien (nguong da khoa, khong chon lai); 'du' = cua so day du. T1003.003: so phien phat hien.

| Tap | k | Recall [CI] | Phat hien | T1003.003 phien |
|---|---|---|---|---|
| T-clean | 4 | 0.833 [0.714, 0.929] | 35/42 | 6/6 |
| T-clean | 8 | 0.833 [0.714, 0.929] | 35/42 | 6/6 |
| T-clean | 16 | 0.881 [0.762, 0.976] | 37/42 | 6/6 |
| T-clean | 32 | 0.952 [0.881, 1.000] | 40/42 | 6/6 |
| T-clean | du | 1.000 [1.000, 1.000] | 42/42 | 6/6 |
| T-novel | 4 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
| T-novel | 8 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
| T-novel | 16 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
| T-novel | 32 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
| T-novel | du | 0.982 [0.940, 1.000] | 53/54 | 6/6 |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-novel | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
