#!/usr/bin/env python3
"""VT-Guard Buoc 9 - lop du lieu cua dashboard (docs/STEP9-BRIEF.md muc 1-3). CHI DOC artefact da dong bang.

- Moi duong dan tinh tu bien moi truong VTGUARD_HOME (mac dinh: goc repo = thu muc cha cua dashboard/), noi bang pathlib,
  khong hard-code duong dan Windows -> chay duoc tren host lan trong container.
- Khong tinh lai chi so: so lieu lay tu reports/step{5,6,7,8}_results.json; dashboard chi dem / loc / sap xep / gom nhom canh bao.
- Hai che do: VAN HANH (mac dinh) khong tra truong nhan; DANH GIA moi goi eval_labels() (doc y / y_ttp tu
  reports/preds/fusion_<split>.jsonl) va cac bang chi so tu results JSON.
- Ma hien thi: window_id / run_id goc mang hau to vai tro phien cua orchestrator (-a / -h / -b) = gan nhu nhan -> che do van hanh
  chi hien ma canh bao VTG-xxxx, ma su co INC-xxx va phien da bo hau to (mask_run / mask_window).
- Checksum: dashboard/artefacts_sha256.json liet ke sha256 cac artefact dashboard doc; verify_artefacts() so lai.
Chay: python dashboard/data.py --write-manifest   (ghi manifest tu artefact hien tai)
      python dashboard/data.py                    (kiem checksum)
"""
import argparse, hashlib, json, os, re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SPLITS = ("t_clean", "t_hard", "t_novel")
TTPS = ("T1016", "T1018", "T1087.002", "T1654", "T1003.003")
# MITRE ATT&CK Enterprise: ky thuat -> (tactic id, ten ky thuat)
MITRE = {"T1016": ("TA0007", "System Network Configuration Discovery"), "T1018": ("TA0007", "Remote System Discovery"),
         "T1087.002": ("TA0007", "Account Discovery: Domain Account"), "T1654": ("TA0007", "Log Enumeration"),
         "T1003.003": ("TA0006", "OS Credential Dumping: NTDS")}
TACTICS = {"TA0007": "Discovery", "TA0006": "Credential Access"}
PRIORITY = {"both": "Cao", "ai": "Can xem lai", "rule": "Can xem lai"}
LABEL_KEYS = ("y", "y_ttp", "label", "label_malicious", "label_ttps", "window_malicious", "window_ttps", "ket_qua", "tp", "fp")
MANIFEST = Path("dashboard") / "artefacts_sha256.json"
ARTEFACTS = ([f"reports/step8/alerts_{s}.jsonl" for s in SPLITS] + [f"reports/preds/fusion_{s}.jsonl" for s in SPLITS] +
             [f"reports/preds/vtseq_M3_ens_{s}.jsonl" for s in SPLITS] +
             ["reports/step8_results.json", "reports/step8/final_fusion.json", "reports/step8/m3_explain.json",
              "reports/step7/rules_provenance.json", "reports/step5_results.json", "reports/step6_results.json",
              "reports/step7_results.json"] +
             [f"reports/step8/eval/fusion_{m}.json" for m in ("F0", "F1", "F3B")] + ["reports/step5/b0_wazuh.json"])

def home():
    return Path(os.environ.get("VTGUARD_HOME") or Path(__file__).resolve().parent.parent).resolve()

def P(rel):
    """Duong dan tuyet doi tu duong dan tuong doi dang 'a/b/c' (dau '/' doc lap he dieu hanh)."""
    return home().joinpath(*str(rel).split("/"))

def sigma_files():
    return sorted(f"rules/sigma/{p.name}" for p in P("rules/sigma").glob("*.yml"))

def all_artefacts():
    return ARTEFACTS + sigma_files()

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def write_manifest():
    m = {rel: sha256(P(rel)) for rel in all_artefacts()}
    with open(P(MANIFEST.as_posix()), "w", encoding="utf-8", newline="\n") as f: json.dump(m, f, indent=1, sort_keys=True)
    return m

def verify_artefacts():
    """-> {rel: True/False/'thieu'} so voi dashboard/artefacts_sha256.json."""
    ref = json.load(open(P(MANIFEST.as_posix()), encoding="utf-8"))
    out = {}
    for rel, h in ref.items():
        p = P(rel); out[rel] = "thieu" if not p.exists() else (sha256(p) == h)
    return out

# ---------------- doc ----------------
def load_json(rel): return json.load(open(P(rel), encoding="utf-8"))

def load_jsonl(rel): return [json.loads(l) for l in open(P(rel), encoding="utf-8") if l.strip()]

def results(step=8): return load_json(f"reports/step{step}_results.json")

def _dt(s):
    """ISO 8601 (co the 7 chu so phan giay, hau to Z) -> datetime UTC."""
    s = s.replace("Z", "+00:00")
    if "." in s:
        head, rest = s.split(".", 1); frac = "".join(c for c in rest.split("+")[0] if c.isdigit())[:6]
        s = f"{head}.{frac}+00:00"
    return datetime.fromisoformat(s)

_ROLE = re.compile(r"-[a-z]$")

def mask_run(run_id):
    """Bo hau to vai tro phien (-a / -h / -b) cua orchestrator: '20261014-133419-dc01-a' -> '20261014-133419-dc01'."""
    return _ROLE.sub("", run_id)

def mask_window(window_id):
    run, w = window_id.split(":", 1)
    return f"{mask_run(run)}:{w}"

def alerts(split):
    """Canh bao cua mot tap (schema Buoc 8 muc 6) + truong 'split'. Ban ghi canh bao KHONG co truong nhan."""
    out = []
    for a in load_jsonl(f"reports/step8/alerts_{split}.jsonl"):
        assert not set(a) & set(LABEL_KEYS), f"canh bao chua truong nhan: {set(a) & set(LABEL_KEYS)}"
        out.append({**a, "split": split})
    return out

def all_alerts():
    """Moi canh bao 3 tap + ma hien thi: code (VTG-xxxx theo thoi gian), session / window (da bo hau to), incident (INC-xxx)."""
    al = [a for s in SPLITS for a in alerts(s)]
    for i, a in enumerate(sorted(al, key=lambda a: (_dt(a["t0"]), a["window_id"])), 1):
        a["code"] = f"VTG-{i:04d}"; a["session"] = mask_run(a["window_id"].split(":", 1)[0]); a["window"] = mask_window(a["window_id"])
    for inc in incidents(al):
        for c in inc["alerts"]:
            next(a for a in al if a["code"] == c)["incident"] = inc["code"]
    return al

def eval_labels():
    """CHI CHE DO DANH GIA: {window_id: (doc_hai, ttps)} tu reports/preds/fusion_<split>.jsonl."""
    out = {}
    for s in SPLITS:
        for r in load_jsonl(f"reports/preds/fusion_{s}.jsonl"): out[r["window_id"]] = (bool(r["y"]), list(r["y_ttp"]))
    return out

def ttp_scores():
    """{window_id: {'s': diem hop nhat, 's_ttp': {k: s_k}, 'p_ttp': {k: p_k AI}}}. CHI lay truong diem (bo y / y_ttp):
    s / s_k tu reports/preds/fusion_<split>.jsonl (F3-B), p_k tu reports/preds/vtseq_M3_ens_<split>.jsonl."""
    out = {}
    for s in SPLITS:
        ai = {r["window_id"]: dict(r["p_ttp"]) for r in load_jsonl(f"reports/preds/vtseq_M3_ens_{s}.jsonl")}
        for r in load_jsonl(f"reports/preds/fusion_{s}.jsonl"):
            out[r["window_id"]] = {"s": r["p_malicious"], "s_ttp": dict(r["p_ttp"]), "p_ttp": ai[r["window_id"]]}
    return out

# ---------------- trang Tong quan ----------------
def overview_counts(al):
    """So canh bao + phan bo nguon quyet dinh theo tap (dem tu file canh bao)."""
    out = {}
    for s in SPLITS:
        a = [x for x in al if x["split"] == s]
        out[s] = {"n": len(a), "with_rule": sum(bool(x["rule_ids"]) for x in a), "decision_source": dict(Counter(x["decision_source"] for x in a))}
    a = al
    out["tong"] = {"n": len(a), "with_rule": sum(bool(x["rule_ids"]) for x in a), "decision_source": dict(Counter(x["decision_source"] for x in a))}
    return out

def ttp_counts(al):
    """So canh bao gan moi TTP (theo du doan) va so su co co TTP do."""
    inc = incidents(al)
    return {k: {"alerts": sum(k in a["ttps"] for a in al), "incidents": sum(k in i["chain"] for i in inc)} for k in TTPS}

def rule_counts(al):
    """So canh bao dan chieu moi luat (tu rule_ids cua canh bao)."""
    return Counter(r["id"] for a in al for r in a["rule_ids"])

def latency():
    """Do tre pipeline (ms / cua so) tu reports/step8_results.json."""
    lat = results(8)["pipeline"]["latency"]
    return {b: {k: (v["mean_ms"], v["p95_ms"]) for k, v in lat[b].items()} for b in ("batch1", "batch32")}, lat["host"]

def pipeline_info():
    """Cau hinh khoa + kiem tra pipeline (doc tu results JSON / final_fusion.json)."""
    r8 = results(8); ch = r8["final_fusion"]["chosen"]
    chk = r8["pipeline"]["check"]
    return {"strategy": ch["strategy"], "variant": ch["variant"], "beta": ch["beta"], "threshold": ch["threshold_binary"],
            "rule_ttp_channels": ch["rule_ttp_channels"], "lock_commit": r8["lock_commit"], "dataset": r8["dataset_version"],
            "n_rules": len(sigma_files()), "n_windows": sum(chk[s]["n"] for s in SPLITS),
            "mismatch": sum(chk[s]["decision_mismatch_binary"] + chk[s]["decision_mismatch_ttp"] + chk[s]["rule_r_mismatch"] for s in SPLITS),
            "deployed_model": results(6)["deployed_model"]}

def precision_by_source():
    """CHI CHE DO DANH GIA: precision theo nguon + CI Wilson, LAY TU results JSON (khong tinh lai)."""
    return results(8)["explanation"]["precision_by_source"]

# ---------------- trang Hang doi ----------------
def queue_rows(al, eval_mode=False, labels=None):
    """Dong cua hang doi. Che do van hanh: KHONG co cot nhan, khong co window_id goc. Che do danh gia: them 'ket_qua',
    'ttp_that' va 'window_id' goc."""
    rows = []
    for a in al:
        r = {"ma": a["code"], "uu_tien": PRIORITY.get(a["decision_source"], "Can xem lai"), "diem": round(float(a["score"]), 4),
             "nguong": a["threshold"], "nguon": a["decision_source"], "host": a["host"], "bat_dau": a["t0"], "ket_thuc": a["t1"],
             "ttps": ", ".join(a["ttps"]), "luat": ", ".join(r_["id"] for r_ in a["rule_ids"]), "tap": a["split"],
             "su_co": a.get("incident", ""), "cua_so": a["window"]}
        if eval_mode:
            assert labels is not None, "che do danh gia can nhan"
            y, yt = labels[a["window_id"]]; r["ket_qua"] = "Dung" if y else "Nham"; r["ttp_that"] = ", ".join(yt); r["window_id"] = a["window_id"]
        rows.append(r)
    return rows

def filter_queue(rows, min_score=None, hosts=None, ttps=None, sources=None, splits=None, t_from=None, t_to=None, text=None):
    out = []
    for r in rows:
        if min_score is not None and r["diem"] < min_score: continue
        if hosts and r["host"] not in hosts: continue
        if sources and r["nguon"] not in sources: continue
        if splits and r["tap"] not in splits: continue
        if ttps and not set(ttps) & set(x for x in r["ttps"].split(", ") if x): continue
        if t_from is not None and _dt(r["bat_dau"]) < t_from: continue
        if t_to is not None and _dt(r["bat_dau"]) > t_to: continue
        if text and text.lower() not in " ".join(str(r[k]) for k in ("ma", "host", "ttps", "luat", "su_co", "cua_so")).lower(): continue
        out.append(r)
    return out

SORTS = {"uu tien roi diem": (lambda r: (r["uu_tien"] != "Cao", -r["diem"], r["ma"])),
         "diem giam dan": (lambda r: (-r["diem"], r["ma"])), "thoi gian tang dan": (lambda r: (_dt(r["bat_dau"]), r["ma"])),
         "host": (lambda r: (r["host"], _dt(r["bat_dau"])))}

def sort_queue(rows, how="uu tien roi diem"):
    return sorted(rows, key=SORTS[how])

# ---------------- trang Chi tiet canh bao ----------------
def alert_detail(a, scores):
    """Phan ra diem cua mot canh bao: s = p + beta * r (nhi phan) va s_k = p_k + beta * r_k (TTP). Chi doc, khong tinh lai quyet dinh:
    'chon' = TTP trong a['ttps'] (output pipeline); 's_k >= tau_k' chi de hien thi va duoc kiem bang test (0 lech).
    Canh bao truc tiep mang san p_ttp_ai / score_ttp trong ban ghi (khong co file preds)."""
    fc = a["fusion_config"]
    sc = {"s": a["score"], "s_ttp": a["score_ttp"], "p_ttp": a["p_ttp_ai"]} if "score_ttp" in a else scores[a["window_id"]]
    ttp = [{"ttp": k, "p": sc["p_ttp"][k], "bonus": round(sc["s_ttp"][k] - sc["p_ttp"][k], 6), "s": sc["s_ttp"][k],
            "tau": a["thresholds_ttp"][k], "kenh_luat": k in fc["rule_ttp_channels"], "chon": k in a["ttps"]} for k in TTPS]
    return {"p": a["p_ai"], "beta": fc["beta"], "r": int(bool(a["rule_ids"])), "bonus": round(a["score"] - a["p_ai"], 6),
            "s": a["score"], "tau": a["threshold"], "margin": round(a["score"] - a["threshold"], 6), "ttp": ttp}

# ---------------- trang Truc tiep (kieu B) ----------------
LIVE_ALERTS = "reports/step9/live/alerts.jsonl"
LIVE_STATUS = "reports/step9/live/status.json"
SAMPLE_LOG = "samples/replay_demo.jsonl.gz"

def live_path(): return os.environ.get("VTGUARD_LIVE_ALERTS") or LIVE_ALERTS

def status_path(): return os.environ.get("VTGUARD_LIVE_STATUS") or LIVE_STATUS

LIVE_GAP_S = 900                                              # su co truc tiep: canh bao cung host cach nhau <= 15 phut

def live_alerts():
    """Canh bao do src/live/run.py (live / replay) ghi. Ma LIVE-xxxx theo thu tu dong cua so; su co LINC-xxx (live_incidents).
    Khong co truong nhan; dong dang ghi do (JSON hong) bi bo qua."""
    p = P(live_path()) if not os.path.isabs(live_path()) else Path(live_path())
    if not p.exists(): return []
    al = []
    for l in open(p, encoding="utf-8"):
        if not l.strip(): continue
        try: a = json.loads(l)
        except json.JSONDecodeError: continue                  # dong dang ghi do
        assert not set(a) & set(LABEL_KEYS), "canh bao truc tiep chua truong nhan"
        al.append({**a, "split": "live"})
    al.sort(key=lambda a: (a.get("closed_at") or "", a["window_id"]))
    for i, a in enumerate(al, 1):
        a["code"] = f"LIVE-{i:04d}"; a["session"] = a["window_id"].split(":", 1)[0]; a["window"] = a["window_id"]
    for inc in live_incidents(al):
        for c in inc["alerts"]: next(a for a in al if a["code"] == c)["incident"] = inc["code"]
    return al

def live_incidents(al, gap_s=LIVE_GAP_S):
    """Su co cua luong truc tiep (khong co phien / manifest): gom canh bao cung host, canh bao sau bat dau khong qua gap_s giay
    sau khi canh bao truoc ket thuc. Cung cau truc ban ghi voi incidents(); ma LINC-xxx theo thoi diem bat dau."""
    by_host = defaultdict(list)
    for a in sorted(al, key=lambda a: (_dt(a["t0"]), a["code"])): by_host[a["host"]].append(a)
    groups = []
    for A in by_host.values():
        cur = [A[0]]
        for a in A[1:]:
            if (_dt(a["t0"]) - max(_dt(x["t1"]) for x in cur)).total_seconds() > gap_s: groups.append(cur); cur = [a]
            else: cur.append(a)
        groups.append(cur)
    out = [_incident(A[0]["host"], A[0]["window_id"].split(":", 1)[0], A) for A in groups]
    out.sort(key=lambda i: (_dt(i["start"]), i["host"]))
    for n, i in enumerate(out, 1): i["code"] = f"LINC-{n:03d}"
    return out

def replay_running(stt):
    """Luong (live / replay) dang chay: status.json chua 'done' va cap nhat trong 30 s gan nhat."""
    if not stt or stt.get("done"): return False
    try: return (datetime.now(timezone.utc) - _dt(stt["updated_at"])).total_seconds() < 30
    except (KeyError, ValueError): return False

def start_replay(speed=10):
    """Chay src/live/run.py replay log mau (nen) tu dashboard; ghi reports/step9/live/. -> True neu da khoi dong."""
    import subprocess, sys
    if replay_running(live_status()) or not P(SAMPLE_LOG).exists(): return False
    subprocess.Popen([sys.executable, str(P("src/live/run.py")), "replay", "--input", str(P(SAMPLE_LOG)), "--speed", str(speed)],
                     cwd=str(home()), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     env={**os.environ, "VTGUARD_HOME": str(home())}, start_new_session=True)
    return True

def live_status():
    p = Path(status_path()) if os.path.isabs(status_path()) else P(status_path())
    try: return json.load(open(p, encoding="utf-8")) if p.exists() else None
    except json.JSONDecodeError: return None

# ---------------- trang Dong thoi gian su co ----------------
def _incident(host, sess, A):
    A = sorted(A, key=lambda a: (_dt(a["t0"]), a["window_id"]))
    chain = []
    for a in A:
        chain += [k for k in TTPS if k in a["ttps"] and k not in chain]
    end = max((a["t1"] for a in A), key=_dt)
    return {"host": host, "session": sess, "start": A[0]["t0"], "end": end, "n": len(A),
            "n_high": sum(a["decision_source"] == "both" for a in A), "max_score": max(a["score"] for a in A), "chain": chain,
            "tactics": list(dict.fromkeys(MITRE[k][0] for k in chain)), "rules": sorted({r["id"] for a in A for r in a["rule_ids"]}),
            "splits": sorted({a["split"] for a in A}), "alerts": [a.get("code", "") for a in A], "_window_ids": [a["window_id"] for a in A],
            "priority": "Cao" if any(a["decision_source"] == "both" for a in A) else "Can xem lai",
            "duration_s": round((_dt(end) - _dt(A[0]["t0"])).total_seconds(), 1)}

def incidents(al):
    """Gom canh bao theo host + phien (phien da bo hau to). Chuoi TTP = thu tu xuat hien dau tien theo thoi gian
    (trong mot canh bao: thu tu MITRE cua TTPS). Ma INC-xxx theo thoi diem bat dau."""
    g = defaultdict(list)
    for a in al: g[(a["host"], mask_run(a["window_id"].split(":", 1)[0]))].append(a)
    out = [_incident(host, sess, A) for (host, sess), A in g.items()]
    out.sort(key=lambda i: (_dt(i["start"]), i["host"], i["session"]))
    for n, i in enumerate(out, 1): i["code"] = f"INC-{n:03d}"
    return out

def incident_rows(inc, eval_mode=False, labels=None):
    """Dong bang su co. Van hanh: khong nhan, khong id goc. Danh gia: them so canh bao nham + TTP that (hop cac cua so)."""
    rows = []
    for i in inc:
        r = {"ma": i["code"], "uu_tien": i["priority"], "host": i["host"], "phien": i["session"], "bat_dau": i["start"], "ket_thuc": i["end"],
             "thoi_luong_s": i["duration_s"], "so_canh_bao": i["n"], "so_cao": i["n_high"], "diem_max": round(i["max_score"], 4),
             "chuoi": " > ".join(i["chain"]), "chien_thuat": " > ".join(TACTICS[t] for t in i["tactics"]), "luat": ", ".join(i["rules"]),
             "tap": ", ".join(i["splits"])}
        if eval_mode:
            assert labels is not None, "che do danh gia can nhan"
            lab = [labels[w] for w in i["_window_ids"]]
            r["so_nham"] = sum(not y for y, _ in lab); r["ttp_that"] = ", ".join(k for k in TTPS if any(k in yt for _, yt in lab))
        rows.append(r)
    return rows

# ---------------- trang Luat ----------------
def sigma_text(rule_id): return open(P(f"rules/sigma/{rule_id}.yml"), encoding="utf-8").read()

def sigma_docs(rule_id):
    import yaml
    return [d for d in yaml.safe_load_all(sigma_text(rule_id)) if d]

def rule_rows(al, eval_mode=False):
    """11 luat: thong tin quy nap (Train / OOF, tu step7_results.json), muc Sigma, so cua so khop moi tap test
    (= tp + fp cua per_rule) va so canh bao dan chieu. Che do danh gia: them TP / FP theo tap."""
    r7 = results(7); used = rule_counts(al)
    rows = []
    for r in r7["rules"]:
        pr = r7["per_rule"][r["id"]]; docs = sigma_docs(r["id"]); top = docs[-1]
        row = {"id": r["id"], "dich": r["target"], "vi_tu": " AND ".join(r["predicates"]), "muc": top.get("level", ""),
               "loai": "correlation" if "correlation" in top else "single", "train_ho_tro": r["train"]["support"],
               "train_precision": r["train"]["precision"], "oof_precision": r["oof"]["precision"], "oof_cua_so": r["oof"]["tp"] + r["oof"]["fp"],
               "fold_lap_lai": len(r["oof"]["folds_rediscovered"]), "canh_bao": used.get(r["id"], 0),
               "tep": f"rules/sigma/{r['id']}.yml"}
        for s in SPLITS: row[f"khop_{s}"] = pr[s]["tp"] + pr[s]["fp"]
        if eval_mode:
            for s in SPLITS: row[f"tp_{s}"] = pr[s]["tp"]; row[f"fp_{s}"] = pr[s]["fp"]
        rows.append(row)
    return rows

def rule_provenance(rule_id):
    p = load_json("reports/step7/rules_provenance.json")
    return next(r for r in p["rules"] if r["id"] == rule_id), {k: p[k] for k in ("source", "engine", "gates", "ttp_without_rule", "approved", "n_rejected_by_gate")}

def rule_engine_info():
    r7 = results(7); sg = r7["sigma"]; vf = sg["validation"]["files"]; eq = sg["equivalence"]
    summary = {"tool": sg["validation"]["tool"], "files": len(vf), "docs": sum(f["n_documents"] for f in vf.values()),
               "errors": sum(len(f["errors"]) for f in vf.values()), "issues": sum(len(f["validator_issues"]) for f in vf.values()),
               "generate_false": sg["generate_false_on_correlation"], "train_mismatch": sum(e["train_mismatch"] for e in eq.values()),
               "test_mismatch": sum(sum(e["test_mismatch_diagnostic"].values()) for e in eq.values()), "n_equiv": len(eq)}
    return {"engine": r7["engine"], "rejected": r7["n_rejected_by_gate"], "features": r7["features"], "sigma": summary,
            "deviations": r7["deviations_from_brief"], "approved_commit": r7["approved_rules_commit"]}

# ---------------- trang Danh gia (CHI CHE DO DANH GIA) ----------------
def cell(v):
    """Chuan hoa mot gia tri chi so trong results JSON -> {'v'[, 'lo', 'hi'] | [, 'sd']} (khong tinh lai)."""
    if v is None: return None
    if isinstance(v, (int, float)): return {"v": float(v)}
    if isinstance(v, list): return {"v": float(v[0]), "sd": float(v[1])}
    if "point" in v: return {"v": v["point"], "lo": v["lo"], "hi": v["hi"]}
    if "mean" in v: return {"v": v["mean"], "sd": v["std"]}
    if "value" in v: return {"v": float(v["value"])}
    raise ValueError(v)

def fmt(c, nd=3, sep=", ", pm=" +- ", signed=False):
    if c is None: return "-"
    f = (lambda x: f"{x:+.{nd}f}") if signed else (lambda x: f"{x:.{nd}f}")
    if "lo" in c: return f"{f(c['v'])} [{f(c['lo'])}{sep}{f(c['hi'])}]"
    if "sd" in c: return f"{f(c['v'])}{pm}{c['sd']:.{nd}f}"
    return f(c["v"])

COMPARE = [("B0", 5, "B0"), ("B1", 5, "B1 TF-IDF (b)"), ("B2", 5, "B2 (a)"), ("B3", 5, "B3 (a)"),
           ("VTSEQ", 8, "F0"), ("RULES", 8, "F1"), ("F3B", 8, "F3B")]
METRICS = ("t_clean_f1", "t_clean_pr_auc", "t_novel_f1", "t_novel_pr_auc", "macro_clean", "macro_novel", "t_hard_fp")

def _metrics_split_style(m, fp):
    return {"t_clean_f1": m["t_clean"]["f1"], "t_clean_pr_auc": m["t_clean"]["pr_auc"], "t_novel_f1": m["t_novel"]["f1"],
            "t_novel_pr_auc": m["t_novel"]["pr_auc"], "macro_clean": m["t_clean"]["macro_f1_ttp"], "macro_novel": m["t_novel"]["macro_f1_ttp"],
            "t_hard_fp": fp}

def model_comparison():
    """Bang so sanh mo hinh tren test. Nguon: step5_results.json (B0-B3; B3 = TB +- DLC 3 seed), step8_results.json test
    (F0 = VT-Seq-ens nguong khoa Buoc 6, F1 = chi-luat, F3B = trien khai)."""
    r5, r8 = results(5), results(8); rows = []
    for key, step, name in COMPARE:
        m = r5["models"][name] if step == 5 else r8["test"][name]
        vals = _metrics_split_style(m, m["t_hard"]["fp"])
        rows.append({"key": key, "step": step, "src": name, "n_hard": 88, **{k: cell(v) for k, v in vals.items()}})
    return rows

def vtseq_final():
    """step6_results.json final.vtseq_M3_ens (de doi chieu voi F0 cua Buoc 8)."""
    return results(6)["final"]["vtseq_M3_ens"]

CHAIN_COLS = (("oof", "macro_f1_ttp"), ("oof", "pr_auc_bin"), ("oof", "fpr_hard_negative"), ("test", "t_novel_f1"),
              ("test", "t_novel_pr_auc"), ("test", "macro_f1_clean"), ("test", "macro_f1_novel"), ("test", "t1654_novel"), ("test", "t_hard_fp"))

def ablation_chain():
    """Chuoi ablation VT-Seq (Buoc 6): M0a -> M4b, TB +- DLC qua seed."""
    ch = results(6)["chain"]
    return [{"code": c, "desc": v["desc"], "n_seeds": v["n_seeds"], **{f"{a}_{b}": cell(v[a][b]) for a, b in CHAIN_COLS}} for c, v in ch.items()]

ABL_FAMILIES = ("B1 TF-IDF", "B1-raw", "B2", "B3")
ABL_VARIANTS = ("a", "b", "c", "c'")

def feature_ablation():
    """Ablation dac trung Buoc 5: (a) du, (b) bo image/parent, (c) chi event trong cay tien trinh (chi T-hard), (c') che nen mot-phia."""
    ms = results(5)["models"]; rows = []
    for f in ABL_FAMILIES:
        for v in ABL_VARIANTS:
            m = ms[f"{f} ({v})"]
            rows.append({"family": f, "variant": v, "t_hard_fp": cell(m["t_hard"]["fp"]),
                         "macro_novel": cell(m["t_novel"]["macro_f1_ttp"]) if "t_novel" in m else None,
                         "t_novel_f1": cell(m["t_novel"]["f1"]) if "t_novel" in m else None})
    return rows

def fusion_tables():
    """Buoc 8: OOF F0-F4 hai bien the (A / B) va test F0, F0', F1, F2, F3-B, F4-B."""
    r8 = results(8)
    oof = [{"variant": var, "strategy": s, "macro_f1_ttp": v["macro_f1_ttp"], "pr_auc": v["pr_auc"], "fpr_hn": v["fpr_hard_negative"],
            "recall": v["recall"]} for var in ("A", "B") for s, v in r8["oof"][var].items()]
    test = [{"strategy": s, **{k: cell(x) for k, x in _metrics_split_style(m, m["t_hard"]["fp"]).items()}} for s, m in r8["test"].items()]
    return oof, test, r8["final_fusion"]["chosen"]

METRIC8 = {"macro_f1_ttp_t_novel": "macro-F1 TTP T-novel", "pr_auc_t_novel": "PR-AUC T-novel", "fpr_t_hard": "FPR T-hard"}

def holm_rows():
    """Paired bootstrap + Holm: Buoc 6 (VT-Seq-ens vs baseline, 9 so sanh) va Buoc 8 (F3-B vs F0 / F1, 6 so sanh)."""
    rows = [{"family": 6, "cmp": f"VT-Seq-ens - {h['baseline']}", "metric": h["metric"], "diff": h["diff"], "lo": h["lo"], "hi": h["hi"],
             "p": h["p"], "p_holm": h["p_holm"]} for h in results(6)["holm"]]
    for cmp_, d in results(8)["paired_bootstrap_holm"].items():
        for m, h in d.items():
            rows.append({"family": 8, "cmp": cmp_.replace("F3B", "F3-B"), "metric": METRIC8[m], "diff": h["diff"], "lo": h["lo"], "hi": h["hi"],
                         "p": h["p"], "p_holm": h["p_holm"]})
    for r in rows: r["sig"] = r["p_holm"] < 0.05
    return rows

def per_ttp_f1(split="t_novel"):
    """F1 theo TTP tren mot tap test: B0 (luat Wazuh), VT-Seq-ens (F0), chi-luat (F1), F3-B - doc tu eval JSON Buoc 5 / 8."""
    src = {"B0": "reports/step5/b0_wazuh.json", "VTSEQ": "reports/step8/eval/fusion_F0.json", "RULES": "reports/step8/eval/fusion_F1.json",
           "F3B": "reports/step8/eval/fusion_F3B.json"}
    out = {}
    for k, rel in src.items():
        pt = load_json(rel)["splits"][split]["ttp_tuned"]["per_ttp"]
        out[k] = {t: {"f1": pt[t]["f1"]["point"], "lo": pt[t]["f1"]["lo"], "hi": pt[t]["f1"]["hi"], "n_pos": pt[t]["n_pos"], "tp": pt[t]["tp"]}
                  for t in TTPS}
    return out

def highlights():
    """So lieu chinh cho 3 yeu cau de tai (chi doc results JSON / eval JSON, khong tinh lai).
    YC1 luat tu sinh co xuat xu (Buoc 7) - YC2 hop nhat AI + luat (Buoc 8) - YC3 mo hinh chuoi tuy bien (Buoc 6)."""
    r6, r7, r8 = results(6), results(7), results(8)
    cmp_ = {r["key"]: r for r in model_comparison()}; hr = holm_rows(); pt = per_ttp_f1("t_novel")
    ro = r7["rules_only"]; sg = rule_engine_info()["sigma"]; pr = r8["explanation"]["precision_by_source"]["gop"]
    st = r8["explanation"]["stats"]
    ch = r6["chain"]
    return {"blind": [t for t in TTPS if pt["B0"][t]["f1"] == 0.0], "per_ttp": pt,
            "yc1": {"n_rules": len(r7["rules"]), "engine": r7["engine"]["chosen"], "rejected": sum(r7["n_rejected_by_gate"].values()),
                    "sigma_errors": sg["errors"], "hard_fp": int(ro["t_hard_fp"]), "b0_hard_fp": int(cmp_["B0"]["t_hard_fp"]["v"]),
                    "novel_f1": ro["t_novel_f1"]["point"], "ttp_rules": sorted({r["target"] for r in r7["rules"] if r["target"] != "bin"})},
            "yc2": {"holm": [r for r in hr if r["family"] == 8], "both_tp": pr["both"]["tp"], "both_n": pr["both"]["n"], "ai_tp": pr["ai"]["tp"],
                    "ai_n": pr["ai"]["n"], "with_rule": sum(st[s]["alerts"]["with_rule"] for s in SPLITS),
                    "n_alerts": sum(st[s]["alerts"]["n"] for s in SPLITS),
                    "rule_only": sum(st[s]["alerts"]["decision_source"].get("rule", 0) for s in SPLITS),
                    "f3_macro": cmp_["F3B"]["macro_novel"], "ai_macro": cmp_["VTSEQ"]["macro_novel"], "rules_macro": cmp_["RULES"]["macro_novel"],
                    "f3_prauc": cmp_["F3B"]["t_novel_pr_auc"], "rules_prauc": cmp_["RULES"]["t_novel_pr_auc"]},
            "yc3": {"holm": next(r for r in hr if r["family"] == 6 and r["sig"]), "oof_m0": cell(ch["M0a"]["oof"]["macro_f1_ttp"]),
                    "oof_m1": cell(ch["M1"]["oof"]["macro_f1_ttp"]), "hard_fp": cmp_["VTSEQ"]["t_hard_fp"]["v"], "b0_hard_fp": cmp_["B0"]["t_hard_fp"]["v"],
                    "macro": cmp_["VTSEQ"]["macro_novel"], "b0_macro": cmp_["B0"]["macro_novel"], "b3_macro": cmp_["B3"]["macro_novel"],
                    "deployed": r6["deployed_model"]}}

def verify_info():
    """Ket qua lenh verify gan nhat (reports/step9/verify.json) va thong tin image Docker (docker/image_info.json) neu co."""
    out = {}
    for k, rel in (("verify", "reports/step9/verify.json"), ("image", "docker/image_info.json")):
        try: out[k] = load_json(rel)
        except (OSError, json.JSONDecodeError): out[k] = None
    return out

def acceptance():
    return {s: results(s)["acceptance"] for s in (6, 7, 8)}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--write-manifest", action="store_true"); a = ap.parse_args()
    print("VTGUARD_HOME =", home())
    if a.write_manifest: m = write_manifest(); print(f"ghi {MANIFEST.as_posix()}: {len(m)} artefact")
    v = verify_artefacts(); print("checksum:", sum(x is True for x in v.values()), "/", len(v), "khop;", {k: x for k, x in v.items() if x is not True} or "")
