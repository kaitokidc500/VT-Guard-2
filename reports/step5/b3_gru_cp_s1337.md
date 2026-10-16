### b3_gru_cp_s1337 (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.7641** (F1 OOF 0.958). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 0.976 [0.919, 1.000] | 0.988 [0.958, 1.000] | 0.000 [0.000, 0.000] | 0.999 [0.995, 1.000] | 0.999 [0.995, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.102 [0.045, 0.171], Wilson [0.055, 0.183] (9/88) | - | - |
| T-novel | 149 (54) | 0.869 [0.783, 0.946] | 0.982 [0.940, 1.000] | 0.922 [0.870, 0.966] | 0.084 [0.034, 0.144] | 0.892 [0.796, 0.973] | 0.960 [0.921, 0.989] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 0.976 [0.921, 1.000] | 0.976 [0.919, 1.000] | 0.976 [0.938, 1.000] | 0.021 [0.000, 0.068] | 0.999 [0.995, 1.000] | 0.999 [0.995, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.102 [0.045, 0.171], Wilson [0.055, 0.183] (9/88) | - | - |
| T-novel | 149 (54) | 0.871 [0.787, 0.946] | 1.000 [1.000, 1.000] | 0.931 [0.881, 0.972] | 0.084 [0.034, 0.144] | 0.892 [0.796, 0.973] | 0.960 [0.921, 0.989] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] | 0.190 [-0.172, 0.510] |
| T-clean | 0.5 | 0/23 | 0.000 [0.000, 0.000] | 1/24 | 0.042 [0.000, 0.125] |  |
| T-hard | khoa | 6/36 | 0.167 [0.056, 0.278] | 3/52 | 0.058 [0.000, 0.115] | 0.577 [0.410, 0.712] |
| T-hard | 0.5 | 6/36 | 0.167 [0.056, 0.278] | 3/52 | 0.058 [0.000, 0.115] |  |
| T-novel | khoa | 7/54 | 0.130 [0.056, 0.222] | 1/41 | 0.024 [0.000, 0.073] | 0.576 [0.387, 0.732] |
| T-novel | 0.5 | 7/54 | 0.130 [0.056, 0.222] | 1/41 | 0.024 [0.000, 0.073] |  |

**T-hard - FPR theo chu ky cong cu (nguong da khoa)**

| Chu ky | n | FP | FPR [bootstrap] | Wilson 95% |
|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | 41 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.086] |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | 12 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.242] |
| `net.exe+net1.exe` | 5 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.434] |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | 5 | 5 | 1.000 [1.000, 1.000] | [0.566, 1.000] |
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
| `nbtstat.exe+netsh.exe+nslookup.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| `netsh.exe+nslookup.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| *khong cmd.exe trong cay tien trinh* | 69 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.053] |
| *co cmd.exe trong cay tien trinh* | 19 | 9 | 0.474 [0.263, 0.685] | [0.273, 0.683] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.775 [0.638, 0.889] (n=21) | 0.851 [0.727, 0.951] (n=23) | 0.873 [0.766, 0.955] (n=24) | 0.809 [0.648, 0.930] (n=17) | 1.000 [1.000, 1.000] (n=12) | 0.862 [0.803, 0.911] |
| T-novel | 0.800 [0.705, 0.882] (n=37) | 0.784 [0.667, 0.875] (n=36) | 0.742 [0.635, 0.835] (n=33) | 0.500 [0.358, 0.630] (n=16) | 1.000 [1.000, 1.000] (n=6) | 0.765 [0.707, 0.812] |

**Phat hien som** - recall cua so duong khi chi giu k event dau tinh tu event malicious dau tien (nguong da khoa, khong chon lai); 'du' = cua so day du. T1003.003: so phien phat hien.

| Tap | k | Recall [CI] | Phat hien | T1003.003 phien |
|---|---|---|---|---|
| T-clean | 4 | 0.809 [0.691, 0.905] | 34/42 | 6/6 |
| T-clean | 8 | 0.786 [0.666, 0.905] | 33/42 | 6/6 |
| T-clean | 16 | 0.905 [0.809, 0.976] | 38/42 | 6/6 |
| T-clean | 32 | 0.976 [0.929, 1.000] | 41/42 | 6/6 |
| T-clean | du | 0.976 [0.919, 1.000] | 41/42 | 6/6 |
| T-novel | 4 | 0.889 [0.796, 0.963] | 48/54 | 1/6 |
| T-novel | 8 | 0.759 [0.648, 0.870] | 41/54 | 0/6 |
| T-novel | 16 | 0.870 [0.778, 0.944] | 47/54 | 1/6 |
| T-novel | 32 | 0.982 [0.944, 1.000] | 53/54 | 6/6 |
| T-novel | du | 0.982 [0.940, 1.000] | 53/54 | 6/6 |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-novel | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
