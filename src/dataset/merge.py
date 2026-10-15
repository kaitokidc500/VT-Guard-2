#!/usr/bin/env python3
"""VT-Guard Buoc 4.1 - gop dataset.
Doc data/processed/<batch>.labeled.jsonl (batch01-05 + ntds), gan truong `batch`,
chi giu event dropped=False, khu trung lap, ghi data/processed/all.events.jsonl
va reports/merge.stats.json (thong ke + sha256 de dung cho dataset card).

Quy tac (xem docs/STEP4-BRIEF.md muc 4.1 va ghi chu trong agent.md):
  - Danh sach batch CO DINH (smoke6 la phien thu nghiem, labeler cu -> khong dua vao).
  - Event "manh vo" (khong co channel/event_id/record_id): Wazuh cat vo message
    4103 cua PowerShell, noi dung la pipeline Invoke-AtomicTest -> LOAI (ro ri dau vet cong cu).
  - Khoa khu trung lap = (host, channel, record_id, event_id, ts_system).
    Khoa cua brief (host, record_id, event_id) KHONG du: khoi phuc snapshot DC01 (ntds)
    lam record_id quay lui, nhieu event KHAC NHAU trung khoa -> chi dung de chan doan.
  - Neu mot ban sao cua cung event bi dropped o bat ky dau -> loai ca event (than trong).
Chay: python src/dataset/merge.py [--root .] [--batches batch01,batch02,...]
"""
import argparse, glob, hashlib, json, os, re, sys
from collections import Counter, defaultdict

DEFAULT_BATCHES = ["batch01", "batch02", "batch03", "batch04", "batch05", "ntds"]
LEAK_RE = re.compile(r"atomic|invoke-|\bT1\d{3}(?:\.\d{3})?\b|vt-?guard", re.I)
FEATURE_TEXT = ["command_line", "parent_command_line", "image", "parent_image"]
RAW_SCRIPT = ["script_block_text", "ps_payload"]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

def load_manifest(f):
    try:
        with open(f, encoding="utf-8-sig") as fh: txt = fh.read().strip()
        return json.loads(txt) if txt else None
    except (json.JSONDecodeError, OSError) as e:
        sys.stderr.write(f"CANH BAO: bo qua manifest loi {os.path.basename(f)}: {e}\n"); return None

def load_manifests(root, batches):
    man = {}  # run_id -> manifest (+ _batch)
    for b in batches:
        for f in sorted(glob.glob(os.path.join(root, "manifests", b, "*.manifest.json"))):
            m = load_manifest(f)
            if not m: continue
            if m["run_id"] in man: sys.exit(f"LOI: run_id trung giua cac manifest: {m['run_id']}")
            m["_batch"] = b; man[m["run_id"]] = m
    return man

def dedup_key(r):
    return (r.get("host"), r.get("channel"), r.get("record_id"), r.get("event_id"), r.get("ts_system"))

def is_fragment(r):
    return r.get("channel") is None and r.get("event_id") is None and r.get("record_id") is None

def merge(root, batches):
    st = Counter()
    per_batch = defaultdict(Counter)
    kept = {}                 # dedup_key -> row
    dropped_keys = set()
    brief_keys = Counter()    # (host, record_id, event_id) -> so event khac nhau (chan doan)
    label_conflict = 0
    for b in batches:
        path = os.path.join(root, "data", "processed", f"{b}.labeled.jsonl")
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                pb = per_batch[b]; pb["read"] += 1
                if r.get("dropped"):
                    pb["dropped_label"] += 1; dropped_keys.add(dedup_key(r)); continue
                if is_fragment(r):
                    pb["dropped_fragment"] += 1; continue
                k = dedup_key(r)
                if k in kept:
                    pb["dup"] += 1
                    o = kept[k]
                    if (o["run_id"], o["label_malicious"], o["label_ttps"]) != (r["run_id"], r["label_malicious"], r["label_ttps"]):
                        label_conflict += 1
                    continue
                r["batch"] = b
                kept[k] = r
                brief_keys[(r["host"], r["record_id"], r["event_id"])] += 1
    # ban sao bi dropped o noi khac -> loai
    for k in [k for k in kept if k in dropped_keys]:
        per_batch[kept[k]["batch"]]["dropped_conflict"] += 1; del kept[k]
    st["label_conflict_on_dup"] = label_conflict
    st["brief_key_collisions"] = sum(v - 1 for v in brief_keys.values() if v > 1)
    rows = sorted(kept.values(), key=lambda r: (r["ts"], r["host"], r["channel"], r["record_id"]))
    return rows, per_batch, st

def summarize(rows, man, batches, per_batch, st):
    s = {"n_events": len(rows), "batches": batches, "per_batch_io": {b: dict(c) for b, c in per_batch.items()}}
    s.update(st)
    s["by_host"] = dict(Counter(r["host"] for r in rows))
    s["by_batch"] = dict(Counter(r["batch"] for r in rows))
    s["malicious"] = sum(1 for r in rows if r["label_malicious"])
    s["benign"] = len(rows) - s["malicious"]
    # phan loai event theo class cua phien (background = khong thuoc cay tien trinh phien nao)
    def ev_class(r):
        if r["run_id"] is None: return "background"
        m = man.get(r["run_id"]); return m["class"] if m else "UNKNOWN_RUN"
    s["events_by_run_class"] = dict(Counter(ev_class(r) for r in rows))
    s["events_by_host_class"] = {f"{h}|{c}": n for (h, c), n in sorted(Counter((r["host"], ev_class(r)) for r in rows).items())}
    ttp = Counter()
    for r in rows:
        for t in r["label_ttps"]: ttp[t] += 1
    s["malicious_events_by_ttp"] = dict(sorted(ttp.items()))
    # run_id
    present = defaultdict(set)
    for r in rows:
        if r["run_id"] is not None: present[ev_class(r)].add(r["run_id"])
    s["unique_run_id_by_class"] = {c: len(v) for c, v in sorted(present.items())}
    s["manifests_by_class"] = dict(sorted(Counter(m["class"] for m in man.values()).items()))
    s["manifests_by_batch"] = dict(sorted(Counter(m["_batch"] for m in man.values()).items()))
    allp = set().union(*present.values()) if present else set()
    empty = sorted(rid for rid in man if rid not in allp)
    s["runs_without_events"] = {"n": len(empty), "by_class": dict(Counter(man[r]["class"] for r in empty)),
                                "run_ids": empty}
    # kiem tra nhat quan
    chk = Counter()
    for r in rows:
        m = man.get(r["run_id"]) if r["run_id"] else None
        if r["run_id"] and not m: chk["run_id_not_in_manifest"] += 1
        if m and m["_batch"] != r["batch"]: chk["run_id_batch_mismatch"] += 1
        if r["label_malicious"] and not (m and m["class"] == "attack" and r["label_ttps"]): chk["malicious_without_attack_run"] += 1
        if m and m["class"] == "attack" and not r["label_malicious"]: chk["attack_run_event_not_malicious"] += 1
        if not r["label_malicious"] and r["label_ttps"]: chk["benign_with_ttps"] += 1
    s["consistency_errors"] = dict(chk)
    # chan doan ro ri van ban (CHI bao cao, khong loc; feature loc o 4.3)
    leak = Counter()
    for r in rows:
        lab = "malicious" if r["label_malicious"] else "benign"
        for f in FEATURE_TEXT + RAW_SCRIPT:
            v = r.get(f)
            if v and LEAK_RE.search(v): leak[f"{f}|{lab}"] += 1
    s["leak_marker_hits"] = dict(sorted(leak.items()))
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--batches", default=",".join(DEFAULT_BATCHES))
    a = ap.parse_args()
    root, batches = a.root, a.batches.split(",")
    man = load_manifests(root, batches)
    rows, per_batch, st = merge(root, batches)
    out = os.path.join(root, "data", "processed", "all.events.jsonl")
    with open(out, "w", encoding="utf-8", newline="\n") as w:
        for r in rows: w.write(json.dumps(r, ensure_ascii=False) + "\n")
    s = summarize(rows, man, batches, per_batch, st)
    skipped = sorted(os.path.basename(f).split(".")[0] for f in glob.glob(os.path.join(root, "data", "processed", "*.labeled.jsonl")))
    s["skipped_files"] = [b for b in skipped if b not in batches]
    s["inputs_sha256"] = {b: sha256(os.path.join(root, "data", "processed", f"{b}.labeled.jsonl")) for b in batches}
    s["output"] = "data/processed/all.events.jsonl"
    s["output_sha256"] = sha256(out)
    os.makedirs(os.path.join(root, "reports"), exist_ok=True)
    with open(os.path.join(root, "reports", "merge.stats.json"), "w", encoding="utf-8", newline="\n") as w:
        json.dump(s, w, ensure_ascii=False, indent=2)
    show = {k: v for k, v in s.items() if k not in ("inputs_sha256",)}
    show["runs_without_events"] = {k: v for k, v in s["runs_without_events"].items() if k != "run_ids" or len(v) <= 20}
    print(json.dumps(show, ensure_ascii=False, indent=2))
    bad = s["consistency_errors"]
    print(f"OK: {len(rows)} event -> {out}" if not bad else f"CANH BAO nhat quan: {bad}")

if __name__ == "__main__":
    main()
