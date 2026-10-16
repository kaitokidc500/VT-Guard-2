#!/usr/bin/env python3
"""VT-Guard Buoc 5 - bootstrap CI va cac chi so co ban (chi numpy, khong phu thuoc sklearn).

- bootstrap_ci(n_units, stat_fn): lay mau lai n_units DON VI (cua so hoac phien) co hoan lai,
  n_boot lan (mac dinh 1000), seed co dinh 1337 -> CI percentile 95%.
  Cung seed + cung n_units => cung chuoi chi so lay mau, nen hai mo hinh tren cung mot tap duoc
  so sanh tren cung cac mau bootstrap (paired).
  Lan lay mau ma chi so khong xac dinh (vd khong co mau duong) bi bo qua; so lan hop le duoc tra ve.
- Chi so nhi phan: precision/recall/F1/FPR (None neu khong xac dinh), average precision (PR-AUC,
  cung dinh nghia voi sklearn average_precision_score), ROC-AUC (Mann-Whitney, hang trung binh khi hoa).
"""
import numpy as np

N_BOOT = 1000
SEED = 1337

def bootstrap_ci(n_units, stat_fn, n_boot=N_BOOT, seed=SEED, alpha=0.05):
    """stat_fn(idx: np.ndarray[int]) -> float | None. Tra ve dict point/lo/hi/n_valid."""
    point = stat_fn(np.arange(n_units))
    if n_units == 0:
        return {"point": point, "lo": None, "hi": None, "n_valid": 0, "n_boot": n_boot, "n_units": 0}
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        v = stat_fn(rng.integers(0, n_units, n_units))
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            vals.append(v)
    if not vals:
        return {"point": point, "lo": None, "hi": None, "n_valid": 0, "n_boot": n_boot, "n_units": n_units}
    lo, hi = np.percentile(vals, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"point": point, "lo": float(lo), "hi": float(hi), "n_valid": len(vals), "n_boot": n_boot, "n_units": n_units}

# ---------------- chi so ----------------
def counts(y, yhat):
    y = np.asarray(y, bool); yhat = np.asarray(yhat, bool)
    return {"tp": int(np.sum(y & yhat)), "fp": int(np.sum(~y & yhat)),
            "fn": int(np.sum(y & ~yhat)), "tn": int(np.sum(~y & ~yhat))}

def precision(y, yhat):
    c = counts(y, yhat); d = c["tp"] + c["fp"]
    return c["tp"] / d if d else None

def recall(y, yhat):
    c = counts(y, yhat); d = c["tp"] + c["fn"]
    return c["tp"] / d if d else None

def f1(y, yhat):
    """None neu tap khong co mau duong va khong co du doan duong (khong xac dinh)."""
    c = counts(y, yhat); d = 2 * c["tp"] + c["fp"] + c["fn"]
    return 2 * c["tp"] / d if d else None

def fpr(y, yhat):
    c = counts(y, yhat); d = c["fp"] + c["tn"]
    return c["fp"] / d if d else None

def average_precision(y, s):
    """PR-AUC = sum_k (R_k - R_{k-1}) * P_k tren cac nguong phan biet (giam dan). None neu khong co duong."""
    y = np.asarray(y, bool); s = np.asarray(s, float)
    npos = int(y.sum())
    if npos == 0: return None
    order = np.argsort(-s, kind="mergesort")
    s_sorted, y_sorted = s[order], y[order]
    distinct = np.where(np.diff(s_sorted))[0]
    idx = np.r_[distinct, len(s_sorted) - 1]          # vi tri cuoi moi nhom diem bang nhau
    tp = np.cumsum(y_sorted)[idx]; fp = (idx + 1) - tp
    prec = tp / (tp + fp); rec = tp / npos
    rec_prev = np.r_[0.0, rec[:-1]]
    return float(np.sum((rec - rec_prev) * prec))

def roc_auc(y, s):
    """Xac suat diem cua mot mau duong > mot mau am (hoa tinh 0.5). None neu thieu mot lop."""
    y = np.asarray(y, bool); s = np.asarray(s, float)
    npos, nneg = int(y.sum()), int((~y).sum())
    if npos == 0 or nneg == 0: return None
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), float)
    s_sorted = s[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s_sorted[j + 1] == s_sorted[i]: j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return float((ranks[y].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))

def best_f1_threshold(y, s):
    """Nguong t toi da F1 cho du doan s >= t (t lay trong cac gia tri diem phan biet).
    Hoa -> chon t lon nhat (it duong tinh gia hon). Tra ve (t, f1)."""
    y = np.asarray(y, bool); s = np.asarray(s, float)
    best_t, best_f = 0.5, -1.0
    for t in np.unique(s):
        v = f1(y, s >= t)
        if v is not None and (v > best_f or (v == best_f and t > best_t)):
            best_t, best_f = float(t), v
    return best_t, (best_f if best_f >= 0 else None)

def wilson(k, n, z=1.959964):
    """Khoang Wilson 95% cho ti le k/n - bo sung cho bootstrap khi ti le = 0 hoac 1 (bootstrap suy bien
    thanh [0,0] / [1,1], vd 6/6 phien hoac 0/87 cua so)."""
    if n == 0: return {"k": k, "n": n, "lo": None, "hi": None}
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return {"k": int(k), "n": int(n), "lo": round(float(max(0.0, c - h)), 4), "hi": round(float(min(1.0, c + h)), 4)}

def rankdata(x):
    """Hang trung binh khi hoa (1..n)."""
    x = np.asarray(x, float); order = np.argsort(x, kind="mergesort")
    r = np.empty(len(x), float); xs = x[order]; i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and xs[j + 1] == xs[i]: j += 1
        r[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r

def spearman(x, y):
    """Tuong quan hang Spearman; None neu < 3 diem hoac mot bien hang so."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 3: return None
    rx, ry = rankdata(x), rankdata(y)
    if rx.std() == 0 or ry.std() == 0: return None
    return float(np.corrcoef(rx, ry)[0, 1])
