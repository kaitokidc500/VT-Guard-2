#!/usr/bin/env python3
"""VT-Guard Buoc 9 (kieu B) - bo chia cua so TRUC TIEP (docs/STEP9-BRIEF.md muc 2.1).

Luc chay that KHONG co manifest / nhan phien, nen gom event theo (host + thoi gian): toi da W = 64 event / cua so; dong cua so
khi du W event, khi host im lang qua idle_s giay (theo dong ho nhan log: Wazuh `timestamp`) hoac khi khoang trong giua hai event
(theo ts_system) vuot gap_s giay. Cua so khong chong lan (dataset dung truot 64 / 32 trong khung manifest -> do lech, xem drift.py).

TIEN XU LY = DUNG pipeline tao dataset-v1.2, KHONG them / bot quy tac:
  R0 normalize v1 (src/normalize/normalize.py, goi lai nguyen ham normalize), chi event Windows eventchannel (`data.win`).
  R1 manh vo 4103 khong co channel / event_id / record_id -> loai (labeler v5 'ps_fragment').
  R2 khu trung lap theo (host, channel, record_id, event_id, ts_system) (merge.py).
  R3 upload manifest: EID1 / 4688 co dong lenh khop UPLOAD_RE + cay con -> loai (labeler v5 'harness_upload').
  R4 tien trinh PowerShell co script block 4103/4104 khop OPERATOR_RE (khung ART / VT) -> loai MOI event cua tien trinh do
     trong doan song cua PID (labeler: 'orchestrator' / 'operator_console'). Con truc tiep cua no + cay con:
       tool_mode="orchestrator" (MAC DINH): nhu executor-root cua orchestrator trong labeler - HARNESS (conhost / hostname /
         whoami / scp / ssh) + cay con loai ('art_harness'), con khac GIU.
       tool_mode="console": nhu 'operator_console' - con truc tiep + cay con LOAI.
     Ly do co hai che do: dataset nhan biet orchestrator bang exclude_pids trong manifest (khong co luc chay that); tien trinh
     chay khung ART chi con nhan biet duoc qua script block, ma labeler co HAI quy tac cho cung dau hieu do. drift.py do ca hai.
  R5 bo event image_name == conhost.exe; parent cmd.exe / powershell.exe -> '<launcher>'; giu dung truong EVENT_FIELDS,
     sap xep theo (ts_system, channel, record_id) (windows.py).
KHONG tai hien duoc (can khung phien trong manifest): 'orch_child_outside' (con cua orchestrator sinh ngoai moi khung phien).
Ghep event khong co process_guid (4103/4104, Security) vao tien trinh theo (host, PID, ts_system) trong vong doi [EID1, EID5]
+- 2 s nhu labeler v6; 4688 khong khop EID1 ke thua theo tien trinh tao nhu labeler v8.
Xuat cua so dung schema windows.jsonl (window_id, host, t0, t1, events) de nap thang vao src/pipeline/infer.py.
"""
import os, sys
from bisect import bisect_right, insort
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("../normalize", "../label", "../dataset"): sys.path.insert(0, os.path.join(HERE, d))
from normalize import normalize                                                   # noqa: E402
from label import HARNESS, UPLOAD_RE, OPERATOR_RE, LIFE_SLACK, is_fragment       # noqa: E402
from windows import EVENT_FIELDS, SCAFFOLD_DROP_IMAGES, neutral_parent            # noqa: E402

W_DEFAULT, IDLE_DEFAULT, GAP_DEFAULT = 64, 30.0, 120.0
DEDUP_MAX = 2_000_000

def ts(s):
    """ISO 8601 (Z / +0000 / 7 chu so phan giay) -> datetime UTC; None neu rong."""
    if not s: return None
    s = s.replace("Z", "+00:00").replace("+0000", "+00:00")
    if "." in s:
        head, rest = s.split(".", 1); off = "+00:00"
        for c in ("+", "-"):
            if c in rest: off = rest[rest.index(c):]; rest = rest[:rest.index(c)]; break
        s = f"{head}.{''.join(ch for ch in rest if ch.isdigit())[:6]}{off}"
    d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

def iso(d): return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def dedup_key(r): return (r.get("host"), r.get("channel"), r.get("record_id"), r.get("event_id"), r.get("ts_system"))

def slim(r):
    """Ban ghi event trong cua so: dung windows.slim (EVENT_FIELDS + ts = ts_system + has_dns_query, parent trung hoa)."""
    e = {k: r.get(k) for k in EVENT_FIELDS}
    e["parent_image_name"] = neutral_parent(e["parent_image_name"])
    e["ts"] = r["ts_system"]
    e["has_dns_query"] = bool(r.get("dns_query"))
    return e

class Prep:
    """Trang thai tien xu ly theo luong (cay tien trinh, vong doi PID, tien trinh khung ART, upload). Chi doc log, khong nhan."""
    def __init__(self, tool_mode="orchestrator"):
        assert tool_mode in ("orchestrator", "console")
        self.tool_mode = tool_mode
        self.seen = set(); self.seen_q = deque()
        self.parent = {}                     # guid -> parent guid
        self.e1 = {}                         # guid -> (host, pid, ppid, image_name, ts)
        self.life = defaultdict(list)        # (host, pid) -> [[start, end|None, guid]] theo ts_system
        self.end = {}                        # guid -> ts EID5
        self.starts = defaultdict(list)      # (host, pid) -> [ts Wazuh cua EID1] (doan song nhu labeler.console_segments)
        self.tools = set()                   # (host, pid, seg) tien trinh chay khung ART / VT
        self.upload = set()                  # guid goc upload
        self.stats = defaultdict(int)

    # ---- nap ----
    def ingest(self, src):
        """Nhan 1 _source tho; -> event chuan hoa (dict) hoac None neu bi loai o R0 / R1 / R2."""
        if not src.get("data", {}).get("win"): self.stats["r0_khong_phai_win"] += 1; return None
        r = normalize(src)
        if is_fragment(r): self.stats["r1_ps_fragment"] += 1; return None
        k = dedup_key(r)
        if k in self.seen: self.stats["r2_trung_lap"] += 1; return None
        self.seen.add(k); self.seen_q.append(k)
        if len(self.seen_q) > DEDUP_MAX: self.seen.discard(self.seen_q.popleft())
        r["_t"] = ts(r.get("ts_system")) or ts(r.get("ts")); r["_w"] = ts(r.get("ts"))
        h, pid = r["host"], r["process_id"]
        if r["event_id"] == 1 and r.get("process_guid"):
            g = r["process_guid"]; self.e1[g] = (h, pid, r.get("parent_process_id"), r.get("image_name"), r["_w"])
            if r.get("parent_process_guid"): self.parent[g] = r["parent_process_guid"]
            if r["_t"]:
                lst = self.life[(h, pid)]; lst.append([r["_t"], self.end.get(g), g]); lst.sort(key=lambda x: x[0])
                for i, x in enumerate(lst):
                    if x[1] is None and i + 1 < len(lst): x[1] = lst[i + 1][0]
            if r["_w"] and pid is not None: insort(self.starts[(h, pid)], r["_w"])
            if UPLOAD_RE.search(r.get("command_line") or ""): self.upload.add(g)
        elif r["event_id"] == 5 and r.get("process_guid") and r["_t"]:
            self.end[r["process_guid"]] = r["_t"]
            for x in self.life.get((h, pid), []):
                if x[2] == r["process_guid"]: x[1] = r["_t"]
        if r["event_id"] in (4103, 4104) and pid is not None and r["_w"]:
            txt = (r.get("script_block_text") or "") + "\n" + (r.get("ps_payload") or "")
            if OPERATOR_RE.search(txt): self.tools.add((h, pid, self.seg(h, pid, r["_w"])))
        return r

    def seg(self, h, pid, w): return bisect_right(self.starts.get((h, pid), []), w)

    def guid_of(self, h, pid, when):
        best = None
        if pid is None or when is None: return None
        for st, en, g in self.life.get((h, pid), []):
            if st - LIFE_SLACK <= when and (en is None or when <= en + LIFE_SLACK): best = g
        return best

    def is_tool(self, h, pid, w):
        return pid is not None and w is not None and (h, pid, self.seg(h, pid, w)) in self.tools

    # ---- quyet dinh loai (goi lai luc dong cua so de dung trang thai moi nhat) ----
    def drop_reason(self, r):
        h, pid, w = r["host"], r["process_id"], r["_w"]
        if (r.get("image_name") or "").lower() in SCAFFOLD_DROP_IMAGES: return "r5_conhost"
        if self.is_tool(h, pid, w): return "r4_tien_trinh_khung_art"
        g = r.get("process_guid") or self.guid_of(h, pid, r["_t"])
        if g is None and r["event_id"] == 4688 and r.get("parent_process_id") is not None:
            pp = r["parent_process_id"]
            if self.is_tool(h, pp, w):                                   # con truc tiep cua tien trinh khung, khong khop EID1
                if UPLOAD_RE.search(r.get("command_line") or ""): return "r3_upload"
                if self.tool_mode == "console": return "r4_con_cua_console"
                return "r4_harness" if (r.get("image_name") or "") in HARNESS else None
            g = self.guid_of(h, pp, r["_t"])
        if g is None: return None
        chain, x = [], g
        while x and x not in chain and len(chain) < 64: chain.append(x); x = self.parent.get(x)
        if any(c in self.upload for c in chain): return "r3_upload"
        for c in chain:                                                   # goc = con truc tiep cua tien trinh khung ART
            e = self.e1.get(c)
            if e and self.is_tool(e[0], e[2], e[4]):
                if self.tool_mode == "console": return "r4_con_cua_console"
                return "r4_harness" if (e[3] or "") in HARNESS else None
        return None

class Windower:
    """Gom event theo host. add(sources, now) / tick(now) -> danh sach cua so da dong (schema windows.jsonl + metadata)."""
    def __init__(self, W=W_DEFAULT, idle_s=IDLE_DEFAULT, gap_s=GAP_DEFAULT, tool_mode="orchestrator"):
        self.W, self.idle, self.gap = W, timedelta(seconds=idle_s), timedelta(seconds=gap_s)
        self.prep = Prep(tool_mode)
        self.buf = defaultdict(list)          # host -> event dang mo
        self.last_arrival = {}                # host -> now luc nhan event gan nhat
        self.burst = {}                       # host -> (ma dot, so event da phat trong dot)
        self.nkeep, self.maxt = {}, {}        # host -> so event giu (uoc luong luc nap) / ts_system lon nhat trong cua so mo
        self.dropped = defaultdict(int)
        self.params = {"W": W, "idle_s": idle_s, "gap_s": gap_s, "tool_mode": tool_mode}

    def add(self, sources, now):
        out = []
        for s in sources:
            r = self.prep.ingest(s)
            if r is None or not r.get("host"): continue
            h = r["host"]
            if self.buf.get(h) and r["_t"] and self.maxt.get(h) and r["_t"] - self.maxt[h] > self.gap:
                out += self._close(h, now, "khoang_trong_su_kien", new_burst=True)
            self.buf[h].append(r); self.last_arrival[h] = now
            if r["_t"] and (self.maxt.get(h) is None or r["_t"] > self.maxt[h]): self.maxt[h] = r["_t"]
            if self.prep.drop_reason(r) is None:
                self.nkeep[h] = self.nkeep.get(h, 0) + 1
                if self.nkeep[h] >= self.W:                      # dem lai voi trang thai moi nhat truoc khi dong
                    self.nkeep[h] = sum(self.prep.drop_reason(x) is None for x in self.buf[h])
                    if self.nkeep[h] >= self.W: out += self._close(h, now, "du_W")
        return out + self.tick(now)

    def tick(self, now, force=False):
        out = []
        for h in list(self.buf):
            if self.buf[h] and (force or now - self.last_arrival[h] > self.idle):
                out += self._close(h, now, "ket_thuc_luong" if force else "host_im_lang", new_burst=True)
        return out

    def _close(self, h, now, why, new_burst=False):
        rows = self.buf.pop(h, []); self.nkeep.pop(h, None); self.maxt.pop(h, None)
        keep = []
        for r in rows:
            d = self.prep.drop_reason(r)
            if d: self.dropped[d] += 1
            else: keep.append(r)
        res = []
        keep.sort(key=lambda r: (r["_t"] or datetime.min.replace(tzinfo=timezone.utc), r["channel"] or "", r["record_id"] or -1))
        for i in range(0, len(keep), self.W):                  # trang thai moi co the giu > W event -> tach, moi cua so <= W
            part = keep[i:i + self.W]
            bid, n = self.burst.get(h) or (f"L{part[0]['_t'].strftime('%Y%m%d-%H%M%S')}-{h.lower()}", 0)
            wins = [ws for ws in (r.get("_w") for r in part) if ws]
            res.append({"window_id": f"{bid}:w{n:05d}", "host": h, "t0": part[0]["ts_system"], "t1": part[-1]["ts_system"],
                        "events": [slim(r) for r in part], "n_events": len(part), "close_reason": why,
                        "ingest_first": iso(min(wins)) if wins else None, "ingest_last": iso(max(wins)) if wins else None,
                        "closed_at": iso(now), "_keys": [dedup_key(r) for r in part]})
            self.burst[h] = (bid, n + len(part))
        if new_burst: self.burst.pop(h, None)
        return res
