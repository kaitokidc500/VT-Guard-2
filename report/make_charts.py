#!/usr/bin/env python3
"""VT-Guard Buoc 10 - ve bieu do so lieu cho bao cao Word (report/figures/*.png). So lieu doc tu artefact da dong bang
(reports/*_results.json, eval JSON) qua dashboard/data.py - khong tinh lai chi so. Chay: python report/make_charts.py"""
import json, os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "dashboard"))
import data as D                                                    # noqa: E402

OUT = os.path.join(ROOT, "report", "figures"); os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "Times New Roman", "font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 200, "savefig.bbox": "tight"})
C = {"B0": "#9aa5b1", "B1": "#c8a2c8", "B2": "#e3b448", "B3": "#7fb3d5", "VTSEQ": "#2e86c1", "RULES": "#8e44ad", "F3B": "#1e8449",
     "pos": "#c0392b", "neg": "#5d6d7e"}
NAME = {"B0": "B0 · luật Wazuh", "B1": "B1 · TF-IDF+LR", "B2": "B2 · LightGBM", "B3": "B3 · GRU thuần", "VTSEQ": "VT-Seq-ens",
        "RULES": "Chỉ luật tự sinh", "F3B": "F3-B (AI + luật)"}
TTP_VI = {"T1016": "T1016\ndò cấu hình mạng", "T1018": "T1018\ndò máy trong mạng", "T1087.002": "T1087.002\nliệt kê TK miền",
          "T1654": "T1654\nliệt kê nhật ký", "T1003.003": "T1003.003\ntrích xuất NTDS"}

def save(fig, name): fig.savefig(os.path.join(OUT, name)); plt.close(fig); print("ghi", name)

def splits():
    st = D.load_json("reports/dataset_stats.json")["splits"]
    rows = [("Train", "train"), ("T-clean", "t_clean"), ("T-hard", "t_hard"), ("T-novel", "t_novel")]
    pos = [st[k]["positive"] if "positive" in st[k] else st[k]["n_pos"] for _, k in rows]
    tot = [st[k]["windows"] if "windows" in st[k] else st[k]["n"] for _, k in rows]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    x = np.arange(len(rows)); neg = [t - p for t, p in zip(tot, pos)]
    ax.bar(x, neg, color=C["neg"], label="Cửa sổ âm (lành tính)", width=0.55)
    ax.bar(x, pos, bottom=neg, color=C["pos"], label="Cửa sổ dương (độc hại)", width=0.55)
    for i, (t, p) in enumerate(zip(tot, pos)): ax.text(i, t + 6, f"{t} ({p} dương)", ha="center", fontsize=11)
    ax.set_xticks(x, [r[0] for r in rows]); ax.set_ylabel("Số cửa sổ"); ax.set_ylim(0, max(tot) * 1.15)
    ax.legend(frameon=False, loc="upper right"); save(fig, "c_splits.png")

def ttp_windows():
    st = D.load_json("reports/dataset_stats.json")["splits"]
    keys = [("Train", "train"), ("T-clean", "t_clean"), ("T-novel", "t_novel")]
    fig, ax = plt.subplots(figsize=(7.2, 3.2)); w = 0.26; x = np.arange(len(D.TTPS))
    cols = ["#2e86c1", "#28b463", "#e67e22"]
    for j, (lab, k) in enumerate(keys):
        tt = st[k]["ttp_windows"]
        v = [tt.get(t, 0) for t in D.TTPS]
        b = ax.bar(x + (j - 1) * w, v, w, label=lab, color=cols[j])
        ax.bar_label(b, fontsize=9, padding=1)
    ax.set_xticks(x, [TTP_VI[t] for t in D.TTPS], fontsize=10); ax.set_ylabel("Số cửa sổ mang nhãn")
    ax.legend(frameon=False); save(fig, "c_ttp_windows.png")

def per_ttp(split="t_novel"):
    pt = D.per_ttp_f1(split); order = ["B0", "RULES", "VTSEQ", "F3B"]
    fig, ax = plt.subplots(figsize=(7.4, 3.5)); w = 0.2; x = np.arange(len(D.TTPS))
    for j, k in enumerate(order):
        v = [pt[k][t]["f1"] for t in D.TTPS]
        b = ax.bar(x + (j - 1.5) * w, v, w, label=NAME[k], color=C[k])
        ax.bar_label(b, labels=[f"{y:.2f}" for y in v], fontsize=8, padding=1, rotation=90)
    ax.set_xticks(x, [TTP_VI[t] for t in D.TTPS], fontsize=10); ax.set_ylabel("F1 theo kỹ thuật"); ax.set_ylim(0, 1.18)
    ax.legend(frameon=False, ncol=4, fontsize=10, loc="upper center", bbox_to_anchor=(0.5, 1.13)); save(fig, f"c_per_ttp_{split}.png")

def compare():
    cm = D.model_comparison()
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.4), gridspec_kw={"width_ratios": [1.5, 1]})
    names = [NAME[r["key"]] for r in cm]; y = np.arange(len(cm))[::-1]
    v = [r["macro_novel"]["v"] for r in cm]
    lo = [r["macro_novel"].get("lo", r["macro_novel"]["v"] - r["macro_novel"].get("sd", 0)) for r in cm]
    hi = [r["macro_novel"].get("hi", r["macro_novel"]["v"] + r["macro_novel"].get("sd", 0)) for r in cm]
    ax = axs[0]
    ax.barh(y, v, color=[C[r["key"]] for r in cm], height=0.6)
    ax.errorbar(v, y, xerr=[np.subtract(v, lo), np.subtract(hi, v)], fmt="none", ecolor="#333", capsize=3, lw=1)
    for yi, vi, h in zip(y, v, hi): ax.text(h + 0.015, yi, f"{vi:.3f}", va="center", fontsize=10)
    ax.set_yticks(y, names, fontsize=10); ax.set_xlim(0, 1.08); ax.set_xlabel("macro-F1 TTP trên T-novel (CI 95%)")
    ax = axs[1]; fp = [r["t_hard_fp"]["v"] for r in cm]
    ax.barh(y, fp, color=["#c0392b" if r["key"] == "B0" else "#5dade2" for r in cm], height=0.6)
    for yi, f in zip(y, fp): ax.text(f + 0.3, yi, f"{f:.1f}".rstrip("0").rstrip("."), va="center", fontsize=10)
    ax.set_yticks(y, [""] * len(y)); ax.set_xlabel("Cảnh báo nhầm trên T-hard (/88)"); ax.set_xlim(0, 20)
    fig.tight_layout(); save(fig, "c_compare.png")

def ablation():
    ch = D.ablation_chain()
    codes = [r["code"] for r in ch]
    fig, ax = plt.subplots(figsize=(7.2, 3.3)); x = np.arange(len(codes))
    for key, lab, col, mk in (("oof_macro_f1_ttp", "OOF macro-F1 TTP (Train)", "#2e86c1", "o"),
                              ("test_macro_f1_novel", "macro-F1 TTP T-novel (test)", "#1e8449", "s"),
                              ("test_t1654_novel", "F1 T1654 T-novel (test)", "#e67e22", "^")):
        v = np.array([r[key]["v"] for r in ch]); s = np.array([r[key].get("sd", 0) for r in ch])
        ax.plot(x, v, marker=mk, color=col, label=lab); ax.fill_between(x, v - s, v + s, color=col, alpha=0.12)
    ax.set_xticks(x, codes); ax.set_ylim(0.4, 0.95); ax.set_ylabel("Giá trị (TB ± độ lệch chuẩn)")
    ax.axvspan(1.5, 2.5, color="#f9e79f", alpha=0.35); ax.text(2, 0.42, "+ attention", ha="center", fontsize=10)
    ax.legend(frameon=False, fontsize=10, loc="lower right"); save(fig, "c_ablation.png")

def early():
    r6 = {"VTSEQ": "reports/step6/eval/vtseq_M3_ens.json", "B0": "reports/step5/b0_wazuh.json", "RULES": "reports/step7/eval/rules.json"}
    ks = ["4", "8", "16", "32"]
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.0), sharey=True)
    for ax, sp, title in ((axs[0], "t_clean", "T-clean"), (axs[1], "t_novel", "T-novel")):
        for k, rel in r6.items():
            e = D.load_json(rel)
            v = [e["early"][sp][kk]["recall"]["point"] for kk in ks] + [e["splits"][sp]["tuned"]["recall"]["point"]]
            ax.plot(range(5), v, marker="o", label=NAME[k], color=C[k])
        ax.set_xticks(range(5), ["4", "8", "16", "32", "đủ"]); ax.set_title(title); ax.set_xlabel("Số event đầu tiên k")
        ax.set_ylim(0.4, 1.03)
    axs[0].set_ylabel("Recall cửa sổ dương"); axs[1].legend(frameon=False, fontsize=10, loc="lower right"); fig.tight_layout()
    save(fig, "c_early.png")

def latency():
    lat, host = D.latency(); steps = [("featurize", "Mã hoá đặc trưng"), ("onnx", "ONNX VT-Seq-ens"), ("sigma", "Sigma 11 luật"), ("fusion", "Hợp nhất F3-B")]
    fig, ax = plt.subplots(figsize=(7.0, 2.2)); left = 0
    cols = ["#5dade2", "#2e86c1", "#8e44ad", "#1e8449"]
    for (k, lab), c in zip(steps, cols):
        v = lat["batch32"][k][0]; ax.barh(0, v, left=left, color=c, label=f"{lab}: {v:.2f} ms"); left += v
        v1 = lat["batch1"][k][0]
    left = 0
    for (k, lab), c in zip(steps, cols):
        v = lat["batch1"][k][0]; ax.barh(1, v, left=left, color=c); left += v
    ax.set_yticks([0, 1], [f"Lô 32 (tổng {lat['batch32']['total'][0]:.2f} ms)", f"Lô 1 (tổng {lat['batch1']['total'][0]:.2f} ms)"])
    ax.set_xlabel("ms / cửa sổ (CPU 1 luồng)"); ax.legend(frameon=False, fontsize=9, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.45))
    save(fig, "c_latency.png")

def labeler():
    vals = [("Tiến trình bộ điều phối", 345393), ("Console người vận hành", 2393), ("Khung (harness) ART", 2195),
            ("Mảnh vỡ PowerShell 4103", 683), ("Upload manifest scp/ssh", 316)]
    fig, ax = plt.subplots(figsize=(7.0, 2.5))
    y = np.arange(len(vals))[::-1]; v = [x[1] for x in vals]
    ax.barh(y, v, color="#5d6d7e", height=0.6); ax.set_xscale("log")
    for yi, vi in zip(y, v): ax.text(vi * 1.15, yi, f"{vi:,}".replace(",", "."), va="center", fontsize=10)
    ax.set_yticks(y, [x[0] for x in vals]); ax.set_xlabel("Số event bị loại (thang log)"); ax.set_xlim(100, 3e6)
    save(fig, "c_labeler_drop.png")

if __name__ == "__main__":
    for f in (splits, ttp_windows, per_ttp, compare, ablation, early, latency, labeler): f()
    per_ttp("t_clean")
