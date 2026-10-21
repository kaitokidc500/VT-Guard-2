#!/usr/bin/env python3
"""VT-Guard Buoc 9 moc 4 - kiem tra suc khoe cho Docker healthcheck / giam sat van hanh.
  live      : luong truc tiep khoe neu reports/step9/live/status.json duoc cap nhat trong 3 chu ky doc + 60 s
              (moi chu ky poll ghi lai status, ke ca khi khong co event moi) va che do la 'live'.
  dashboard : Streamlit tra loi http://127.0.0.1:<VTG_PORT>/_stcore/health.
In mot dong tom tat; ma thoat 0 = khoe, 1 = loi. Chay: python src/live/health.py [live|dashboard]
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("VTGUARD_HOME") or os.path.abspath(os.path.join(HERE, "..", ".."))

def live():
    p = os.path.join(ROOT, "reports", "step9", "live", "status.json")
    try: st = json.load(open(p, encoding="utf-8"))
    except (OSError, json.JSONDecodeError): print("KHONG KHOE: chua co status.json"); return 1
    upd = datetime.strptime(st["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - upd).total_seconds(); lim = 3 * float(st.get("poll_s") or 12) + 60
    src = st.get("source") or {}
    ok = st.get("mode") == "live" and age <= lim
    print(f"{'KHOE' if ok else 'KHONG KHOE'}: che do {st.get('mode')}, cap nhat {age:.0f} s truoc (gioi han {lim:.0f} s), "
          f"{st.get('events_read', 0)} event, {st.get('windows', 0)} cua so, {st.get('alerts', 0)} canh bao, loi Indexer {src.get('errors', 0)}")
    return 0 if ok else 1

def dashboard():
    port = os.environ.get("VTG_PORT", "8501")
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=5).read().decode()
        print(f"KHOE: dashboard :{port} {r}"); return 0
    except Exception as e:                                                   # noqa: BLE001
        print(f"KHONG KHOE: dashboard :{port} {type(e).__name__}"); return 1

if __name__ == "__main__":
    sys.exit({"live": live, "dashboard": dashboard}[sys.argv[1] if len(sys.argv) > 1 else "live"]())
