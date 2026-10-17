### vtseq_M4b_s99 (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.9163** (F1 OOF 0.956). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.000 [0.000, 0.000], Wilson [0.000, 0.042] (0/88) | - | - |
| T-novel | 149 (54) | 0.941 [0.868, 1.000] | 0.889 [0.796, 0.966] | 0.914 [0.854, 0.964] | 0.032 [0.000, 0.075] | 0.988 [0.972, 0.998] | 0.993 [0.983, 0.999] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.023 [0.000, 0.057], Wilson [0.006, 0.079] (2/88) | - | - |
| T-novel | 149 (54) | 0.900 [0.821, 0.968] | 1.000 [1.000, 1.000] | 0.947 [0.902, 0.984] | 0.063 [0.020, 0.120] | 0.988 [0.972, 0.998] | 0.993 [0.983, 0.999] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] | 0.351 [0.024, 0.592] |
| T-clean | 0.5 | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] |  |
| T-hard | khoa | 0/36 | 0.000 [0.000, 0.000] | 0/52 | 0.000 [0.000, 0.000] | 0.084 [-0.131, 0.276] |
| T-hard | 0.5 | 0/36 | 0.000 [0.000, 0.000] | 2/52 | 0.038 [0.000, 0.096] |  |
| T-novel | khoa | 3/54 | 0.056 [0.000, 0.112] | 0/41 | 0.000 [0.000, 0.000] | -0.001 [-0.196, 0.189] |
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
| T-clean | 0.824 [0.700, 0.925] (n=21) | 0.783 [0.634, 0.895] (n=23) | 0.808 [0.667, 0.913] (n=24) | 0.944 [0.857, 1.000] (n=17) | 1.000 [1.000, 1.000] (n=12) | 0.872 [0.812, 0.918] |
| T-novel | 0.851 [0.767, 0.919] (n=37) | 0.861 [0.771, 0.929] (n=36) | 0.706 [0.567, 0.822] (n=33) | 0.696 [0.531, 0.833] (n=16) | 0.000 [0.000, 0.000] (n=6) | 0.623 [0.558, 0.669] |

**Phat hien som** - recall cua so duong khi chi giu k event dau tinh tu event malicious dau tien (nguong da khoa, khong chon lai); 'du' = cua so day du. T1003.003: so phien phat hien.

| Tap | k | Recall [CI] | Phat hien | T1003.003 phien |
|---|---|---|---|---|
| T-clean | 4 | 0.786 [0.667, 0.905] | 33/42 | 5/6 |
| T-clean | 8 | 0.857 [0.761, 0.952] | 36/42 | 6/6 |
| T-clean | 16 | 0.905 [0.809, 0.976] | 38/42 | 6/6 |
| T-clean | 32 | 0.976 [0.929, 1.000] | 41/42 | 6/6 |
| T-clean | du | 1.000 [1.000, 1.000] | 42/42 | 6/6 |
| T-novel | 4 | 0.889 [0.796, 0.963] | 48/54 | 0/6 |
| T-novel | 8 | 0.889 [0.796, 0.963] | 48/54 | 0/6 |
| T-novel | 16 | 0.889 [0.796, 0.963] | 48/54 | 0/6 |
| T-novel | 32 | 0.889 [0.796, 0.963] | 48/54 | 0/6 |
| T-novel | du | 0.889 [0.796, 0.966] | 48/54 | 0/6 |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
| T-novel | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
