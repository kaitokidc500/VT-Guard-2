#!/usr/bin/env python3
"""VT-Guard Buoc 9 moc 4 - bao cao doi chieu Wazuh <-> VT-Guard theo tung kich ban demo (docs/STEP9-M4-DEMO.md).

Moi kich ban demo la mot phien cua bo dieu phoi (orchestrator/Invoke-VTSession.ps1) nen co manifest: run_id, class, host, ttps,
t_start, t_end. Voi moi phien, trong khung [t_start - 60 s, t_end + GRACE_S] (cong do tre Wazuh + cho dong cua so) va cung may:
  - Wazuh   : canh bao trong wazuh-alerts-* (rule.id, level, description, mitre.id); "gan dung ky thuat" = co canh bao co
              rule.mitre.id khop TTP cua phien (trung, ky thuat con hoac cha - cung quy tac baseline B0).
  - VT-Guard: canh bao trong reports/step9/live/alerts.jsonl giao khung thoi gian; "gan dung" = TTP cua phien nam trong ttps canh bao.
Phien lanh tinh / hard-negative: dung = KHONG canh bao. Bao cao chi DOC (tai khoan Indexer rieng can quyen read wazuh-alerts-*).
Chay: python src/live/demo_report.py --manifests <thu_muc_manifest> --env-file secrets/vtguard.env [--out reports/step9/m4]
"""
import argparse, glob, json, os, sys
from collections import Counter
from datetime import timedelta

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import connector as C                                                       # noqa: E402
from windower import ts                                                    # noqa: E402

GRACE_S = 240

def mitre_match(m, t): return m == t or m.startswith(t + ".") or t.startswith(m + ".")

def load_manifests(path):
    out = []
    for f in sorted(glob.glob(os.path.join(path, "**", "*.manifest.json"), recursive=True) + glob.glob(os.path.join(path, "*.json"))):
        try: txt = open(f, encoding="utf-8-sig").read().strip(); m = json.loads(txt) if txt else None
        except (OSError, json.JSONDecodeError): continue
        if isinstance(m, dict) and m.get("run_id") and m.get("t_start") and m.get("t_end"): out.append(m)
    uniq = {m["run_id"]: m for m in out}
    return sorted(uniq.values(), key=lambda m: ts(m["t_start"]))

def wazuh_alerts(src, host, t0, t1, size=500):
    q = {"bool": {"filter": [{"term": {"agent.name": host}},
                             {"range": {"timestamp": {"gte": int(t0.timestamp() * 1000), "lte": int(t1.timestamp() * 1000), "format": "epoch_millis"}}}]}}
    r = src.req("/wazuh-alerts-*/_search", {"size": size, "sort": [{"timestamp": "asc"}], "query": q,
                                            "_source": ["timestamp", "rule.id", "rule.level", "rule.description", "rule.mitre.id"]})
    return [h["_source"] for h in r["hits"]["hits"]]

def vtguard_alerts(path, host, t0, t1):
    out = []
    if not os.path.exists(path): return out
    for l in open(path, encoding="utf-8"):
        try: a = json.loads(l)
        except json.JSONDecodeError: continue
        if a.get("host") == host and ts(a["t0"]) <= t1 and ts(a["t1"]) >= t0: out.append(a)
    return out

def judge(m, wz, vg, min_level):
    ttps = m.get("ttps") or []; attack = m.get("class") == "attack"
    wz_lv = [a for a in wz if (a.get("rule") or {}).get("level", 0) >= min_level]
    wz_mitre = {mid for a in wz for mid in ((a.get("rule") or {}).get("mitre") or {}).get("id", []) or []}
    wz_ttp = {t: any(mitre_match(x, t) for x in wz_mitre) for t in ttps}
    vg_ttp = {t: any(t in a.get("ttps", []) for a in vg) for t in ttps}
    row = {"run_id": m["run_id"], "class": m.get("class"), "host": m.get("host"), "ttps": ttps, "t_start": m["t_start"], "t_end": m["t_end"],
           "wazuh": {"n": len(wz), f"n_level_ge_{min_level}": len(wz_lv), "ttp_dung": wz_ttp,
                     "rules": Counter(f"{(a.get('rule') or {}).get('id')} L{(a.get('rule') or {}).get('level')} "
                                      f"{(a.get('rule') or {}).get('description', '')[:70]}" for a in wz).most_common(5)},
           "vtguard": {"n": len(vg), "both": sum(a.get("decision_source") == "both" for a in vg), "ttp_dung": vg_ttp,
                       "ttps": sorted({t for a in vg for t in a.get("ttps", [])}),
                       "luat": sorted({r["id"] for a in vg for r in a.get("rule_ids", [])}),
                       "tre_s": sorted(a["latency"]["total_s"] for a in vg if (a.get("latency") or {}).get("total_s") is not None)[:1]}}
    if attack:
        row["ket_luan"] = ("VT-Guard gan dung, Wazuh khong" if all(vg_ttp.values()) and not any(wz_ttp.values()) else
                           "ca hai gan dung" if all(vg_ttp.values()) and all(wz_ttp.values()) else
                           "VT-Guard gan dung mot phan" if any(vg_ttp.values()) else "VT-Guard bo sot")
    else:
        row["ket_luan"] = ("VT-Guard im lang (dung)" if not vg else "VT-Guard canh bao nham") + \
                          (f"; Wazuh {len(wz_lv)} canh bao muc >= {min_level}" if wz_lv else "; Wazuh im lang")
    return row

def render(rows, min_level):
    L = ["# Doi chieu Wazuh <-> VT-Guard theo kich ban demo", "",
         f"Khung moi phien: [t_start - 60 s, t_end + {GRACE_S} s], cung may. Wazuh 'gan dung' = co canh bao rule.mitre.id khop TTP phien. "
         f"VT-Guard 'gan dung' = TTP phien nam trong canh bao. Cot Wazuh >= L{min_level} dem canh bao muc >= {min_level} (nguong baseline B0).", "",
         f"| Phien | Lop | May | TTP | Wazuh: canh bao (>= L{min_level}) | Wazuh gan dung TTP | VT-Guard: canh bao (AI + luat) | VT-Guard gan dung TTP | Ket luan |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        w, v = r["wazuh"], r["vtguard"]
        fmt = lambda d: ", ".join(f"{k} {'co' if ok else 'KHONG'}" for k, ok in d.items()) or "-"
        L.append(f"| {r['run_id']} | {r['class']} | {r['host']} | {', '.join(r['ttps']) or '-'} | {w['n']} ({w[f'n_level_ge_{min_level}']}) | "
                 f"{fmt(w['ttp_dung'])} | {v['n']} ({v['both']}) | {fmt(v['ttp_dung'])} | {r['ket_luan']} |")
    L += ["", "## Chi tiet luat Wazuh da ban (5 luat nhieu nhat moi phien)", ""]
    for r in rows:
        L.append(f"- **{r['run_id']}** ({r['class']}, {', '.join(r['ttps']) or 'khong TTP'}): "
                 + ("; ".join(f"{k} x{n}" for k, n in r["wazuh"]["rules"]) or "khong co canh bao")
                 + f" | VT-Guard TTP {r['vtguard']['ttps'] or '-'}, luat {r['vtguard']['luat'] or '-'}")
    att = [r for r in rows if r["class"] == "attack"]; neg = [r for r in rows if r["class"] != "attack"]
    L += ["", "## Tong hop", "",
          f"- Phien tan cong: {len(att)}; VT-Guard gan dung du TTP: {sum(all(r['vtguard']['ttp_dung'].values()) for r in att)}; "
          f"Wazuh gan dung du TTP: {sum(bool(r['wazuh']['ttp_dung']) and all(r['wazuh']['ttp_dung'].values()) for r in att)}.",
          f"- Phien lanh tinh / quan tri: {len(neg)}; VT-Guard canh bao nham: {sum(r['vtguard']['n'] > 0 for r in neg)}; "
          f"Wazuh co canh bao muc >= {min_level}: {sum(r['wazuh'][f'n_level_ge_{min_level}'] > 0 for r in neg)}."]
    return "\n".join(L) + "\n"

def build(manifests, alerts_path, src, min_level=4):
    rows = []
    for m in manifests:
        t0 = ts(m["t_start"]) - timedelta(seconds=60); t1 = ts(m["t_end"]) + timedelta(seconds=GRACE_S)
        rows.append(judge(m, wazuh_alerts(src, m["host"], t0, t1) if src else [], vtguard_alerts(alerts_path, m["host"], t0, t1), min_level))
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifests", required=True, help="thu muc manifest cua cac phien demo (vd ban sao C:\\VT-Guard-runs)")
    ap.add_argument("--alerts", default=os.path.join(os.environ.get("VTGUARD_HOME") or os.path.join(HERE, "..", ".."), "reports", "step9", "live", "alerts.jsonl"))
    ap.add_argument("--env-file", help="thong tin Indexer (bo qua -> chi bao cot VT-Guard)")
    ap.add_argument("--min-level", type=int, default=4, help="muc luat Wazuh tinh la canh bao (B0 chon L = 4 tren Train)")
    ap.add_argument("--out", default=os.path.join("reports", "step9", "m4"))
    a = ap.parse_args()
    ms = load_manifests(a.manifests)
    if not ms: sys.exit(f"Khong tim thay manifest trong {a.manifests}")
    src = None
    if a.env_file:
        C.load_env_file(a.env_file); src = C.IndexerSource(None, poll_s=0)
    rows = build(ms, a.alerts, src, a.min_level)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "demo_report.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(rows, f, indent=1, ensure_ascii=False)
    md = render(rows, a.min_level)
    with open(os.path.join(a.out, "demo_report.md"), "w", encoding="utf-8", newline="\n") as f: f.write(md)
    print(md)

if __name__ == "__main__":
    main()
