### vtseq_M4b_s2024 (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.3331** (F1 OOF 0.989). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.045 [0.011, 0.091], Wilson [0.018, 0.111] (4/88) | - | - |
| T-novel | 149 (54) | 0.900 [0.821, 0.968] | 1.000 [1.000, 1.000] | 0.947 [0.902, 0.984] | 0.063 [0.020, 0.120] | 0.990 [0.976, 0.999] | 0.994 [0.986, 0.999] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.034 [0.000, 0.068], Wilson [0.012, 0.096] (3/88) | - | - |
| T-novel | 149 (54) | 0.900 [0.821, 0.968] | 1.000 [1.000, 1.000] | 0.947 [0.902, 0.984] | 0.063 [0.020, 0.120] | 0.990 [0.976, 0.999] | 0.994 [0.986, 0.999] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] | 0.053 [-0.259, 0.330] |
| T-clean | 0.5 | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] |  |
| T-hard | khoa | 3/36 | 0.083 [0.000, 0.194] | 1/52 | 0.019 [0.000, 0.058] | 0.192 [-0.029, 0.396] |
| T-hard | 0.5 | 2/36 | 0.056 [0.000, 0.139] | 1/52 | 0.019 [0.000, 0.058] |  |
| T-novel | khoa | 6/54 | 0.111 [0.037, 0.186] | 0/41 | 0.000 [0.000, 0.000] | 0.489 [0.328, 0.625] |
| T-novel | 0.5 | 6/54 | 0.111 [0.037, 0.186] | 0/41 | 0.000 [0.000, 0.000] |  |

**T-hard - FPR theo chu ky cong cu (nguong da khoa)**

| Chu ky | n | FP | FPR [bootstrap] | Wilson 95% |
|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | 41 | 1 | 0.024 [0.000, 0.073] | [0.004, 0.126] |
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
| `netsh.exe+nslookup.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| *khong cmd.exe trong cay tien trinh* | 69 | 1 | 0.015 [0.000, 0.043] | [0.003, 0.078] |
| *co cmd.exe trong cay tien trinh* | 19 | 3 | 0.158 [0.000, 0.316] | [0.055, 0.376] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.824 [0.700, 0.925] (n=21) | 0.868 [0.755, 0.955] (n=23) | 0.889 [0.791, 0.967] (n=24) | 0.944 [0.857, 1.000] (n=17) | 1.000 [1.000, 1.000] (n=12) | 0.905 [0.854, 0.948] |
| T-novel | 0.800 [0.705, 0.886] (n=37) | 0.800 [0.700, 0.882] (n=36) | 0.767 [0.658, 0.860] (n=33) | 0.714 [0.550, 0.853] (n=16) | 1.000 [1.000, 1.000] (n=6) | 0.816 [0.756, 0.869] |

**Phat hien som** - recall cua so duong khi chi giu k event dau tinh tu event malicious dau tien (nguong da khoa, khong chon lai); 'du' = cua so day du. T1003.003: so phien phat hien.

| Tap | k | Recall [CI] | Phat hien | T1003.003 phien |
|---|---|---|---|---|
| T-clean | 4 | 0.929 [0.857, 1.000] | 39/42 | 6/6 |
| T-clean | 8 | 0.952 [0.881, 1.000] | 40/42 | 6/6 |
| T-clean | 16 | 0.976 [0.929, 1.000] | 41/42 | 6/6 |
| T-clean | 32 | 0.976 [0.929, 1.000] | 41/42 | 6/6 |
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
