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
from windows import BATCHES, NOVEL_BATCHES, load_manifests, DATASET_VERSION, SCAFFOLD_DROP_IMAGES, LAUNCHERS, LAUNCHER_TOKEN
from scaffold_scan import scan as scaffold_scan
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "eval"))
from evaluate import fci

LEAK_RE = re.compile(r"atomic|invoke-|\bT10\d\d|\bT1\d{3}\b|vt-?guard", re.I)
SPLIT_NAME = {"train": "Train", "t_clean": "T-clean", "t_hard": "T-hard", "t_novel": "T-novel"}
NORMALIZE_VERSION = "v0"
# Cong cu can theo doi coverage (them tu dong moi image co >= 80% cua so chua no la duong)
TOOLS = ["ping.exe", "wevtutil.exe", "ntdsutil.exe", "vssadmin.exe", "nltest.exe", "net.exe", "net1.exe",
         "ipconfig.exe", "arp.exe", "route.exe", "netstat.exe", "nslookup.exe", "nbtstat.exe", "netsh.exe",
         "systeminfo.exe", "whoami.exe", "esentutl.exe", "dsquery.exe", "quser.exe", "cmd.exe", "powershell.exe"]
CHECK9_TOOLS = ["ntdsutil.exe", "vssadmin.exe", "ping.exe", "wevtutil.exe", "nltest.exe", "nslookup.exe",
                "nbtstat.exe", "netsh.exe", "cmd.exe"]
CHECK9_MIN_NEG = 0.15
SEP11 = 0.98
_BENIGN_SCEN = re.compile(r"(route|netstat|ipconfig|print|-ano|admins|list|shadows|/dsgetdc|/sc_query)", re.I)

def categorize11(feature, side):
    """Phan loai so bo dac trung mot-phia (de nguoi duyet): scaffold con sot / kich ban benign / tac dong phu
    NTDS / hanh vi tan cong."""
    if feature.startswith("eid="): return "tac dong phu NTDS (ESENT/Directory Service)" if side == "attack" else "kich ban benign"
    if "shcreatelocalserverrundll" in feature or "shell0.dll" in feature: return "tac dong phu nen (svchost->rundll32 COM, ngoai cay tien trinh)"
    if re.match(r"^cmdtok=[a-z0-9_-]+\.exe$", feature) and side == "hard_negative": return "scaffold con sot (.exe cua lenh goi tu PowerShell)"
    if feature == f"pair={LAUNCHER_TOKEN}->powershell.exe": return "gioi han co chu y (ART chay test PowerShell trong tien trinh con)"
    if side == "hard_negative": return "kich ban benign (coverage attack thieu)" if _BENIGN_SCEN.search(feature) else "kich ban benign"
    return "hanh vi tan cong"
EXCLUDE_WHY = {"hard_negative_labeled0_khong_co_tien_trinh_con":
               "không có event tiến trình con trong khung phiên, nghi do agent hoặc đồng hồ sau khi khôi phục snapshot; "
               "loại hẳn (quy tắc chung: hard_negative labeled=0 bị loại như phiên attack)",
               "attack_labeled0_atomic_khong_sinh_tien_trinh_con":
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
    bgdist = {"t1003_pos": Counter(), "revert_control": Counter()}   # kiem tra #10: event NEN theo (channel, event_id)
    nwin10 = Counter()
    for l in open(P("data", "processed", "windows.jsonl"), encoding="utf-8"):
        w = json.loads(l)
        sets = ([("t1003_pos")] if "T1003.003" in w["window_ttps"] else []) + (["revert_control"] if w.get("revert_control") else [])
        for name in sets:
            nwin10[name] += 1
            for e, o in zip(w["events"], w["event_origin"]):
                if o == "bg": bgdist[name][f"{e['channel']}:{e['event_id']}"] += 1
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
    # ---- #11: khong dac trung don le nao tach attack vs hard_negative voi muc tach >= 0.98 (thuong truc) ----
    rows11, meta11 = scaffold_scan(a.root, canon=False, min_sep=0.5, min_windows=3)
    over11 = [r for r in rows11 if r["separation"] >= SEP11]
    one_sided = sorted([r for r in rows11 if (r["pct_windows_hn"] <= 0.01 and r["pct_windows_attack"] >= 0.10 and r["sessions_hn"] == 0)
                        or (r["pct_windows_attack"] <= 0.01 and r["pct_windows_hn"] >= 0.10 and r["sessions_attack"] == 0)],
                       key=lambda r: -max(r["pct_windows_attack"], r["pct_windows_hn"]))
    for r in one_sided: r["category"] = categorize11(r["feature"], r["side"])
    acc["11_single_feature_separation"] = {
        "threshold": SEP11, "unit": "cua so attack duong vs cua so hard_negative; diem = ti le event mang gia tri",
        "max_separation": rows11[0]["separation"] if rows11 else None, "max_feature": rows11[0]["feature"] if rows11 else None,
        "over_threshold": over11, "top10": rows11[:10], "one_sided": one_sided, "meta": meta11, "ok": not over11}
    passed = (not acc["1_run_id_in_gt1_split"] and not bad_src and nonnum == 0
              and acc["3_t_hard_non_hn_windows"] == 0 and acc["3_t_novel_non_novel_batch_windows"] == 0
              and acc["3_novel_batch_outside_t_novel"] == 0 and acc["5_positive_windows"]["ok"]
              and not hits and not vocab_hits and not acc["7_train_test_time_overlap"] and acc["8_vocab_fit_only_train"])
    # bang chung moc A (B1 / B1-raw / B1-canon tren dataset-v1.0)
    mocA = {}
    for m in ("b1_tfidf_lr", "b1_raw_lr", "b1_canon_lr"):
        fp = P("reports", "step5", "v1.0_mocA", f"{m}.json")
        if os.path.exists(fp):
            r = json.load(open(fp, encoding="utf-8")); S = r["splits"]; h = S["t_hard"]["tuned"]
            mocA[m] = {"t_clean_f1": S["t_clean"]["tuned"]["f1"], "t_hard_fpr": h["fpr"], "t_hard_fp": h["fp"],
                       "t_hard_fp_cmd": h["fpr_by_cmd"].get("co cmd.exe", {}).get("fp"), "t_novel_f1": S["t_novel"]["tuned"]["f1"],
                       "t_novel_pr_auc": S["t_novel"]["pr_auc"], "macro_f1_clean": S["t_clean"]["ttp_tuned"]["macro_f1"]["point"],
                       "macro_f1_novel": S["t_novel"]["ttp_tuned"]["macro_f1"]["point"],
                       "top_pos": r.get("top_pos_features", [])[:5], "top_neg": r.get("top_neg_features", [])[:5]}
    scan10 = {}
    fp = P("reports", "step5", "scaffold_scan_v1.0.json")
    if os.path.exists(fp):
        d10 = json.load(open(fp, encoding="utf-8"))["v1.0"]["rows"]
        pure10 = [r for r in d10 if (r["pct_windows_hn"] <= 0.01 and r["pct_windows_attack"] >= 0.10 and r["sessions_hn"] == 0)
                  or (r["pct_windows_attack"] <= 0.01 and r["pct_windows_hn"] >= 0.10 and r["sessions_attack"] == 0)]
        scan10 = {"top": d10[:8], "n_one_sided": len(pure10), "max": d10[0]["separation"] if d10 else None}
    v10 = {}
    fp = P("data", "processed", "v1.0", "dataset_stats.v1.0.json")
    if os.path.exists(fp):
        o = json.load(open(fp, encoding="utf-8"))
        v10 = {"windows": o["windows"]["total"], "positive": o["windows"]["positive"], "before_cap": o["windows"]["before_cap"],
               "splits": {k: {"windows": v["windows"], "positive": v["positive"], "sessions": v["sessions"]} for k, v in o["splits"].items()},
               "files_sha256": o["files_sha256"]}

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

    # ---- kiem tra #9: Train phai co cua so am >= 15% so cua so chua cong cu (KHONG ep dat) ----
    c9 = {}
    for t in CHECK9_TOOLS:
        c = cov.get(t, {}).get("train", Counter())
        n = c["pos"] + c["neg"]
        c9[t] = {"train_pos": c["pos"], "train_neg": c["neg"], "neg_share": round(c["neg"] / n, 3) if n else None,
                 "ok": bool(n) and c["neg"] / n >= CHECK9_MIN_NEG}
    acc["9_train_neg_share_per_tool"] = {"min_neg_share": CHECK9_MIN_NEG, "tools": c9,
                                         "failed": [t for t, v in c9.items() if not v["ok"]]}
    # ---- kiem tra #10: phan bo event NEN (channel, event_id) cua cua so duong T1003.003 vs revert_control ----
    tot10 = {k: sum(v.values()) for k, v in bgdist.items()}
    keys = set(bgdist["t1003_pos"]) | set(bgdist["revert_control"])
    share = lambda k, x: bgdist[k][x] / tot10[k] if tot10[k] else 0.0
    diff = sorted(keys, key=lambda x: -abs(share("t1003_pos", x) - share("revert_control", x)))[:10]
    tvd = round(0.5 * sum(abs(share("t1003_pos", x) - share("revert_control", x)) for x in keys), 3)
    acc["10_bg_dist_t1003_vs_revert_control"] = {
        "windows": dict(nwin10), "bg_events": tot10, "total_variation_distance": tvd,
        "top10": [{"channel_event": x, "t1003_pos": round(share("t1003_pos", x), 4),
                   "revert_control": round(share("revert_control", x), 4),
                   "diff": round(share("t1003_pos", x) - share("revert_control", x), 4)} for x in diff]}
    # ---- truoc/sau batch07: ti le duong cua tung cong cu ----
    before_after = {}
    bpath = P("reports", "dataset_stats.pre_batch07.json")
    if os.path.exists(bpath):
        bcov = json.load(open(bpath, encoding="utf-8")).get("tool_coverage", {})
        for t in coverage:
            b = bcov.get(t); a_ = coverage[t]
            rate = lambda p, n: round(p / (p + n), 3) if p + n else None
            before_after[t] = {"before_pos": b["all_pos"] if b else None, "before_neg": b["all_neg"] if b else None,
                               "before_rate": rate(b["all_pos"], b["all_neg"]) if b else None,
                               "after_pos": a_["all_pos"], "after_neg": a_["all_neg"], "after_rate": rate(a_["all_pos"], a_["all_neg"]),
                               "before_train_neg": b["train_neg"] if b else None, "after_train_neg": a_["train_neg"]}

    # ---- so lieu ro ri tu file gan nhan ----
    drops = Counter(); drops_by_batch = {}
    for b in BATCHES:
        c = Counter()
        for l in open(P("data", "processed", f"{b}.labeled.jsonl"), encoding="utf-8"):
            r = json.loads(l)
            if r["dropped"]: c[r["drop_reason"]] += 1
        drops_by_batch[b] = dict(c); drops += c

    # ---- gio log ----
    # SO CHINH: tong thoi luong phien theo manifest (t_end - t_start; dong ho khach cua orchestrator).
    # KHONG dung min/max ts_system: sau khoi phuc snapshot dong ho DC01 lech (vd batch07|DC01 ra 21 h vi
    # event mang gio snapshot 14/10). Kem: hop khung phien theo host (khong dem trung phien song song) va
    # khoang export theo gio Wazuh `ts` (dong ho manager, khong bi snapshot lam lech) - chi de doi chieu.
    man_dur = Counter(); dur_bh = Counter(); ivs = defaultdict(list)
    for m in man.values():
        d = max(0.0, (m["_t1"] - m["_t0"]).total_seconds()) / 3600
        man_dur[m["class"]] += d; dur_bh[f"{m['_batch']}|{m['host']}"] += d
        ivs[m["host"]].append((m["_t0"], m["_t1"]))
    union_h = {}
    for h, v in ivs.items():
        tot = 0.0; cur = None
        for a0, a1 in sorted(v):
            if cur and a0 <= cur[1]: cur = (cur[0], max(cur[1], a1))
            else:
                if cur: tot += (cur[1] - cur[0]).total_seconds()
                cur = (a0, a1)
        if cur: tot += (cur[1] - cur[0]).total_seconds()
        union_h[h] = round(tot / 3600, 2)
    span = {}
    for l in open(P("data", "processed", "all.events.jsonl"), encoding="utf-8"):
        r = json.loads(l); t = ts(r["ts"]); k = (r.get("source_file", r["batch"]), r["host"])
        lo, hi = span.get(k, (t, t)); span[k] = (min(lo, t), max(hi, t))
    export_h = {f"{b}|{h}": round((hi - lo).total_seconds() / 3600, 2) for (b, h), (lo, hi) in sorted(span.items())}

    shutil.copyfile(P("data", "processed", "vocab.json"), P("reports", "vocab.json"))
    stats = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "dataset_version": DATASET_VERSION,
        "versions": {"normalize": NORMALIZE_VERSION, "label": LABEL_VERSION, "featurizer": featurize.FEATURIZER_VERSION},
        "scaffold": {**wst.get("scaffold", {}), "evidence_mocA_v1.0": mocA, "scan_v1.0": scan10, "v1.0": v10},
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
                   "events_from_neighbor_file": merge.get("events_from_neighbor_file", 0),
                   "runs_without_events": merge["runs_without_events"]["by_class"]},
        "log_hours_method": "tong thoi luong phien theo manifest (t_end - t_start); khong dung min/max ts_system",
        "log_hours_total": round(sum(man_dur.values()), 2),
        "log_hours_by_batch_host": {k: round(v, 2) for k, v in sorted(dur_bh.items())},
        "session_hours_union_by_host": union_h,
        "export_hours_by_file_host_wazuh_ts": export_h, "export_hours_total": round(sum(export_h.values()), 2),
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
        "tool_rate_before_after_batch07": before_after,
        "hn_signature_split": sst.get("hn_signature_split", {}),
        "excluded_sessions_detail": {r: {"class": c, "why": why, "batch": man[r]["_batch"],
                                         "tasks": [x["source"] for x in man[r].get("steps", [])],
                                         "snapshot_before": man[r].get("snapshot_before") or ""}
                                     for r, c, why in wst["sessions_excluded"] if c != "benign"},
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
    c11 = acc["11_single_feature_separation"]
    print("#11: max tach", c11["max_separation"], c11["max_feature"], "| >= 0.98:", [r["feature"] for r in c11["over_threshold"]],
          "| mot phia:", len(c11["one_sided"]), dict(Counter(r["category"] for r in c11["one_sided"])))

def render_card(s):
    P = s["splits"]; ac = s["acceptance"]; pv = s["provenance"]; ev = s["events"]; wn = s["windows"]
    T3 = s["t1003_003_by_split"]; cov = s["tool_coverage"]; dr = ev["dropped_by_reason"]
    ttps = ["T1016", "T1018", "T1087.002", "T1654", "T1003.003"]
    tick = lambda ok: "ĐẠT" if ok else "KHÔNG ĐẠT"
    c9 = s["acceptance"]["9_train_neg_share_per_tool"]; c10 = s["acceptance"]["10_bg_dist_t1003_vs_revert_control"]
    fmt = lambda x: f"{x:,}".replace(",", " ")
    pct = lambda x: f"{x:.0%}"
    novel = " + ".join(s["params"]["t_novel_batches"])
    excl = Counter(why for _, _, why in wn["sessions_excluded"])
    excl_attack = [(r, why) for r, c, why in wn["sessions_excluded"] if c == "attack"]
    fr = wn["full64_rate"]
    L = []
    sc = s["scaffold"]; c11 = ac["11_single_feature_separation"]; v10 = sc.get("v1.0", {})
    L += [f"# VT-Guard — Dataset card ({s['dataset_version'].replace('v', 'dataset-v')}, bản đóng băng)", "",
          f"Sinh tự động bởi `src/dataset/card.py` lúc {s['generated']}. Số liệu chi tiết: `reports/dataset_stats.json`.", "",
          f"> **Phiên bản `dataset-{s['dataset_version']}` — ĐÓNG BĂNG, thay thế dataset-v1.0.** Split (`data/processed/splits/*.jsonl`), "
          "`vocab.json` và checksum ở mục 10 là cố định: mọi mô hình ở Bước 5–8 phải dùng đúng các file này; trước khi chạy, so sha256 với mục 10. "
          "v1.1 trung hoà dấu vết bộ sinh dữ liệu (mục 7a); thành viên các tập (run_id) giữ nguyên so với v1.0. "
          "Muốn đổi dữ liệu → tạo phiên bản mới, không sửa tại chỗ.", "",
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
          "  - `batch07`: 30 phiên hard-negative gọi công cụ qua `cmd.exe /c` (dc_db_maint 12 trên DC01 có khôi phục snapshot "
          "= phiên đối chứng `revert_control`; admin_net_sweep 8 với ping.exe thật; admin_net_diag 10 với nslookup/nbtstat/netsh/ipconfig).",
          "  - `ntds2`: 15 phiên T1003.003 test 3 (`ntdsutil ifm`); `ntds2v`: 6 phiên T1003.003 test 1 (biến thể vssadmin/shadow copy) — giữ làm biến thể held-out.",
          f"- Manifest: {sum(pv['manifests_by_batch'].values())} phiên — " +
          ", ".join(f"{k} {v}" for k, v in pv["manifests_by_batch"].items()) + "; theo lớp: " +
          ", ".join(f"{k} {v}" for k, v in pv["manifests_by_class"].items()) + ".",
          f"- Pipeline: `normalize.py` ({s['versions']['normalize']}) → `label.py` (labeler {s['versions']['label']}) → "
          f"`merge.py` → `windows.py` → `featurize.py` ({s['versions']['featurizer']}) → `split.py`. Seed cố định {s['seed']}.",
          f"- Event: đọc {fmt(ev['read'])}, giữ {fmt(ev['kept'])} (malicious {fmt(ev['malicious'])}, benign {fmt(ev['benign'])}; "
          f"trong đó nền {fmt(ev['by_run_class'].get('background', 0))}). DC01 {fmt(ev['by_host']['DC01'])} · WIN10-01 {fmt(ev['by_host']['WIN10-01'])}.",
          "- Event malicious theo TTP: " + ", ".join(f"{k} {fmt(v)}" for k, v in ev["malicious_by_ttp"].items()) + ".",
          f"- Thời lượng log: **{s['log_hours_total']} giờ** = tổng thời lượng phiên theo manifest (t_end − t_start, đồng hồ của orchestrator); "
          "theo lớp: " + ", ".join(f"{k} {v} h" for k, v in s["session_hours_by_class"].items()) + ". "
          "Hợp các khung phiên theo host (không đếm trùng phiên chạy song song): " +
          ", ".join(f"{h} {v} h" for h, v in s["session_hours_union_by_host"].items()) + ". "
          f"Đối chiếu: khoảng export theo giờ Wazuh (`ts`, đồng hồ manager) cộng theo file × host = {s['export_hours_total']} giờ, "
          "gồm cả thời gian nghỉ giữa phiên. Không dùng min/max `ts_system` vì sau khi khôi phục snapshot đồng hồ DC01 lệch "
          "(bản trước tính ra 21,1 giờ cho batch07|DC01).", "",
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
    for r, d in s["excluded_sessions_detail"].items():
        tasks = ", ".join(x.split(":", 1)[-1] for x in d["tasks"]) or "—"
        snap = f", snapshot {d['snapshot_before']}" if d["snapshot_before"] else ""
        why = EXCLUDE_WHY.get(d["why"], d["why"])
        if d["why"] == "hard_negative_labeled0_khong_co_tien_trinh_con" and not d["snapshot_before"]:
            why = ("không có event tiến trình con trong khung phiên (task chỉ chạy cmdlet ngay trong tiến trình orchestrator, "
                   "không có khôi phục snapshot); loại hẳn theo quy tắc chung hard_negative labeled=0")
        L.append(f"  - `{r}` ({d['class']}, {d['batch']}, {tasks}{snap}): {why}.")
    L += [f"  - {sum(1 for _, c, why in wn['sessions_excluded'] if c == 'benign')} phiên benign: {EXCLUDE_WHY['stream_rong']}.",
          "- `revert_control` = phiên hard_negative chạy sau khi khôi phục snapshot (dc_db_maint batch07). Chỉ dùng cho card và kiểm tra #10, "
          "KHÔNG làm feature (nằm trong mẫu trường cấm của `featurize.py`).", "",
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
          "**T-hard** chọn theo **chữ ký công cụ** của phiên hard_negative (tập image_name trong cây tiến trình, bỏ cmd/conhost/powershell; "
          "phiên revert_control là chữ ký riêng): mỗi chữ ký có ≥1 phiên vào T-hard và ≥50% vào Train (khi có ≥2 phiên), mục tiêu ~40%; "
          "chỉ nhóm thuần hard_negative mới vào được T-hard. batch07 không vào T-novel. "
          "Phần còn lại (gồm ntds2) chia **Train 80% / T-clean 20%** theo nhóm, phân tầng theo (lớp, host, chữ ký TTP).",
          "- **Nhóm phiên**: các phiên cùng host chồng thời gian (kể cả bắc cầu) dùng chung event nền, nên cả nhóm vào cùng một tập.", "",
          "Phân bổ hard_negative theo chữ ký công cụ (số phiên):", "",
          "| Chữ ký | Tổng | Train | T-clean | T-hard | Điều kiện |", "|---|---|---|---|---|---|"]
    for k, v in s["hn_signature_split"].items():
        L.append(f"| `{k}` | {v['n']} | {v['train']} | {v['t_clean']} | {v['t_hard']} | {tick(v['ok_hard_ge1'] and v['ok_train_ge50'])} |")
    L += ["",
          "### 5a. Cửa sổ T1003.003 theo tập", "",
          "| Tập | Phiên T1003.003 (theo đợt) | Cửa sổ dương T1003.003 | Âm trong phiên T1003.003 | Âm trên DC01 | Âm toàn tập |",
          "|---|---|---|---|---|---|"]
    for k, v in T3.items():
        sb = ", ".join(f"{b} {n}" for b, n in v["sessions_by_batch"].items()) or "—"
        L.append(f"| {SPLIT_NAME[k]} | {v['sessions']} ({sb}) | {v['positive']} | {v['negative_in_t1003_sessions']} | {v['negative_dc01']} | {v['negative_all']} |")
    L += ["",
          "### 5b. Coverage theo công cụ (số cửa sổ chứa tiến trình)", "",
          "Mục tiêu: không công cụ nào chỉ xuất hiện ở phía dương, để mô hình không thể phát hiện chỉ nhờ tên tiến trình.", "",
          "| image_name | Dương (tất cả) | Âm (tất cả) | Train dương / âm | Train % âm | T-clean dương / âm | T-hard âm | T-novel dương / âm | Cảnh báo |",
          "|---|---|---|---|---|---|---|---|---|"]
    for t, v in cov.items():
        warn = "CHỈ DƯƠNG" if v["positive_only_all"] else ("chỉ dương trong Train" if v["positive_only_train"] else "")
        n = v["train_pos"] + v["train_neg"]
        share = v["train_neg"] / n if n else 0
        L.append(f"| `{t}` | {v['all_pos']} | {v['all_neg']} | {v['train_pos']} / {v['train_neg']} | {share:.0%} | "
                 f"{v['t_clean_pos']} / {v['t_clean_neg']} | {v['t_hard_neg']} | {v['t_novel_pos']} / {v['t_novel_neg']} | {warn} |")
    ba = s["tool_rate_before_after_batch07"]
    if ba:
        L += ["", "**Trước / sau batch07** — tỉ lệ dương = số cửa sổ dương chứa công cụ / tổng số cửa sổ chứa công cụ "
              "(trước = bản đóng băng commit d1db577, labeler v6; sau = bản này, labeler v7):", "",
              "| image_name | Trước: dương / âm | Trước: tỉ lệ dương | Sau: dương / âm | Sau: tỉ lệ dương | Train âm trước → sau |",
              "|---|---|---|---|---|---|"]
        for t, v in ba.items():
            br = "—" if v["before_rate"] is None else f"{v['before_rate']:.0%}"
            ar = "—" if v["after_rate"] is None else f"{v['after_rate']:.0%}"
            bpn = "—" if v["before_pos"] is None else f"{v['before_pos']} / {v['before_neg']}"
            btn = "—" if v["before_train_neg"] is None else v["before_train_neg"]
            L.append(f"| `{t}` | {bpn} | {br} | {v['after_pos']} / {v['after_neg']} | {ar} | {btn} → {v['after_train_neg']} |")
    L += ["",
          f"Công cụ chỉ xuất hiện ở phía dương: **toàn bộ dữ liệu: {', '.join(s['tools_positive_only_all']) or 'không có'}**; "
          f"riêng Train: {', '.join(s['tools_positive_only_train']) or 'không có'}.", "",
          "## 6. Đặc trưng (mỗi event → 268 cột)",
          f"- 7 categorical → chỉ số embedding (`vocab.json`): " + ", ".join(f"`{f}` ({s['features']['vocab_size'][f]})" for f in featurize.CAT_FIELDS) +
          ". Id 0=`<pad>`, 1=`<unk>`, 2=`<none>`. Token vào vocab khi xuất hiện ở ≥2 phiên Train; `integrity_level` gộp SID về tên; "
          f"`parent_image_name` ∈ {{{', '.join(sorted(LAUNCHERS))}}} → `{LAUNCHER_TOKEN}` (gộp ngay trong windows.jsonl).",
          f"- `command_line` → {featurize.CMD_DIM} chiều: chuẩn hoá ({s['versions']['featurizer']}: `canon_cmd` — basename file thực thi đầu dòng lệnh, "
          "bỏ chuyển hướng `>nul 2>&1 1> 2> >>`, `& && | ||` → khoảng trắng; rồi chữ thường, bỏ nháy, GUID/hex/số → ký hiệu), char n-gram 3–5, "
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
          "  - v7: phiên = đúng khung [t_start, t_end] của manifest (±5 s) so bằng `ts_system`; con của orchestrator sinh ngoài mọi khung "
          f"bị loại (`orch_child_outside`, {fmt(dr.get('orch_child_outside', 0))} event). v4–v6 gán tiến trình vào phiên theo giờ Wazuh (trễ 40–60 s) "
          "và kéo khung tới lúc phiên kế tiếp bắt đầu, nên (1) 102 event của phiên attack bị gán nhãn benign/hard-negative của phiên chạy ngay sau "
          "(vd nbtstat/netsh/nslookup của T1016), (2) lệnh người vận hành gõ sau phiên trong cùng cửa sổ PowerShell (w32tm, VMwareToolboxCmd timesync, "
          "whoami) bị gán vào phiên (batch07 `20261015-122828-dc01-h`: 61 → 45 event). Đối chiếu v6↔v7: 400 event đổi trạng thái hoặc phiên.",
          "  - v7 cũng nạp manifest của đợt bên cạnh khi khung phiên giao với khung các phiên của đợt đang gán nhãn (±10 phút): "
          "export cắt theo giờ Wazuh nên tiến trình của `20261015-084801-dc01-a` (ntds2v) nằm trong file ntds2; phiên này nay có "
          f"{ev.get('events_from_neighbor_file', 0)} event và không còn bị loại.",
          f"- Khử trùng lặp theo `(host, channel, record_id, event_id, ts_system)`: khôi phục snapshot DC01 làm `record_id` quay lui, "
          f"khoá chỉ có `record_id` sẽ xoá nhầm {fmt(ev['brief_key_collisions'])} event thật.",
          "- Chia theo phiên và nhóm phiên: không `run_id`/session nào ở 2 tập, không cặp phiên Train/kiểm thử nào chồng thời gian trên cùng host.",
          "- Vocab fit chỉ trên Train; T-novel thật sự chứa token chưa thấy.", "",
          "### 7a. Rò rỉ dấu vết bộ sinh dữ liệu (scaffold) và cách xử lý (dataset-v1.1)",
          "Ở Bước 5, B1 lộ ra rằng **cách khởi chạy công cụ** khác nhau giữa bộ sinh tấn công (Atomic Red Team) và script hard-negative tự viết "
          "(batch06/07) — không phải hành vi:",
          "- **Đường dẫn cmd**: ART gọi `\"cmd.exe\" /c …` (283/283 dòng lệnh attack); script hard-negative gọi `\"C:\\Windows\\System32\\cmd.exe\" /c …` (236/236).",
          "- **Chuyển hướng**: chỉ hard-negative batch07 có `>nul 2>&1` (212/212).",
          "- **conhost.exe**: ART chạy cmd trong console riêng → `cmd.exe→conhost.exe` ở 131/149 phiên attack, 0 phiên hard-negative "
          "(script dùng `Start-Process -NoNewWindow`).",
          "- **Launcher cha**: công cụ trong script benign do `powershell.exe` sinh trực tiếp, trong ART do `cmd.exe` sinh "
          "(`powershell.exe→arp/netstat/route/ipconfig/net` chỉ ở hard-negative; `cmd.exe→arp`, `powershell.exe→powershell.exe` chỉ ở attack).", "",
          "**Bằng chứng định lượng (mốc A, dataset-v1.0, B1 TF-IDF+LR):** bỏ dấu vết đường dẫn + chuyển hướng (B1-canon) gần như không đổi kết quả "
          "— chênh nằm trong khoảng tin cậy; mô hình vẫn tách được nhờ tín hiệu khác (đứng đầu là `img=conhost.exe`):", "",
          "| Mô hình (v1.0) | T-clean F1 | T-hard FPR (FP, trong đó có cmd.exe) | T-novel F1 | T-novel PR-AUC | macro-F1 TTP clean/novel |", "|---|---|---|---|---|---|"]
    for m, v in sc.get("evidence_mocA_v1.0", {}).items():
        L.append(f"| {m} | {fci(v['t_clean_f1'])} | {fci(v['t_hard_fpr'])} ({v['t_hard_fp']}, {v['t_hard_fp_cmd']}) | {fci(v['t_novel_f1'])} | "
                 f"{fci(v['t_novel_pr_auc'])} | {v['macro_f1_clean']:.3f}/{v['macro_f1_novel']:.3f} |")
    s10 = sc.get("scan_v1.0", {})
    L += ["",
          "**Cách xử lý (áp ĐỒNG NHẤT mọi lớp, không xoá event hành vi):**",
          f"1. Loại hẳn mọi event `image_name` ∈ {{{', '.join(sorted(sc.get('dropped_images', [])))}}} khi dựng stream "
          f"({fmt(sc.get('dropped_total', 0))} event: " + ", ".join(f"{k} {fmt(v)}" for k, v in sc.get("dropped_events", {}).items()) + ").",
          "2. Chuẩn hoá dòng lệnh (featurizer f2): basename file thực thi đầu dòng lệnh, bỏ chuyển hướng `>nul 2>&1 1> 2> >>` và toán tử `& && | ||`.",
          "4. Bỏ đuôi `.exe` của mọi token file thực thi trong dòng lệnh (featurizer f3): công cụ do PowerShell gọi trực tiếp mang `arp.exe -a`, "
          "`net.exe …` còn ART gõ `arp -a`, `net …`. Chỉ đổi text dòng lệnh; `image_name` giữ nguyên. Số cửa sổ và thành viên các tập không đổi.",
          f"3. Gộp `parent_image_name` ∈ {{{', '.join(sorted(sc.get('launcher_parents', [])))}}} → `{sc.get('launcher_token')}` ở mọi nơi dùng parent "
          "(windows.jsonl, vocab, cặp cha→con).",
          "- **Giữ nguyên có chủ ý**: route/netstat/ipconfig/\"Domain Admins\" của kịch bản benign; tham số tấn công (arp, `%USERDNSDOMAIN%`, "
          "`-timeout`, truy vấn nslookup, adsisearcher, `ifm`); event ESENT/Directory Service do `ntdsutil ifm` sinh ra. Đây là hành vi hoặc lỗ hổng "
          "coverage — xử lý bằng ablation + hạn chế (mục 9), không xoá dữ liệu.", "",
          f"**Ảnh hưởng tới cửa sổ:** {v10.get('windows', '?')} → {wn['total']} cửa sổ ({v10.get('positive', '?')} → {wn['positive']} dương; "
          f"trước khi chặn K: {v10.get('before_cap', '?')} → {wn['before_cap']}). Bỏ conhost làm stream ngắn lại; phiên có stream vượt 64 event "
          "chỉ nhờ event conhost giờ chỉ còn 1 cửa sổ (16 phiên mất đúng 1 cửa sổ). Cả 149 phiên attack vẫn có ≥1 cửa sổ dương. "
          "**Thành viên các tập giữ nguyên**: danh sách run_id mỗi tập và `assignment.json` trùng khớp v1.0 (split tất định theo seed + run_id).", "",
          "| Tập | Phiên | Cửa sổ v1.0 → v1.1 | Dương v1.0 → v1.1 |", "|---|---|---|---|"]
    for k, p_ in P.items():
        o = v10.get("splits", {}).get(k, {})
        L.append(f"| {SPLIT_NAME[k]} | {p_['sessions']} | {o.get('windows', '?')} → {p_['windows']} | {o.get('positive', '?')} → {p_['positive']} |")
    L += ["",
          f"**Quét đặc trưng đơn lẻ trước/sau** (`src/dataset/scaffold_scan.py`): mức tách cao nhất {s10.get('max', '?')} (`image=conhost.exe`, v1.0) → "
          f"{c11['max_separation']} (`{c11['max_feature']}`, v1.1); số đặc trưng một-phía {s10.get('n_one_sided', '?')} → {len(c11['one_sided'])}. "
          "Danh sách đầy đủ: `reports/step5/scaffold_scan_v1.0.json`, `scaffold_scan_v1.1.json`.", "",
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
          f"| 8 | Vocab chỉ fit trên Train | {tick(ac['8_vocab_fit_only_train'])} |",
          f"| 9 | Train có cửa sổ âm ≥{c9['min_neg_share']:.0%} số cửa sổ chứa từng công cụ ({', '.join(t.replace('.exe', '') for t in c9['tools'])}) | "
          + tick(not c9["failed"]) + (f" ({', '.join(c9['failed'])})" if c9["failed"] else "") + " |",
          f"| 10 | So phân bố (channel, event_id) của event nền: cửa sổ dương T1003.003 vs cửa sổ revert_control | "
          f"đã chạy: khoảng cách biến phân toàn phần (TVD) = {c10['total_variation_distance']} (xem bảng dưới) |", "",
          f"| 11 | Không đặc trưng đơn lẻ nào tách attack/hard_negative với mức tách ≥ {c11['threshold']} (thường trực) | "
          f"{tick(c11['ok'])}: cao nhất {c11['max_separation']} (`{c11['max_feature']}`) |", "",
          f"**Tổng 1–8: {tick(s['acceptance_pass'])}. #9: {tick(not c9['failed'])}. #10: báo cáo (không có ngưỡng). #11: {tick(c11['ok'])}.**", "",
          "Kiểm tra #9 — tỉ lệ cửa sổ âm trong Train theo công cụ (không sửa số liệu để ép đạt):", "",
          "| Công cụ | Train dương | Train âm | % âm | Kết quả |", "|---|---|---|---|---|"]
    for t, v in c9["tools"].items():
        ns = "—" if v["neg_share"] is None else f"{v['neg_share']:.0%}"
        L.append(f"| `{t}` | {v['train_pos']} | {v['train_neg']} | {ns} | {tick(v['ok'])} |")
    L += ["",
          f"Kiểm tra #10 — event nền trong {c10['windows'].get('t1003_pos', 0)} cửa sổ dương T1003.003 ({fmt(c10['bg_events'].get('t1003_pos', 0))} event) "
          f"so với {c10['windows'].get('revert_control', 0)} cửa sổ revert_control ({fmt(c10['bg_events'].get('revert_control', 0))} event); "
          "10 cặp (channel, event_id) chênh lệch nhiều nhất (tỉ lệ trên tổng event nền mỗi phía):", "",
          "| channel:event_id | Dương T1003.003 | revert_control | Chênh |", "|---|---|---|---|"]
    for x in c10["top10"]:
        L.append(f"| `{x['channel_event']}` | {x['t1003_pos']:.1%} | {x['revert_control']:.1%} | {x['diff']:+.1%} |")
    L += ["",
          "Kiểm tra #11 — 10 đặc trưng có mức tách cao nhất (max(AUC, 1−AUC); điểm = tỉ lệ event mang giá trị trong cửa sổ):", "",
          "| Đặc trưng | Mức tách | Phía | % cửa sổ attack | % cửa sổ HN |", "|---|---|---|---|---|"]
    for r in c11["top10"]:
        L.append(f"| `{r['feature']}` | {r['separation']:.3f} | {r['side']} | {100 * r['pct_windows_attack']:.1f}% | {100 * r['pct_windows_hn']:.1f}% |")
    L += ["", f"Đặc trưng **một phía** còn lại sau trung hoà ({len(c11['one_sided'])}; có ở ≥10% cửa sổ một nhóm, 0 phiên nhóm kia) — "
          "phân loại sơ bộ để người duyệt:", "",
          "| Đặc trưng | Phía | % cửa sổ | Phiên | Phân loại sơ bộ |", "|---|---|---|---|---|"]
    for r in c11["one_sided"]:
        pctw = r["pct_windows_attack"] if r["side"] == "attack" else r["pct_windows_hn"]
        ns = r["sessions_attack"] if r["side"] == "attack" else r["sessions_hn"]
        L.append(f"| `{r['feature']}` | {r['side']} | {100 * pctw:.1f}% | {ns} | {r['category']} |")
    L += ["",
          "Đọc kết quả #10: phần chênh không hoàn toàn là nhiễu khôi phục snapshot. `Application:216` và `Application:330` (ESENT) chỉ xuất hiện "
          "ở ntds/ntds2 — ESENT ghi khi `ntdsutil ifm` sao chép CSDL AD, tức tác động phụ thật của kỹ thuật nằm ngoài cây tiến trình "
          "(vẫn là event nền, nhãn benign). Các mục còn lại (Sysmon 3/22, logon 4624/4672/4634, WER 1001) là hoạt động nền khác nhau "
          "giữa hai nhóm phiên; revert_control mới có 12 cửa sổ nên ước lượng còn nhiễu.", "",
          "## 9. Hạn chế đã biết"]
    sa, st = s["tools_positive_only_all"], s["tools_positive_only_train"]
    pc = lambda t, k: cov.get(t, {}).get(k, 0)
    L += [f"- **Kiểm tra #9**: " + (f"{', '.join(f'`{t}`' for t in c9['failed'])} có ít hơn {c9['min_neg_share']:.0%} cửa sổ âm trong Train "
          "(không ép đạt bằng cách sửa số liệu; cần thêm phiên hard-negative hoặc chấp nhận và báo cáo ablation)." if c9["failed"]
          else f"mọi công cụ theo dõi đều có ≥{c9['min_neg_share']:.0%} cửa sổ âm trong Train."),
          f"- **Đường tắt theo tiến trình**: sau khi thêm batch06–07, "
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
          "Từ v6 không còn ghép nhầm event theo PID, nhưng event nền phát ra lúc đồng hồ lệch có `ts_system` sai nên có thể rơi ra ngoài (hoặc vào nhầm) khung thời gian phiên. "
          "Hệ quả hệ thống của việc khôi phục (dịch vụ khởi động lại) có thể tương quan với lớp. batch07 thêm phiên đối chứng revert_control "
          f"(hard_negative có khôi phục snapshot); kiểm tra #10 cho TVD = {c10['total_variation_distance']} giữa event nền của cửa sổ dương T1003.003 "
          f"và cửa sổ revert_control — chênh lớn nhất ở `{c10['top10'][0]['channel_event']}` ({c10['top10'][0]['diff']:+.1%}).",
          f"- **Độ dài cửa sổ khác nhau theo lớp**: tỉ lệ cửa sổ đủ 64 event — " +
          ", ".join(f"{k} {pct(v)}" for k, v in fr.items()) + ". Không đưa `n_events` vào feature; khi huấn luyện nên cắt ngẫu nhiên độ dài.",
          "- **Phiên chạy song song trên WIN10-01**: tác động phụ của phiên attack (logon mạng, DNS…) không thuộc cây tiến trình có thể nằm trong "
          "cửa sổ của phiên benign chạy cùng lúc dưới dạng event nền benign → nhiễu nhãn nhẹ.",
          f"- **Phiên không có event riêng**: {ev['runs_without_events'].get('benign', 0)} phiên benign chạy cmdlet ngay trong orchestrator "
          "nên event bị loại cùng orchestrator; cửa sổ của chúng chỉ gồm event nền.",
          f"- **DC01 ít trong T-clean** ({P['t_clean']['windows_by_host'].get('DC01', 0)} cửa sổ so với "
          f"{P['t_clean']['windows_by_host'].get('WIN10-01', 0)} của WIN10-01) do phân tầng theo phiên.",
          "- **Nhiễu nhãn nhỏ đã biết**: một lệnh `net user /domain` người vận hành gõ tay trên DC01 ở batch05 được giữ làm event nền benign.",
          "- **Lỗ hổng coverage (hành vi, giữ nguyên có chủ ý):** (1) phía attack không có `route print`, `netstat -ano`, truy vấn \"Domain Admins\" "
          "— các lệnh này chỉ có ở kịch bản benign nên là đường tắt ngược (sự hiện diện ⇒ benign); (2) phía benign không có hoạt động IFM/ESENT "
          "(event 216/330/2001–2006… của `ntdsutil ifm` chỉ có ở attack). Đo bằng ablation (b)/(c) ở Bước 5–6, không xoá dữ liệu.",
          "- **Giới hạn có chủ ý — `<launcher>→powershell.exe`** (chỉ ở attack, 22% cửa sổ): ART chạy test PowerShell trong một tiến trình "
          "powershell con, còn script benign chạy cmdlet ngay trong tiến trình hiện tại. Không gộp thêm vì `image_name=powershell.exe` là hành vi "
          "được quan sát; đo bằng ablation (b) (bỏ image_name + parent_image_name).",
          "- **Tác động phụ nền chỉ có ở phiên attack**: `svchost.exe→rundll32.exe shell32.dll,SHCreateLocalServerRunDll` (COM local server, "
          "26 event nền ở 25 phiên attack, ngoài cây tiến trình, nhãn benign) và các event ESENT/Directory Service của `ntdsutil ifm` — "
          "mô hình có thể dựa vào event nền này; đo bằng ablation (c) (chỉ cây tiến trình).",
          "- Chỉ 2 host, 2 tài khoản, 1 domain lab; phạm vi là 5 TTP Discovery/Credential Access, chưa có lateral movement hay persistence.", "",
          "## 10. Tái lập",
          "```",
          "python src/label/label.py data/interim/<b>.norm.jsonl manifests/<b>,manifests/<cac dot khac...> data/processed/<b>.labeled.jsonl > reports/<b>.stats.json",
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
