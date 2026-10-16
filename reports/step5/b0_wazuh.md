### b0_wazuh

Nguong nhi phan chon tren Train OOF: **0.2667** (F1 OOF 0.869). CI bootstrap 95%, 1000 lan, seed 1337.

**Nhi phan - nguong da khoa**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 91 (45) | 0.978 [0.930, 1.000] | 1.000 [1.000, 1.000] | 0.989 [0.964, 1.000] | 0.022 [0.000, 0.075] | 0.987 [0.955, 1.000] | 0.994 [0.977, 1.000] |
| T-hard | 87 (0) | - | - | - | 0.195 [0.126, 0.276], Wilson [0.126, 0.291] (17/87) | - | - |
| T-novel | 152 (55) | 0.828 [0.734, 0.908] | 0.964 [0.909, 1.000] | 0.891 [0.826, 0.942] | 0.113 [0.059, 0.181] | 0.813 [0.714, 0.898] | 0.929 [0.889, 0.962] |

**Nhi phan - nguong 0.5**

| Tap | n (duong) | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| T-clean | 91 (45) | 1.000 [1.000, 1.000] | 0.111 [0.024, 0.206] | 0.200 [0.048, 0.342] | 0.000 [0.000, 0.000] | 0.987 [0.955, 1.000] | 0.994 [0.977, 1.000] |
| T-hard | 87 (0) | - | - | - | 0.000 [0.000, 0.000], Wilson [0.000, 0.042] (0/87) | - | - |
| T-novel | 152 (55) | - | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.813 [0.714, 0.898] | 0.929 [0.889, 0.962] |

**T-hard - FPR theo chu ky cong cu (nguong da khoa)**

| Chu ky | n | FP | FPR [bootstrap] | Wilson 95% |
|---|---|---|---|---|
| `arp.exe+ipconfig.exe+netstat.exe+route.exe` | 41 | 2 | 0.049 [0.000, 0.122] | [0.013, 0.161] |
| `arp.exe+ipconfig.exe+net.exe+net1.exe+netstat.exe+route.exe` | 12 | 1 | 0.083 [0.000, 0.250] | [0.015, 0.354] |
| `net.exe+net1.exe` | 5 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.434] |
| `ipconfig.exe+nbtstat.exe+netsh.exe+nslookup.exe` | 4 | 3 | 0.750 [0.250, 1.000] | [0.301, 0.954] |
| `ntdsutil.exe+vssadmin.exe [revert_control]` | 4 | 3 | 0.750 [0.250, 1.000] | [0.301, 0.954] |
| `net.exe+nltest.exe+ping.exe` | 3 | 2 | 0.667 [0.000, 1.000] | [0.208, 0.939] |
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
| `ntdsutil.exe+vssadmin.exe+wevtutil.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| `arp.exe+net.exe+nltest.exe+ntdsutil.exe+ping.exe+vssadmin.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| `arp.exe+net.exe+nltest.exe+ping.exe+wevtutil.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| `nbtstat.exe+netsh.exe+nslookup.exe` | 1 | 0 | 0.000 [0.000, 0.000] | [0.000, 0.793] |
| `netsh.exe+nslookup.exe` | 1 | 1 | 1.000 [1.000, 1.000] | [0.206, 1.000] |
| *khong cmd.exe trong cay tien trinh* | 69 | 3 | 0.043 [0.000, 0.101] | [0.015, 0.120] |
| *co cmd.exe trong cay tien trinh* | 18 | 14 | 0.778 [0.611, 0.944] | [0.548, 0.910] |

**Da nhan - F1 theo TTP (nguong theo TTP chon tren Train OOF)**

| Tap | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | macro-F1 |
|---|---|---|---|---|---|---|
| T-clean | 0.000 [0.000, 0.000] (n=24) | 0.000 [0.000, 0.000] (n=26) | 0.638 [0.500, 0.765] (n=27) | 0.000 [0.000, 0.000] (n=20) | 0.000 [0.000, 0.000] (n=12) | 0.128 [0.100, 0.153] |
| T-novel | 0.000 [0.000, 0.000] (n=37) | 0.000 [0.000, 0.000] (n=37) | 0.600 [0.489, 0.707] (n=34) | 0.000 [0.000, 0.000] (n=17) | 0.000 [0.000, 0.000] (n=6) | 0.120 [0.098, 0.142] |

**T1003.003 - recall muc PHIEN** (bootstrap theo phien; F1 muc cua so voi so mau nay khong co y nghia thong ke)

| Tap | Nguong | Nhi phan: phat hien | Recall [bootstrap] | Wilson 95% | Nhan T1003.003: phat hien | Recall [bootstrap] | Wilson 95% |
|---|---|---|---|---|---|---|---|
| T-novel | khoa | 5/6 | 0.833 [0.500, 1.000] | [0.436, 0.970] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
| T-novel | 0.5 | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
| T-clean | khoa | 6/6 | 1.000 [1.000, 1.000] | [0.610, 1.000] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
| T-clean | 0.5 | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] | 0/6 | 0.000 [0.000, 0.000] | [0.000, 0.390] |
