#!/usr/bin/env python3
"""VT-Guard normalizer v0.
Doc moi event tho (archives JSON tu Wazuh Indexer) -> 1 dong schema phang.
Chay: python normalize.py <input.json | input_dir> <output.jsonl>
Ho tro: file _search cua Indexer (hits.hits) HOAC file JSONL moi dong 1 _source.
"""
import json, sys, glob, os, re, hashlib

HOST_ROLE = {"DC01": "domain_controller", "WIN10-01": "workstation"}

def to_int(v):
    if v is None: return None
    s = str(v).strip()
    try:
        return int(s, 16) if s.lower().startswith("0x") else int(s)
    except ValueError:
        return None

def norm_user(*vals):
    for v in vals:
        if v: return str(v).replace("\\\\", "\\")
    return None

def iter_sources(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        txt = fh.read().strip()
    if not txt: return
    # file _search cua Indexer
    try:
        obj = json.loads(txt)
        if isinstance(obj, dict) and "hits" in obj:
            for h in obj["hits"]["hits"]:
                yield h.get("_source", {})
            return
        if isinstance(obj, dict):
            yield obj; return
        if isinstance(obj, list):
            yield from obj; return
    except json.JSONDecodeError:
        pass
    # JSONL
    for line in txt.splitlines():
        line = line.strip()
        if line:
            try: yield json.loads(line)
            except json.JSONDecodeError: pass

def normalize(s):
    win = s.get("data", {}).get("win", {})
    sysd = win.get("system", {})
    ed = win.get("eventdata", {})
    host = s.get("agent", {}).get("name")
    eid = to_int(sysd.get("eventID"))

    img = ed.get("image") or ed.get("newProcessName")
    pimg = ed.get("parentImage") or ed.get("parentProcessName")
    row = {
        # --- dinh danh & thoi gian ---
        "event_uid": s.get("id") or sysd.get("eventRecordID"),
        "ts": s.get("timestamp"),                      # ISO, da chuan +0000
        "ts_system": sysd.get("systemTime"),
        "host": host,
        "host_role": HOST_ROLE.get(host, "unknown"),
        "agent_id": s.get("agent", {}).get("id"),
        "channel": sysd.get("channel"),
        "event_id": eid,
        "provider": sysd.get("providerName"),
        "record_id": to_int(sysd.get("eventRecordID")),
        # --- tien trinh (xuong song de gan nhan theo cay) ---
        "process_guid": ed.get("processGuid"),
        "parent_process_guid": ed.get("parentProcessGuid"),
        "process_id": to_int(ed.get("processId") or ed.get("newProcessId") or sysd.get("processID")),
        "parent_process_id": to_int(ed.get("parentProcessId")),
        "image": img,
        "image_name": img.split("\\")[-1].lower() if img else None,
        "parent_image": pimg,
        "parent_image_name": pimg.split("\\")[-1].lower() if pimg else None,
        "command_line": ed.get("commandLine"),
        "parent_command_line": ed.get("parentCommandLine"),
        "original_file_name": ed.get("originalFileName"),
        "integrity_level": ed.get("integrityLevel") or ed.get("mandatoryLabel"),
        # --- danh tinh / logon ---
        "user": norm_user(ed.get("user"), None),
        "subject_user": norm_user(ed.get("subjectUserName")),
        "subject_domain": ed.get("subjectDomainName"),
        "subject_logon_id": ed.get("subjectLogonId"),
        "target_user": ed.get("targetUserName"),
        "target_domain": ed.get("targetDomainName"),
        "target_logon_id": ed.get("targetLogonId"),
        "logon_id": ed.get("logonId"),
        "logon_type": to_int(ed.get("logonType")),
        "logon_guid": ed.get("logonGuid"),
        "auth_package": ed.get("authenticationPackageName"),
        # --- mang / DNS (Sysmon 3/22) ---
        "dst_ip": ed.get("destinationIp"),
        "dst_port": to_int(ed.get("destinationPort")),
        "dst_host": ed.get("destinationHostname"),
        "protocol": ed.get("protocol"),
        "dns_query": ed.get("queryName"),
        "dns_result": ed.get("queryResults"),
        # --- script (4103/4104) - giu rieng, dung can than ---
        "script_block_text": ed.get("scriptBlockText"),
        "ps_payload": ed.get("payload"),
        # --- ngu canh luat Wazuh: CHI dung cho baseline B0, KHONG lam feature ---
        "wazuh_rule_id": s.get("rule", {}).get("id"),
        "wazuh_rule_level": s.get("rule", {}).get("level"),
        "wazuh_rule_mitre": s.get("rule", {}).get("mitre", {}).get("id"),
        # --- cho (dien o Buoc 4) ---
        "run_id": None, "label_malicious": None, "label_ttps": [], "label_source": None,
    }
    return row

def main():
    src, out = sys.argv[1], sys.argv[2]
    files = sorted(glob.glob(os.path.join(src, "*.json"))) if os.path.isdir(src) else [src]
    n = 0
    with open(out, "w", encoding="utf-8") as w:
        for f in files:
            for s in iter_sources(f):
                if not s.get("data", {}).get("win"):  # bo event khong phai windows eventchannel
                    continue
                w.write(json.dumps(normalize(s), ensure_ascii=False) + "\n")
                n += 1
    print(f"OK: {n} dong -> {out}")

if __name__ == "__main__":
    main()
