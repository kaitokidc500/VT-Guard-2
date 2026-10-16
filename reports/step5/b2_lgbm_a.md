### b2_lgbm_a (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.6673** (F1 OOF 0.986). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 0.952 [0.881, 1.000] | 0.976 [0.937, 1.000] | 0.000 [0.000, 0.000] | 0.999 [0.995, 1.000] | 0.999 [0.995, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.011 [0.000, 0.034], Wilson [0.002, 0.062] (1/88) | - | - |
| T-novel | 149 (54) | 0.927 [0.855, 0.983] | 0.944 [0.875, 1.000] | 0.936 [0.882, 0.979] | 0.042 [0.010, 0.087] | 0.990 [0.975, 0.999] | 0.995 [0.986, 0.999] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 0.952 [0.881, 1.000] | 0.976 [0.937, 1.000] | 0.000 [0.000, 0.000] | 0.999 [0.995, 1.000] | 0.999 [0.995, 1.000] |
| T-hard | 88 (0) | - | - | - | 0.011 [0.000, 0.034], Wilson [0.002, 0.062] (1/88) | - | - |
| T-novel | 149 (54) | 0.930 [0.862, 0.983] | 0.982 [0.936, 1.000] | 0.955 [0.912, 0.990] | 0.042 [0.010, 0.087] | 0.990 [0.975, 0.999] | 0.995 [0.986, 0.999] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] | -0.088 [-0.375, 0.203] |
| T-clean | 0.5 | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] |  |
| T-hard | khoa | 1/36 | 0.028 [0.000, 0.083] | 0/52 | 0.000 [0.000, 0.000] | 0.016 [-0.196, 0.253] |
| T-hard | 0.5 | 1/36 | 0.028 [0.000, 0.083] | 0/52 | 0.000 [0.000, 0.000] |  |
| T-novel | khoa | 4/54 | 0.074 [0.018, 0.148] | 0/41 | 0.000 [0.000, 0.000] | 0.289 [0.104, 0.469] |
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
| `ipconfig.exe+netsh.exe` | 2 | 1 | 0.500 [0.000, 1.000] | [0.095, 0.905] |
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
| *co cmd.exe trong cay tien trinh* | 19 | 1 | 0.053 [0.000, 0.158] | [0.009, 0.246] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.909 [0.812, 0.980] (n=21) | 0.684 [0.500, 0.829] (n=23) | 0.939 [0.864, 1.000] (n=24) | 0.857 [0.706, 0.963] (n=17) | 1.000 [1.000, 1.000] (n=12) | 0.878 [0.822, 0.923] |
| T-novel | 0.833 [0.727, 0.914] (n=37) | 0.831 [0.733, 0.907] (n=36) | 0.756 [0.643, 0.849] (n=33) | 0.588 [0.423, 0.735] (n=16) | 1.000 [1.000, 1.000] (n=6) | 0.802 [0.753, 0.846] |

**Phat hien som** - recall cua so duong khi chi giu k event dau tinh tu event malicious dau tien (nguong da khoa, khong chon lai); 'du' = cua so day du. T1003.003: so phien phat hien.

| Tap | k | Recall [CI] | Phat hien | T1003.003 phien |
|---|---|---|---|---|
| T-clean | 4 | 0.714 [0.571, 0.857] | 30/42 | 5/6 |
| T-clean | 8 | 0.786 [0.667, 0.905] | 33/42 | 5/6 |
| T-clean | 16 | 0.809 [0.691, 0.929] | 34/42 | 5/6 |
| T-clean | 32 | 0.833 [0.714, 0.929] | 35/42 | 5/6 |
| T-clean | du | 0.952 [0.881, 1.000] | 40/42 | 5/6 |
| T-novel | 4 | 0.907 [0.833, 0.982] | 49/54 | 1/6 |
| T-novel | 8 | 0.852 [0.759, 0.944] | 46/54 | 0/6 |
| T-novel | 16 | 1.000 [1.000, 1.000] | 54/54 | 6/6 |
| T-novel | 32 | 0.926 [0.852, 0.982] | 50/54 | 2/6 |
| T-novel | du | 0.944 [0.875, 1.000] | 51/54 | 4/6 |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 4/6 | 0.667 [0.333, 1.000] | [0.300, 0.903] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-novel | 0.5 | 5/6 | 0.833 [0.500, 1.000] | [0.436, 0.970] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | khoa | 5/6 | 0.833 [0.500, 1.000] | [0.436, 0.970] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | 0.5 | 5/6 | 0.833 [0.500, 1.000] | [0.436, 0.970] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
