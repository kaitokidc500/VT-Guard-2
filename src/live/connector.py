#!/usr/bin/env python3
"""VT-Guard Buoc 9 (kieu B) - nguon log cho che do truc tiep (docs/STEP9-BRIEF.md muc 2.1, 2.3, 5).

Hai nguon, cung giao dien poll() -> (danh sach _source tho, now):
  IndexerSource : moi chu ky (~10-15 s) doc event MOI trong wazuh-archives-* qua REST API Indexer. Truy van giong
                  scripts/export_batch.py (term agent.name + range timestamp, dong goi _source), chi lay phan SAU moc da
                  doc; moc (timestamp + id cac event tai dung moc) luu ra file trang thai de khong doc trung khi khoi dong lai.
  FileSource    : phat lai mot file log da ghi (JSONL moi dong 1 _source, hoac .gz; hoac thu muc *.json nhu data/raw/<dot>/)
                  theo dung thu tu `timestamp` cua Wazuh, chia thanh cac chu ky poll_s giay theo dong ho mo phong -> CUNG
                  pipeline truc tiep (che do replay, du phong buoi bao ve).
Thong tin dang nhap Indexer CHI nap luc chay tu bien moi truong hoac --env-file (KEY=VALUE), KHONG ghi vao code / image / log:
  VTG_INDEXER_URL (vd https://10.20.30.10:9200), VTG_INDEXER_USER, VTG_INDEXER_PASSWORD,
  VTG_INDEXER_CA (duong dan file CA, mount tu ngoai) [+ VTG_INDEXER_CHECK_HOSTNAME=0 khi noi bang IP] hoac
  VTG_INDEXER_INSECURE=1 (bo kiem chung chi, chi lab),
  VTG_AGENTS (mac dinh DC01,WIN10-01).
AlertPusher (tuy chon, mac dinh TAT): ghi canh bao vao index vtguard-alerts-YYYY.MM.DD bang _bulk.
"""
import base64, glob, gzip, json, os, ssl, time, urllib.request
from datetime import datetime, timedelta, timezone

DEFAULT_AGENTS = ("DC01", "WIN10-01")

def load_env_file(path):
    """Doc KEY=VALUE (bo dong trong / '#'), dat vao os.environ neu chua co. Khong in gia tri."""
    if not path: return []
    keys = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1); k = k.strip(); v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v); keys.append(k)
    return keys

def _parse(s):
    s = s.replace("Z", "+00:00").replace("+0000", "+00:00")
    if "." in s:
        head, rest = s.split(".", 1); off = "+00:00"
        for c in ("+", "-"):
            if c in rest: off = rest[rest.index(c):]; rest = rest[:rest.index(c)]; break
        s = f"{head}.{''.join(ch for ch in rest if ch.isdigit())[:6]}{off}"
    return datetime.fromisoformat(s)

# ---------------- file (replay) ----------------
def read_log(path):
    """-> list _source tu file JSONL (.jsonl / .json / .gz) hoac thu muc chua *.json / *.jsonl / *.gz."""
    files = sorted(sum((glob.glob(os.path.join(path, p)) for p in ("*.json", "*.jsonl", "*.gz")), [])) if os.path.isdir(path) else [path]
    out = []
    for f in files:
        op = gzip.open if f.endswith(".gz") else open
        with op(f, "rt", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line: continue
                try: o = json.loads(line)
                except json.JSONDecodeError: continue
                if isinstance(o, dict) and "hits" in o:
                    out += [h.get("_source", {}) for h in o["hits"]["hits"]]
                elif isinstance(o, dict): out.append(o.get("_source", o))
    return out

class FileSource:
    """Phat lai log theo timestamp Wazuh; moi poll() tra cac event co timestamp trong (t, t + poll_s]. speed: 0 = nhanh nhat,
    k > 0 = ngu poll_s / k giay giua cac chu ky (demo, vd 10 = nhanh gap 10 lan thoi gian that), tua nhanh khoang im lang > FF_GAP_S."""
    FF_GAP_S = 120.0
    def __init__(self, path, poll_s=10.0, speed=0.0):
        rows = [r for r in read_log(path) if r.get("timestamp")]
        rows.sort(key=lambda r: _parse(r["timestamp"]))
        self.rows, self.i, self.poll_s, self.speed = rows, 0, poll_s, speed
        self.now = _parse(rows[0]["timestamp"]) if rows else datetime.now(timezone.utc)
        self.mode = "replay"; self.path = path

    def done(self): return self.i >= len(self.rows)

    def info(self): return {"kind": "file", "name": os.path.basename(self.path.rstrip("/\\")), "n_events": len(self.rows)}

    def poll(self):
        self.now += timedelta(seconds=self.poll_s); out = []
        while self.i < len(self.rows) and _parse(self.rows[self.i]["timestamp"]) <= self.now:
            out.append(self.rows[self.i]); self.i += 1
        # speed > 0: chi ngu khi co event hoac event ke tiep trong FF_GAP_S giay; khoang im lang dai (vd giua hai doan log mau) tua
        # nhanh. Dong ho luong van tien dung poll_s moi chu ky -> cua so / canh bao giong het speed = 0.
        if self.speed > 0 and (out or (self.i < len(self.rows) and (_parse(self.rows[self.i]["timestamp"]) - self.now).total_seconds() <= self.FF_GAP_S)):
            time.sleep(self.poll_s / self.speed)
        return out, self.now

# ---------------- Indexer (live) ----------------
class IndexerSource:
    def __init__(self, state_path, poll_s=12.0, agents=None, start=None, page=2000):
        self.url = os.environ.get("VTG_INDEXER_URL", "").rstrip("/")
        user, pw = os.environ.get("VTG_INDEXER_USER"), os.environ.get("VTG_INDEXER_PASSWORD")
        if not (self.url and user and pw): raise SystemExit("Thieu VTG_INDEXER_URL / VTG_INDEXER_USER / VTG_INDEXER_PASSWORD (nap qua --env-file).")
        self.auth = "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()
        ca = os.environ.get("VTG_INDEXER_CA")
        if ca:
            self.ctx = ssl.create_default_context(cafile=ca)
            # wazuh-docker: chung chi Indexer cap cho CN 'wazuh.indexer'; noi bang IP thi van kiem CA nhung bo kiem ten may
            if os.environ.get("VTG_INDEXER_CHECK_HOSTNAME", "1") == "0": self.ctx.check_hostname = False
        elif os.environ.get("VTG_INDEXER_INSECURE") == "1":
            self.ctx = ssl.create_default_context(); self.ctx.check_hostname = False; self.ctx.verify_mode = ssl.CERT_NONE
        else: raise SystemExit("Can VTG_INDEXER_CA (file CA mount tu ngoai) hoac VTG_INDEXER_INSECURE=1 (chi lab).")
        self.agents = list(agents or os.environ.get("VTG_AGENTS", ",".join(DEFAULT_AGENTS)).split(","))
        self.poll_s, self.page, self.state_path, self.mode = poll_s, page, state_path, "live"
        self.errors = 0
        st = json.load(open(state_path, encoding="utf-8")) if state_path and os.path.exists(state_path) else {}
        self.cp = st.get("checkpoint") or start or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        self.cp_ids = set(st.get("ids_at_checkpoint", []))
        self.req("/", method="GET")                                           # kiem tra ket noi + xac thuc

    def req(self, path, body=None, method="POST", ndjson=None):
        data = ndjson.encode() if ndjson is not None else (json.dumps(body).encode() if body is not None else None)
        r = urllib.request.Request(self.url + path, data=data, method=method,
                                   headers={"Content-Type": "application/x-ndjson" if ndjson is not None else "application/json",
                                            "Authorization": self.auth})
        with urllib.request.urlopen(r, context=self.ctx, timeout=60) as resp: return json.load(resp)

    def _save(self):
        if not self.state_path: return
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: json.dump({"checkpoint": self.cp, "ids_at_checkpoint": sorted(self.cp_ids)}, f)
        os.replace(tmp, self.state_path)

    RETRY_MAX_S = 60.0

    def search(self, body):
        """POST _search co thu lai: loi tam thoi (mat mang, timeout, HTTP 5xx / 429) -> cho 5, 10, 20 ... toi da 60 s roi thu lai,
        khong mat checkpoint; sai dang nhap / thieu quyen (401 / 403) -> dung han (loi cau hinh, thu lai vo ich)."""
        import urllib.error
        wait = 5.0
        while True:
            try: return self.req("/wazuh-archives-*/_search", body)
            except urllib.error.HTTPError as e:
                if e.code in (401, 403): raise SystemExit(f"Indexer tu choi ({e.code}): kiem tra tai khoan / role vtguard.")
                err = f"HTTP {e.code}"
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                err = type(e).__name__
            self.errors += 1
            print(f"[live] Indexer tam loi ({err}); thu lai sau {wait:.0f} s (checkpoint {self.cp})", flush=True)
            time.sleep(wait); wait = min(wait * 2, self.RETRY_MAX_S)

    def poll(self):
        time.sleep(self.poll_s); out = []
        while True:
            ms = int(_parse(self.cp).timestamp() * 1000)                   # epoch_millis: khong phu thuoc dinh dang chuoi ngay
            q = {"bool": {"filter": [{"terms": {"agent.name": self.agents}},
                                     {"range": {"timestamp": {"gte": ms, "format": "epoch_millis"}}}]}}
            hits = self.search({"size": self.page, "sort": [{"timestamp": "asc"}], "query": q})["hits"]["hits"]
            new = [h for h in hits if h["_id"] not in self.cp_ids]
            out += [h["_source"] for h in new]
            if hits:
                last = hits[-1]["_source"]["timestamp"]
                same = {h["_id"] for h in hits if h["_source"]["timestamp"] == last}
                self.cp_ids = (self.cp_ids | same) if last == self.cp else same
                self.cp = last
            if len(hits) < self.page or not new: break
        self._save()
        return out, datetime.now(timezone.utc)

    def done(self): return False

    def check(self, minutes=15):
        """Kiem tra truoc khi chay that (khong doi checkpoint, khong ghi gi): phien ban Indexer, user + role cua tai khoan,
        so event moi agent trong `minutes` phut gan nhat va timestamp moi nhat (theo gio Wazuh)."""
        out = {"url": self.info()["name"], "agents": {}}
        root = self.req("/", method="GET"); out["cluster"] = root.get("cluster_name"); out["version"] = (root.get("version") or {}).get("number")
        try:
            au = self.req("/_plugins/_security/authinfo", method="GET"); out["user"] = au.get("user_name"); out["roles"] = au.get("roles")
        except Exception as e:                                                # noqa: BLE001 - chi de in, khong chan
            out["user"] = f"(khong doc duoc authinfo: {type(e).__name__})"
        since = int((datetime.now(timezone.utc) - timedelta(minutes=minutes)).timestamp() * 1000)
        for ag in self.agents:
            q = {"bool": {"filter": [{"term": {"agent.name": ag}}, {"range": {"timestamp": {"gte": since, "format": "epoch_millis"}}}]}}
            r = self.req("/wazuh-archives-*/_search", {"size": 1, "track_total_hits": True, "sort": [{"timestamp": "desc"}], "query": q,
                                                       "_source": ["timestamp"]})
            hits = r["hits"]["hits"]
            out["agents"][ag] = {"events_last_min": r["hits"]["total"]["value"], "latest": hits[0]["_source"]["timestamp"] if hits else None}
        return out

    def info(self):
        """Mo ta nguon cho dashboard: chi host:port cua Indexer (khong user / mat khau), index, agent, moc da doc."""
        from urllib.parse import urlparse
        return {"kind": "indexer", "name": urlparse(self.url).netloc.split("@")[-1], "index": "wazuh-archives-*", "agents": self.agents,
                "checkpoint": self.cp, "errors": self.errors}

class AlertPusher:
    """Ghi canh bao vao vtguard-alerts-YYYY.MM.DD (tai khoan Indexer rieng: chi ghi index nay)."""
    def __init__(self, src): self.src = src

    def push(self, alerts):
        if not alerts: return 0
        idx = "vtguard-alerts-" + datetime.now(timezone.utc).strftime("%Y.%m.%d")
        nd = "".join(json.dumps({"index": {"_index": idx}}) + "\n" + json.dumps({**a, "@timestamp": a.get("received_at")}) + "\n" for a in alerts)
        res = self.src.req("/_bulk", ndjson=nd)
        return sum(1 for it in res.get("items", []) if it.get("index", {}).get("status") in (200, 201))
