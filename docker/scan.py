#!/usr/bin/env python3
"""VT-Guard Buoc 9 (kieu A) - quet file nhay cam (docs/STEP9-BRIEF.md muc 6.1, 6.3). Dung cho build context (host) va ben trong
image (`docker run --rm --entrypoint python vtguard:step9 docker/scan.py /app`).
Vi pham:
  S1 checkpoint / trong so huan luyen: *.pt *.pth *.ckpt *.h5 *.joblib
  S2 log tho / event da gan nhan: data/raw/**, *.labeled.jsonl, all.events.jsonl, file JSON/JSONL/GZ co ban ghi Wazuh tho
     (`agent` + `data.win`) - NGOAI TRU samples/replay_demo.jsonl.gz (log mau duy nhat brief 6.1 yeu cau)
  S3 thong tin dang nhap: .env / *.env, khoa rieng / chung chi PEM, gan gia tri cho VTG_INDEXER_PASSWORD / password= / token=
     trong moi file van ban (ke ca log mau .gz)
Ma thoat 0 = sach.
Chay: python docker/scan.py <thu_muc>
"""
import gzip, json, os, re, sys

CKPT = (".pt", ".pth", ".ckpt", ".h5", ".joblib")
ALLOWED_RAW = {"samples/replay_demo.jsonl.gz"}
SECRET_RE = re.compile(r"(-----BEGIN [A-Z ]*(PRIVATE KEY|CERTIFICATE)-----|VTG_INDEXER_PASSWORD\s*=\s*\S+"
                       r"|\b(password|passwd|pwd|token|secret|api[_-]?key)\s*[=:]\s*['\"]?(?P<v>[^\s'\",}\x5c]{6,}))", re.I)
# Gia tri gia trong tai lieu / ma (khong phai bi mat that)
SECRET_OK = re.compile(r"(<[^>]*>|\$\{?[A-Z_]+\}?|xxx|\.\.\.|changeme|example|placeholder|getenv|environ|os\.environ)", re.I)
SKIP_TEXT = {"docker/scan.py"}                                    # chinh file nay chua mau regex
TEXT_EXT = (".py", ".md", ".json", ".jsonl", ".yml", ".yaml", ".txt", ".sh", ".ps1", ".toml", ".cfg", ".ini", ".env", ".css", ".html", "")

def looks_secret(m):
    """Gia tri gan cho password / token phai giong bi mat that: >= 6 ky tu, co chu VA co so hoac ky hieu (loai tu thuong nhu
    'ConfirmPasswordPrompt', ten bien 'TOK_RE', co '0'). PEM / VTG_INDEXER_PASSWORD luon tinh."""
    v = m.group("v")
    if v is None: return True
    return bool(re.search(r"[A-Za-z]", v) and re.search(r"[0-9!@#$%^&*]", v)) and not SECRET_OK.search(m.group(0))

def is_raw(obj):
    s = obj.get("_source", obj) if isinstance(obj, dict) else None
    return isinstance(s, dict) and "agent" in s and isinstance(s.get("data"), dict) and "win" in s["data"]

def scan(root):
    bad, notes = [], []
    for dp, dns, fs in os.walk(root):
        dns[:] = [d for d in dns if d not in ("proc", "sys", "dev", "__pycache__")]
        for f in fs:
            p = os.path.join(dp, f); rel = os.path.relpath(p, root).replace(os.sep, "/"); low = f.lower()
            if low.endswith(CKPT): bad.append(f"S1 {rel}"); continue
            if rel.startswith("data/raw/") or "/data/raw/" in rel or low.endswith(".labeled.jsonl") or low == "all.events.jsonl":
                bad.append(f"S2 {rel}"); continue
            if low == ".env" or low.endswith(".env") or low.startswith(".env."): bad.append(f"S3 {rel}"); continue
            if not (low.endswith(TEXT_EXT) or low.endswith(".gz")) or rel in SKIP_TEXT: continue
            try:
                op = gzip.open if low.endswith(".gz") else open
                with op(p, "rt", encoding="utf-8", errors="replace") as fh:
                    raw_seen = False
                    for i, line in enumerate(fh):
                        m = SECRET_RE.search(line)
                        if m and looks_secret(m): bad.append(f"S3 {rel}:{i + 1} '{m.group(0)[:40]}'"); break
                        if not raw_seen and low.endswith((".jsonl", ".json", ".gz")) and i < 50 and line.lstrip().startswith("{"):
                            try: raw_seen = is_raw(json.loads(line))
                            except json.JSONDecodeError: pass
                    if raw_seen:
                        if rel in ALLOWED_RAW: notes.append(f"log mau cho phep: {rel}")
                        else: bad.append(f"S2 {rel} (ban ghi Wazuh tho)")
            except (OSError, EOFError, gzip.BadGzipFile): continue
    return bad, notes

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    bad, notes = scan(root)
    for n in notes: print("  ghi chu:", n)
    for b in bad[:50]: print("  VI PHAM:", b)
    print(f"QUET {root}: {'SACH' if not bad else f'{len(bad)} VI PHAM'} (S1 checkpoint, S2 log tho, S3 dang nhap)")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
