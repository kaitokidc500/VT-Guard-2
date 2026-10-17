# VT-Guard Buoc 6 moc 4 - giai thich bang attention + ONNX (chay tren host)

Brief muc 6 da SUA (2026-10-17): hat giong luat CHI tu Train (attention OOF); attention test CHI de giai thich.

**(1) Faithfulness** - cua so duong duoc VT-Seq-ens phat hien: T-clean 42/42, T-novel 54/54. Xoa top-k event theo alpha vs xoa k event ngau nhien (10 lan, cung k); muc giam p_bin va p_ttp (trung binh cac TTP that). Hieu = giam top-k - giam ngau nhien, CI bootstrap 95% (1000, theo cua so). 'Dat' = CI > 0.

| Mo hinh | k | n | p_bin: giam top-k / ngau nhien / hieu [CI] | p_ttp dung TTP: giam top-k / ngau nhien / hieu [CI] |
|---|---|---|---|---|
| ens | 1 | 96 | 0.025 / 0.001 / **+0.023** [+0.011, +0.041] dat | 0.040 / 0.002 / **+0.038** [+0.025, +0.055] dat |
| ens | 3 | 96 | 0.111 / 0.002 / **+0.109** [+0.059, +0.166] dat | 0.123 / 0.004 / **+0.119** [+0.075, +0.170] dat |
| ens | 5 | 96 | 0.230 / 0.003 / **+0.227** [+0.157, +0.304] dat | 0.234 / 0.006 / **+0.228** [+0.165, +0.298] dat |
| s1337 | 1 | 96 | 0.006 / 0.000 / **+0.006** [+0.001, +0.014] dat | 0.018 / 0.001 / **+0.018** [+0.012, +0.025] dat |
| s1337 | 3 | 96 | 0.108 / 0.001 / **+0.108** [+0.050, +0.177] dat | 0.115 / 0.002 / **+0.113** [+0.061, +0.176] dat |
| s1337 | 5 | 96 | 0.206 / 0.001 / **+0.206** [+0.133, +0.287] dat | 0.221 / 0.002 / **+0.219** [+0.151, +0.292] dat |
| s7 | 1 | 96 | 0.017 / 0.001 / **+0.016** [-0.006, +0.048] KHONG dat | 0.025 / 0.000 / **+0.025** [+0.004, +0.052] dat |
| s7 | 3 | 96 | 0.174 / 0.002 / **+0.172** [+0.106, +0.246] dat | 0.163 / 0.002 / **+0.162** [+0.106, +0.224] dat |
| s7 | 5 | 96 | 0.295 / 0.004 / **+0.291** [+0.212, +0.376] dat | 0.283 / 0.004 / **+0.279** [+0.211, +0.357] dat |
| s42 | 1 | 96 | 0.018 / 0.000 / **+0.017** [+0.005, +0.039] dat | 0.035 / 0.001 / **+0.035** [+0.018, +0.057] dat |
| s42 | 3 | 96 | 0.082 / 0.001 / **+0.081** [+0.036, +0.132] dat | 0.096 / 0.004 / **+0.092** [+0.051, +0.139] dat |
| s42 | 5 | 96 | 0.299 / 0.002 / **+0.297** [+0.211, +0.386] dat | 0.295 / 0.006 / **+0.289** [+0.212, +0.367] dat |
| s2024 | 1 | 96 | 0.021 / 0.001 / **+0.021** [+0.004, +0.043] dat | 0.033 / 0.002 / **+0.032** [+0.013, +0.054] dat |
| s2024 | 3 | 96 | 0.098 / 0.002 / **+0.095** [+0.048, +0.149] dat | 0.124 / 0.005 / **+0.119** [+0.079, +0.169] dat |
| s2024 | 5 | 96 | 0.212 / 0.002 / **+0.210** [+0.141, +0.287] dat | 0.215 / 0.007 / **+0.208** [+0.153, +0.270] dat |
| s99 | 1 | 96 | 0.042 / 0.003 / **+0.039** [+0.014, +0.072] dat | 0.066 / 0.004 / **+0.061** [+0.033, +0.096] dat |
| s99 | 3 | 96 | 0.144 / 0.004 / **+0.140** [+0.080, +0.210] dat | 0.166 / 0.008 / **+0.158** [+0.105, +0.219] dat |
| s99 | 5 | 96 | 0.395 / 0.005 / **+0.390** [+0.302, +0.481] dat | 0.387 / 0.010 / **+0.377** [+0.302, +0.455] dat |

**(2) Hat giong luat theo TTP - CHI Train, attention OOF** (alpha tu mo hinh fold khong thay cua so, trung binh 5 seed; mo hinh fold huan luyen lai tren host, tuong quan diem OOF voi Colab 0.991-0.999). Top-5 event/cua so; pos/neg = ti le cua so Train duong (TTP) / am co gia tri trong top-5; lift = pos/neg. Day du: `reports/step6/rule_seeds_train.json`.

- **T1016** (85 cua so; top-5 tu event cay 97% / nen 3%)
  - image_name: `cmd.exe` 0.87/0.08 (lift 11.14); `nslookup.exe` 0.34/0.02 (lift 20.95); `net.exe` 0.40/0.18 (lift 2.27); `wevtutil.exe` 0.21/0.01 (lift 21.67); `net1.exe` 0.25/0.15 (lift 1.65); `powershell.exe` 0.14/0.00 (lift 43.34)
  - event_id: `1` 0.99/0.79 (lift 1.25); `4688` 0.80/0.67 (lift 1.2); `5` 0.15/0.25 (lift 0.62); `40961` 0.08/0.00 (lift 25.28); `4104` 0.05/0.00 (lift 14.45); `53504` 0.02/0.00 (lift 7.22)
  - cmd_token: `/c` 0.83/0.09 (lift 9.86); `cmd` 0.83/0.07 (lift 11.15); `net` 0.53/0.18 (lift 2.9); `0` 0.43/0.16 (lift 2.67); `-querytype` 0.33/0.00 (lift 101.13); `-timeout` 0.33/0.00 (lift 101.13)
- **T1018** (78 cua so; top-5 tu event cay 96% / nen 4%)
  - image_name: `cmd.exe` 0.80/0.08 (lift 10.17); `net.exe` 0.37/0.18 (lift 2.11); `nslookup.exe` 0.22/0.02 (lift 13.38); `net1.exe` 0.23/0.15 (lift 1.54); `wevtutil.exe` 0.13/0.01 (lift 13.12); `ping.exe` 0.20/0.01 (lift 20.99)
  - event_id: `1` 0.99/0.79 (lift 1.25); `4688` 0.74/0.67 (lift 1.11); `5` 0.20/0.25 (lift 0.83); `4104` 0.04/0.00 (lift 11.81); `3` 0.05/0.30 (lift 0.17); `40961` 0.03/0.00 (lift 7.87)
  - cmd_token: `/c` 0.74/0.09 (lift 8.78); `cmd` 0.74/0.07 (lift 9.93); `net` 0.46/0.18 (lift 2.53); `/domain` 0.41/0.17 (lift 2.47); `0` 0.42/0.16 (lift 2.6); `group` 0.29/0.13 (lift 2.21)
- **T1087.002** (95 cua so; top-5 tu event cay 96% / nen 4%)
  - image_name: `cmd.exe` 0.74/0.08 (lift 9.43); `powershell.exe` 0.26/0.00 (lift 80.79); `nslookup.exe` 0.21/0.02 (lift 12.93); `net.exe` 0.40/0.18 (lift 2.27); `<none>` 0.25/0.10 (lift 2.59); `net1.exe` 0.26/0.15 (lift 1.76)
  - event_id: `1` 0.99/0.79 (lift 1.25); `4688` 0.74/0.67 (lift 1.1); `40961` 0.21/0.00 (lift 64.63); `4104` 0.14/0.00 (lift 42.01); `5` 0.17/0.25 (lift 0.68); `53504` 0.06/0.00 (lift 19.39)
  - cmd_token: `/c` 0.70/0.09 (lift 8.33); `cmd` 0.70/0.07 (lift 9.41); `net` 0.52/0.18 (lift 2.83); `/domain` 0.42/0.17 (lift 2.53); `user` 0.55/0.13 (lift 4.1); `group` 0.27/0.13 (lift 2.05)
- **T1654** (83 cua so; top-5 tu event cay 97% / nen 3%)
  - image_name: `cmd.exe` 0.76/0.08 (lift 9.71); `powershell.exe` 0.22/0.00 (lift 66.58); `wevtutil.exe` 0.28/0.01 (lift 28.36); `nslookup.exe` 0.20/0.02 (lift 12.58); `net.exe` 0.31/0.18 (lift 1.78); `net1.exe` 0.23/0.15 (lift 1.53)
  - event_id: `1` 0.99/0.79 (lift 1.25); `4688` 0.84/0.67 (lift 1.26); `5` 0.20/0.25 (lift 0.83); `40961` 0.16/0.00 (lift 48.08); `4104` 0.10/0.00 (lift 29.59); `3` 0.01/0.30 (lift 0.04)
  - cmd_token: `/c` 0.72/0.09 (lift 8.54); `cmd` 0.72/0.07 (lift 9.65); `enum-logs` 0.30/0.00 (lift 92.47); `wevtutil` 0.30/0.01 (lift 30.82); `net` 0.41/0.18 (lift 2.25); `/domain` 0.35/0.17 (lift 2.1)
- **T1003.003** (42 cua so; top-5 tu event cay 66% / nen 34%)
  - image_name: `ntdsutil.exe` 0.81/0.00 (lift 248.52); `cmd.exe` 0.86/0.08 (lift 10.96); `<none>` 0.69/0.10 (lift 7.07); `vssadmin.exe` 0.07/0.03 (lift 2.44); `rundll32.exe` 0.12/0.01 (lift 12.18); `vssvc.exe` 0.12/0.00 (lift 36.55)
  - event_id: `1` 0.69/0.79 (lift 0.87); `22` 0.74/0.15 (lift 5.04); `4688` 0.52/0.67 (lift 0.78); `5` 0.45/0.25 (lift 1.83); `216` 0.31/0.00 (lift 95.02); `103` 0.29/0.00 (lift 87.71)
  - cmd_token: `c` 0.71/0.04 (lift 19.94); `create` 0.59/0.00 (lift 182.74); `\windows\temp\ntds_t0` 0.52/0.00 (lift 160.81); `ac` 0.52/0.01 (lift 53.6); `full` 0.52/0.00 (lift 160.81); `i` 0.52/0.11 (lift 4.73)

**Canh bao cho Buoc 7 (khong dung truc tiep lam luat):**
- `\windows\temp\ntds_t0` = duong dan mac dinh cua ART (`ntds_T1003`), chua ma ky thuat -> dau vet bo sinh; loai khoi hat giong.
- `cmd.exe` / `cmd /c` dung dau moi TTP: ART chay qua cmd (cmd.exe chi o 8% cua so am Train) - bat doi xung bo sinh da biet (#9); luat phai dua tren lenh con, khong dua tren vo cmd.
- Attention dung chung cho moi TTP (mot pooling): cua so nhieu TTP (phien mixed) lam token cua TTP khac xuat hien (vd nslookup o moi TTP) -> Buoc 7 can do do dac hieu theo TTP (cua so mot TTP / so voi cua so TTP khac).
- T1003.003: 34% top-5 la event NEN (ESENT 216/103, vssvc, rundll32) - tac dong phu mot-phia (#10/#11); luat nen dua tren ntdsutil `ifm create full`, khong tren event nen.
- T1087.002: token dau la `powershell.exe` (lift ~81) va EID 40961/4104 - dau vet bo sinh (ART chay test trong powershell con; gioi han `<launcher>`->powershell.exe da biet, dataset card #11). Luat T1087.002 phai dua tren lenh that (`net user /domain`, `adsisearcher`, `objectcategory`), khong dua tren su hien dien cua PowerShell.

**(3) ONNX** (opset 17, truc dong batch + time; dau ra p_bin, p_ttp, alpha). Parity voi PyTorch (ban pack) tren toan T-novel; do tre onnxruntime 1.31.0 CPU 1 thread tren host (Intel64 Family 6 Model 158 Stepping 13, GenuineIntel).

| Mo hinh | File | So mang | max abs diff p_bin / p_ttp / alpha | Parity < 1e-4 | batch 1: ms/cua so (TB / p95) | batch 32: ms/cua so (TB / p95) |
|---|---|---|---|---|---|---|
| vtseq_M3_s1337 | `models/vtseq_M3_s1337.onnx` (0.40 MB) | 1 | 1.2e-07 / 1.8e-07 / 6.6e-07 | dat | 0.326 / 0.439 | 0.197 / 0.204 |
| vtseq_M3_ens | `models/vtseq_M3_ens.onnx` (2.01 MB) | 5 | 1.8e-07 / 1.8e-07 / 3.3e-07 | dat | 1.435 / 1.854 | 0.993 / 1.012 |
