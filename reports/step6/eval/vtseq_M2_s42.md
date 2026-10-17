### vtseq_M2_s42 (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.9221** (F1 OOF 0.95). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.023 [0.000, 0.057], Wilson [0.006, 0.079] (2/88) | - | - |
| T-novel | 149 (54) | 0.900 [0.821, 0.968] | 1.000 [1.000, 1.000] | 0.947 [0.902, 0.984] | 0.063 [0.020, 0.120] | 0.967 [0.923, 0.996] | 0.985 [0.961, 0.998] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.045 [0.011, 0.091], Wilson [0.018, 0.111] (4/88) | - | - |
| T-novel | 149 (54) | 0.885 [0.804, 0.959] | 1.000 [1.000, 1.000] | 0.939 [0.891, 0.979] | 0.074 [0.024, 0.136] | 0.967 [0.923, 0.996] | 0.985 [0.961, 0.998] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] | 0.553 [0.249, 0.777] |
| T-clean | 0.5 | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] |  |
| T-hard | khoa | 2/36 | 0.056 [0.000, 0.139] | 0/52 | 0.000 [0.000, 0.000] | 0.605 [0.445, 0.736] |
| T-hard | 0.5 | 2/36 | 0.056 [0.000, 0.139] | 2/52 | 0.038 [0.000, 0.096] |  |
| T-novel | khoa | 6/54 | 0.111 [0.037, 0.186] | 0/41 | 0.000 [0.000, 0.000] | 0.491 [0.305, 0.648] |
| T-novel | 0.5 | 7/54 | 0.130 [0.056, 0.222] | 0/41 | 0.000 [0.000, 0.000] |  |

**T-hard - FPR theo chu ky cong cu (nguong da khoa)**

| Chu ky | n | FP | FPR [bootstrap] | Wilson 95% |
|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | 41 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.086] |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | 12 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.242] |
| `net.exe+net1.exe` | 5 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.434] |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | 5 | 2 | 0.400 [0.000, 0.800] | [0.118, 0.769] |
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
| *co cmd.exe trong cay tien trinh* | 19 | 2 | 0.105 [0.000, 0.263] | [0.029, 0.314] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.821 [0.667, 0.930] (n=21) | 0.766 [0.605, 0.885] (n=23) | 0.889 [0.791, 0.967] (n=24) | 0.895 [0.769, 1.000] (n=17) | 1.000 [1.000, 1.000] (n=12) | 0.874 [0.810, 0.922] |
| T-novel | 0.806 [0.689, 0.897] (n=37) | 0.854 [0.762, 0.924] (n=36) | 0.742 [0.635, 0.835] (n=33) | 0.615 [0.453, 0.762] (n=16) | 1.000 [1.000, 1.000] (n=6) | 0.803 [0.746, 0.852] |

**Phat hien som** - recall cua so duong khi chi giu k event dau tinh tu event malicious dau tien (nguong da khoa, khong chon lai); 'du' = cua so day du. T1003.003: so phien phat hien.

| Tap | k | Recall [CI] | Phat hien | T1003.003 phien |
|---|---|---|---|---|
| T-clean | 4 | 0.857 [0.762, 0.952] | 36/42 | 6/6 |
| T-clean | 8 | 0.881 [0.786, 0.976] | 37/42 | 6/6 |
| T-clean | 16 | 0.952 [0.881, 1.000] | 40/42 | 6/6 |
| T-clean | 32 | 1.000 [1.000, 1.000] | 42/42 | 6/6 |
| T-clean | du | 1.000 [1.000, 1.000] | 42/42 | 6/6 |
| T-novel | 4 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
| T-novel | 8 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
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
