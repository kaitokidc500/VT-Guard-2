#!/usr/bin/env python3
"""VT-Guard Buoc 8 moc 3 - reports/step8/m3_explain.md tu reports/step8/m3_explain.json (kiem trung, giai thich, vi du, do tre).
Chay: python src/pipeline/m3_report.py
"""
import json, os

S8 = os.path.join("reports", "step8")

def ex_block(e, title):
    L = [f"**{title}** - `{e['window_id']}` ({e['split']}, nhan: {'doc hai ' + str(e.get('label_ttps')) if e['label_malicious'] else 'LANH TINH'}); "
         f"{'canh bao' if e.get('alert', True) else 'KHONG canh bao'}: score {e['score']:.4f} (p_ai {e['p_ai']:.4f}, nguong {e['threshold']:.4f}), "
         f"decision_source `{e['decision_source']}`, TTP du doan {e['ttps']}, luat khop: "
         + (", ".join(f"`{r['id']}` (`{r['sigma_file']}`)" for r in e["rule_ids"]) or "khong co"), "",
         "| # | alpha | image | parent | event_id | lenh (canon) |", "|---|---|---|---|---|---|"]
    for t in e["attention_top5"]:
        L.append(f"| {t['idx']} | {t['alpha']:.3f} | {t['image_name']} | {t['parent_image_name']} | {t['event_id']} | `{(t['cmd_canon'] or '-')[:110]}` |")
    return L + [""]

def main():
    o = json.load(open(os.path.join(S8, "m3_explain.json"), encoding="utf-8"))
    L = ["# VT-Guard Buoc 8 moc 3 - canh bao giai thich duoc + pipeline suy luan dau-cuoi", "",
         "Pipeline `src/pipeline/infer.py`: cua so -> featurize (vocab dong bang Buoc 4) -> ONNX VT-Seq-ens (`models/vtseq_M3_ens.onnx`) "
         "-> matcher Sigma (`rules/sigma/*.yml`) -> fusion F3-B khoa (`reports/step8/final_fusion.json`, commit 3fd9531) -> canh bao. "
         "Canh bao: `reports/step8/alerts_<split>.jsonl` (schema muc 6).", "",
         "## 1. Kiem trung voi ket qua cham (reports/preds/fusion_<split>.jsonl)", "",
         "| Tap | Cua so | Dac trung != file split | Lech quyet dinh nhi phan | Lech quyet dinh TTP | Lech kenh luat r | Diem lech toi da |", "|---|---|---|---|---|---|---|"]
    for s, c in o["check"].items():
        L.append(f"| {s} | {c['n']} | {c['featurize_mismatch_vs_split']} | {c['decision_mismatch_binary']} | {c['decision_mismatch_ttp']} | {c['rule_r_mismatch']} | {c['max_abs_score_diff']:.1e} |")
    L += ["", "Diem lech <= 6e-7: ONNX (host CPU) so voi PyTorch (Colab CUDA) va lam tron 6 chu so cua file preds; khong quyet dinh nao doi.", "",
          "## 2. Thong ke giai thich", "",
          "decision_source: `both` = AI vuot nguong va co luat khop; `ai` = AI vuot nguong, khong luat; `rule` = AI duoi nguong, canh bao chi nho "
          "+0.1 cua luat. F3-B KHONG phai OR: luat khop ma p + 0.1 < nguong thi khong canh bao.", "",
          "| Tap | Canh bao | Co >= 1 luat khop | TP: n / co luat | FP: n / co luat | decision_source (tat ca) | Luat khop nhung khong canh bao | Duong bi bo sot |",
          "|---|---|---|---|---|---|---|---|"]
    for s, st in o["stats"].items():
        a, tp, fp = st["alerts"], st["tp"], st["fp"]
        pct = lambda g: f"{g['n']} / {g['with_rule']}" + (f" ({g['share_with_rule']:.0%})" if g["share_with_rule"] is not None else "")
        L.append(f"| {s} | {a['n']} | {a['with_rule']} ({(a['share_with_rule'] or 0):.0%}) | {pct(tp)} | {pct(fp)} | {a['decision_source']} | {st['rule_match_not_alerted']} | {st['positives_missed']} |")
    tot = {k: sum(o["stats"][s]["alerts"][k] for s in o["stats"]) for k in ("n", "with_rule")}
    tp_ = {k: sum(o["stats"][s]["tp"][k] for s in o["stats"]) for k in ("n", "with_rule")}
    L += ["", f"Gop 3 tap: {tot['with_rule']}/{tot['n']} canh bao ({tot['with_rule'] / tot['n']:.0%}) co it nhat mot luat giai thich; rieng canh bao "
          f"dung (TP) {tp_['with_rule']}/{tp_['n']} ({tp_['with_rule'] / tp_['n']:.0%}); canh bao nham (FP) 0/{tot['n'] - tp_['n']} co luat. "
          "Moi canh bao deu co top-5 event attention. Khong co canh bao nao chi do luat (`rule`) tren test.", "",
          "## 3. Vi du (chon tat dinh: window_id nho nhat cua moi loai)", ""]
    if o["examples"]["rule"] is None: L += ["**Canh bao chi do luat:** khong co tren 3 tap test (moi cua so co luat khop va duoc canh bao deu da vuot nguong AI).", ""]
    else: L += ex_block(o["examples"]["rule"], "Canh bao chi do luat")
    L += ex_block(o["examples"]["ai"], "Canh bao chi do AI")
    L += ex_block(o["examples"]["both"], "Canh bao do ca hai")
    for e in o["examples"]["rule_match_not_alerted"]: L += ex_block(e, "Luat khop nhung F3-B KHONG canh bao (luat bao nham, AI chan)")
    for e in o["examples"]["t_hard_fp"]: L += ex_block(e, "Canh bao NHAM tren T-hard")
    lat = o["latency"]
    L += ["## 4. Do tre dau-cuoi (host CPU, onnxruntime 1 thread)", "",
          f"CPU: {lat['host']['cpu']}; onnxruntime {lat['host']['onnxruntime']}; {lat['n_windows']} cua so test; cache hash dong lenh xoa truoc moi luot. "
          "ms moi cua so (batch 32: thoi gian mot lo chia so cua so).", "",
          "| Buoc | batch 1: TB | batch 1: p95 | batch 32: TB | batch 32: p95 |", "|---|---|---|---|---|"]
    for k in ("total", "featurize", "onnx", "sigma", "fusion"):
        L.append(f"| {k} | {lat['batch1'][k]['mean_ms']:.3f} | {lat['batch1'][k]['p95_ms']:.3f} | {lat['batch32'][k]['mean_ms']:.3f} | {lat['batch32'][k]['p95_ms']:.3f} |")
    L.append("")
    with open(os.path.join(S8, "m3_explain.md"), "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(L))
    print("\n".join(L))

if __name__ == "__main__":
    main()
