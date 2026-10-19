#!/usr/bin/env python3
"""VT-Guard Buoc 9 - tao file log mau cho che do replay: cat nguyen van (_source tho, theo `timestamp` Wazuh) cac khoang thoi gian
cua log da export (mac dinh: batch05 13:33-13:58 UTC gom quan tri lanh tinh + discovery; ntds2v 08:47-08:56 UTC gom T1003.003).
Khong sua event nao. Ghi samples/replay_demo.jsonl.gz.
Chay: python src/live/make_sample.py
"""
import argparse, gzip, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from connector import read_log, _parse          # noqa: E402
from run import home                            # noqa: E402

SLICES = [("batch05", "2026-10-14T13:33:00Z", "2026-10-14T13:58:00Z"), ("ntds2v", "2026-10-15T08:47:00Z", "2026-10-15T08:56:00Z")]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=None); a = ap.parse_args()
    root = home(); out = a.out or os.path.join(root, "samples", "replay_demo.jsonl.gz"); os.makedirs(os.path.dirname(out), exist_ok=True)
    rows = []
    for b, lo, hi in SLICES:
        lo, hi = _parse(lo), _parse(hi)
        rows += [r for r in read_log(os.path.join(root, "data", "raw", b)) if r.get("timestamp") and lo <= _parse(r["timestamp"]) <= hi]
    rows.sort(key=lambda r: _parse(r["timestamp"]))
    with gzip.open(out, "wt", encoding="utf-8", newline="\n") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rows)} event -> {out} ({os.path.getsize(out) / 1e6:.1f} MB)")

if __name__ == "__main__":
    main()
