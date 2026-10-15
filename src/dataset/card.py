#!/usr/bin/env python3
"""VT-Guard Buoc 4.5 - dataset card + kiem thu chap nhan cuoi.
Gom thong ke cac buoc 4.1-4.4 (reports/*.stats.json), chay lai kiem thu chap nhan (brief muc 5)
tren chinh cac file split, ghi reports/dataset_stats.json + reports/dataset_card.md
va ban sao reports/vocab.json (data/ khong vao git).
Bo sung: bang cua so T1003.003 theo tap, bang coverage theo cong cu (image_name) o cua so duong/am,
kiem tra session/run_id khong nam o 2 tap.
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
from windows import BATCHES, NOVEL_BATCHES, load_manifests

LEAK_RE = re.compile(r"atomic|invoke-|\bT10\d\d|\bT1\d{3}\b|vt-?guard", re.I)
SPLIT_NAME = {"train": "Train", "t_clean": "T-clean", "t_hard": "T-hard", "t_novel": "T-novel"}
NORMALIZE_VERSION = "v0"
# Cong cu can theo doi coverage (them tu dong moi image co >= 80% cua so chua no la duong)
TOOLS = ["ping.exe", "wevtutil.exe", "ntdsutil.exe", "vssadmin.exe", "nltest.exe", "net.exe", "net1.exe",
         "ipconfig.exe", "arp.exe", "route.exe", "netstat.exe", "nslookup.exe", "nbtstat.exe", "netsh.exe",
         "systeminfo.exe", "whoami.exe", "esentutl.exe", "dsquery.exe", "quser.exe", "cmd.exe", "powershell.exe"]
EXCLUDE_WHY = {"attack_labeled0_atomic_khong_sinh_tien_trinh_con":
               "atomic không sinh tiến trình con nào (labeled=0); loại hẳn, KHÔNG coi là benign",
               "attack_khong_co_event_malicious": "phiên attack không có event malicious trong stream",
               "stream_rong": "không có event nào trong khoảng thời gian phiên"}

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
    man = load_manifests(a.root)

    # ---- doc lai cac split ----
    W = {s: [json.loads(l) for l in open(P("data", "processed", "splits", f"{s}.jsonl"), encoding="utf-8")] for s in SPLITS}
    split_of = {w["window_id"]: s for s, ws in W.items() for w in ws}
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
    acc["3_t_novel_batches"] = NOVEL_BATCHES
    acc["3_t_novel_non_novel_batch_windows"] = sum(w["batch"] not in NOVEL_BATCHES for w in W["t_novel"])
    acc["3_novel_batch_outside_t_novel"] = sum(w["batch"] in NOVEL_BATCHES for s in SPLITS if s != "t_novel" for w in W[s])
    # 4) thong ke tung tap
    per = {}
    for s in SPLITS:
        ws = W[s]; pos = sum(w["window_malicious"] for w in ws)
        per[s] = {"sessions": len({w["run_id"] for w in ws}), "windows": len(ws), "positive": pos,
                  "negative": len(ws) - pos, "positive_rate": round(pos / max(1, len(ws)), 4),
                  "sessions_by_batch": dict(sorted(Counter(b for b, r in {(w["batch"], w["run_id"]) for w in ws}).items())),
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

    # ---- doc windows.jsonl: quet ro ri + coverage cong cu + do dai ----
    pos_ids = [w["window_id"] for s in SPLITS for w in W[s] if w["window_malicious"]]
    samp = set(random.Random(a.seed).sample(pos_ids, min(200, len(pos_ids))))
    hits = Counter(); scanned = 0
    cov = defaultdict(lambda: defaultdict(Counter))   # image -> split|all -> pos/neg
    full = defaultdict(Counter)
    for l in open(P("data", "processed", "windows.jsonl"), encoding="utf-8"):
        w = json.loads(l)
        s = split_of[w["window_id"]]; lab = "pos" if w["window_malicious"] else "neg"
        for img in {e["image_name"] for e in w["events"] if e["image_name"]}:
            cov[img]["all"][lab] += 1; cov[img][s][lab] += 1
        k = f"{w['window_class']}{'+' if w['window_malicious'] else '-'}"
        full[k]["n"] += 1; full[k]["full"] += w["n_events"] == 64
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
    acc["7_train_test_time_overlap"] = sst["acceptance"]["train_test_time_overlap"]
    acc["8_vocab_fit_only_train"] = vocab["_meta"]["fit"].startswith("run_id trong train_runs") and \
        vocab["_meta"]["fit_sessions"] == per["train"]["sessions"]
    passed = (not acc["1_run_id_in_gt1_split"] and not bad_src and nonnum == 0
              and acc["3_t_hard_non_hn_windows"] == 0 and acc["3_t_novel_non_novel_batch_windows"] == 0
              and acc["3_novel_batch_outside_t_novel"] == 0 and acc["5_positive_windows"]["ok"]
              and not hits and not vocab_hits and not acc["7_train_test_time_overlap"] and acc["8_vocab_fit_only_train"])

    # ---- bang T1003.003 theo tap ----
    ntds_runs = {r for r, m in man.items() if "T1003.003" in m["ttps"]}
    t1003 = {}
    for s in SPLITS:
        ws = W[s]
        t1003[s] = {"positive": sum("T1003.003" in w["window_ttps"] for w in ws),
                    "negative_in_t1003_sessions": sum(w["run_id"] in ntds_runs and "T1003.003" not in w["window_ttps"] for w in ws),
                    "negative_dc01": sum(w["host"] == "DC01" and "T1003.003" not in w["window_ttps"] for w in ws),
                    "negative_all": sum("T1003.003" not in w["window_ttps"] for w in ws),
                    "sessions": len({w["run_id"] for w in ws if w["run_id"] in ntds_runs}),
                    "sessions_by_batch": dict(sorted(Counter(b for b, r in {(w["batch"], w["run_id"]) for w in ws if w["run_id"] in ntds_runs}).items()))}
    # ---- coverage cong cu ----
    tools = [t for t in TOOLS if t in cov]
    tools += sorted(t for t, c in cov.items() if t not in tools and c["all"]["pos"] and
                    c["all"]["pos"] / (c["all"]["pos"] + c["all"]["neg"]) >= 0.8)
    coverage = {}
    for t in tools:
        c = cov[t]
        coverage[t] = {"all_pos": c["all"]["pos"], "all_neg": c["all"]["neg"],
                       **{f"{s}_pos": c[s]["pos"] for s in SPLITS}, **{f"{s}_neg": c[s]["neg"] for s in SPLITS},
                       "positive_only_all": c["all"]["pos"] > 0 and c["all"]["neg"] == 0,
                       "positive_only_train": c["train"]["pos"] > 0 and c["train"]["neg"] == 0}
    shortcut_all = [t for t, v in coverage.items() if v["positive_only_all"]]
    shortcut_train = [t for t, v in coverage.items() if v["positive_only_train"]]

    # ---- so lieu ro ri tu file gan nhan ----
    drops = Counter(); drops_by_batch = {}
    for b in BATCHES:
        c = Counter()
        for l in open(P("data", "processed", f"{b}.labeled.jsonl"), encoding="utf-8"):
            r = json.loads(l)
            if r["dropped"]: c[r["drop_reason"]] += 1
        drops_by_batch[b] = dict(c); drops += c

    # ---- gio log uoc luong ----
    span = {}
    for l in open(P("data", "processed", "all.events.jsonl"), encoding="utf-8"):
        r = json.loads(l); t = ts(r["ts_system"]); k = (r["batch"], r["host"])
        lo, hi = span.get(k, (t, t)); span[k] = (min(lo, t), max(hi, t))
    log_hours = {f"{b}|{h}": round((hi - lo).total_seconds() / 3600, 2) for (b, h), (lo, hi) in sorted(span.items())}
    man_dur = Counter()
    for m in man.values(): man_dur[m["class"]] += (m["_t1"] - m["_t0"]).total_seconds() / 3600

    shutil.copyfile(P("data", "processed", "vocab.json"), P("reports", "vocab.json"))
    stats = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "versions": {"normalize": NORMALIZE_VERSION, "label": LABEL_VERSION, "featurizer": featurize.FEATURIZER_VERSION},
        "seed": a.seed,
        "params": {"W": wst["params"]["W"], "stride": wst["params"]["stride"], "K": wst["params"]["K"],
                   "time_field": wst["params"]["time_field"], "hard_frac": sst["hard_frac"],
                   "clean_frac": sst["clean_frac"], "min_sessions_vocab": vocab["_meta"]["min_sessions"],
                   "cmd_hash_dim": featurize.CMD_DIM, "cmd_ngram": list(featurize.NGRAM), "t_novel_batches": NOVEL_BATCHES},
        "provenance": {"batches": merge["batches"], "skipped_files": merge["skipped_files"],
                       "manifests_by_batch": merge["manifests_by_batch"], "manifests_by_class": merge["manifests_by_class"],
                       "labeled_inputs_sha256": merge["inputs_sha256"]},
        "events": {"read": sum(v["read"] for v in merge["per_batch_io"].values()),
                   "kept": merge["n_events"], "malicious": merge["malicious"], "benign": merge["benign"],
                   "by_run_class": merge["events_by_run_class"], "by_host": merge["by_host"],
                   "malicious_by_ttp": merge["malicious_events_by_ttp"],
                   "dropped_by_reason": dict(drops), "dropped_by_batch": drops_by_batch,
                   "brief_key_collisions": merge["brief_key_collisions"],
                   "runs_without_events": merge["runs_without_events"]["by_class"]},
        "log_hours_by_batch_host": log_hours, "log_hours_total": round(sum(log_hours.values()), 2),
        "session_hours_by_class": {k: round(v, 2) for k, v in sorted(man_dur.items())},
        "windows": {"total": wst["windows"], "positive": wst["positive"], "negative": wst["negative"],
                    "before_cap": wst["windows_before_cap"], "sessions_capped": wst["sessions_capped"],
                    "sessions_excluded": wst["sessions_excluded"], "by_class": wst["by_class"],
                    "by_batch": wst["by_batch"],
                    "full64_rate": {k: round(v["full"] / v["n"], 3) for k, v in sorted(full.items())}},
        "features": {"event_vector": fst["event_vector"], "vocab_size": fst["vocab_size_incl_special"],
                     "unk_rate": fst["unk_rate"]},
        "splits": per,
        "t1003_003_by_split": t1003,
        "tool_coverage": coverage, "tools_positive_only_all": shortcut_all, "tools_positive_only_train": shortcut_train,
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
        f.write(render_card(stats))
    print(json.dumps({"acceptance": acc, "acceptance_pass": passed}, ensure_ascii=False, indent=2))
    print("Tap:", {SPLIT_NAME[s]: (p["windows"], p["positive_rate"]) for s, p in per.items()})
    print("T1003.003:", {SPLIT_NAME[s]: (v["positive"], v["negative_in_t1003_sessions"], v["negative_dc01"]) for s, v in t1003.items()})
    print("Cong cu chi o phia duong: toan bo =", shortcut_all, "| trong Train =", shortcut_train)
    print("ACCEPTANCE (8 kiem tra):", "DAT" if passed else "KHONG DAT")

def render_card(s):
    P = s["splits"]; ac = s["acceptance"]; pv = s["provenance"]; ev = s["events"]; wn = s["windows"]
    T3 = s["t1003_003_by_split"]; cov = s["tool_coverage"]; dr = ev["dropped_by_reason"]
    ttps = ["T1016", "T1018", "T1087.002", "T1654", "T1003.003"]
    tick = lambda ok: "ĐẠT" if ok else "KHÔNG ĐẠT"
    fmt = lambda x: f"{x:,}".replace(",", " ")
    pct = lambda x: f"{x:.0%}"
    novel = " + ".join(s["params"]["t_novel_batches"])
    excl = Counter(why for _, _, why in wn["sessions_excluded"])
    excl_attack = [(r, why) for r, c, why in wn["sessions_excluded"] if c == "attack"]
    fr = wn["full64_rate"]
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
          "  - `batch06`: 27 phiên hard-negative bổ sung (quét mạng quản trị bằng ping, kiểm tra log bằng wevtutil, "
          "bảo trì CSDL AD bằng ntdsutil…) để giảm đường tắt theo tên tiến trình.",
          "  - `ntds2`: 15 phiên T1003.003 test 3 (`ntdsutil ifm`); `ntds2v`: 6 phiên T1003.003 test 1 (biến thể vssadmin/shadow copy) — giữ làm biến thể held-out.",
          f"- Manifest: {sum(pv['manifests_by_batch'].values())} phiên — " +
          ", ".join(f"{k} {v}" for k, v in pv["manifests_by_batch"].items()) + "; theo lớp: " +
          ", ".join(f"{k} {v}" for k, v in pv["manifests_by_class"].items()) + ".",
          f"- Pipeline: `normalize.py` ({s['versions']['normalize']}) → `label.py` (labeler {s['versions']['label']}) → "
          f"`merge.py` → `windows.py` → `featurize.py` ({s['versions']['featurizer']}) → `split.py`. Seed cố định {s['seed']}.",
          f"- Event: đọc {fmt(ev['read'])}, giữ {fmt(ev['kept'])} (malicious {fmt(ev['malicious'])}, benign {fmt(ev['benign'])}; "
          f"trong đó nền {fmt(ev['by_run_class'].get('background', 0))}). DC01 {fmt(ev['by_host']['DC01'])} · WIN10-01 {fmt(ev['by_host']['WIN10-01'])}.",
          "- Event malicious theo TTP: " + ", ".join(f"{k} {fmt(v)}" for k, v in ev["malicious_by_ttp"].items()) + ".",
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
          f"(lấy mẫu phân tầng dương/âm, seed). {wn['sessions_capped']} phiên bị chặn, {wn['before_cap']} → {wn['total']} cửa sổ "
          f"({wn['positive']} dương, {wn['negative']} âm).",
          f"- `window_malicious` = có ít nhất 1 event malicious; `window_ttps` = hợp TTP của event malicious; `window_class` = lớp phiên.",
          f"- **Phiên bị loại ({len(wn['sessions_excluded'])})**:"]
    for r, why in excl_attack:
        L.append(f"  - `{r}` (attack): {EXCLUDE_WHY.get(why, why)}.")
    L += [f"  - {excl.get('stream_rong', 0)} phiên benign/hard-negative: {EXCLUDE_WHY['stream_rong']}.", "",
          "## 5. Các tập (chia theo PHIÊN và NHÓM PHIÊN)", "",
          "| Tập | Vai trò | Phiên | Cửa sổ | Dương | Tỉ lệ dương | DC01 / WIN10-01 | " + " | ".join(ttps) + " |",
          "|---|---|---|---|---|---|---|" + "---|" * len(ttps)]
    role = {"train": "huấn luyện", "t_clean": "kiểm thử cùng phân phối", "t_hard": "đo false-positive trên quản trị hợp lệ",
            "t_novel": f"holdout thời gian + biến thể ({novel})"}
    for k, p in P.items():
        L.append(f"| {SPLIT_NAME[k]} | {role[k]} | {p['sessions']} | {p['windows']} | {p['positive']} | {p['positive_rate']:.1%} | "
                 f"{p['windows_by_host'].get('DC01', 0)} / {p['windows_by_host'].get('WIN10-01', 0)} | " +
                 " | ".join(str(p["ttp_windows"].get(t, 0)) for t in ttps) + " |")
    L += ["", "Số phiên theo đợt trong từng tập:", "",
          "| Tập | " + " | ".join(pv["batches"]) + " |", "|---|" + "---|" * len(pv["batches"])]
    for k, p in P.items():
        L.append(f"| {SPLIT_NAME[k]} | " + " | ".join(str(p["sessions_by_batch"].get(b, "")) for b in pv["batches"]) + " |")
    L += ["",
          f"- **T-novel** = toàn bộ phiên {novel}: batch05 là holdout thời gian, ntds2v là biến thể T1003.003 (test 1) không có trong Train. "
          "**T-hard** = 40% phiên hard_negative còn lại (kể cả batch06), chọn ngẫu nhiên theo nhóm chỉ gồm hard_negative. "
          "Phần còn lại (gồm ntds2) chia **Train 80% / T-clean 20%** theo nhóm, phân tầng theo (lớp, host, chữ ký TTP).",
          "- **Nhóm phiên**: các phiên cùng host chồng thời gian (kể cả bắc cầu) dùng chung event nền, nên cả nhóm vào cùng một tập.", "",
          "### 5a. Cửa sổ T1003.003 theo tập", "",
          "| Tập | Phiên T1003.003 (theo đợt) | Cửa sổ dương T1003.003 | Âm trong phiên T1003.003 | Âm trên DC01 | Âm toàn tập |",
          "|---|---|---|---|---|---|"]
    for k, v in T3.items():
        sb = ", ".join(f"{b} {n}" for b, n in v["sessions_by_batch"].items()) or "—"
        L.append(f"| {SPLIT_NAME[k]} | {v['sessions']} ({sb}) | {v['positive']} | {v['negative_in_t1003_sessions']} | {v['negative_dc01']} | {v['negative_all']} |")
    L += ["",
          "### 5b. Coverage theo công cụ (số cửa sổ chứa tiến trình)", "",
          "Mục tiêu: không công cụ nào chỉ xuất hiện ở phía dương, để mô hình không thể phát hiện chỉ nhờ tên tiến trình.", "",
          "| image_name | Dương (tất cả) | Âm (tất cả) | Train dương / âm | T-clean dương / âm | T-hard âm | T-novel dương / âm | Cảnh báo |",
          "|---|---|---|---|---|---|---|---|"]
    for t, v in cov.items():
        warn = "CHỈ DƯƠNG" if v["positive_only_all"] else ("chỉ dương trong Train" if v["positive_only_train"] else "")
        L.append(f"| `{t}` | {v['all_pos']} | {v['all_neg']} | {v['train_pos']} / {v['train_neg']} | {v['t_clean_pos']} / {v['t_clean_neg']} | "
                 f"{v['t_hard_neg']} | {v['t_novel_pos']} / {v['t_novel_neg']} | {warn} |")
    L += ["",
          f"Công cụ chỉ xuất hiện ở phía dương: **toàn bộ dữ liệu: {', '.join(s['tools_positive_only_all']) or 'không có'}**; "
          f"riêng Train: {', '.join(s['tools_positive_only_train']) or 'không có'}.", "",
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
          f"- **Labeler {s['versions']['label']}** loại event công cụ thay vì gán nhãn (tổng trên {len(ev['dropped_by_batch'])} đợt): "
          f"orchestrator {fmt(dr.get('orchestrator', 0))}, harness ART {fmt(dr.get('art_harness', 0))}, "
          f"upload manifest scp/ssh {fmt(dr.get('harness_upload', 0))}, console PowerShell người vận hành {fmt(dr.get('operator_console', 0))}, "
          f"mảnh vỡ 4103 mất PID {fmt(dr.get('ps_fragment', 0))}.",
          "  - v5: chặn upload manifest (v4 gán nhầm 72 event thành malicious T1003.003 ở ntds), console người vận hành, mảnh vỡ 4103.",
          "  - v6: event không có `process_guid` chỉ được ghép vào tiến trình khi `ts_system` nằm trong vòng đời tiến trình (EID1→EID5). "
          "v5 ghép theo PID ±300 s bằng giờ Wazuh: sau khi khôi phục snapshot, đồng hồ DC01 lệch ~55 phút nên 204 event PowerShell (pid 1112, "
          "nạp module CIM) bị gán nhầm malicious T1003.003 vào phiên ntds2 `20261015-084208-dc01-a`, và 27 event PowerShell khác bị ghép nhầm vào cây scp. "
          "Đối chiếu từng event v5↔v6: chỉ 231 event này đổi, các đợt khác giữ nguyên.",
          f"- Khử trùng lặp theo `(host, channel, record_id, event_id, ts_system)`: khôi phục snapshot DC01 làm `record_id` quay lui, "
          f"khoá chỉ có `record_id` sẽ xoá nhầm {fmt(ev['brief_key_collisions'])} event thật.",
          "- Chia theo phiên và nhóm phiên: không `run_id`/session nào ở 2 tập, không cặp phiên Train/kiểm thử nào chồng thời gian trên cùng host.",
          "- Vocab fit chỉ trên Train; T-novel thật sự chứa token chưa thấy.", "",
          "## 8. Kiểm thử chấp nhận (chạy lại trên file split)", "",
          "| # | Kiểm tra | Kết quả |", "|---|---|---|",
          f"| 1 | Không session/run_id ở >1 tập | {tick(not ac['1_run_id_in_gt1_split'])} ({len(ac['1_run_id_in_gt1_split'])} vi phạm) |",
          f"| 2 | Không feature từ trường cấm; giá trị feature chỉ là số | {tick(not ac['2_forbidden_feature_sources'] and ac['2_non_numeric_feature_values'] == 0)} |",
          f"| 3 | T-hard chỉ hard_negative; T-novel chỉ {novel} (và các đợt này không ở tập khác) | "
          f"{tick(ac['3_t_hard_non_hn_windows'] == 0 and ac['3_t_novel_non_novel_batch_windows'] == 0 and ac['3_novel_batch_outside_t_novel'] == 0)} |",
          f"| 4 | Thống kê mỗi tập (cửa sổ, tỉ lệ dương, TTP, host) | xem mục 5 |",
          f"| 5 | Số cửa sổ dương hợp lý | {tick(ac['5_positive_windows']['ok'])}: {ac['5_positive_windows']['positive']} ≤ "
          f"{ac['5_positive_windows']['attack_sessions']}×8; trung bình {ac['5_positive_windows']['mean_pos_per_attack_session']}/phiên |",
          f"| 6 | Quét rò rỉ {ac['6_leak_scan']['positive_windows_scanned']} cửa sổ dương (atomic/invoke-/T10xx/VT-Guard) + token vocab | "
          f"{tick(not ac['6_leak_scan']['text_hits'] and not ac['6_leak_scan']['vocab_token_hits'])} "
          f"({sum(ac['6_leak_scan']['text_hits'].values()) + len(ac['6_leak_scan']['vocab_token_hits'])} hit) |",
          f"| 7 | Không cặp phiên Train/kiểm thử chồng thời gian | {tick(not ac['7_train_test_time_overlap'])} |",
          f"| 8 | Vocab chỉ fit trên Train | {tick(ac['8_vocab_fit_only_train'])} |", "",
          f"**Tổng: {tick(s['acceptance_pass'])}.** Kiểm tra bổ sung (mục 5b): công cụ chỉ ở phía dương trên toàn bộ dữ liệu — "
          f"{'không có' if not s['tools_positive_only_all'] else ', '.join(s['tools_positive_only_all'])}.", "",
          "## 9. Hạn chế đã biết"]
    sa, st = s["tools_positive_only_all"], s["tools_positive_only_train"]
    pc = lambda t, k: cov.get(t, {}).get(k, 0)
    L += [f"- **Đường tắt theo tiến trình**: sau khi thêm batch06, "
          + (f"vẫn còn công cụ chỉ ở phía dương: {', '.join(sa)}. " if sa else "không công cụ nào chỉ xuất hiện ở phía dương trên toàn bộ dữ liệu. ")
          + f"Phía âm vẫn mỏng: `ping.exe` dương {pc('ping.exe', 'all_pos')} / âm {pc('ping.exe', 'all_neg')}, "
          f"`wevtutil.exe` {pc('wevtutil.exe', 'all_pos')} / {pc('wevtutil.exe', 'all_neg')}, `ntdsutil.exe` {pc('ntdsutil.exe', 'all_pos')} / {pc('ntdsutil.exe', 'all_neg')} cửa sổ. "
          + (f"**Riêng Train**, {', '.join(f'`{t}`' for t in st)} chỉ có ở cửa sổ dương (các phiên hard-negative tương ứng rơi vào T-hard), "
             "nên mô hình vẫn có thể học đường tắt này; T-hard là nơi đo đúng lỗi đó. " if st else "")
          + "Gần như chỉ dương (≥90% số cửa sổ chứa là dương): "
          + (", ".join(f"`{t}` {v['all_pos']}/{v['all_neg']}" for t, v in cov.items()
                       if v["all_neg"] and v["all_pos"] / (v["all_pos"] + v["all_neg"]) >= 0.9) or "không có") + ". "
          + "Đường tắt ngược (chỉ xuất hiện ở phía âm): "
          + (", ".join(f"`{t}`" for t, v in cov.items() if v["all_pos"] == 0 and v["all_neg"] > 0) or "không có")
          + " — kịch bản benign dùng chúng còn biến thể tấn công thì không. Nên báo cáo ablation bỏ `image_name`.",
          f"- **T1003.003 ít dữ liệu đánh giá**: T-clean có {T3['t_clean']['positive']} cửa sổ dương, T-novel (ntds2v) {T3['t_novel']['positive']}; "
          "báo cáo kèm khoảng tin cậy. Phiên ntds2/ntds2v rất ngắn (thường 1–2 cửa sổ, toàn cửa sổ dương), nên không có cửa sổ âm bên trong phiên NTDS mới.",
          "- **Khôi phục snapshot ở ntds/ntds2/ntds2v**: phiên attack NTDS có bước khôi phục snapshot DC01, làm đồng hồ lệch tới ~55 phút cho tới khi đồng bộ lại. "
          "v6 không ghép nhầm event theo PID nữa, nhưng event nền phát ra lúc đồng hồ lệch có `ts_system` sai nên có thể rơi ra ngoài (hoặc vào nhầm) khung thời gian phiên. "
          "Hệ quả hệ thống của việc khôi phục (dịch vụ khởi động lại) có thể tương quan với lớp.",
          f"- **Độ dài cửa sổ khác nhau theo lớp**: tỉ lệ cửa sổ đủ 64 event — " +
          ", ".join(f"{k} {pct(v)}" for k, v in fr.items()) + ". Không đưa `n_events` vào feature; khi huấn luyện nên cắt ngẫu nhiên độ dài.",
          "- **Phiên chạy song song trên WIN10-01**: tác động phụ của phiên attack (logon mạng, DNS…) không thuộc cây tiến trình có thể nằm trong "
          "cửa sổ của phiên benign chạy cùng lúc dưới dạng event nền benign → nhiễu nhãn nhẹ.",
          f"- **Phiên không có event riêng**: {ev['runs_without_events'].get('benign', 0)} phiên benign chạy cmdlet ngay trong orchestrator "
          "nên event bị loại cùng orchestrator; cửa sổ của chúng chỉ gồm event nền.",
          f"- **DC01 ít trong T-clean** ({P['t_clean']['windows_by_host'].get('DC01', 0)} cửa sổ so với "
          f"{P['t_clean']['windows_by_host'].get('WIN10-01', 0)} của WIN10-01) do phân tầng theo phiên.",
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
