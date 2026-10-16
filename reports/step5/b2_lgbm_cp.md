### b2_lgbm_cp (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.6665** (F1 OOF 0.978). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 0.952 [0.881, 1.000] | 0.976 [0.937, 1.000] | 0.000 [0.000, 0.000] | 0.999 [0.995, 1.000] | 0.999 [0.995, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.023 [0.000, 0.057], Wilson [0.006, 0.079] (2/88) | - | - |
| T-novel | 149 (54) | 0.943 [0.875, 1.000] | 0.926 [0.849, 0.984] | 0.935 [0.878, 0.979] | 0.032 [0.000, 0.074] | 0.994 [0.983, 1.000] | 0.996 [0.990, 1.000] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 0.976 [0.923, 1.000] | 0.952 [0.881, 1.000] | 0.964 [0.919, 1.000] | 0.021 [0.000, 0.068] | 0.999 [0.995, 1.000] | 0.999 [0.995, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.023 [0.000, 0.057], Wilson [0.006, 0.079] (2/88) | - | - |
| T-novel | 149 (54) | 0.946 [0.879, 1.000] | 0.963 [0.906, 1.000] | 0.954 [0.909, 0.991] | 0.032 [0.000, 0.074] | 0.994 [0.983, 1.000] | 0.996 [0.990, 1.000] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] | -0.099 [-0.389, 0.188] |
| T-clean | 0.5 | 0/23 | 0.000 [0.000, 0.000] | 1/24 | 0.042 [0.000, 0.125] |  |
| T-hard | khoa | 0/36 | 0.000 [0.000, 0.000] | 2/52 | 0.038 [0.000, 0.096] | -0.048 [-0.258, 0.184] |
| T-hard | 0.5 | 0/36 | 0.000 [0.000, 0.000] | 2/52 | 0.038 [0.000, 0.096] |  |
| T-novel | khoa | 3/54 | 0.056 [0.000, 0.130] | 0/41 | 0.000 [0.000, 0.000] | 0.163 [-0.038, 0.356] |
| T-novel | 0.5 | 3/54 | 0.056 [0.000, 0.130] | 0/41 | 0.000 [0.000, 0.000] |  |

**T-hard - FPR theo chu ky cong cu (nguong da khoa)**

| Chu ky | n | FP | FPR [bootstrap] | Wilson 95% |
|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | 41 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.086] |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | 12 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.242] |
| `net.exe+net1.exe` | 5 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.434] |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | 5 | 1 | 0.200 [0.000, 0.600] | [0.036, 0.625] |
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
| `ntdsutil.exe+vssadmin.exe+wevtutil.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| `arp.exe+net.exe+nltest.exe+ntdsutil.exe+ping.exe+vssadmin.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `arp.exe+net.exe+nltest.exe+ping.exe+wevtutil.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `nbtstat.exe+netsh.exe+nslookup.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `netsh.exe+nslookup.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| *khong cmd.exe trong cay tien trinh* | 69 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.053] |
| *co cmd.exe trong cay tien trinh* | 19 | 2 | 0.105 [0.000, 0.263] | [0.029, 0.314] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.889 [0.778, 0.972] (n=21) | 0.649 [0.457, 0.811] (n=23) | 0.917 [0.829, 0.984] (n=24) | 0.882 [0.750, 0.978] (n=17) | 1.000 [1.000, 1.000] (n=12) | 0.867 [0.801, 0.914] |
| T-novel | 0.880 [0.788, 0.949] (n=37) | 0.794 [0.685, 0.881] (n=36) | 0.786 [0.688, 0.871] (n=33) | 0.612 [0.444, 0.760] (n=16) | 1.000 [1.000, 1.000] (n=6) | 0.815 [0.767, 0.859] |

**Phat hien som** - recall cua so duong khi chi giu k event dau tinh tu event malicious dau tien (nguong da khoa, khong chon lai); 'du' = cua so day du. T1003.003: so phien phat hien.

| Tap | k | Recall [CI] | Phat hien | T1003.003 phien |
|---|---|---|---|---|
| T-clean | 4 | 0.714 [0.571, 0.857] | 30/42 | 5/6 |
| T-clean | 8 | 0.786 [0.667, 0.905] | 33/42 | 5/6 |
| T-clean | 16 | 0.809 [0.691, 0.929] | 34/42 | 5/6 |
| T-clean | 32 | 0.833 [0.714, 0.929] | 35/42 | 5/6 |
| T-clean | du | 0.952 [0.881, 1.000] | 40/42 | 5/6 |
| T-novel | 4 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
| T-novel | 8 | 0.982 [0.944, 1.000] | 53/54 | 5/6 |
| T-novel | 16 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
| T-novel | 32 | 0.963 [0.907, 1.000] | 52/54 | 4/6 |
| T-novel | du | 0.926 [0.849, 0.984] | 50/54 | 3/6 |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 3/6 | 0.500 [0.167, 0.833] | [0.188, 0.812] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-novel | 0.5 | 5/6 | 0.833 [0.500, 1.000] | [0.436, 0.970] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | khoa | 5/6 | 0.833 [0.500, 1.000] | [0.436, 0.970] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | 0.5 | 5/6 | 0.833 [0.500, 1.000] | [0.436, 0.970] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
