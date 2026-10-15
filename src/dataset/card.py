#!/usr/bin/env python3
"""VT-Guard Buoc 4.5 - dataset card + kiem thu chap nhan cuoi.
Gom thong ke cac buoc 4.1-4.4 (reports/*.stats.json), chay lai kiem thu chap nhan (brief muc 5)
tren chinh cac file split, ghi reports/dataset_stats.json + reports/dataset_card.md
va ban sao reports/vocab.json (data/ khong vao git).
Chay: python src/dataset/card.py [--root .] [--seed 1337]
"""
import argparse, hashlib, json, os, random, re, shutil, sys
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "label"))
import featurize
from label import LABEL_VERSION
from split import SPLITS

LEAK_RE = re.compile(r"atomic|invoke-|\bT10\d\d|\bT1\d{3}\b|vt-?guard", re.I)
SPLIT_NAME = {"train": "Train", "t_clean": "T-clean", "t_hard": "T-hard", "t_novel": "T-novel"}
NORMALIZE_VERSION = "v0"

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def ts(s):
    s = s.replace("Z", "+00:00").replace("+0000", "+00:00")
    if "." in s:
        head, rest = s.split(".", 1)
        s = f"{head}.{''.join(c for c in rest.split('+')[0] if c.isdigit())[:6]}+00:00"
    return datetime.fromisoformat(s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--seed", type=int, default=1337)
    a = ap.parse_args()
    P = lambda *p: os.path.join(a.root, *p)
    J = lambda *p: json.load(open(P(*p), encoding="utf-8"))
    merge, wst, fst, sst = (J("reports", f) for f in ("merge.stats.json", "windows.stats.json",
                                                      "featurize.stats.json", "split.stats.json"))
    vocab = J("data", "processed", "vocab.json")

    # ---- doc lai cac split ----
    W = {}
    for s in SPLITS:
        W[s] = [json.loads(l) for l in open(P("data", "processed", "splits", f"{s}.jsonl"), encoding="utf-8")]
    acc = {}
    where = defaultdict(set)
    for s, ws in W.items():
        for w in ws: where[w["run_id"]].add(s)
    acc["1_run_id_in_gt1_split"] = sorted(r for r, ss in where.items() if len(ss) > 1)
    # 2) nguon feature + noi dung ban ghi split chi la so
    bad_src = [f for f in sorted(featurize.SOURCE_FIELDS) if featurize.FORBIDDEN.search(f)]
    nonnum = 0
    for ws in W.values():
        for w in ws:
            for row in w["cat"] + w["num"]: nonnum += sum(not isinstance(x, (int, float)) for x in row)
            for c in w["cmd"]: nonnum += sum(not isinstance(x, (int, float)) for p in c for x in p)
    acc["2_forbidden_feature_sources"] = bad_src
    acc["2_non_numeric_feature_values"] = nonnum
    acc["2_feature_sources"] = sorted(featurize.SOURCE_FIELDS)
    # 3) T-hard / T-novel
    acc["3_t_hard_non_hn_windows"] = sum(w["window_class"] != "hard_negative" for w in W["t_hard"])
    acc["3_t_novel_non_batch05_windows"] = sum(w["batch"] != "batch05" for w in W["t_novel"])
    acc["3_batch05_outside_t_novel"] = sum(w["batch"] == "batch05" for s in SPLITS if s != "t_novel" for w in W[s])
    # 4) thong ke tung tap
    per = {}
    for s in SPLITS:
        ws = W[s]; pos = sum(w["window_malicious"] for w in ws)
        per[s] = {"sessions": len({w["run_id"] for w in ws}), "windows": len(ws), "positive": pos,
                  "negative": len(ws) - pos, "positive_rate": round(pos / max(1, len(ws)), 4),
                  "windows_by_class": dict(sorted(Counter(w["window_class"] for w in ws).items())),
                  "windows_by_host": dict(sorted(Counter(w["host"] for w in ws).items())),
                  "ttp_windows": dict(sorted(Counter(t for w in ws for t in w["window_ttps"]).items())),
                  "multi_label_windows": sum(len(w["window_ttps"]) > 1 for w in ws),
                  "events": sum(w["n_events"] for w in ws),
                  "sha256": sha256(P("data", "processed", "splits", f"{s}.jsonl"))}
    # 5) tong cua so duong
    n_pos = sum(p["positive"] for p in per.values())
    n_att = wst["by_class"]["attack"]["sessions"]
    acc["5_positive_windows"] = {"positive": n_pos, "attack_sessions": n_att, "cap": n_att * 8,
                                 "mean_pos_per_attack_session": round(n_pos / n_att, 2), "ok": n_pos <= n_att * 8}
    # 6) quet ro ri cuoi: 200 cua so duong (text nguon trong windows.jsonl + token vocab)
    pos_ids = [w["window_id"] for s in SPLITS for w in W[s] if w["window_malicious"]]
    samp = set(random.Random(a.seed).sample(pos_ids, min(200, len(pos_ids))))
    hits = Counter(); scanned = 0
    for l in open(P("data", "processed", "windows.jsonl"), encoding="utf-8"):
        w = json.loads(l)
        if w["window_id"] not in samp: continue
        scanned += 1
        for e in w["events"]:
            for f in ("command_line", "image_name", "parent_image_name"):
                v = e.get(f)
                if v and (LEAK_RE.search(v) or (f == "command_line" and LEAK_RE.search(featurize.norm_cmd(v)))):
                    hits[f] += 1
    vocab_hits = [(f, t) for f in featurize.CAT_FIELDS for t in vocab[f] if LEAK_RE.search(t)]
    acc["6_leak_scan"] = {"positive_windows_scanned": scanned, "pattern": LEAK_RE.pattern,
                          "text_hits": dict(hits), "vocab_token_hits": vocab_hits}
    # them: chong ro ri theo thoi gian (gom nhom) + vocab chi fit tren Train
    acc["7_train_test_time_overlap"] = sst["acceptance"]["train_test_time_overlap"]
    acc["8_vocab_fit_only_train"] = vocab["_meta"]["fit"].startswith("run_id trong train_runs") and \
        vocab["_meta"]["fit_sessions"] == per["train"]["sessions"]
    passed = (not acc["1_run_id_in_gt1_split"] and not bad_src and nonnum == 0
              and acc["3_t_hard_non_hn_windows"] == 0 and acc["3_t_novel_non_batch05_windows"] == 0
              and acc["3_batch05_outside_t_novel"] == 0 and acc["5_positive_windows"]["ok"]
              and not hits and not vocab_hits and not acc["7_train_test_time_overlap"] and acc["8_vocab_fit_only_train"])

    # ---- gio log uoc luong (theo ts_system cua event da giu) ----
    span = {}
    for l in open(P("data", "processed", "all.events.jsonl"), encoding="utf-8"):
        r = json.loads(l); t = ts(r["ts_system"]); k = (r["batch"], r["host"])
        lo, hi = span.get(k, (t, t)); span[k] = (min(lo, t), max(hi, t))
    log_hours = {f"{b}|{h}": round((hi - lo).total_seconds() / 3600, 2) for (b, h), (lo, hi) in sorted(span.items())}
    man_dur = Counter()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from windows import load_manifests
    man = load_manifests(a.root)
    for m in man.values(): man_dur[m["class"]] += (m["_t1"] - m["_t0"]).total_seconds() / 3600

    shutil.copyfile(P("data", "processed", "vocab.json"), P("reports", "vocab.json"))
    stats = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "versions": {"normalize": NORMALIZE_VERSION, "label": LABEL_VERSION,
                     "featurizer": featurize.FEATURIZER_VERSION},
        "seed": a.seed,
        "params": {"W": wst["params"]["W"], "stride": wst["params"]["stride"], "K": wst["params"]["K"],
                   "time_field": wst["params"]["time_field"], "hard_frac": sst["hard_frac"],
                   "clean_frac": sst["clean_frac"], "min_sessions_vocab": vocab["_meta"]["min_sessions"],
                   "cmd_hash_dim": featurize.CMD_DIM, "cmd_ngram": list(featurize.NGRAM)},
        "provenance": {"batches": merge["batches"], "skipped_files": merge["skipped_files"],
                       "manifests_by_batch": merge["manifests_by_batch"], "manifests_by_class": merge["manifests_by_class"],
                       "labeled_inputs_sha256": merge["inputs_sha256"]},
        "events": {"read": sum(v["read"] for v in merge["per_batch_io"].values()),
                   "kept": merge["n_events"], "malicious": merge["malicious"], "benign": merge["benign"],
                   "by_run_class": merge["events_by_run_class"], "by_host": merge["by_host"],
                   "dropped_by_reason_note": "xem reports/<batch>.stats.json va drop_reason trong *.labeled.jsonl"},
        "log_hours_by_batch_host": log_hours, "log_hours_total": round(sum(log_hours.values()), 2),
        "session_hours_by_class": {k: round(v, 2) for k, v in sorted(man_dur.items())},
        "windows": {"total": wst["windows"], "positive": wst["positive"], "negative": wst["negative"],
                    "before_cap": wst["windows_before_cap"], "sessions_capped": wst["sessions_capped"],
                    "sessions_excluded": wst["sessions_excluded"], "by_class": wst["by_class"]},
        "features": {"event_vector": fst["event_vector"], "vocab_size": fst["vocab_size_incl_special"],
                     "unk_rate": fst["unk_rate"]},
        "splits": per,
        "files_sha256": {"all.events.jsonl": merge["output_sha256"],
                         "windows.jsonl": sha256(P("data", "processed", "windows.jsonl")),
                         "features.jsonl": sha256(P("data", "processed", "features.jsonl")),
                         "vocab.json": sha256(P("data", "processed", "vocab.json")),
                         **{f"splits/{s}.jsonl": per[s]["sha256"] for s in SPLITS}},
        "acceptance": acc, "acceptance_pass": passed,
    }
    with open(P("reports", "dataset_stats.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    with open(P("reports", "dataset_card.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_card(stats, vocab))
    print(json.dumps({"acceptance": acc, "acceptance_pass": passed}, ensure_ascii=False, indent=2))
    print("Tap:", {SPLIT_NAME[s]: (p["windows"], p["positive_rate"]) for s, p in per.items()})
    print("Gio log uoc luong:", stats["log_hours_total"], "| ACCEPTANCE:", "DAT" if passed else "KHONG DAT")

def render_card(s, vocab):
    P = s["splits"]; ac = s["acceptance"]; pv = s["provenance"]; ev = s["events"]; wn = s["windows"]
    ttps = ["T1016", "T1018", "T1087.002", "T1654", "T1003.003"]
    tick = lambda ok: "ĐẠT" if ok else "KHÔNG ĐẠT"
    fmt = lambda x: f"{x:,}".replace(",", " ")
    L = []
    L += ["# VT-Guard — Dataset card (Bước 4, bản đóng băng)", "",
          f"Sinh tự động bởi `src/dataset/card.py` lúc {s['generated']}. Số liệu chi tiết: `reports/dataset_stats.json`.", "",
          "## 1. Mục đích",
          "Phát hiện hành vi APT kiểu **Volt Typhoon** (living-off-the-land) trên log Windows thu bằng Wazuh. "
          "Đơn vị phát hiện là **cửa sổ phiên** (chuỗi tối đa 64 event), nhãn **đa nhãn** ở mức cửa sổ: "
          "`window_malicious` (nhị phân) và `window_ttps` (tập TTP).", "",
          "## 2. Nguồn gốc",
          "- Hạ tầng: Wazuh agent trên **DC01** (domain controller) và **WIN10-01** (workstation) → Wazuh Indexer.",
          "- Mô phỏng: Atomic Red Team qua orchestrator sinh phiên; mỗi phiên có một manifest (`manifests/<đợt>/`).",
          f"- Đợt dùng: {', '.join(pv['batches'])}. Bỏ: {', '.join(pv['skipped_files'])} (chạy thử, gán nhãn bằng labeler cũ).",
          f"- Manifest: {sum(pv['manifests_by_batch'].values())} phiên — " +
          ", ".join(f"{k} {v}" for k, v in pv["manifests_by_batch"].items()) + "; theo lớp: " +
          ", ".join(f"{k} {v}" for k, v in pv["manifests_by_class"].items()) + ".",
          f"- Pipeline: `normalize.py` ({s['versions']['normalize']}) → `label.py` (labeler {s['versions']['label']}) → "
          f"`merge.py` → `windows.py` → `featurize.py` ({s['versions']['featurizer']}) → `split.py`. Seed cố định {s['seed']}.",
          f"- Event: đọc {fmt(ev['read'])}, giữ {fmt(ev['kept'])} (malicious {fmt(ev['malicious'])}, benign {fmt(ev['benign'])}; "
          f"trong đó nền {fmt(ev['by_run_class'].get('background', 0))}). DC01 {fmt(ev['by_host']['DC01'])} · WIN10-01 {fmt(ev['by_host']['WIN10-01'])}.",
          f"- Log ước lượng: **{s['log_hours_total']} giờ** (cộng khoảng thời gian log theo đợt × host); "
          "thời lượng phiên theo manifest: " + ", ".join(f"{k} {v} h" for k, v in s["session_hours_by_class"].items()) + ".", "",
          "## 3. Lớp và TTP",
          "| TTP | Kỹ thuật |", "|---|---|",
          "| T1016 | System Network Configuration Discovery |", "| T1018 | Remote System Discovery |",
          "| T1087.002 | Account Discovery: Domain Account |", "| T1654 | Log Enumeration |",
          "| T1003.003 | OS Credential Dumping: NTDS |", "",
          "Lớp phiên: `attack` (chạy TTP), `benign` (hoạt động người dùng/quản trị thường), "
          "`hard_negative` (hoạt động quản trị hợp lệ giống tấn công). Event nền (không thuộc cây tiến trình phiên nào) luôn là benign.", "",
          "## 4. Cửa sổ",
          f"- Stream phiên = event cây tiến trình của phiên + event nền cùng host trong [t_start, t_end] (theo `{s['params']['time_field']}`); "
          "không lấy event của phiên khác chạy song song.",
          f"- Cửa sổ trượt W={s['params']['W']}, stride={s['params']['stride']}; tối đa K={s['params']['K']} cửa sổ/phiên "
          f"(lấy mẫu phân tầng dương/âm, seed). {wn['sessions_capped']} phiên bị chặn, {wn['before_cap']} → {wn['total']} cửa sổ.",
          f"- Loại {len(wn['sessions_excluded'])} phiên: " +
          ", ".join(f"`{r}` ({why})" for r, c, why in wn["sessions_excluded"] if c == "attack") +
          f" và {sum(1 for _, c, _ in wn['sessions_excluded'] if c != 'attack')} phiên benign/hard-negative có stream rỗng.",
          f"- `window_malicious` = có ít nhất 1 event malicious; `window_ttps` = hợp TTP của event malicious; `window_class` = lớp phiên.", "",
          "## 5. Các tập (chia theo PHIÊN và NHÓM PHIÊN)", "",
          "| Tập | Vai trò | Phiên | Cửa sổ | Dương | Tỉ lệ dương | DC01 / WIN10-01 | " + " | ".join(ttps) + " |",
          "|---|---|---|---|---|---|---|" + "---|" * len(ttps)]
    role = {"train": "huấn luyện", "t_clean": "kiểm thử cùng phân phối", "t_hard": "đo false-positive trên quản trị hợp lệ",
            "t_novel": "holdout thời gian/biến thể (batch05)"}
    for k, p in P.items():
        L.append(f"| {SPLIT_NAME[k]} | {role[k]} | {p['sessions']} | {p['windows']} | {p['positive']} | {p['positive_rate']:.1%} | "
                 f"{p['windows_by_host'].get('DC01', 0)} / {p['windows_by_host'].get('WIN10-01', 0)} | " +
                 " | ".join(str(p["ttp_windows"].get(t, 0)) for t in ttps) + " |")
    L += ["",
          "- **T-novel** = toàn bộ phiên batch05. **T-hard** = 40% phiên hard_negative còn lại, chọn ngẫu nhiên theo nhóm chỉ gồm hard_negative. "
          "Phần còn lại chia **Train 80% / T-clean 20%** theo nhóm, phân tầng theo (lớp, host, chữ ký TTP).",
          "- **Nhóm phiên**: các phiên cùng host chồng thời gian (kể cả bắc cầu) dùng chung event nền, nên cả nhóm vào cùng một tập.", "",
          "## 6. Đặc trưng (mỗi event → 268 cột)",
          f"- 7 categorical → chỉ số embedding (`vocab.json`): " + ", ".join(f"`{f}` ({s['features']['vocab_size'][f]})" for f in featurize.CAT_FIELDS) +
          ". Id 0=`<pad>`, 1=`<unk>`, 2=`<none>`. Token vào vocab khi xuất hiện ở ≥2 phiên Train; `integrity_level` gộp SID về tên.",
          f"- `command_line` → {featurize.CMD_DIM} chiều: chuẩn hoá (chữ thường, bỏ nháy, GUID/hex/số → ký hiệu), char n-gram 3–5, "
          "signed hashing md5, log1p, chuẩn L2. **Không lưu text thô.**",
          "- 5 số: `dt_log` = log(1+Δt giây), `has_network`, `has_dns`, `is_powershell_channel`, `is_security_channel`.",
          "- Vocab fit **chỉ trên Train**; tỉ lệ `<unk>` của `image_name`: " +
          ", ".join(f"{g} {r['image_name']:.1%}" for g, r in s["features"]["unk_rate"].items()) + " (fit = Train, other = T-clean + T-hard).", "",
          "## 7. Biện pháp chống rò rỉ",
          "- **Trường không bao giờ làm feature**: `wazuh_rule_*` (chỉ cho baseline B0), `label_*`, `run_id`, `event_uid`, `process_guid`, "
          "`parent_process_guid`, `script_block_text`, `ps_payload`, đường dẫn đầy đủ `image`/`parent_image`, `n_events`. "
          "`featurize.py` assert nguồn feature không khớp mẫu cấm; cửa sổ chỉ mang 11 trường nguồn được phép.",
          "- **Labeler v5** loại event của công cụ, không gán nhãn: orchestrator (theo `exclude_pids`), harness ART (conhost/hostname/whoami), "
          "**upload manifest scp/ssh** (v4 đã gán nhầm 72 event thành malicious T1003.003 = 35% số event NTDS), "
          "**console PowerShell của người vận hành** có script gọi ART/VT (2 415 event, có `runas`/`w32tm` trước mỗi phiên NTDS), "
          "và **mảnh vỡ 4103** mất PID chứa text Invoke-AtomicTest (680 event).",
          "- Khử trùng lặp theo `(host, channel, record_id, event_id, ts_system)`: khôi phục snapshot DC01 làm `record_id` quay lui, "
          "khoá chỉ có `record_id` sẽ xoá nhầm 3 558 event thật.",
          "- Chia theo phiên và nhóm phiên: không `run_id` nào ở 2 tập, không cặp phiên Train/kiểm thử nào chồng thời gian trên cùng host.",
          "- Vocab fit chỉ trên Train; T-novel thật sự chứa token chưa thấy.", "",
          "## 8. Kiểm thử chấp nhận (chạy lại trên file split)", "",
          "| # | Kiểm tra | Kết quả |", "|---|---|---|",
          f"| 1 | Không run_id ở >1 tập | {tick(not ac['1_run_id_in_gt1_split'])} ({len(ac['1_run_id_in_gt1_split'])} vi phạm) |",
          f"| 2 | Không feature từ trường cấm; giá trị feature chỉ là số | {tick(not ac['2_forbidden_feature_sources'] and ac['2_non_numeric_feature_values'] == 0)} |",
          f"| 3 | T-hard chỉ hard_negative; T-novel chỉ batch05 (và batch05 không ở tập khác) | "
          f"{tick(ac['3_t_hard_non_hn_windows'] == 0 and ac['3_t_novel_non_batch05_windows'] == 0 and ac['3_batch05_outside_t_novel'] == 0)} |",
          f"| 4 | Thống kê mỗi tập (cửa sổ, tỉ lệ dương, TTP, host) | xem mục 5 |",
          f"| 5 | Số cửa sổ dương hợp lý | {tick(ac['5_positive_windows']['ok'])}: {ac['5_positive_windows']['positive']} ≤ "
          f"{ac['5_positive_windows']['attack_sessions']}×8; trung bình {ac['5_positive_windows']['mean_pos_per_attack_session']}/phiên |",
          f"| 6 | Quét rò rỉ {ac['6_leak_scan']['positive_windows_scanned']} cửa sổ dương (atomic/invoke-/T10xx/VT-Guard) + token vocab | "
          f"{tick(not ac['6_leak_scan']['text_hits'] and not ac['6_leak_scan']['vocab_token_hits'])} (0 hit) |",
          f"| 7 | Không cặp phiên Train/kiểm thử chồng thời gian | {tick(not ac['7_train_test_time_overlap'])} |",
          f"| 8 | Vocab chỉ fit trên Train | {tick(ac['8_vocab_fit_only_train'])} |", "",
          f"**Tổng: {tick(s['acceptance_pass'])}.**", "",
          "## 9. Hạn chế đã biết",
          "- **Đường tắt theo tiến trình**: `ping.exe` (T1018), `wevtutil.exe` (T1654) và `ntdsutil.exe` (T1003.003) chỉ xuất hiện trong cửa sổ dương. "
          "Không phiên benign/hard-negative nào dùng ping hay wevtutil, nên T-hard chưa thử thách các TTP này; "
          "mô hình có thể đạt điểm cao chỉ nhờ tên tiến trình. Cần thu thêm hard-negative dùng ping/wevtutil hợp lệ, "
          "và báo cáo ablation bỏ `image_name`.",
          "- **T1003.003 chỉ có trong Train/T-clean** (đợt ntds riêng, batch05 không có NTDS): T-clean chỉ có "
          f"{P['t_clean']['ttp_windows'].get('T1003.003', 0)} cửa sổ T1003.003 → độ tin cậy thấp; T-novel không đo được TTP này.",
          "- **Khôi phục snapshot ở ntds**: phiên attack NTDS có bước khôi phục snapshot DC01 trước mỗi lần chạy, hard-negative thì không. "
          "Hệ quả phụ (dịch vụ khởi động lại, nhảy đồng hồ) có thể tương quan với lớp; event công cụ đã loại, nhưng hệ quả hệ thống thì không lọc được.",
          "- **Độ dài cửa sổ khác nhau theo lớp**: cửa sổ đủ 64 event chiếm 72% ở attack dương, 54% ở benign, 44% ở hard-negative. "
          "Không đưa `n_events` vào feature; khi huấn luyện nên cắt ngẫu nhiên độ dài và đánh giá thêm trên tập cân bằng độ dài.",
          "- **Phiên chạy song song trên WIN10-01**: tác động phụ của phiên attack (logon mạng, DNS…) không thuộc cây tiến trình có thể nằm trong "
          "cửa sổ của phiên benign chạy cùng lúc dưới dạng event nền benign → nhiễu nhãn nhẹ.",
          "- **Phiên benign không có event riêng**: 47 phiên benign chạy cmdlet ngay trong orchestrator nên event bị loại cùng orchestrator; "
          "cửa sổ của chúng chỉ gồm event nền.",
          f"- **DC01 ít trong T-clean** ({P['t_clean']['windows_by_host'].get('DC01', 0)} cửa sổ so với "
          f"{P['t_clean']['windows_by_host'].get('WIN10-01', 0)} của WIN10-01) do phân tầng theo phiên, phiên DC01 nhiều cửa sổ rơi vào Train.",
          "- **Nhiễu nhãn nhỏ đã biết**: một lệnh `net user /domain` người vận hành gõ tay trên DC01 ở batch05 được giữ làm event nền benign.",
          "- Chỉ 2 host, 2 tài khoản, 1 domain lab; phạm vi là 5 TTP Discovery/Credential Access, chưa có lateral movement hay persistence.", "",
          "## 10. Tái lập",
          "```",
          "python src/label/label.py data/interim/<b>.norm.jsonl manifests/<b> data/processed/<b>.labeled.jsonl > reports/<b>.stats.json",
          "python src/dataset/merge.py",
          "python src/dataset/windows.py",
          "python src/dataset/featurize.py",
          "python src/dataset/split.py      # fit lại vocab trên Train và ghi data/processed/splits/",
          "python src/dataset/card.py",
          "```", "",
          "Checksum sha256 (data/ không nằm trong git):", "",
          "| File | sha256 |", "|---|---|"]
    L += [f"| `{k}` | `{v}` |" for k, v in s["files_sha256"].items()]
    L += ["", "Bản sao vocab dùng khi inference: `reports/vocab.json`.", ""]
    return "\n".join(L)

if __name__ == "__main__":
    main()
