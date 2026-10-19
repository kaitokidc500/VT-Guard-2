#!/usr/bin/env python3
"""VT-Guard Buoc 9 - kiem thu lop du lieu + 5 trang dashboard, 2 phan (docs/STEP9-BRIEF.md muc 3).
(1) checksum artefact, (2) so canh bao tap test trung step8_results.json, (3) precision theo nguon trung results JSON, tinh lai tu
canh bao + nhan, va step8_report.md, (4) do tre trung results JSON, (5) ham hang doi / su co khong lo nhan khi khong truyen nhan,
(6) loc / sap xep / tim kiem, (7) VTGUARD_HOME (ban sao artefact o thu muc khac) + khong duong dan Windows + code ASCII,
(8) 5 trang chay trong streamlit.testing: Phan A (SIEM, luong truc tiep tu fixture dashboard/fixtures/, khong nhan) va Phan B
(ket qua nghien cuu, co nhan), (9) su co, phan ra diem, luat, bang danh gia trung results JSON va report Markdown (0 lech),
(10) luong truc tiep: canh bao / su co LINC / phan ra diem, (11) so lieu 3 yeu cau de tai trung nguon doc lap.
Chay: python dashboard/test_data.py
"""
import json, os, re, shutil, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
sys.path.insert(0, str(HERE))
import data as D          # noqa: E402

RES = []
_STR = json.load(open(HERE / "ui_vi.json", encoding="utf-8"))

def S(k): return _STR[k]

def check(name, cond, detail=""):
    RES.append(bool(cond)); print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""), flush=True)

def md_rows(rel, prefix):
    """Cac dong bang Markdown bat dau bang prefix (theo thu tu trong file)."""
    return [l for l in open(D.P(rel), encoding="utf-8").read().splitlines() if l.startswith(prefix)]

def main():
    t0 = time.time()
    # ---- 1. checksum ----
    v = D.verify_artefacts()
    check("1 checksum artefact khop dashboard/artefacts_sha256.json", all(x is True for x in v.values()), f"{sum(x is True for x in v.values())}/{len(v)}")
    # ---- 2. canh bao tap test == step8_results ----
    al = D.all_alerts(); ov = D.overview_counts(al); st8 = D.results(8)["explanation"]["stats"]
    bad = [s for s in D.SPLITS if (ov[s]["n"], ov[s]["with_rule"], ov[s]["decision_source"]) !=
           (st8[s]["alerts"]["n"], st8[s]["alerts"]["with_rule"], st8[s]["alerts"]["decision_source"])]
    check("2a so canh bao / co luat / decision_source theo tap == step8_results.json", not bad, f"tong {ov['tong']}")
    check("2b tong 101 canh bao, 76 co luat, both 76 / ai 25, khong co 'rule'",
          (ov["tong"]["n"], ov["tong"]["with_rule"], ov["tong"]["decision_source"]) == (101, 76, {"both": 76, "ai": 25}))
    # ---- 3. precision theo nguon ----
    pr = D.precision_by_source(); lab = D.eval_labels()
    ok = True
    for s in list(D.SPLITS) + ["gop"]:
        A = al if s == "gop" else [a for a in al if a["split"] == s]
        for src in ("both", "ai"):
            a = [x for x in A if x["decision_source"] == src]; tp = sum(lab[x["window_id"]][0] for x in a)
            ok &= (pr[s][src]["n"], pr[s][src]["tp"]) == (len(a), tp)
    check("3a precision theo nguon (results JSON) == dem lai tu canh bao + nhan (0 lech)", ok, f"gop: both {pr['gop']['both']['tp']}/{pr['gop']['both']['n']}, ai {pr['gop']['ai']['tp']}/{pr['gop']['ai']['n']}")
    row = md_rows("reports/step8_report.md", "| gop 3 tap |")[0]
    want = [f"{pr['gop'][k]['tp']}/{pr['gop'][k]['n']} = {pr['gop'][k]['precision']:.3f} [{pr['gop'][k]['wilson']['lo']:.3f}, {pr['gop'][k]['wilson']['hi']:.3f}]" for k in ("both", "ai")]
    check("3b so hien thi == dong 'gop 3 tap' cua step8_report.md", all(w in row for w in want), row[:120])
    tot_rule = re.search(r"Gop 3 tap: (\d+)/(\d+) canh bao", open(D.P("reports/step8/m3_explain.md"), encoding="utf-8").read())
    check("3c 76/101 co luat == m3_explain.md", tot_rule and (int(tot_rule.group(1)), int(tot_rule.group(2))) == (ov["tong"]["with_rule"], ov["tong"]["n"]))
    # ---- 4. do tre ----
    lat, host = D.latency(); m3 = D.load_json("reports/step8/m3_explain.json")["latency"]
    okl = all(lat[b][k] == (m3[b][k]["mean_ms"], m3[b][k]["p95_ms"]) for b in ("batch1", "batch32") for k in lat[b])
    check("4 do tre hien thi == step8_results.json == m3_explain.json", okl, f"tong batch1 {lat['batch1']['total']}, batch32 {lat['batch32']['total']} ms")
    # ---- 5. khong lo nhan khi khong truyen nhan ----
    rows_ops = D.queue_rows(al, eval_mode=False); inc = D.incidents(al); inc_ops = D.incident_rows(inc, eval_mode=False)
    leak = {k for r in rows_ops + inc_ops for k in r if k in D.LABEL_KEYS or k in ("ket_qua", "ttp_that", "window_id", "so_nham")}
    raw = "".join(open(D.P(f"reports/step8/alerts_{s}.jsonl"), encoding="utf-8").read() for s in D.SPLITS)
    check("5a hang doi + bang su co khong co cot nhan / window_id goc khi khong truyen nhan", not leak, f"cot hang doi: {sorted(rows_ops[0])}")
    check("5b file canh bao khong chua truong nhan", not any(f'"{k}"' in raw for k in D.LABEL_KEYS))
    guard = []
    for fn in (lambda: D.queue_rows(al, eval_mode=True), lambda: D.incident_rows(inc, eval_mode=True)):
        try: fn(); guard.append(False)
        except AssertionError: guard.append(True)
    check("5c co nhan bat buoc truyen nhan tuong minh (hang doi + su co)", all(guard))
    rows_ev = D.queue_rows(al, eval_mode=True, labels=lab)
    check("5d bang canh bao Phan B: cot ket_qua, so 'Nham' == 5 canh bao nham", sum(r["ket_qua"] == "Nham" for r in rows_ev) == sum(st8[s]["fp"]["n"] for s in D.SPLITS))
    runs = {a["window_id"].split(":", 1)[0] for a in al}
    shown = [str(x) for r in rows_ops + inc_ops for x in r.values()] + [a[k] for a in al for k in ("code", "session", "window", "incident")]
    hit = sorted({s for s in shown for run in runs if run in s})
    check("5e ma hien thi khong mang hau to vai tro phien (-a / -h) cua window_id goc", not hit and all(not re.search(r"-[a-z]$", a["session"]) for a in al),
          f"{len(runs)} phien; vd {al[0]['window_id']} -> {al[0]['window']}")
    sc = D.ttp_scores()
    check("5f ttp_scores() chi tra truong diem (khong y / y_ttp)", all(set(r) == {"s", "s_ttp", "p_ttp"} for r in sc.values()), f"{len(sc)} cua so")
    # ---- 6. loc / sap xep ----
    f = D.filter_queue(rows_ops, hosts=["DC01"]); g = D.filter_queue(rows_ops, ttps=["T1003.003"]); h = D.filter_queue(rows_ops, min_score=1.0)
    s1 = D.sort_queue(rows_ops)
    okf = (all(r["host"] == "DC01" for r in f) and all("T1003.003" in r["ttps"] for r in g) and all(r["diem"] >= 1.0 for r in h)
           and len(f) + len(D.filter_queue(rows_ops, hosts=["WIN10-01"])) == len(rows_ops))
    okp = [r["uu_tien"] for r in rows_ops if r["nguon"] == "both"] and all(r["uu_tien"] == "Cao" for r in rows_ops if r["nguon"] == "both") \
        and all(r["uu_tien"] == "Can xem lai" for r in rows_ops if r["nguon"] == "ai")
    check("6a loc theo host / TTP / diem dung", okf, f"DC01 {len(f)}, T1003 {len(g)}, diem>=1 {len(h)}")
    check("6b uu tien: both = Cao, ai = Can xem lai; sap xep uu tien dat 'Cao' truoc", okp and s1[0]["uu_tien"] == "Cao" and s1[-1]["uu_tien"] == "Can xem lai")
    tf = datetime(2026, 10, 15, tzinfo=timezone.utc)
    t1 = D.filter_queue(rows_ops, text="VTR-T1003003-01"); t2 = D.filter_queue(rows_ops, text=al[0]["incident"])
    check("6c loc thoi gian + tim kiem (ma luat, ma su co)", all(D._dt(r["bat_dau"]) >= tf for r in D.filter_queue(rows_ops, t_from=tf))
          and len(t1) == D.rule_counts(al)["VTR-T1003003-01"] and all(r["su_co"] == al[0]["incident"] for r in t2) and t2, f"tim VTR-T1003003-01: {len(t1)}")
    # ---- 7. VTGUARD_HOME ----
    tmp = Path(tempfile.mkdtemp())
    try:
        for rel in D.all_artefacts() + [D.MANIFEST.as_posix(), "reports/step8_report.md", "reports/step8/m3_explain.md"]:
            dst = tmp.joinpath(*rel.split("/")); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(D.P(rel), dst)
        old = os.environ.get("VTGUARD_HOME"); os.environ["VTGUARD_HOME"] = str(tmp)
        try:
            okh = (D.home() == tmp.resolve() and all(x is True for x in D.verify_artefacts().values()) and len(D.all_alerts()) == len(al)
                   and len(D.rule_rows(al)) == 11 and len(D.model_comparison()) == len(D.COMPARE) and D.highlights()["yc1"]["n_rules"] == 11)
        finally:
            if old is None: os.environ.pop("VTGUARD_HOME", None)
            else: os.environ["VTGUARD_HOME"] = old
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check("7a VTGUARD_HOME tro sang ban sao artefact: doc + checksum + luat + bang danh gia + 3 yeu cau dung", okh, f"{tmp.as_posix()}")
    pys = [p for p in sorted(HERE.rglob("*.py"))]
    win = [f"{p.name}:{i}" for p in pys if p.name != "test_data.py" for i, l in enumerate(open(p, encoding="utf-8"), 1)
           if re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/](?!/)", l) or re.search(r"[\"'][^\"']*\\\\[^\"'nu]", l)]
    check("7b khong co duong dan Windows hard-code trong dashboard/**/*.py", not win, f"{win}")
    nonascii = [f"{p.relative_to(HERE).as_posix()}:{i}" for p in pys for i, l in enumerate(open(p, encoding="utf-8"), 1) if any(ord(c) > 127 for c in l)]
    check("7c code dashboard ASCII (chuoi co dau chi o ui_vi.json)", not nonascii, f"{len(pys)} file .py; {nonascii[:5]}")
    # ---- 9. su co, phan ra diem, luat, bang danh gia ----
    by_inc = {i["code"]: i for i in inc}
    ok9a = (len(inc) == 55 and sum(i["n"] for i in inc) == len(al) and len(by_inc) == len(inc)
            and all(by_inc[a["incident"]]["host"] == a["host"] and by_inc[a["incident"]]["session"] == a["session"] and a["code"] in by_inc[a["incident"]]["alerts"] for a in al)
            and all(set(i["chain"]) == {k for a in al if a["incident"] == i["code"] for k in a["ttps"]} for i in inc)
            and all((i["priority"] == "Cao") == any(a["decision_source"] == "both" for a in al if a["incident"] == i["code"]) for i in inc))
    check("9a su co tap test: 55 nhom host + phien, 101 canh bao, chuoi TTP == hop TTP canh bao, uu tien dung", ok9a,
          f"{sum(i['priority'] == 'Cao' for i in inc)} uu tien cao; {sum('TA0006' in i['tactics'] for i in inc)} co Credential Access")
    bad_d = []
    for a in al:
        d = D.alert_detail(a, sc)
        if {t["ttp"] for t in d["ttp"] if t["s"] >= t["tau"]} != set(a["ttps"]): bad_d.append((a["code"], "ttp"))
        if abs(d["p"] + d["beta"] * d["r"] - d["s"]) > 1e-6 or abs(sc[a["window_id"]]["s"] - a["score"]) > 1e-6: bad_d.append((a["code"], "s"))
        if not (a["score"] >= a["threshold"]): bad_d.append((a["code"], "tau"))
        for t in d["ttp"]:
            if not (abs(t["bonus"]) < 1e-6 or (t["kenh_luat"] and abs(t["bonus"] - d["beta"]) < 1e-6 and d["r"] == 1)): bad_d.append((a["code"], t["ttp"]))
    check("9b chi tiet: s = p + beta*r, s >= tau, {k: s_k >= tau_k} == TTP canh bao, beta*r_k chi o kenh luat (0 lech)", not bad_d, f"{len(al)} canh bao; {bad_d[:3]}")
    rr = D.rule_rows(al); prov = {r["id"]: r for r in D.load_json("reports/step7/rules_provenance.json")["rules"]}
    rr_ev = D.rule_rows(al, eval_mode=True); rc = D.rule_counts(al)
    ok9c = len(rr) == 11 and len(D.sigma_files()) == 11
    for r, re_ in zip(rr, rr_ev):
        p = prov[r["id"]]; line = md_rows("reports/step7_report.md", f"| {r['id']} |")[-1]
        ok9c &= (r["train_ho_tro"], r["oof_cua_so"]) == (p["train"]["support"], p["oof"]["tp"] + p["oof"]["fp"])
        ok9c &= f"| {p['train']['tp']}/{p['train']['fp']} | {re_['tp_t_clean']}/{re_['fp_t_clean']} | {re_['fp_t_hard']} | {re_['tp_t_novel']}/{re_['fp_t_novel']} |" in line
        ok9c &= all(sum(1 for a in al if a["split"] == s and any(x["id"] == r["id"] for x in a["rule_ids"])) <= r[f"khop_{s}"] for s in D.SPLITS)
        ok9c &= r["canh_bao"] == rc.get(r["id"], 0) and not any(k.startswith(("tp_", "fp_")) for k in r)
        ok9c &= bool(D.sigma_docs(r["id"])) and D.sigma_docs(r["id"])[-1].get("level") in ("high", "medium")
    okr = all(sum(x["p_malicious"] >= 0.5 for x in D.load_jsonl(f"reports/preds/rules_{s}.jsonl")) == st8[s]["alerts"]["with_rule"] + st8[s]["rule_match_not_alerted"] for s in D.SPLITS)
    check("9c luat: 11 luat, Train / OOF == provenance, TP/FP theo tap == step7_report.md, canh bao dan chieu <= so cua so khop, "
          "cua so co luat == co luat + khop khong canh bao (step8)", ok9c and okr, f"{sum(rc.values())} lan dan chieu")
    cm = {r["key"]: r for r in D.model_comparison()}; fmt = D.fmt
    names = {"B0": "b0_wazuh", "B1": "b1_tfidf_b", "B2": "b2_lgbm_a", "VTSEQ": "fusion_F0", "RULES": "fusion_F1", "F3B": "fusion_F3B"}
    ok9d, det = True, []
    for k, n in names.items():
        main_ = md_rows("reports/step8_report.md", f"| {n} |")
        r = cm[k]; l1, l2 = main_[0], main_[1]
        okk = all(fmt(r[m]) in l1 for m in ("t_clean_f1", "t_clean_pr_auc", "t_novel_f1", "t_novel_pr_auc"))
        okk &= f"{fmt(r['macro_clean'], nd=2)} / {fmt(r['macro_novel'], nd=2)}" in l1 and f"| {int(r['t_hard_fp']['v'])}/88 |" in l2
        ok9d &= okk; det.append(f"{k}:{'ok' if okk else 'LECH'}")
    b3 = cm["B3"]; m0a = md_rows("reports/step6_report.md", "| M0a |")[0]
    okb3 = all(fmt(b3[m], pm=" +- ") in m0a for m in ("t_novel_f1", "t_novel_pr_auc")) and fmt(b3["t_hard_fp"], nd=1, pm=" +- ") in m0a
    vf = D.vtseq_final()
    okf0 = all(abs(cm["VTSEQ"][a]["v"] - vf[b][0]) < 1e-4 for a, b in (("t_clean_f1", "t_clean_f1"), ("t_novel_f1", "t_novel_f1"), ("t_novel_pr_auc", "t_novel_pr_auc"),
                                                                     ("macro_clean", "macro_f1_clean"), ("macro_novel", "macro_f1_novel"), ("t_hard_fp", "t_hard_fp")))
    check("9d bang so sanh mo hinh == step8_report.md (B0/B1/B2/F0/F1/F3-B) + step6_report.md (B3 (a) = M0a); F0 == step6 final.vtseq_M3_ens",
          ok9d and okb3 and okf0, ", ".join(det) + f", B3:{'ok' if okb3 else 'LECH'}, F0=VT-Seq-ens:{'ok' if okf0 else 'LECH'}")
    ok9e = True
    for r in D.ablation_chain():
        l = md_rows("reports/step6_report.md", f"| {r['code']} |")[0]
        ok9e &= all(fmt(r[k], pm=" +- ") in l for k in ("oof_macro_f1_ttp", "oof_pr_auc_bin", "oof_fpr_hard_negative", "test_t_novel_f1", "test_t_novel_pr_auc"))
        ok9e &= fmt(r["test_t_hard_fp"], nd=1, pm=" +- ") in l and f"{fmt(r['test_macro_f1_clean'], nd=2, pm=' +- ')} / {fmt(r['test_macro_f1_novel'], nd=2, pm=' +- ')}" in l
    for r in D.feature_ablation():
        l = md_rows("reports/step5_report.md", f"| {r['family']} ({r['variant']}) |")[0]
        fp = fmt(r["t_hard_fp"], nd=1, pm=" +- ") if "sd" in r["t_hard_fp"] else str(int(r["t_hard_fp"]["v"]))
        ok9e &= f"| {fp} |" in l and (r["macro_novel"] is None or f"/ {fmt(r['macro_novel'], nd=2, pm=' +- ')} |" in l)
    oof, test, _ = D.fusion_tables()
    for r in oof:
        l = md_rows("reports/step8_report.md", f"| {r['variant']}: {r['strategy']} |")[0]
        ok9e &= l.startswith(f"| {r['variant']}: {r['strategy']} | {r['macro_f1_ttp']:.3f} |") and all(f"| {r[k]:.3f} " in l + " " for k in ("pr_auc", "fpr_hn", "recall"))
    check("9e chuoi ablation Buoc 6 + ablation dac trung Buoc 5 + OOF hop nhat Buoc 8 == step6/5/8_report.md", ok9e,
          f"{len(D.ablation_chain())} cau hinh, {len(D.feature_ablation())} bien the, {len(oof)} OOF")
    hr = D.holm_rows(); ok9f = len(hr) == 15
    for r in hr:
        rest = f" | {r['metric']} | {r['diff']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}] | {r['p']:.3f} | {r['p_holm']:.3f} |"
        lead = f"| {r['cmp'].replace('VT-Seq-ens - ', '')}" if r["family"] == 6 else f"| {r['cmp']}"
        ok9f &= any(l.startswith(lead + rest) for l in md_rows(f"reports/step{r['family']}_report.md", "| "))
    sig = [f"{r['cmp']} / {r['metric']}" for r in hr if r["sig"]]
    check("9f bang Holm (9 + 6 so sanh) == step6_report.md + step8_report.md; co y nghia khi p Holm < 0.05", ok9f, f"co y nghia: {sig}")
    acc = D.acceptance()
    check("9g tieu chi chap nhan Buoc 6/7/8 doc tu results JSON: 8/6/6 dat", {k: (sum(c["pass"] for c in v), len(v)) for k, v in acc.items()} == {6: (8, 8), 7: (6, 6), 8: (6, 6)})
    # ---- 10. luong truc tiep (fixture: 17 canh bao phat lai log mau) ----
    os.environ["VTGUARD_LIVE_ALERTS"] = str(FIX / "live_alerts.jsonl"); os.environ["VTGUARD_LIVE_STATUS"] = str(FIX / "live_status.json")
    la = D.live_alerts(); li = D.live_incidents(la); lst = D.live_status()
    raw_l = open(FIX / "live_alerts.jsonl", encoding="utf-8").read()
    ok10a = (len(la) == 17 and not any(f'"{k}"' in raw_l for k in D.LABEL_KEYS) and [a["code"] for a in la] == [f"LIVE-{i:04d}" for i in range(1, 18)]
             and all(a["split"] == "live" for a in la) and lst and lst["alerts"] == 17 and lst["done"])
    check("10a canh bao truc tiep: 17 ban ghi, khong truong nhan, ma LIVE-xxxx theo thu tu dong cua so, status.json khop", ok10a,
          f"{sum(a['decision_source'] == 'both' for a in la)} both")
    ok10b = sorted(c for i in li for c in i["alerts"]) == sorted(a["code"] for a in la) and all(a["incident"] in {i["code"] for i in li} for a in la)
    for i in li:
        A = sorted([a for a in la if a["incident"] == i["code"]], key=lambda a: D._dt(a["t0"]))
        ok10b &= all(a["host"] == i["host"] for a in A) and set(i["chain"]) == {k for a in A for k in a["ttps"]}
        ok10b &= all((D._dt(A[j]["t0"]) - max(D._dt(x["t1"]) for x in A[:j])).total_seconds() <= D.LIVE_GAP_S for j in range(1, len(A)))
    for hh in {i["host"] for i in li}:                    # hai su co lien tiep cung host cach nhau > LIVE_GAP_S
        I = sorted([i for i in li if i["host"] == hh], key=lambda i: D._dt(i["start"]))
        ok10b &= all((D._dt(y["start"]) - D._dt(x["end"])).total_seconds() > D.LIVE_GAP_S for x, y in zip(I, I[1:]))
    check("10b su co truc tiep (LINC): moi canh bao dung 1 su co, cung host, khoang nghi <= 15 phut ben trong, > 15 phut giua su co", ok10b,
          ", ".join(f"{i['code']} {i['host']} {i['n']}" for i in li))
    rq = D.queue_rows(la); bad10 = []
    for a in la:
        d = D.alert_detail(a, {})
        if {t["ttp"] for t in d["ttp"] if t["s"] >= t["tau"]} != set(a["ttps"]) or abs(d["p"] + d["beta"] * d["r"] - a["score"]) > 1e-6: bad10.append(a["code"])
    check("10c hang doi truc tiep khong cot nhan; phan ra diem s = p + beta*r va TTP s_k >= tau_k == TTP canh bao (0 lech)",
          not bad10 and not {k for r in rq for k in r if k in D.LABEL_KEYS or k in ("ket_qua", "ttp_that", "window_id")}, f"{bad10}")
    # ---- 11. so lieu 3 yeu cau de tai ----
    H = D.highlights(); b0 = D.results(5)["models"]["B0"]; r7 = D.results(7)
    ok11 = all(abs(H["per_ttp"]["B0"][t]["f1"] - b0["t_novel"]["per_ttp_f1"][t]["point"]) < 1e-9 for t in D.TTPS)
    ok11 &= H["blind"] == [t for t in D.TTPS if b0["t_novel"]["per_ttp_f1"][t]["point"] == 0]
    ok11 &= (H["yc1"]["n_rules"], H["yc1"]["hard_fp"], H["yc1"]["b0_hard_fp"]) == (11, r7["rules_only"]["t_hard_fp"], 17)
    ok11 &= (H["yc2"]["both_tp"], H["yc2"]["both_n"], H["yc2"]["ai_tp"], H["yc2"]["ai_n"], H["yc2"]["with_rule"], H["yc2"]["n_alerts"]) == (76, 76, 20, 25, 76, 101)
    ok11 &= abs(H["yc3"]["holm"]["diff"] - 0.092) < 1e-9 and H["yc3"]["holm"]["p_holm"] < 0.05 and H["yc3"]["hard_fp"] == 1
    ev3 = D.load_json("reports/step8/eval/fusion_F3B.json")["splits"]["t_novel"]["ttp_tuned"]
    ok11 &= abs(ev3["macro_f1"]["point"] - H["yc2"]["f3_macro"]["v"]) < 1e-9
    check("11 so lieu 3 yeu cau (the Phan B) == step5/7/8 results + eval JSON; B0 F1 theo TTP == step5_results.json", ok11,
          f"Wazuh B0 F1=0 o {H['blind']}; YC3 {H['yc3']['holm']['diff']:+.3f} p Holm {H['yc3']['holm']['p_holm']:.3f}")
    # ---- 8. 5 trang, 2 phan ----
    from streamlit.testing.v1 import AppTest
    def run_page(page, state=None, env=None):
        old = {k: os.environ.get(k) for k in (env or {})}
        os.environ.update(env or {})
        try:
            import streamlit as st_
            st_.cache_data.clear()                         # cache dung chung tien trinh: khong de du lieu trang truoc lot sang
            at = AppTest.from_file(str(HERE / "pages" / f"{page}.py"), default_timeout=120)
            for k, v in (state or {}).items(): at.session_state[k] = v
            at.run()
        finally:
            for k, v in old.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k] = v
        md = [m.value for m in at.markdown] + [c.value for c in at.caption] + [i.value for i in at.info]
        dfs = []
        for d in at.dataframe:
            x = d.value; dfs.append(x.data if hasattr(x, "data") and not hasattr(x, "columns") else x)
        return at, md, dfs
    label_cols = {"ket_qua", "ttp_that", "window_id", "so_nham", "TP", "FP", S("col_ket_qua"), S("col_ttp_that"), S("col_window_id")}
    okp8, det = True, []
    cases = [("live", None, None, "siem", lambda md, dfs: any(">17<" in m for m in md) and any(len(x) == 17 for x in dfs)),
             ("live", None, {"VTGUARD_LIVE_ALERTS": str(FIX / "khong_co.jsonl"), "VTGUARD_LIVE_STATUS": str(FIX / "khong_co.json")}, "siem",
              lambda md, dfs: any(S("lv_empty")[:30] in m for m in md)),
             ("detail", None, None, "siem", lambda md, dfs: not any(S("d_truth") in m for m in md) and any("LIVE-0017" in m for m in md)),
             ("timeline", None, None, "siem", lambda md, dfs: any(len(x) == len(li) for x in dfs)),
             ("detail", {"detail_src": "test"}, None, "research", lambda md, dfs: any(S("d_truth") in m for m in md)),
             ("evaluation", None, None, "research", lambda md, dfs: any("vtg-reqs" in m for m in md) and any(len(x) == 101 for x in dfs)),
             ("rules", None, None, "research", lambda md, dfs: any(len(x) == 11 and any(str(c).startswith("tpfp_") for c in x.columns) for x in dfs))]
    for page, state, env, part, extra in cases:
        at, md, dfs = run_page(page, state, env)
        err = [e.value for e in at.exception]
        ok8 = not err and any(f"vtg-top vtg-{part}" in m for m in md) and extra(md, dfs)
        if part == "siem":      # Phan A: khong cot nhan, khong id cua so tap test
            cells = [str(c) for x in dfs for c in list(x.columns) + [v for col in x.columns for v in x[col].tolist()]]
            ok8 &= not any(c in label_cols for x in dfs for c in x.columns) and not any(run in s_ for s_ in cells + md for run in runs)
        okp8 &= bool(ok8); det.append(f"{page}/{part}{'/rong' if env else ''}:{'ok' if ok8 else err or 'sai'}")
    check("8 5 trang chay khong loi; Phan A (SIEM) khong nhan / khong id tap test, Phan B co nhan; thanh tieu de ghi dung phan", okp8, ", ".join(det))
    print(f"\nKET QUA: {sum(RES)}/{len(RES)} PASS trong {time.time() - t0:.1f}s")
    sys.exit(0 if all(RES) else 1)

if __name__ == "__main__":
    main()
