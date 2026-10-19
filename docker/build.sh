#!/bin/sh
# VT-Guard Buoc 9 - dung context -> build image linux/amd64 -> kiem offline -> xuat vtguard.tar (docs/STEP9-BRIEF.md muc 6.3).
# Chay tu goc repo (host co data/processed + models/*.onnx):  sh docker/build.sh [linux/amd64|linux/arm64]
set -e
export MSYS_NO_PATHCONV=1           # Git Bash tren Windows: khong doi /app/... thanh duong dan Windows
PLAT="${1:-linux/amd64}"; TAG="vtguard:step9"; OUT="docker/out"
python docker/stage.py
docker build --platform "$PLAT" -t "$TAG" docker/build
mkdir -p "$OUT"
echo "== verify offline (--network none) =="
docker run --rm --network none --platform "$PLAT" "$TAG" verify | tee "$OUT/verify_container.txt"
echo "== selftest offline =="
docker run --rm --network none --platform "$PLAT" "$TAG" selftest > "$OUT/selftest_container.txt" 2>&1 || { tail -20 "$OUT/selftest_container.txt"; exit 1; }
grep -E "KET QUA|QUET|SELFTEST" "$OUT/selftest_container.txt"
echo "== dashboard + demo khoi dong (health check) =="
docker rm -f vtguard_smoke > /dev/null 2>&1 || true
docker run -d --name vtguard_smoke --network none --platform "$PLAT" "$TAG" demo > /dev/null
ok=0; for i in $(seq 1 30); do
  if docker exec vtguard_smoke python -c "import urllib.request as u; print(u.urlopen('http://127.0.0.1:8501/_stcore/health').read().decode())" 2>/dev/null; then ok=1; break; fi
  sleep 2
done
docker logs vtguard_smoke 2>&1 | tail -5 > "$OUT/demo_container.txt"; docker rm -f vtguard_smoke > /dev/null
[ $ok -eq 1 ] || { echo "dashboard khong len"; cat "$OUT/demo_container.txt"; exit 1; }
docker run --rm --entrypoint cat "$TAG" /app/docker/requirements.freeze.txt > docker/requirements.freeze.txt
SUF=$(echo "$PLAT" | tr '/' '-' | sed 's/linux-//')
TAR="$OUT/vtguard_${SUF}.tar"
docker save -o "$TAR" "$TAG"
python - "$TAR" "$TAG" "$PLAT" <<'EOF'
import hashlib, json, os, subprocess, sys
tar, tag, plat = sys.argv[1:4]
h = hashlib.sha256()
with open(tar, "rb") as f:
    for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
img = json.loads(subprocess.run(["docker", "image", "inspect", tag], capture_output=True, text=True, check=True).stdout)[0]
info = {"tar": os.path.basename(tar), "bytes": os.path.getsize(tar), "sha256": h.hexdigest(), "image": tag, "platform": plat,
        "image_id": img["Id"], "image_size": img["Size"]}
p = "docker/image_info.json"
d = json.load(open(p)) if os.path.exists(p) else {}
d[plat] = info
json.dump(d, open(p, "w"), indent=1)
print(json.dumps(info, indent=1))
EOF
