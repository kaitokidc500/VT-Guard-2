#!/usr/bin/env python3
# Xuat TOAN BO log Wazuh archives theo khoang thoi gian (scroll, khong gioi han 10000).
# Dau ra JSONL (moi dong 1 _source) - normalize.py doc truc tiep.
# Dung: python3 export_batch.py <GTE> <LTE> <ten_dot>
#   vd: python3 export_batch.py 2026-10-14T03:25:00Z 2026-10-14T06:00:00Z batch01
import sys, os, json, ssl, getpass, urllib.request, urllib.parse

ES = "https://localhost:9200"
GTE, LTE, NAME = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = os.path.expanduser(f"~/vt-guard/data/raw/{NAME}"); os.makedirs(OUT, exist_ok=True)
PW = getpass.getpass("Mat khau Indexer: ")
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
AUTH = "Basic " + __import__("base64").b64encode(f"admin:{PW}".encode()).decode()

def req(path, body=None, method="POST"):
    url = ES + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method,
            headers={"Content-Type":"application/json","Authorization":AUTH})
    with urllib.request.urlopen(r, context=CTX, timeout=120) as resp:
        return json.load(resp)

# kiem tra xac thuc
try:
    info = req("/", method="GET")
    assert "cluster_name" in info
except Exception as e:
    print("Loi xac thuc/ket noi:", e); sys.exit(1)

def q(ag):
    return {"bool":{"filter":[
        {"term":{"agent.name":ag}},
        {"range":{"timestamp":{"gte":GTE,"lte":LTE}}}]}}

for AG in ("DC01","WIN10-01"):
    outf = os.path.join(OUT, f"{AG}.json")
    total = req("/wazuh-archives-*/_count", {"query":q(AG)}).get("count",0)
    print(f"{AG}: tong {total} event trong Indexer, dang keo...")
    got = 0
    with open(outf, "w", encoding="utf-8") as w:
        resp = req("/wazuh-archives-*/_search?scroll=3m",
                   {"size":5000, "sort":["_doc"], "query":q(AG)})
        sid = resp.get("_scroll_id")
        while True:
            hits = resp["hits"]["hits"]
            if not hits: break
            for h in hits:
                w.write(json.dumps(h["_source"], ensure_ascii=False) + "\n"); got += 1
            resp = req("/_search/scroll", {"scroll":"3m","scroll_id":sid})
            sid = resp.get("_scroll_id")
    try: req("/_search/scroll", {"scroll_id":sid}, method="DELETE")
    except Exception: pass
    print(f"{AG}: da keo {got}/{total} event -> {outf}")

print(f"Xong. Chep thu muc {OUT} ve host, chay normalize.py (doc JSONL tu dong).")
