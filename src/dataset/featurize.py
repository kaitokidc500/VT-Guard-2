#!/usr/bin/env python3
"""VT-Guard Buoc 4.3 - trich dac trung.
Doc data/processed/windows.jsonl (4.2), bien moi event thanh vector, ghi
data/processed/features.jsonl + data/processed/vocab.json + reports/featurize.stats.json.

Vector moi event (268 cot tho):
  - 7 categorical -> chi so embedding (vocab.json): channel, event_id, image_name,
    parent_image_name, host_role, integrity_level, logon_type.
    Id: 0=<pad>, 1=<unk> (token la), 2=<none> (truong rong). Token vao vocab chi khi xuat hien
    o >= MIN_SESSIONS phien KHAC NHAU cua tap fit (chong hoc thuoc token rieng mot phien).
  - command_line -> 256 chieu: chuan hoa (lower, bo dau nhay/escape, GUID/hex/so -> ky hieu),
    char n-gram 3..5, signed hashing md5 (chi so = md5 mod 256, dau = 1 bit md5), log1p, chuan L2.
    KHONG luu text tho.
  - 5 so: dt_log = log(1 + dt giay so voi event truoc trong cua so, theo ts_system),
    has_network, has_dns, is_powershell_channel, is_security_channel.
KHONG dung (muc 3 brief): wazuh_rule_*, label_*, run_id, event_uid, process_guid,
script_block_text, ps_payload, duong dan day du (image/parent_image), n_events.

Vocab duoc FIT tren mot tap con: mac dinh moi cua so tru batch05 (T-novel chac chan khong lot vao
vocab). O 4.4, split.py fit lai tren Train (--fit-runs) de vocab chi thay du lieu huan luyen.
Chay: python src/dataset/featurize.py [--root .] [--fit-runs runs.txt] [--min-sessions 2]
"""
import argparse, hashlib, json, math, os, re
from collections import Counter, defaultdict
from datetime import datetime

CAT_FIELDS = ["channel", "event_id", "image_name", "parent_image_name", "host_role",
              "integrity_level", "logon_type"]
NUM_FIELDS = ["dt_log", "has_network", "has_dns", "is_powershell_channel", "is_security_channel"]
SOURCE_FIELDS = set(CAT_FIELDS) | {"command_line", "ts", "dst_port", "has_dns_query"}
FORBIDDEN = re.compile(r"^(wazuh_rule_|label_)|^(run_id|event_uid|process_guid|parent_process_guid|"
                       r"script_block_text|ps_payload|image|parent_image|n_events)$")
CMD_DIM, NGRAM = 256, (3, 5)
PAD, UNK, NONE = "<pad>", "<unk>", "<none>"
FEATURIZER_VERSION = "f1"

# Security 4688 ghi mandatory label dang SID, Sysmon ghi chu -> gop ve mot ten
IL_SID = {"S-1-16-0": "Untrusted", "S-1-16-4096": "Low", "S-1-16-8192": "Medium",
          "S-1-16-8448": "MediumPlus", "S-1-16-12288": "High", "S-1-16-16384": "System"}
GUID_RE = re.compile(r"\{?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}?")
HEX_RE = re.compile(r"\b0x[0-9a-f]+\b")
NUM_RE = re.compile(r"\d+")
WS_RE = re.compile(r"\s+")

def token(field, v):
    if v is None or v == "": return NONE
    if field == "integrity_level": return IL_SID.get(v, v)
    return str(v).lower() if field in ("image_name", "parent_image_name") else str(v)

def norm_cmd(s):
    s = s.lower().replace('\\"', " ").replace('"', " ").replace("'", " ")
    s = s.replace("\\\\", "\\")
    s = GUID_RE.sub("<guid>", s); s = HEX_RE.sub("<hex>", s); s = NUM_RE.sub("0", s)
    return WS_RE.sub(" ", s).strip()[:1024]

_cmd_cache = {}
def hash_cmd(s):
    """-> list [(idx, val)] thua, da chuan L2."""
    if not s: return []
    if s in _cmd_cache: return _cmd_cache[s]
    t = norm_cmd(s); acc = defaultdict(float)
    for n in range(NGRAM[0], NGRAM[1] + 1):
        for i in range(len(t) - n + 1):
            d = hashlib.md5(t[i:i + n].encode("utf-8")).digest()
            idx = int.from_bytes(d[:4], "little") % CMD_DIM
            acc[idx] += 1.0 if d[4] & 1 else -1.0
    v = {i: math.copysign(math.log1p(abs(x)), x) for i, x in acc.items() if x != 0}
    nrm = math.sqrt(sum(x * x for x in v.values())) or 1.0
    out = sorted((i, round(x / nrm, 5)) for i, x in v.items())
    _cmd_cache[s] = out
    return out

def ts(s):
    s = s.replace("Z", "+00:00")
    if "." in s:
        head, rest = s.split(".", 1)
        s = f"{head}.{''.join(c for c in rest.split('+')[0] if c.isdigit())[:6]}+00:00"
    return datetime.fromisoformat(s)

def build_vocab(windows, min_sessions):
    seen = {f: defaultdict(set) for f in CAT_FIELDS}
    for w in windows:
        for e in w["events"]:
            for f in CAT_FIELDS: seen[f][token(f, e[f])].add(w["run_id"])
    vocab = {}
    for f in CAT_FIELDS:
        toks = sorted(t for t, runs in seen[f].items() if len(runs) >= min_sessions and t != NONE)
        vocab[f] = {PAD: 0, UNK: 1, NONE: 2, **{t: i + 3 for i, t in enumerate(toks)}}
    return vocab

def featurize_window(w, vocab):
    cat, cmd, num = [], [], []
    prev = None
    for e in w["events"]:
        assert set(e) <= SOURCE_FIELDS, f"truong la trong event: {set(e) - SOURCE_FIELDS}"
        cat.append([vocab[f].get(token(f, e[f]), 1) for f in CAT_FIELDS])
        cmd.append(hash_cmd(e["command_line"]))
        t = ts(e["ts"]); dt = 0.0 if prev is None else max(0.0, (t - prev).total_seconds()); prev = t
        ch = e["channel"] or ""
        num.append([round(math.log1p(dt), 5),
                    int(e["event_id"] == 3 or e["dst_port"] is not None),
                    int(e["event_id"] == 22 or bool(e["has_dns_query"])),
                    int("PowerShell" in ch), int(ch == "Security")])
    return cat, cmd, num

META = ["window_id", "run_id", "batch", "host", "user_role", "tempo", "variant", "t0", "t1",
        "window_malicious", "window_ttps", "window_class", "session_windows_total"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--fit-runs", help="file chua run_id (moi dong 1) dung de fit vocab; mac dinh: moi phien tru batch05")
    ap.add_argument("--min-sessions", type=int, default=2)
    a = ap.parse_args()
    P = lambda *p: os.path.join(a.root, *p)

    # chot danh sach feature: khong nguon nao thuoc danh sach cam
    bad = [f for f in sorted(SOURCE_FIELDS) if FORBIDDEN.search(f)]
    assert not bad, f"feature dung truong cam: {bad}"

    windows = [json.loads(l) for l in open(P("data", "processed", "windows.jsonl"), encoding="utf-8")]
    if a.fit_runs:
        fit_runs = {l.strip() for l in open(a.fit_runs, encoding="utf-8") if l.strip()}
        fit_desc = f"run_id trong {os.path.basename(a.fit_runs)}"
    else:
        fit_runs = {w["run_id"] for w in windows if w["batch"] != "batch05"}
        fit_desc = "moi phien tru batch05 (tam thoi, fit lai tren Train o 4.4)"
    fit = [w for w in windows if w["run_id"] in fit_runs]
    vocab = build_vocab(fit, a.min_sessions)
    vocab["_meta"] = {"featurizer_version": FEATURIZER_VERSION, "cat_fields": CAT_FIELDS,
                      "num_fields": NUM_FIELDS, "special": {PAD: 0, UNK: 1, NONE: 2},
                      "min_sessions": a.min_sessions, "fit": fit_desc, "fit_sessions": len(fit_runs & {w["run_id"] for w in windows}),
                      "fit_windows": len(fit),
                      "cmd": {"dim": CMD_DIM, "ngram": list(NGRAM), "hash": "md5: idx=uint32le(d[0:4]) % dim, sign=d[4]&1",
                              "value": "signed count -> sign*log1p(|x|) -> L2", "normalize": "lower; bo dau nhay; \\\\->\\; GUID-><guid>; 0x..-><hex>; so->0; gop khoang trang; cat 1024"},
                      "integrity_level_map": IL_SID}
    with open(P("data", "processed", "vocab.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=1)

    unk = {s: Counter() for s in ("fit", "batch05", "other")}
    n_ev = 0; nnz = []
    with open(P("data", "processed", "features.jsonl"), "w", encoding="utf-8", newline="\n") as out:
        for w in windows:
            cat, cmd, num = featurize_window(w, vocab)
            grp = "fit" if w["run_id"] in fit_runs else ("batch05" if w["batch"] == "batch05" else "other")
            for row in cat:
                unk[grp]["events"] += 1
                for f, i in zip(CAT_FIELDS, row): unk[grp][f] += i == 1
            nnz += [len(c) for c in cmd if c]; n_ev += len(cat)
            rec = {k: w[k] for k in META}
            rec.update(n_events=len(cat), cat=cat, cmd=cmd, num=num)
            out.write(json.dumps(rec, separators=(",", ":")) + "\n")

    vsize = {f: len(vocab[f]) for f in CAT_FIELDS}
    stats = {
        "featurizer_version": FEATURIZER_VERSION,
        "event_vector": {"categorical_ids": len(CAT_FIELDS), "cmd_hash_dim": CMD_DIM, "numeric": len(NUM_FIELDS),
                         "total_raw_columns": len(CAT_FIELDS) + CMD_DIM + len(NUM_FIELDS)},
        "window_tensor": f"[64, {len(CAT_FIELDS) + CMD_DIM + len(NUM_FIELDS)}] (+ mask; cua so ngan duoc pad o buoc model)",
        "vocab_size_incl_special": vsize,
        "vocab_fit": vocab["_meta"]["fit"], "fit_windows": len(fit), "min_sessions": a.min_sessions,
        "windows": len(windows), "events": n_ev,
        "cmd_events_nonzero": len(nnz), "cmd_unique_strings": len(_cmd_cache),
        "cmd_nnz_per_event": {"median": sorted(nnz)[len(nnz) // 2], "max": max(nnz)} if nnz else {},
        "unk_rate": {g: {f: round(c[f] / c["events"], 4) for f in CAT_FIELDS} for g, c in unk.items() if c["events"]},
        "feature_sources": sorted(SOURCE_FIELDS),
        "forbidden_pattern": FORBIDDEN.pattern,
    }
    with open(P("reports", "featurize.stats.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"OK: {len(windows)} cua so -> data/processed/features.jsonl ; vocab -> data/processed/vocab.json")

if __name__ == "__main__":
    main()
