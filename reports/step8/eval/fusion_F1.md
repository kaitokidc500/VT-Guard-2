### fusion_F1 (dataset-v1.2)

Nguong nhi phan chon tren Train OOF: **0.5000** (F1 OOF 0.821). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 0.786 [0.651, 0.906] | 0.880 [0.789, 0.951] | 0.000 [0.000, 0.000] | 0.887 [0.809, 0.953] | 0.893 [0.826, 0.953] |
| T-hard | 88 (0) | - | - | - | 0.000 [0.000, 0.000], Wilson [0.000, 0.042] (0/88) | - | - |
| T-novel | 149 (54) | 0.977 [0.923, 1.000] | 0.796 [0.679, 0.902] | 0.878 [0.796, 0.942] | 0.011 [0.000, 0.033] | 0.852 [0.763, 0.928] | 0.893 [0.833, 0.946] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 89 (42) | 1.000 [1.000, 1.000] | 0.786 [0.651, 0.906] | 0.880 [0.789, 0.951] | 0.000 [0.000, 0.000] | 0.887 [0.809, 0.953] | 0.893 [0.826, 0.953] |
| T-hard | 88 (0) | - | - | - | 0.000 [0.000, 0.000], Wilson [0.000, 0.042] (0/88) | - | - |
| T-novel | 149 (54) | 0.977 [0.923, 1.000] | 0.796 [0.679, 0.902] | 0.878 [0.796, 0.942] | 0.011 [0.000, 0.033] | 0.852 [0.763, 0.928] | 0.893 [0.833, 0.946] |

**FPR phan tang theo do dai cua so** (chi cua so am; n_events chi dung de phan tang bao cao, khong la feature) va Spearman diem ~ n_events tren cua so am (confounder da biet, khong phai bang chung mo hinh hoc do dai)

| Tap | Nguong | Du 64: FP/n | FPR du 64 [CI] | Ngan: FP/n | FPR ngan [CI] | Spearman(diem, n_events | am) [CI] |
|---|---|---|---|---|---|---|
| T-clean | khoa | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] | - |
| T-clean | 0.5 | 0/23 | 0.000 [0.000, 0.000] | 0/24 | 0.000 [0.000, 0.000] |  |
| T-hard | khoa | 0/36 | 0.000 [0.000, 0.000] | 0/52 | 0.000 [0.000, 0.000] | - |
| T-hard | 0.5 | 0/36 | 0.000 [0.000, 0.000] | 0/52 | 0.000 [0.000, 0.000] |  |
| T-novel | khoa | 1/54 | 0.018 [0.000, 0.056] | 0/41 | 0.000 [0.000, 0.000] | 0.085 [0.071, 0.164] |
| T-novel | 0.5 | 1/54 | 0.018 [0.000, 0.056] | 0/41 | 0.000 [0.000, 0.000] |  |

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
| T-clean | 0.000 [0.000, 0.000] (n=21) | 0.516 [0.285, 0.718] (n=23) | 0.000 [0.000, 0.000] (n=24) | 0.640 [0.375, 0.833] (n=17) | 0.800 [0.571, 0.957] (n=12) | 0.391 [0.319, 0.448] |
| T-novel | 0.000 [0.000, 0.000] (n=37) | 0.468 [0.270, 0.634] (n=36) | 0.000 [0.000, 0.000] (n=33) | 0.615 [0.353, 0.800] (n=16) | 1.000 [1.000, 1.000] (n=6) | 0.417 [0.354, 0.468] |

**Phat hien som** - recall cua so duong khi chi giu k event dau tinh tu event malicious dau tien (nguong da khoa, khong chon lai); 'du' = cua so day du. T1003.003: so phien phat hien.

| Tap | k | Recall [CI] | Phat hien | T1003.003 phien |
|---|---|---|---|---|
| T-clean | 4 | 0.548 [0.405, 0.691] | 23/42 | 6/6 |
| T-clean | 8 | 0.571 [0.429, 0.714] | 24/42 | 6/6 |
| T-clean | 16 | 0.571 [0.429, 0.714] | 24/42 | 6/6 |
| T-clean | 32 | 0.667 [0.524, 0.809] | 28/42 | 6/6 |
| T-clean | du | 0.786 [0.651, 0.906] | 33/42 | 6/6 |
| T-novel | 4 | 0.704 [0.593, 0.815] | 38/54 | 6/6 |
| T-novel | 8 | 0.704 [0.593, 0.815] | 38/54 | 6/6 |
| T-novel | 16 | 0.722 [0.611, 0.833] | 39/54 | 6/6 |
| T-novel | 32 | 0.741 [0.630, 0.852] | 40/54 | 6/6 |
| T-novel | du | 0.796 [0.679, 0.902] | 43/54 | 6/6 |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-novel | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
| T-clean | 0.5 | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] |
