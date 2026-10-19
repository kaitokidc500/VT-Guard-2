#!/usr/bin/env python3
"""VT-Guard Buoc 9 (kieu A) - dung build context cho image Docker (docs/STEP9-BRIEF.md muc 6.1).

Chon file theo DANH SACH CHO PHEP, khong copy ca repo:
  - ma + artefact van ban: file git theo doi / chua bi .gitignore loai (`git ls-files --cached --others --exclude-standard`)
    trong src/, dashboard/, rules/sigma/, reports/, docker/ + README_DOCKER.md; bo reports/step6/m3/** (dau ra Colab), __pycache__;
    trang thai luong chay (reports/step9/live/alerts.jsonl, status.json) da bi .gitignore loai.
  - artefact KHONG nam trong git (lay tu host): models/vtseq_M3_ens.onnx (sha256 == step6_results.json), data/processed/vocab.json,
    data/processed/splits/*.jsonl (sha256 == dataset card), data/processed/windows.jsonl CHI cua so 3 tap test, samples/replay_demo.jsonl.gz.
  - KHONG: data/raw, *.labeled.jsonl, all.events.jsonl, checkpoint .pt, .env / thong tin dang nhap.
Ghi docker/MANIFEST.json (sha256 + kich thuoc tung file) va chay docker/scan.py tren context (dung lai neu vi pham).
Chay: python docker/stage.py [--out docker/build]
"""
import argparse, hashlib, json, os, shutil, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GIT_PREFIXES = ("src/", "dashboard/", "rules/sigma/", "reports/", "docker/")
GIT_FILES = ("README_DOCKER.md",)
SKIP_PREFIXES = ("reports/step6/m3/", "docker/build/", "docker/out/")
SKIP_PARTS = ("__pycache__",)
EXTRA = ["models/vtseq_M3_ens.onnx", "data/processed/vocab.json", "data/processed/splits/train.jsonl",
         "data/processed/splits/t_clean.jsonl", "data/processed/splits/t_hard.jsonl", "data/processed/splits/t_novel.jsonl",
         "data/processed/splits/assignment.json", "samples/replay_demo.jsonl.gz"]
TEST_SPLITS = ("t_clean", "t_hard", "t_novel")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def git_files():
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    fs = [f for f in out.decode("utf-8").split("\0") if f]
    return sorted(f for f in fs if (f.startswith(GIT_PREFIXES) or f in GIT_FILES) and not f.startswith(SKIP_PREFIXES)
                  and not any(p in f.split("/") for p in SKIP_PARTS) and os.path.isfile(os.path.join(ROOT, f)))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(ROOT, "docker", "build")); a = ap.parse_args()
    out = os.path.abspath(a.out)
    assert out.startswith(os.path.join(ROOT, "docker")), "chi dung trong docker/"
    if os.path.exists(out): shutil.rmtree(out)
    os.makedirs(out)
    files = git_files()
    for f in files + EXTRA:
        src = os.path.join(ROOT, f)
        if not os.path.exists(src): sys.exit(f"Thieu {f}")
        dst = os.path.join(out, f); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
    # kiem sha artefact ngoai git
    s6 = json.load(open(os.path.join(ROOT, "reports", "step6_results.json"), encoding="utf-8"))["onnx"]["vtseq_M3_ens"]["sha256"]
    assert sha(os.path.join(out, "models", "vtseq_M3_ens.onnx")) == s6, "ONNX khac step6_results.json"
    ref = json.load(open(os.path.join(ROOT, "reports", "dataset_stats.json"), encoding="utf-8"))["files_sha256"]
    for k in ["vocab.json"] + [f"splits/{s}.jsonl" for s in ("train",) + TEST_SPLITS]:
        assert sha(os.path.join(out, "data", "processed", *k.split("/"))) == ref[k], f"{k} khac dataset-v1.2"
    # windows.jsonl: chi cua so 3 tap test (giu nguyen dong)
    want = set()
    for s in TEST_SPLITS:
        for l in open(os.path.join(ROOT, "data", "processed", "splits", f"{s}.jsonl"), encoding="utf-8"): want.add(json.loads(l)["window_id"])
    n = 0
    with open(os.path.join(ROOT, "data", "processed", "windows.jsonl"), encoding="utf-8") as fi, \
         open(os.path.join(out, "data", "processed", "windows.jsonl"), "w", encoding="utf-8", newline="\n") as fo:
        for l in fi:
            if json.loads(l)["window_id"] in want: fo.write(l); n += 1
    assert n == len(want), f"windows.jsonl: {n} / {len(want)} cua so test"
    os.makedirs(os.path.join(out, "reports", "step9", "live"), exist_ok=True)
    # Dockerfile + .dockerignore o goc context
    shutil.copy2(os.path.join(ROOT, "docker", "Dockerfile"), os.path.join(out, "Dockerfile"))
    with open(os.path.join(out, ".dockerignore"), "w", encoding="utf-8", newline="\n") as f:
        f.write("**/__pycache__\n**/*.pt\n**/*.pth\n**/*.ckpt\n**/.env\n**/.env.*\n**/*.labeled.jsonl\ndata/raw\n")
    # MANIFEST
    entries = {}
    for dp, _, fs in os.walk(out):
        for f in fs:
            p = os.path.join(dp, f); rel = os.path.relpath(p, out).replace(os.sep, "/")
            if rel in ("docker/MANIFEST.json", "Dockerfile", ".dockerignore"): continue
            entries[rel] = {"sha256": sha(p), "bytes": os.path.getsize(p)}
    git_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
    man = {"image": "vtguard:step9", "git_head": git_head, "worktree_dirty": dirty, "dataset": "dataset-v1.2",
           "n_files": len(entries), "bytes": sum(e["bytes"] for e in entries.values()),
           "notes": {"windows.jsonl": f"chi {n} cua so cua 3 tap test (t_clean, t_hard, t_novel), dong nguyen van tu ban host",
                     "samples/replay_demo.jsonl.gz": "log Wazuh mau duy nhat (brief 6.1: 'mot file log mau cho replay'); khong co log tho nao khac",
                     "khong_dua_vao": "data/raw, *.labeled.jsonl, all.events.jsonl, *.pt, .env / thong tin dang nhap"},
           "files": dict(sorted(entries.items()))}
    for p in (os.path.join(out, "docker", "MANIFEST.json"), os.path.join(ROOT, "docker", "MANIFEST.json")):
        with open(p, "w", encoding="utf-8", newline="\n") as f: json.dump(man, f, indent=1, ensure_ascii=False)
    print(f"context {out}: {len(entries)} file, {man['bytes'] / 1e6:.1f} MB; windows test {n}")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "docker", "scan.py"), out])
    if r.returncode: sys.exit("QUET KHONG DAT - khong build.")

if __name__ == "__main__":
    main()
