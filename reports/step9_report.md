# VT-Guard - Bao cao Buoc 9: Dashboard SOC + luong truc tiep + dong goi Docker

Dac ta: `docs/STEP9-BRIEF.md`. Buoc 9 KHONG huan luyen them, KHONG doi ket qua nao: moi so lieu chinh thuc van la ket qua tren
tap test dong bang (`dataset-v1.2`, Buoc 5-8). Anh chup: `reports/step9/screenshots/`.

## 0. Tom tat

- **Dashboard tieng Viet, 5 trang, 2 phan** (`dashboard/`, Streamlit): Phan A SIEM thoi gian thuc (Truc tiep - Hang doi, Chi tiet,
  Dong thoi gian; khong nhan) va Phan B Ket qua nghien cuu (Ket qua & danh gia lam noi 3 yeu cau de tai, Luat Sigma tu sinh; co nhan).
  31/31 test (`dashboard/test_data.py`): moi con so tren man hinh trung artefact Buoc 5-8 (0 lech).
- **Luong truc tiep (kieu B)** (`src/live/`): connector Indexer `wazuh-archives-*` (hoac phat lai file) -> bo chia cua so theo
  host + thoi gian (tien xu ly GIONG dataset-v1.2) -> nguyen `src/pipeline/infer.py` (ONNX VT-Seq-ens -> Sigma -> F3-B khoa) ->
  `reports/step9/live/alerts.jsonl` -> trang Truc tiep tu lam moi. Tuy chon ghi nguoc `vtguard-alerts-*`. 8/8 test
  (`src/live/test_live.py`).
- **Phat lai log mau** (`samples/replay_demo.jsonl.gz`, 31 054 event): 58 cua so -> 17 canh bao (13 `both`, 4 `ai`), phu ca 5 TTP.
- **Do lech truc tiep <-> offline** (batch05 = T-novel): bao phu 52/52 cua so canh bao offline, 40/41 canh bao truc tiep giao
  cua so canh bao offline; canh bao sai tren phan lanh tinh 4/90 (4,4%) - bang dung so offline cua cung dot (4/95).
- **Docker kieu A**: image `vtguard:step9` (linux/amd64); `verify` chay voi `--network none` **DAT 7/7** (0 lech so voi bao cao);
  `selftest` DAT; quet image 0 checkpoint / 0 log tho ngoai log mau / 0 thong tin dang nhap.
- **Chua lam (can lab):** moc 4 - chay `live` noi Indexer that + kich ban demo muc 4 + anh Wazuh <-> VT-Guard song song.

## 1. Dashboard: 5 trang, HAI PHAN

Dashboard tach ro hai muc dich (thay cho cong tac "che do danh gia" cua moc 1-2):

| Phan | Trang | Thong diep | Du lieu | Nhan |
|---|---|---|---|---|
| **A - SIEM thoi gian thuc** | Truc tiep - Hang doi (man hinh chinh) | dai so (gop Tong quan cu), ha tang agent -> Indexer -> VT-Guard, luu luong event, dong ho do tre, MITRE, hang doi tu lam moi + loc / sap / xuat CSV; nut phat lai log mau | luong live / replay (`reports/step9/live/`) | khong |
| A | Chi tiet canh bao (triage) | dai "3 yeu cau de tai tren canh bao nay"; diem AI vs nguong (YC3), luat Sigma + YAML + xuat xu (YC1), nguon quyet dinh (YC2), top-5 attention | luong truc tiep (mac dinh) hoac tap test | chi khi chon tap test |
| A | Dong thoi gian su co | su co LINC = canh bao cung host cach nhau <= 15 phut; kill chain MITRE + Gantt | luong truc tiep | khong |
| **B - Ket qua nghien cuu** | Ket qua & danh gia | 3 the yeu cau de tai (YC1 11 luat, 0/88 FP; YC2 76/76 dung khi ca hai nguon, hon chi-luat sau Holm; YC3 0,817 macro-F1 TTP, hon GRU tron sau Holm) + tab: VT-Guard so voi Wazuh (F1 theo ky thuat), YC3, YC2, so sanh mo hinh, 101 canh bao test co nhan, tai lap (verify / Docker / do lech) + tieu chi | results / eval JSON Buoc 5-8 | co |
| B | Luat Sigma tu sinh | 11 luat, TP/FP theo tap, provenance, cong chat luong, YAML, tai ca bo | step7 | co |

- **Tuong phan voi Wazuh lay tu B0 that** (trang B, tab dau): luat Wazuh co san KHONG gan duoc 4/5 ky thuat (T1016, T1018, T1654,
  T1003.003: F1 = 0 tren T-novel), van bat "co gi do bat thuong" (F1 nhi phan 0,898) nhung 17/88 canh bao nham tren quan tri hop le.
- Phan A khong bao gio hien nhan / id cua so tap test (test 8); Phan B doc nguyen so lieu da cham (test 2-4, 9, 11 so voi results JSON
  + report Markdown, 0 lech). Thanh cong cu tieng Anh mac dinh cua Streamlit (bang / bieu do) da an; xuat CSV bang nut tieng Viet.
- Kiem thu `dashboard/test_data.py`: **31/31** (luong truc tiep tu fixture `dashboard/fixtures/` = 17 canh bao phat lai, de chay
  duoc trong container).

## 2. Luong truc tiep (moc 3)

`python src/live/run.py live --env-file <file> [--push-alerts]` / `replay --input <log> [--speed k]`.

- **Connector** (`connector.py`): truy van giong `scripts/export_batch.py` (term `agent.name` + range `timestamp`, sap tang), chi lay phan
  SAU moc da doc; moc + id event tai moc luu `connector_state.json` (khoi dong lai khong doc trung). Dang nhap chi qua bien moi truong /
  `--env-file` mount tu ngoai; bat buoc CA (hoac `VTG_INDEXER_INSECURE=1` chi trong lab). `FileSource` phat lai theo `timestamp`
  Wazuh, cung chu ky poll; `--speed k` chi ngu o chu ky co event, tua nhanh khoang im lang dai (dong ho luong khong doi -> ket qua
  giong het speed 0, test L1b).
- **Windower** (`windower.py`): gom theo host, toi da 64 event; dong khi du 64 / host im lang > 30 s / khoang trong su kien > 120 s /
  het luong. Tien xu ly = dung quy tac dataset-v1.2 (normalize v1, manh vo 4103, khu trung lap, upload manifest, tien trinh khung ART
  qua script block, conhost, `<launcher>`), goi lai nguyen ham cua `normalize.py` / `label.py` / `windows.py`. Khong tai hien duoc
  `orch_child_outside` (can khung phien manifest).
- **Ban ghi canh bao** = schema Buoc 8 (`Pipeline.alert_record`) + `mode`, `closed_at`, `ingest_first/last`, `n_events`,
  `close_reason`, `p_ttp_ai`, `score_ttp`, `latency` (wazuh_s, wait_s, infer_ms, total_s). Khong co truong nhan.

**Phat lai log mau** (`samples/replay_demo.jsonl.gz`: batch05 13:33-13:58 UTC quan tri lanh tinh + discovery, ntds2v 08:47-08:56 UTC
T1003.003; cat nguyen van tu `data/raw`, khong sua event): 31 054 event -> 58 cua so -> **17 canh bao** (DC01 11, WIN10-01 6;
`both` 13, `ai` 4). TTP du doan: T1016 13, T1087.002 13, T1654 13, T1018 9, T1003.003 4. Luat khop nhieu nhat: VTR-BIN-01/02,
VTR-T1003003-01 (4 lan moi luat). Do tre (trung vi, dong ho luong): Wazuh nhan log 1,9 s; chu ky doc + cho dong cua so 2,5 s;
suy luan 2,95 ms/cua so. Mot canh bao co `wazuh_s` 3 672 s: dong ho DC01 lech sau khoi phuc snapshot (da biet tu Buoc 4), khong
phai do tre that. Tren lab that cong them chu ky doc 12 s va nguong im lang 30 s -> uoc tinh ~1 phut nhu brief muc 2.2.

**Do lech truc tiep <-> offline** (`src/live/drift.py`, `reports/step9/live/drift_report.json`; batch05 = toan bo T-novel,
143 cua so offline, 52 canh bao offline):

| Cach hieu quy tac tien trinh khung ART | Cua so | Canh bao | Offline duoc phu | Truc tiep giao offline | Jaccard event | Canh bao sai / cua so lanh tinh | Offline cung dot |
|---|---|---|---|---|---|---|---|
| **orchestrator (mac dinh)** | 129 | 41 | 52/52 (100%) | 40/41 (97,6%) | 0,688 | 4/90 (4,4%) | 4/95 |
| console | 111 | 6 | 10/52 (19,2%) | 5/6 (83,3%) | 0,137 | 5/109 (4,6%) | 4/95 |

- Lech tien xu ly (mac dinh): 7 060 event truc tiep giu; 7 054 trung dataset, 6 la event dataset loai theo PID orchestrator
  (exclude_pids trong manifest, khong co luc chay that); 0 event dataset giu ma truc tiep loai.
- Che do `console` loai ca con truc tiep cua tien trinh khung -> mat phan lon hanh vi tan cong (1 171 event dataset giu bi loai)
  -> chi phu 19% canh bao offline. Vi vay mac dinh `orchestrator` (giong labeler cho executor-root). Khi demo that, tan cong chay
  qua ART tu console thuong: can do lai sau moc 4.
- Han che: cua so truc tiep chia theo thoi gian (khong chong lan) khac cua so offline (truot 64/32 trong khung phien) -> Jaccard
  event 0,69; so lieu chinh thuc van la ket qua tap test dong bang.

## 3. Docker kieu A (moc 5)

| Muc | Ket qua |
|---|---|
| Image | `vtguard:step9`, python:3.12-slim + onnxruntime 1.31.0, numpy 2.5.3, pandas 3.0.6, PyYAML 6.0.3, streamlit 1.66.0 (khong PyTorch); ghim `docker/requirements.lock`, ban day du `docker/requirements.freeze.txt` |
| Noi dung | dung tu danh sach cho phep (`docker/stage.py`), sha256 tung file o `docker/MANIFEST.json`: ma `src/` + `dashboard/`, ONNX ens, 11 Sigma, splits + vocab dataset-v1.2, `windows.jsonl` CHI 326 cua so test, `reports/`, 1 log mau |
| `verify --network none` | **DAT 7/7** (V1 checksum dataset, V2 ONNX + 27 artefact, V3 featurize, V4 0 quyet dinh lech / diem lech <= 6,1e-7, V5 101 canh bao, V6 evaluate gom CI bootstrap trung eval Buoc 8, V7 TP/FP/FN B0 / VT-Seq-ens / chi-luat) - trung host |
| `selftest --network none` | dashboard 31/31, luong truc tiep 9/9, quet file SACH |
| Quet image (`docker/scan.py`) | 0 checkpoint; 0 log tho / event gan nhan (ngoai `samples/replay_demo.jsonl.gz`, brief 6.1 yeu cau); 0 thong tin dang nhap |
| `demo` | dashboard + phat lai log mau x10 trong container, health check DAT |
| Xuat file | `docker/out/vtguard_amd64.tar` 223 MB, sha256 `4aa7ac7f768e91cf...f5347fa5` (day du o `docker/image_info.json`) |
| Huong dan | `README_DOCKER.md` |

Chua lam: ban `linux/arm64` (chua biet kien truc may giang vien - brief 6.3), chay thu tren may sach.

## 4. Tieu chi chap nhan (brief muc 7)

| # | Tieu chi | Trang thai |
|---|---|---|
| 1 | Dashboard tieng Viet, 5 trang gon, hai che do tach bach; so lieu trung artefact | DAT: 5 trang, 2 phan (SIEM khong nhan / Nghien cuu co nhan), 31/31 test so lieu + trang |
| 2 | `live` doc `wazuh-archives-*` -> trang Truc tiep; (tuy chon) `vtguard-alerts-*`; `replay` khong can Indexer | Code + test xong; `replay` DAT; **`live` chua chay voi Indexer that (moc 4, trong lab)** |
| 3 | Kich ban demo muc 4 chay tron | **Chua** (moc 4, trong lab) |
| 4 | Docker build duoc, `verify` DAT voi `--network none`, khong log tho / checkpoint / dang nhap | DAT |
| 5 | `vtguard.tar` + `README_DOCKER.md` + `docker/MANIFEST.json` + bao cao do lech | DAT (tar khong vao git) |
| 6 | `step9_report.md` + anh, commit, push, tag `step9-done` | Bao cao + anh xong; commit / tag cho xac nhan |
