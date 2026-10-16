#!/usr/bin/env python3
"""VT-Guard dataset-v1.2 - cac kiem dinh phu tro cho dataset card (chi doc du lieu).

- ratio_4688_eid1(): #12 - ti le Security 4688 / Sysmon EID1 cua tien trinh trong cay phien, theo host x lop
  (bo event scaffold conhost nhu windows.py). Sau normalize v1 + labeler v8, moi tien trinh cua cay phien co
  ca hai ban ghi nen ti le ~1 o moi lop; lech -> dau hieu bat doi xung do quy tac gan nhan.
- excluded_audit(): voi moi phien bi loai, dem event cay phien, event cua orchestrator trong khung, event tao
  tien trinh (EID1/4688) con cua orchestrator trong khung (moi trang thai, ke ca bi loai), event nen -> ly do
  dung bang chung (khong suy dien "atomic khong sinh tien trinh con").
- pid_reuse(): quy tac loai orchestrator theo PID KHONG gioi han thoi gian -> tien trinh khac trung PID voi mot
  orchestrator (cung host) bi loai nham. Dem tien trinh (EID1/4688 co image khac powershell.exe, PID thuoc
  exclude_pids) va moi event cua chung (theo process_guid), kem nhan tien trinh cha (de uoc luong co thuoc cay phien).
Chay: python src/dataset/audit.py
"""
import json, os, sys
from collections import Counter, defaultdict
from datetime import timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from windows import BATCHES, load_manifests, ts, is_scaffold_event

RATIO_BAND = (0.9, 1.1)

def _labeled(root):
    for b in BATCHES:
        with open(os.path.join(root, "data", "processed", f"{b}.labeled.jsonl"), encoding="utf-8") as fh:
            for l in fh: yield b, json.loads(l)

def ratio_4688_eid1(root, man=None):
    man = man or load_manifests(root); c = Counter()
    with open(os.path.join(root, "data", "processed", "all.events.jsonl"), encoding="utf-8") as fh:
        for l in fh:
            r = json.loads(l)
            if not r["run_id"] or r["event_id"] not in (1, 4688) or is_scaffold_event(r): continue
            c[(r["host"], man[r["run_id"]]["class"], r["event_id"])] += 1
    out = {}
    for h in sorted({k[0] for k in c}):
        for cl in ("attack", "benign", "hard_negative"):
            e1, e4 = c[(h, cl, 1)], c[(h, cl, 4688)]
            if not e1 and not e4: continue
            r_ = e4 / e1 if e1 else None
            out[f"{h}|{cl}"] = {"eid1": e1, "e4688": e4, "ratio": None if r_ is None else round(r_, 3),
                                "ok": r_ is not None and RATIO_BAND[0] <= r_ <= RATIO_BAND[1]}
    return {"band": list(RATIO_BAND), "cells": out, "ok": all(v["ok"] for v in out.values())}

def excluded_audit(root, excluded, man=None):
    man = man or load_manifests(root)
    ids = {e[0]: e for e in excluded}
    own = Counter()
    with open(os.path.join(root, "data", "processed", "all.events.jsonl"), encoding="utf-8") as fh:
        for l in fh:
            r = json.loads(l)
            if r["run_id"] in ids: own[r["run_id"]] += 1
    by_host = defaultdict(list)
    for rid in ids:
        m = man[rid]; by_host[m["host"]].append((m["_t0"] - timedelta(seconds=5), m["_t1"] + timedelta(seconds=5), rid, set(m["exclude_pids"])))
    orch, child, bg = Counter(), Counter(), Counter()
    for _, r in _labeled(root):
        if not r.get("ts_system"): continue
        t = ts(r["ts_system"])
        for t0, t1, rid, pids in by_host.get(r["host"], []):
            if not (t0 <= t <= t1): continue
            if r["process_id"] in pids: orch[rid] += 1
            elif r["event_id"] in (1, 4688) and r.get("parent_process_id") in pids: child[rid] += 1
            elif not r["run_id"] and not r["dropped"]: bg[rid] += 1
    out = {}
    for rid, (r_, cls, code) in ids.items():
        m = man[rid]; snap = m.get("snapshot_before") or ""
        tasks = [s["source"].split(":", 1)[-1] for s in m.get("steps", [])]
        if orch[rid] == 0 and own[rid] == 0 and bg[rid] == 0: why = "no_telemetry"
        elif child[rid] == 0 and own[rid] == 0: why = "snapshot_no_process_creation" if snap else "cmdlet_in_orchestrator"
        else: why = "needs_review"
        out[rid] = {"class": cls, "batch": m["_batch"], "tasks": tasks, "snapshot_before": snap, "code": code,
                    "own_events": own[rid], "orchestrator_events": orch[rid], "child_process_creation": child[rid],
                    "background_in_window": bg[rid], "why_code": why}
    return out

def pid_reuse(root, man=None):
    man = man or load_manifests(root)
    excl = defaultdict(set)
    for m in man.values(): excl[m["host"]] |= set(m.get("exclude_pids", []))
    guids, procs = set(), []
    rows = []
    for b, r in _labeled(root):
        if r["dropped"] and r["drop_reason"] == "orchestrator" and r["event_id"] in (1, 4688) \
                and r.get("image_name") and r["image_name"] != "powershell.exe" and r["process_id"] in excl[r["host"]]:
            procs.append({"batch": b, "host": r["host"], "pid": r["process_id"], "event_id": r["event_id"], "image": r["image_name"],
                          "parent_image": r.get("parent_image_name"), "ts": r["ts_system"], "process_guid": r.get("process_guid")})
            if r.get("process_guid"): guids.add(r["process_guid"])
    n_ev = Counter()
    for b, r in _labeled(root):
        if r.get("process_guid") in guids and r["dropped"] and r["drop_reason"] == "orchestrator": n_ev[r["event_id"]] += 1
    n_ev[4688] += sum(1 for p in procs if p["event_id"] == 4688)
    return {"process_records": len(procs), "distinct_processes": len({(p["host"], p["pid"], p["image"], p["ts"][:19]) for p in procs if p["event_id"] == 1}) or len(procs),
            "events_dropped": sum(n_ev.values()), "events_by_eid": dict(n_ev),
            "by_image": dict(Counter(p["image"] for p in procs).most_common()),
            "by_parent": dict(Counter(p["parent_image"] for p in procs).most_common()),
            "examples": procs[:12]}

if __name__ == "__main__":
    root = "."
    print(json.dumps(ratio_4688_eid1(root), indent=1))
    print(json.dumps(pid_reuse(root), indent=1, ensure_ascii=False)[:3000])
