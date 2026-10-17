# VT-Guard Buoc 8 moc 3 - canh bao giai thich duoc + pipeline suy luan dau-cuoi

Pipeline `src/pipeline/infer.py`: cua so -> featurize (vocab dong bang Buoc 4) -> ONNX VT-Seq-ens (`models/vtseq_M3_ens.onnx`) -> matcher Sigma (`rules/sigma/*.yml`) -> fusion F3-B khoa (`reports/step8/final_fusion.json`, commit 3fd9531) -> canh bao. Canh bao: `reports/step8/alerts_<split>.jsonl` (schema muc 6).

## 1. Kiem trung voi ket qua cham (reports/preds/fusion_<split>.jsonl)

| Tap | Cua so | Dac trung != file split | Lech quyet dinh nhi phan | Lech quyet dinh TTP | Lech kenh luat r | Diem lech toi da |
|---|---|---|---|---|---|---|
| t_clean | 89 | 0 | 0 | 0 | 0 | 6.1e-07 |
| t_hard | 88 | 0 | 0 | 0 | 0 | 5.7e-07 |
| t_novel | 149 | 0 | 0 | 0 | 0 | 5.6e-07 |

Diem lech <= 6e-7: ONNX (host CPU) so voi PyTorch (Colab CUDA) va lam tron 6 chu so cua file preds; khong quyet dinh nao doi.

## 2. Thong ke giai thich

decision_source: `both` = AI vuot nguong va co luat khop; `ai` = AI vuot nguong, khong luat; `rule` = AI duoi nguong, canh bao chi nho +0.1 cua luat. F3-B KHONG phai OR: luat khop ma p + 0.1 < nguong thi khong canh bao.

| Tap | Canh bao | Co >= 1 luat khop | TP: n / co luat | FP: n / co luat | decision_source (tat ca) | Luat khop nhung khong canh bao | Duong bi bo sot |
|---|---|---|---|---|---|---|---|
| t_clean | 42 | 33 (79%) | 42 / 33 (79%) | 0 / 0 | {'both': 33, 'ai': 9} | 0 | 0 |
| t_hard | 1 | 0 (0%) | 0 / 0 | 1 / 0 (0%) | {'ai': 1} | 0 | 0 |
| t_novel | 58 | 43 (74%) | 54 / 43 (80%) | 4 / 0 (0%) | {'both': 43, 'ai': 15} | 1 | 0 |

Gop 3 tap: 76/101 canh bao (75%) co it nhat mot luat giai thich; rieng canh bao dung (TP) 76/96 (79%); canh bao nham (FP) 0/5 co luat. Moi canh bao deu co top-5 event attention. Khong co canh bao nao chi do luat (`rule`) tren test.

## 3. Vi du (chon tat dinh: window_id nho nhat cua moi loai)

**Canh bao chi do luat:** khong co tren 3 tap test (moi cua so co luat khop va duoc canh bao deu da vuot nguong AI).

**Canh bao chi do AI** - `20261014-043324-win10-01-a:w00032` (t_clean, nhan: doc hai ['T1016', 'T1087.002']); canh bao: score 0.9975 (p_ai 0.9975, nguong 0.8692), decision_source `ai`, TTP du doan ['T1016', 'T1018', 'T1087.002', 'T1654'], luat khop: khong co

| # | alpha | image | parent | event_id | lenh (canon) |
|---|---|---|---|---|---|
| 2 | 0.318 | cmd.exe | <launcher> | 1 | `cmd /c ipconfig /all netsh interface show interface arp -a nbtstat -n net config` |
| 16 | 0.234 | net.exe | <launcher> | 1 | `net  config` |
| 13 | 0.163 | nbtstat.exe | <launcher> | 1 | `nbtstat  -n` |
| 18 | 0.092 | net1.exe | net.exe | 1 | `net1  config` |
| 17 | 0.047 | net1.exe | net.exe | 4688 | `net1  config` |

**Canh bao do ca hai** - `20261014-043324-win10-01-a:w00000` (t_clean, nhan: doc hai ['T1016', 'T1087.002']); canh bao: score 1.0966 (p_ai 0.9966, nguong 0.8692), decision_source `both`, TTP du doan ['T1016', 'T1087.002', 'T1654'], luat khop: `VTR-BIN-04` (`rules/sigma/VTR-BIN-04.yml`)

| # | alpha | image | parent | event_id | lenh (canon) |
|---|---|---|---|---|---|
| 34 | 0.249 | cmd.exe | <launcher> | 1 | `cmd /c ipconfig /all netsh interface show interface arp -a nbtstat -n net config` |
| 48 | 0.135 | net.exe | <launcher> | 1 | `net  config` |
| 10 | 0.110 | &lt;unknown process&gt; | None | 22 | `-` |
| 45 | 0.085 | nbtstat.exe | <launcher> | 1 | `nbtstat  -n` |
| 1 | 0.081 | powershell.exe | <launcher> | 1 | `powershell {([adsisearcher]\""objectcategory=user\"").FindAll(); ([adsisearcher]\""objectcategory=user\"").Fin` |

**Luat khop nhung F3-B KHONG canh bao (luat bao nham, AI chan)** - `20261014-150302-win10-01-a:w00224` (t_novel, nhan: LANH TINH); KHONG canh bao: score 0.8383 (p_ai 0.7383, nguong 0.8692), decision_source `None`, TTP du doan ['T1016', 'T1087.002'], luat khop: `VTR-T1654-01` (`rules/sigma/VTR-T1654-01.yml`)

| # | alpha | image | parent | event_id | lenh (canon) |
|---|---|---|---|---|---|
| 54 | 0.255 | auditpol.exe | wazuh-agent.exe | 1 | `auditpol /get /subcategory:"System Integrity"` |
| 51 | 0.221 | auditpol.exe | wazuh-agent.exe | 1 | `auditpol /get /subcategory:"Security System Extension"` |
| 53 | 0.032 | auditpol.exe | wazuh-agent.exe | 4688 | `auditpol /get /subcategory:"System Integrity"` |
| 55 | 0.031 | auditpol.exe | None | 5 | `-` |
| 48 | 0.030 | auditpol.exe | wazuh-agent.exe | 1 | `auditpol /get /subcategory:"Security State Change"` |

**Canh bao NHAM tren T-hard** - `20261015-122705-win10-01-h:w00015` (t_hard, nhan: LANH TINH); canh bao: score 0.9339 (p_ai 0.9339, nguong 0.8692), decision_source `ai`, TTP du doan ['T1016'], luat khop: khong co

| # | alpha | image | parent | event_id | lenh (canon) |
|---|---|---|---|---|---|
| 34 | 0.117 | cmd.exe | <launcher> | 1 | `cmd /c netsh interface show interface  ` |
| 36 | 0.109 | netsh.exe | <launcher> | 1 | `netsh  interface show interface` |
| 49 | 0.098 | cmd.exe | <launcher> | 1 | `cmd /c nbtstat -n  ` |
| 51 | 0.069 | nbtstat.exe | <launcher> | 1 | `nbtstat  -n` |
| 53 | 0.057 | cmd.exe | None | 5 | `-` |

## 4. Do tre dau-cuoi (host CPU, onnxruntime 1 thread)

CPU: Intel64 Family 6 Model 158 Stepping 13, GenuineIntel; onnxruntime 1.31.0; 326 cua so test; cache hash dong lenh xoa truoc moi luot. ms moi cua so (batch 32: thoi gian mot lo chia so cua so).

| Buoc | batch 1: TB | batch 1: p95 | batch 32: TB | batch 32: p95 |
|---|---|---|---|---|
| total | 2.773 | 5.973 | 2.123 | 3.059 |
| featurize | 0.860 | 3.436 | 0.779 | 1.414 |
| onnx | 1.460 | 1.884 | 0.955 | 1.025 |
| sigma | 0.400 | 0.866 | 0.372 | 0.666 |
| fusion | 0.025 | 0.030 | 0.003 | 0.005 |
