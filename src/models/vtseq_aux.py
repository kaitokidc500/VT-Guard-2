#!/usr/bin/env python3
"""VT-Guard Buoc 6 - xuat file phu (aux) cho VT-Seq, CHI chay tren host (can windows.jsonl + all.events.jsonl).

File split dong bang chi co cat/cmd/num + nhan muc cua so. VT-Seq can them, KHONG lam feature:
  - origin      : moi event thuoc cay phien ("o") hay event nen ("b") - mat na ablation (c) va vi tri event malicious
                  dau tien cho phat hien som (nhu evaluate.early_starts). Moi tap.
  - one_sided   : event nen mot-phia da biet ("1"/"0", common.is_known_one_sided_bg) - mat na ablation (c'). Moi tap.
  - ev_mal, ev_ttps : nhan TUNG event (label_malicious, label_ttps) - CHI cho Train, CHI de tinh lai nhan doan crop
                  khi huan luyen (nhu B3). Khong co cho T-clean/T-hard/T-novel.
Thu tu event = thu tu trong file split (= windows.jsonl). Tu doi chieu: do dai khop split, hop nhan event Train khop
window_malicious/window_ttps. Ghi data/processed/step6/aux.jsonl + reports/step6/aux_manifest.json (sha256).
Chay: python src/models/vtseq_aux.py
"""
import argparse, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("baselines", "eval", "dataset"): sys.path.insert(0, os.path.join(HERE, "..", d))
from common import window_events, full_window_events, is_known_one_sided_bg   # noqa: E402
from evaluate import check_dataset, load_all_meta, SPLITS, TTPS               # noqa: E402

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); a = ap.parse_args()
    print("checksum dataset:", check_dataset(a.root))
    meta = load_all_meta(a.root)
    wev = window_events(a.root, [w["window_id"] for s in SPLITS for w in meta[s]])
    fe = full_window_events(a.root, [w["window_id"] for w in meta["train"]])
    nlen = {}
    for s in SPLITS:
        with open(os.path.join(a.root, "data", "processed", "splits", f"{s}.jsonl"), encoding="utf-8") as fh:
            for l in fh:
                r = json.loads(l); nlen[r["window_id"]] = len(r["cat"])
    out_dir = os.path.join(a.root, "data", "processed", "step6"); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "aux.jsonl")
    n = {s: 0 for s in SPLITS}
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for s in SPLITS:
            for w in meta[s]:
                wid = w["window_id"]; ev, origin = wev[wid]
                assert len(ev) == nlen[wid], wid
                rec = {"window_id": wid, "split": s,
                       "origin": "".join("o" if o == "own" else "b" for o in origin),
                       "one_sided": "".join("1" if is_known_one_sided_bg(e, o) else "0" for e, o in zip(ev, origin))}
                if s == "train":
                    fev = fe[wid]; assert len(fev) == len(ev), wid
                    mal = [bool(e["label_malicious"]) for e in fev]
                    tts = [[TTPS.index(t) for t in (e.get("label_ttps") or []) if t in TTPS] if m else [] for e, m in zip(fev, mal)]
                    assert any(mal) == bool(w["window_malicious"]), wid
                    assert {TTPS[i] for t in tts for i in t} == set(w["window_ttps"]), wid
                    rec["ev_mal"] = "".join("1" if m else "0" for m in mal); rec["ev_ttps"] = tts
                f.write(json.dumps(rec, separators=(",", ":")) + "\n"); n[s] += 1
    man = {"file": "data/processed/step6/aux.jsonl", "sha256": sha256(out), "windows": n, "dataset_version": "v1.2",
           "fields": {"origin": "o=event cay phien, b=event nen (moi tap; mat na ablation c + phat hien som)",
                      "one_sided": "1=event nen mot-phia da biet (moi tap; mat na ablation c')",
                      "ev_mal/ev_ttps": "nhan tung event, CHI Train, CHI tinh nhan doan crop; ev_ttps = chi so trong TTPS"},
           "ttps": TTPS}
    os.makedirs(os.path.join(a.root, "reports", "step6"), exist_ok=True)
    with open(os.path.join(a.root, "reports", "step6", "aux_manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(man, f, indent=1)
    print("aux:", n, "sha256", man["sha256"][:16])
    # goi dau vao Colab: CHI splits (+ assignment.json de chia fold theo nhom) + vocab + aux. Khong log tho.
    import zipfile
    files = [f"data/processed/splits/{s}.jsonl" for s in SPLITS] + ["data/processed/splits/assignment.json",
             "data/processed/vocab.json", "data/processed/step6/aux.jsonl"]
    zp = os.path.join(out_dir, "colab_inputs.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files: z.write(os.path.join(a.root, *f.split("/")), f)
    print("colab_inputs.zip:", files, "sha256", sha256(zp)[:16])

if __name__ == "__main__":
    main()
