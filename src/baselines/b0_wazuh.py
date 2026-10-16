#!/usr/bin/env python3
"""VT-Guard Buoc 5 - B0: luat Wazuh co san ("SIEM mua ve, chua tinh chinh").  docs/STEP5-BRIEF.md muc 4.1

- Nhi phan: cua so duong neu co IT NHAT mot event co wazuh_rule_level >= L.
  Diem cua so = max(wazuh_rule_level) / 15 (de co PR-AUC/ROC-AUC); nguong khoa = L/15.
  L quet 3..12 TREN TRAIN, chon L toi da F1 (hoa -> L lon hon), KHOA, roi cham tren test.
  B0 khong hoc nen khong can cross-validation; "OOF" cua Train = chinh du doan tren Train.
- Da nhan TTP: cua so mang TTP t neu co event co wazuh_rule_mitre khop t, theo quan he ky thuat:
  trung khop, ky thuat con (T1016.001 -> T1016) hoac ky thuat CHA (Wazuh gan T1087 -> T1087.002).
  Khong dieu kien muc luat. Nguong TTP co dinh 0.5 tren chi bao 0/1 (khong tinh chinh).
  TTP nao Wazuh khong co luat -> B0 mu (recall 0): ly do can luat tu sinh o Buoc 7.
- CHI doc wazuh_rule_level, wazuh_rule_mitre cua event (B0 la mo hinh duy nhat duoc cham wazuh_rule_*).
Chay: python src/baselines/b0_wazuh.py
"""
import json, os, sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "eval"))
from common import full_window_events
from evaluate import (check_dataset, load_all_meta, evaluate, render_markdown, write_preds, check_predictions,
                      TTPS, SPLITS, TEST_SPLITS)
from bootstrap import f1, precision, recall, fpr

MODEL = "b0_wazuh"
LEVELS = range(3, 13)
USED_FIELDS = ("wazuh_rule_level", "wazuh_rule_mitre")

def mitre_to_ttp(m, t):
    return m == t or m.startswith(t + ".") or t.startswith(m + ".")

def main(root="."):
    print("checksum dataset-v1.0:", check_dataset(root))
    meta = load_all_meta(root)
    ev = full_window_events(root, [w["window_id"] for s in SPLITS for w in meta[s]])
    feat, mitre_seen = {}, Counter()
    for wid, events in ev.items():
        lv = max([e["wazuh_rule_level"] or 0 for e in events] + [0])
        ms = {m for e in events for m in (e["wazuh_rule_mitre"] or [])}
        for m in ms: mitre_seen[m] += 1
        feat[wid] = {"max_level": lv, "ttp": {t: any(mitre_to_ttp(m, t) for m in ms) for t in TTPS}}

    # ---- quet L tren Train ----
    tr = meta["train"]
    y = np.array([w["window_malicious"] for w in tr], bool)
    lv = np.array([feat[w["window_id"]]["max_level"] for w in tr])
    sweep = []
    for L in LEVELS:
        yh = lv >= L
        sweep.append({"L": L, "pos_pred": int(yh.sum()), "precision": precision(y, yh), "recall": recall(y, yh),
                      "f1": f1(y, yh), "fpr": fpr(y, yh)})
    best = max(sweep, key=lambda r: ((r["f1"] if r["f1"] is not None else -1), r["L"]))
    L = best["L"]
    print("\n== Quet L tren Train (cua so duong neu co event level >= L) ==")
    print("  L | du doan + |  Prec |  Rec  |  F1   |  FPR")
    for r in sweep:
        fmt = lambda v: " -   " if v is None else f"{v:.3f}"
        print(f" {r['L']:2d} | {r['pos_pred']:8d} | {fmt(r['precision'])} | {fmt(r['recall'])} | {fmt(r['f1'])} | {fmt(r['fpr'])}"
              + ("   <- chon" if r["L"] == L else ""))
    print(f"L DA CHON = {L} (F1 Train {best['f1']:.3f}); nguong diem = {L}/15 = {L / 15:.4f}")

    # ---- du doan ----
    preds = {s: {w["window_id"]: {"p": feat[w["window_id"]]["max_level"] / 15.0,
                                  "p_ttp": {t: float(feat[w["window_id"]]["ttp"][t]) for t in TTPS}} for w in meta[s]}
             for s in SPLITS}
    ttp_train_f1 = {t: f1(np.array([t in w["window_ttps"] for w in tr]),
                          np.array([feat[w["window_id"]]["ttp"][t] for w in tr])) for t in TTPS}
    thresholds = {"binary": L / 15.0, "binary_train_oof_f1": best["f1"], "binary_L": L,
                  "ttp": {t: 0.5 for t in TTPS}, "ttp_train_oof_f1": ttp_train_f1,
                  "note": "B0 khong hoc: L chon truc tiep tren Train (khong CV); nguong TTP co dinh 0.5 tren chi bao 0/1"}
    res = evaluate(MODEL, meta, {s: preds[s] for s in TEST_SPLITS}, thresholds, root=root)
    res["level_sweep_train"] = sweep
    res["mitre_tags_seen_windows"] = dict(mitre_seen.most_common())
    res["ttp_mapping"] = {t: sorted(m for m in mitre_seen if mitre_to_ttp(m, t)) for t in TTPS}
    res["blind_ttps"] = [t for t in TTPS if not res["ttp_mapping"][t]]
    res["fields_used"] = list(USED_FIELDS)
    res["acceptance"] = {"one_pred_per_window_no_leak": check_predictions(meta, {s: preds[s] for s in TEST_SPLITS})["ok"]}

    for s in SPLITS: write_preds(root, MODEL, s, meta[s], preds[s])
    os.makedirs(os.path.join(root, "reports", "step5"), exist_ok=True)
    with open(os.path.join(root, "reports", "step5", f"{MODEL}.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    md = render_markdown(res)
    with open(os.path.join(root, "reports", "step5", f"{MODEL}.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print()
    print(md)
    print("Anh xa wazuh_rule_mitre -> TTP:", res["ttp_mapping"])
    print("TTP B0 mu (khong co luat Wazuh nao gan):", res["blind_ttps"])
    print("Tag mitre trong cac cua so:", res["mitre_tags_seen_windows"])
    print("Truong duoc dung:", res["fields_used"], "| moi cua so 1 du doan, khong ro ri run_id:", res["acceptance"])

if __name__ == "__main__":
    main()
