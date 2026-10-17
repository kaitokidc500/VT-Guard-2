#!/usr/bin/env python3
"""VT-Guard Buoc 6 - VT-Seq: GRU-Attention da nhiem (docs/STEP6-BRIEF.md muc 3-5). MOT nguon code cho host va Colab.

Dau vao CHI tu file split dong bang (cat / cmd / num, nhan muc cua so) + vocab.json + file phu aux.jsonl
(src/models/vtseq_aux.py: origin / one_sided = mat na; ev_mal / ev_ttps = nhan tung event CHI Train, CHI de tinh lai
nhan doan crop). Khong doc truong nao khac cua ban ghi split (load_split chi lay ALLOWED_KEYS).
  - dt tren chuoi con: tu num[:,0] = log1p(dt) (lam tron 5 so) dung lai moc thoi gian tuong doi tcum, tinh lai dt.
    Crop lien tiep: dt giu nguyen, event dau = 0 (dung nhu B3). Mat na (c)/(c'): dt = log1p(tong khoang).
Kien truc (3.1-3.4): embedding 7 truong (16 cho event_id/image/parent, 8 cac truong khac) + cmd Linear(256->64) + 5 so
  -> Linear -> LayerNorm (d=96) -> GRU 1 lop mot chieu hidden 96 (pack_padded_sequence) -> pooling:
  "attn" (additive, softmax CHI tren event that, luu alpha) | "last" (trang thai cuoi, = B3) -> dropout 0.3 ->
  dau nhi phan (1) va/hoac dau TTP (5). Da nhiem: loss = BCE_bin + lambda*BCE_ttp (pos_weight tu Train).
  Don nhiem (M1): hai mang rieng, moi mang mot dau.
Name dropout (3.1): khi train thay image_name + parent_image_name bang <unk> voi xac suat p theo CA cua so;
  drop_names=True (ablation b / M4(b)): luon thay, ca luc suy luan.
Crop (3.5): "none" | "b3" (xac suat 0.5, do dai ~U[4, n], nhu B3) | "uniform" (MOI cua so moi lop, moi epoch,
  do dai ~U[4, n]); nhan doan = nhan cac event TRONG doan.
Huan luyen (4.1-4.2): AdamW lr 1e-3, wd 1e-4, batch 32, grad clip 1.0, toi da 100 epoch, patience 10 tren val loss fold;
  CV 5 fold theo nhom (evaluate.cv_folds); mo hinh cuoi fit toan Train, so epoch = trung vi cac fold.
Nguong (4.3): nhi phan theo FPR muc tieu <= 1% tren cua so am OOF (kem max-F1 tham chieu); TTP max-F1 OOF;
  p_bin hay p_bin' = max(p_bin, max_k p_ttp) chon theo PR-AUC OOF. Khong nhin test.
"""
import hashlib, json, math, os, sys, time
from dataclasses import dataclass, asdict, replace

import numpy as np
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "eval"))
from evaluate import cv_folds, check_dataset, TTPS, SPLITS          # noqa: E402
from bootstrap import best_f1_threshold, average_precision, roc_auc  # noqa: E402

CAT_FIELDS = ["channel", "event_id", "image_name", "parent_image_name", "host_role", "integrity_level", "logon_type"]
NAME_COLS = (2, 3)                     # image_name, parent_image_name
BIG = {"event_id", "image_name", "parent_image_name"}
PAD, UNK = 0, 1
CMD_DIM, NUM_DIM = 256, 5
ALLOWED_KEYS = ("window_id", "cat", "cmd", "num", "window_malicious", "window_ttps")   # duy nhat cac khoa duoc doc
SEEDS = (1337, 7, 42, 2024, 99)

@dataclass(frozen=True)
class Config:
    name: str = "vtseq"
    pooling: str = "attn"          # "attn" | "last"
    multitask: bool = True         # False: hai mang don nhiem (bin, ttp)
    crop: str = "uniform"          # "none" | "b3" | "uniform" (U[4, n] moi lop)
    crop_p: float = 0.5            # chi cho crop="b3"
    crop_min: int = 4
    name_drop: float = 0.0         # xac suat theo cua so khi train
    drop_names: bool = False       # ablation (b): luon thay ten cong cu bang <unk>
    mask: str = "a"                # "a" | "b" (= a, ten xu ly bang drop_names) | "c" | "cp"
    d_event: int = 96
    hidden: int = 96
    emb_big: int = 16
    emb_small: int = 8
    cmd_dim: int = 64
    dropout: float = 0.3
    lam: float = 1.0
    lr: float = 1e-3
    weight_decay: float = 1e-4
    batch: int = 32
    clip: float = 1.0
    max_epochs: int = 100
    patience: int = 10
    fpr_target: float = 0.01

# Chuoi ablation kien truc (5.1); M0 = B3 (Buoc 5)
PRESETS = {
    "M1": Config(name="M1", pooling="attn", multitask=False, crop="b3"),
    "M2": Config(name="M2", pooling="attn", multitask=True, crop="b3"),
    "M3": Config(name="M3", pooling="attn", multitask=True, crop="uniform"),
    "M4": Config(name="M4", pooling="attn", multitask=True, crop="uniform", name_drop=0.5),
    "M4b": Config(name="M4b", pooling="attn", multitask=True, crop="uniform", drop_names=True),
}

# ---------------- du lieu ----------------
class Window:
    """Mot cua so: tensor numpy tu file split + mat na/nhan event tu aux (khong phai feature)."""
    __slots__ = ("wid", "cat", "cmd", "num", "tcum", "y_bin", "y_ttp", "origin", "one_sided", "ev_mal", "ev_ttp")

    def __init__(self, rec, aux=None):
        self.wid = rec["window_id"]
        self.cat = np.asarray(rec["cat"], np.int64).reshape(-1, len(CAT_FIELDS))
        n = len(self.cat)
        self.cmd = np.zeros((n, CMD_DIM), np.float32)
        for i, c in enumerate(rec["cmd"]):
            for j, x in c: self.cmd[i, j] = x
        self.num = np.asarray(rec["num"], np.float32).reshape(n, NUM_DIM)
        self.tcum = np.cumsum(np.expm1(self.num[:, 0].astype(np.float64)))   # moc thoi gian tuong doi (giay)
        self.y_bin = float(bool(rec["window_malicious"]))
        self.y_ttp = np.array([float(t in rec["window_ttps"]) for t in TTPS], np.float32)
        self.origin = self.one_sided = self.ev_mal = self.ev_ttp = None
        if aux is not None:
            assert len(aux["origin"]) == n and len(aux["one_sided"]) == n, self.wid
            self.origin = np.array([c == "o" for c in aux["origin"]], bool)
            self.one_sided = np.array([c == "1" for c in aux["one_sided"]], bool)
            if "ev_mal" in aux:
                self.ev_mal = np.array([c == "1" for c in aux["ev_mal"]], bool)
                self.ev_ttp = np.zeros((n, len(TTPS)), np.float32)
                for i, tt in enumerate(aux["ev_ttps"]):
                    for k in tt: self.ev_ttp[i, k] = 1.0
                # nhan event phai hop lai dung nhan cua so
                assert bool(self.ev_mal.any()) == bool(self.y_bin), self.wid
                assert np.array_equal(self.ev_ttp.max(0) if n else np.zeros(len(TTPS)), self.y_ttp), self.wid

    def __len__(self): return len(self.cat)

    def base_idx(self, mask):
        """Chi so event giu lai theo ablation: a/b: tat ca; c: cay tien trinh; cp: bo event nen mot-phia."""
        n = len(self)
        if mask in ("a", "b"): return np.arange(n)
        if mask == "c": return np.flatnonzero(self.origin)
        if mask == "cp": return np.flatnonzero(~self.one_sided)
        raise ValueError(mask)

    def seq(self, idx):
        """(cat, cmd, num) cua chuoi con idx (tang dan); dt tinh lai tren chuoi con, event dau = 0."""
        idx = np.asarray(idx, np.int64)
        if len(idx) == 0:
            return np.zeros((1, len(CAT_FIELDS)), np.int64), np.zeros((1, CMD_DIM), np.float32), np.zeros((1, NUM_DIM), np.float32)
        num = self.num[idx].copy()
        dt = np.zeros(len(idx), np.float64); dt[1:] = np.maximum(0.0, np.diff(self.tcum[idx]))
        num[:, 0] = np.log1p(dt).astype(np.float32)
        return self.cat[idx], self.cmd[idx], num

    def targets(self, idx):
        """Nhan cua doan idx tu nhan TUNG event (chi Train): bin = co event malicious; ttp = hop TTP cac event trong doan."""
        assert self.ev_mal is not None, f"{self.wid}: khong co nhan event (chi Train co)"
        idx = np.asarray(idx, np.int64)
        if len(idx) == 0: return 0.0, np.zeros(len(TTPS), np.float32)
        return float(self.ev_mal[idx].any()), self.ev_ttp[idx].max(0)

    def first_own(self):
        own = np.flatnonzero(self.origin)
        return int(own[0]) if len(own) else None

def load_split(root, split, aux=None):
    """Doc file split dong bang; CHI lay ALLOWED_KEYS cua moi ban ghi."""
    out = []
    with open(os.path.join(root, "data", "processed", "splits", f"{split}.jsonl"), encoding="utf-8") as fh:
        for l in fh:
            r = json.loads(l)
            rec = {k: r[k] for k in ALLOWED_KEYS}
            out.append(Window(rec, None if aux is None else aux[rec["window_id"]]))
    return out

def load_aux(root, manifest=None):
    p = os.path.join(root, "data", "processed", "step6", "aux.jsonl")
    if manifest is not None:
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h != manifest["sha256"]: raise SystemExit(f"LOI: aux.jsonl sha256 {h[:16]} != manifest {manifest['sha256'][:16]}. DUNG.")
    return {json.loads(l)["window_id"]: json.loads(l) for l in open(p, encoding="utf-8")}

def load_data(root="."):
    """Kiem checksum dataset + aux, tra {split: [Window]} va vocab (kich thuoc tu vocab.json)."""
    check_dataset(root)
    man = json.load(open(os.path.join(root, "reports", "step6", "aux_manifest.json"), encoding="utf-8"))
    aux = load_aux(root, man)
    vocab = json.load(open(os.path.join(root, "data", "processed", "vocab.json"), encoding="utf-8"))
    assert vocab["_meta"]["cat_fields"] == CAT_FIELDS
    data = {s: load_split(root, s, aux) for s in SPLITS}
    assert all(w.ev_mal is not None for w in data["train"]) and not any(w.ev_mal is not None for s in SPLITS[1:] for w in data[s])
    return data, vocab

def vocab_sizes(vocab): return [max(vocab[f].values()) + 1 for f in CAT_FIELDS]

# ---------------- mo hinh ----------------
class VTSeq(nn.Module):
    def __init__(self, vsizes, cfg, heads=("bin", "ttp")):
        super().__init__()
        self.cfg, self.heads = cfg, tuple(heads)
        dims = [cfg.emb_big if f in BIG else cfg.emb_small for f in CAT_FIELDS]
        self.embs = nn.ModuleList([nn.Embedding(v, d, padding_idx=PAD) for v, d in zip(vsizes, dims)])
        self.cmd = nn.Linear(CMD_DIM, cfg.cmd_dim)
        self.proj = nn.Linear(sum(dims) + cfg.cmd_dim + NUM_DIM, cfg.d_event)
        self.norm = nn.LayerNorm(cfg.d_event)
        self.gru = nn.GRU(cfg.d_event, cfg.hidden, num_layers=1, batch_first=True)
        if cfg.pooling == "attn":
            self.att_w = nn.Linear(cfg.hidden, cfg.hidden)
            self.att_v = nn.Linear(cfg.hidden, 1, bias=False)
        self.drop = nn.Dropout(cfg.dropout)
        if "bin" in self.heads: self.head_bin = nn.Linear(cfg.hidden, 1)
        if "ttp" in self.heads: self.head_ttp = nn.Linear(cfg.hidden, len(TTPS))

    def encode_events(self, cat, cmd, num):
        x = torch.cat([e(cat[:, :, i]) for i, e in enumerate(self.embs)] + [self.cmd(cmd), num], -1)
        return self.norm(self.proj(x))

    def forward(self, cat, cmd, num, lens):
        B, T = cat.shape[:2]
        x = self.encode_events(cat, cmd, num)
        packed = pack_padded_sequence(x, lens.cpu(), batch_first=True, enforce_sorted=False)
        out, h = self.gru(packed)
        mask = torch.arange(T, device=cat.device)[None, :] < lens[:, None].to(cat.device)
        if self.cfg.pooling == "attn":
            H, _ = pad_packed_sequence(out, batch_first=True, total_length=T)
            e = self.att_v(torch.tanh(self.att_w(H))).squeeze(-1)
            e = e.masked_fill(~mask, float("-inf"))
            alpha = torch.softmax(e, dim=1)
            c = torch.bmm(alpha.unsqueeze(1), H).squeeze(1)
        else:
            c = h[-1]; alpha = None
        c = self.drop(c)
        res = {"alpha": alpha, "mask": mask}
        if "bin" in self.heads: res["logit_bin"] = self.head_bin(c).squeeze(-1)
        if "ttp" in self.heads: res["logit_ttp"] = self.head_ttp(c)
        return res

# ---------------- batch ----------------
def apply_names(cat, cfg, rng, train):
    """Name dropout theo CA cua so; drop_names: luon thay (ca suy luan)."""
    if cfg.drop_names or (train and cfg.name_drop > 0 and rng.random() < cfg.name_drop):
        cat = cat.copy(); cat[:, list(NAME_COLS)] = UNK
    return cat

def collate(seqs):
    L = max(len(c) for c, _, _ in seqs); B = len(seqs)
    cat = np.zeros((B, L, len(CAT_FIELDS)), np.int64); cmd = np.zeros((B, L, CMD_DIM), np.float32)
    num = np.zeros((B, L, NUM_DIM), np.float32); lens = np.zeros(B, np.int64)
    for i, (c, m, n) in enumerate(seqs):
        k = len(c); cat[i, :k] = c; cmd[i, :k] = m; num[i, :k] = n; lens[i] = k
    return torch.from_numpy(cat), torch.from_numpy(cmd), torch.from_numpy(num), torch.from_numpy(lens)

def crop_idx(base, cfg, rng):
    """Doan lien tiep tren chuoi da ap mat na."""
    n = len(base)
    if cfg.crop == "none" or n <= cfg.crop_min: return base
    if cfg.crop == "b3" and rng.random() >= cfg.crop_p: return base
    L = int(rng.integers(cfg.crop_min, n + 1)); s = int(rng.integers(0, n - L + 1))
    return base[s:s + L]

def train_sample(w, cfg, rng):
    idx = crop_idx(w.base_idx(cfg.mask), cfg, rng)
    cat, cmd, num = w.seq(idx)
    yb, yt = w.targets(idx)
    return (apply_names(cat, cfg, rng, True), cmd, num), yb, yt

def eval_seq(w, cfg, idx=None):
    cat, cmd, num = w.seq(w.base_idx(cfg.mask) if idx is None else idx)
    return apply_names(cat, cfg, None, False), cmd, num

# ---------------- huan luyen ----------------
def set_seed(seed):
    torch.manual_seed(seed); np.random.seed(seed % (2 ** 32))
    torch.use_deterministic_algorithms(True, warn_only=True)

def pos_weights(ws):
    yb = np.array([w.y_bin for w in ws]); yt = np.stack([w.y_ttp for w in ws])
    pb = yb.sum(); pt = yt.sum(0); n = len(ws)
    return (torch.tensor([(n - pb) / max(pb, 1)], dtype=torch.float32),
            torch.tensor(np.where(pt > 0, (n - pt) / np.maximum(pt, 1), 1.0), dtype=torch.float32))

def loss_fn(out, yb, yt, pw_bin, pw_ttp, lam):
    l = torch.zeros((), device=yb.device)
    if "logit_bin" in out: l = l + nn.functional.binary_cross_entropy_with_logits(out["logit_bin"], yb, pos_weight=pw_bin.to(yb.device))
    if "logit_ttp" in out: l = l + lam * nn.functional.binary_cross_entropy_with_logits(out["logit_ttp"], yt, pos_weight=pw_ttp.to(yb.device))
    return l

def fit(cfg, vsizes, train_ws, val_ws=None, epochs=None, seed=1337, tag=0, heads=("bin", "ttp"), device="cpu",
        max_batches=None, log=None):
    """Huan luyen mot mang. val_ws -> early stopping (patience) tren val loss (cua so day du, khong crop).
    Tra (net, best_epoch, best_val, hit_ceiling)."""
    set_seed(seed * 1000 + tag)
    rng = np.random.default_rng([seed, tag, len(heads)])
    net = VTSeq(vsizes, cfg, heads).to(device)
    opt = torch.optim.AdamW(net.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    pw_bin, pw_ttp = pos_weights(train_ws)
    if val_ws is not None:
        vb = [eval_seq(w, cfg) for w in val_ws]
        vyb = torch.tensor([w.y_bin for w in val_ws], dtype=torch.float32, device=device)
        vyt = torch.from_numpy(np.stack([w.y_ttp for w in val_ws])).to(device)
    n_ep = epochs if epochs is not None else cfg.max_epochs
    best, best_ep, best_state, wait = math.inf, 0, None, 0
    for ep in range(1, n_ep + 1):
        net.train(); order = rng.permutation(len(train_ws)); tl = []
        for bi, i in enumerate(range(0, len(order), cfg.batch)):
            if max_batches is not None and bi >= max_batches: break
            smp = [train_sample(train_ws[j], cfg, rng) for j in order[i:i + cfg.batch]]
            cat, cmd, num, lens = [t.to(device) for t in collate([s for s, _, _ in smp])]
            yb = torch.tensor([b for _, b, _ in smp], dtype=torch.float32, device=device)
            yt = torch.from_numpy(np.stack([t for _, _, t in smp])).to(device)
            opt.zero_grad(); l = loss_fn(net(cat, cmd, num, lens), yb, yt, pw_bin, pw_ttp, cfg.lam)
            l.backward(); nn.utils.clip_grad_norm_(net.parameters(), cfg.clip); opt.step(); tl.append(float(l.detach()))
        if val_ws is None:
            if log is not None: log.append({"epoch": ep, "train_loss": float(np.mean(tl))})
            continue
        net.eval()
        with torch.no_grad():
            vl = []
            for i in range(0, len(vb), 128):
                cat, cmd, num, lens = [t.to(device) for t in collate(vb[i:i + 128])]
                o = net(cat, cmd, num, lens)
                vl.append(float(loss_fn(o, vyb[i:i + 128], vyt[i:i + 128], pw_bin, pw_ttp, cfg.lam)) * len(lens))
            vl = sum(vl) / len(vb)
        if log is not None: log.append({"epoch": ep, "train_loss": float(np.mean(tl)), "val_loss": vl})
        if vl < best - 1e-4:
            best, best_ep, wait = vl, ep, 0
            best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}
        else:
            wait += 1
            if wait >= cfg.patience: break
    if best_state is not None: net.load_state_dict(best_state)
    return net, best_ep, best, (val_ws is not None and best_ep >= n_ep)

def predict(nets, ws, cfg, device="cpu", idx_fn=None, bs=128):
    """nets: {"joint": net} (da nhiem) hoac {"bin": net, "ttp": net} (don nhiem).
    Tra p_bin (n,), p_ttp (n,5), alpha (list mang numpy theo do dai that, hoac None)."""
    seqs = [eval_seq(w, cfg, None if idx_fn is None else idx_fn(w)) for w in ws]
    pb, pt, al = [], [], []
    for net in nets.values(): net.eval()
    with torch.no_grad():
        for i in range(0, len(seqs), bs):
            cat, cmd, num, lens = [t.to(device) for t in collate(seqs[i:i + bs])]
            ob = (nets["joint"] if "joint" in nets else nets["bin"])(cat, cmd, num, lens)
            ot = ob if "joint" in nets else nets["ttp"](cat, cmd, num, lens)
            pb.append(torch.sigmoid(ob["logit_bin"]).cpu().numpy()); pt.append(torch.sigmoid(ot["logit_ttp"]).cpu().numpy())
            if ob["alpha"] is not None:
                a = ob["alpha"].cpu().numpy()
                al += [a[j, :int(lens[j])] for j in range(len(lens))]
    return np.concatenate(pb), np.concatenate(pt), (al if al else None)

def fit_nets(cfg, vsizes, train_ws, val_ws=None, epochs=None, seed=1337, tag=0, device="cpu", max_batches=None):
    """Da nhiem: mot mang hai dau. Don nhiem: hai mang rieng (bin, ttp). Tra (nets, info)."""
    plan = [("joint", ("bin", "ttp"))] if cfg.multitask else [("bin", ("bin",)), ("ttp", ("ttp",))]
    nets, info = {}, {}
    for k, heads in plan:
        e = None if epochs is None else epochs[k]
        lg = []
        net, ep, vl, ceil = fit(cfg, vsizes, train_ws, val_ws, e, seed, tag, heads, device, max_batches, lg)
        nets[k] = net; info[k] = {"best_epoch": ep, "val_loss": None if val_ws is None else round(vl, 5), "hit_ceiling": ceil,
                   "stop_epoch": len(lg), "log": lg}
    return nets, info

def run_cv(cfg, vsizes, train_ws, folds, seed, device="cpu", max_batches=None):
    """OOF tren Train (5 fold theo nhom) + so epoch tot nhat moi fold."""
    n = len(train_ws); P_bin = np.zeros(n); P_ttp = np.zeros((n, len(TTPS))); folds_info = []
    for fi, (tr, va) in enumerate(folds):
        nets, info = fit_nets(cfg, vsizes, [train_ws[i] for i in tr], [train_ws[i] for i in va], None, seed, fi + 1, device, max_batches)
        pb, pt, _ = predict(nets, [train_ws[i] for i in va], cfg, device)
        P_bin[va] = pb; P_ttp[va] = pt
        folds_info.append({k: {kk: vv for kk, vv in v.items() if kk != "log"} for k, v in info.items()})
    return P_bin, P_ttp, folds_info

def final_epochs(folds_info):
    return {k: max(1, int(np.median([f[k]["best_epoch"] for f in folds_info]))) for k in folds_info[0]}

# ---------------- nguong & lua chon (CHI tren OOF) ----------------
def threshold_at_fpr(y, s, target):
    """Nguong nho nhat sao cho FPR tren cua so am <= target (diem >= nguong la duong)."""
    y = np.asarray(y, bool); neg = np.sort(np.asarray(s, float)[~y])[::-1]
    k = int(math.floor(target * len(neg)))                      # so FP cho phep
    if k >= len(neg): return float(neg.min())
    thr = float(np.nextafter(neg[k], np.inf))                  # cao hon diem am thu k+1
    return thr

def choose_on_oof(train_ws, P_bin, P_ttp, cfg):
    """p_bin vs p_bin' (PR-AUC OOF), nguong nhi phan FPR<=muc tieu (+ max-F1 tham chieu), nguong TTP max-F1."""
    y = np.array([w.y_bin for w in train_ws], bool)
    cand = {"p_bin": P_bin, "p_bin_max": np.maximum(P_bin, P_ttp.max(1))}
    ap = {k: average_precision(y, v) for k, v in cand.items()}
    use = max(ap, key=lambda k: (ap[k], k == "p_bin"))
    s = cand[use]
    thr_fpr = threshold_at_fpr(y, s, cfg.fpr_target); thr_f1, f1 = best_f1_threshold(y, s)
    out = {"binary_score": use, "oof_pr_auc": {k: round(float(v), 4) for k, v in ap.items()},
           "binary": thr_fpr, "binary_rule": f"FPR<={cfg.fpr_target} tren cua so am OOF",
           "binary_max_f1": thr_f1, "binary_train_oof_f1_at_maxf1": f1, "ttp": {}, "ttp_train_oof_f1": {}}
    for j, t in enumerate(TTPS):
        yt = np.array([w.y_ttp[j] > 0 for w in train_ws]); out["ttp"][t], out["ttp_train_oof_f1"][t] = best_f1_threshold(yt, P_ttp[:, j])
    return out

def oof_summary(train_ws, P_bin, P_ttp, sel, hn_mask=None):
    """Tieu chi 4.3: macro-F1 TTP OOF, PR-AUC nhi phan OOF, FPR OOF tren cua so hard_negative."""
    y = np.array([w.y_bin for w in train_ws], bool)
    s = P_bin if sel["binary_score"] == "p_bin" else np.maximum(P_bin, P_ttp.max(1))
    f1s = []
    for j, t in enumerate(TTPS):
        yt = np.array([w.y_ttp[j] > 0 for w in train_ws]); pr = P_ttp[:, j] >= sel["ttp"][t]
        tp = int((pr & yt).sum()); fp = int((pr & ~yt).sum()); fn = int((~pr & yt).sum())
        f1s.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    pred = s >= sel["binary"]
    res = {"macro_f1_ttp": round(float(np.mean(f1s)), 4), "f1_ttp": dict(zip(TTPS, [round(x, 4) for x in f1s])),
           "pr_auc_bin": round(float(average_precision(y, s)), 4), "roc_auc_bin": round(float(roc_auc(y, s)), 4),
           "fpr_neg": round(float(pred[~y].mean()), 4), "recall": round(float(pred[y].mean()), 4)}
    if hn_mask is not None and hn_mask.any(): res["fpr_hard_negative"] = round(float(pred[hn_mask].mean()), 4)
    return res

# ---------------- dau ra (cung dinh dang Buoc 5) ----------------
def preds_records(ws, split, p_bin, p_ttp, run_of=None):
    return [{"window_id": w.wid, "split": split, "p_malicious": round(float(p_bin[i]), 6),
             "p_ttp": {t: round(float(p_ttp[i, j]), 6) for j, t in enumerate(TTPS)}} for i, w in enumerate(ws)]

def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows: f.write(json.dumps(r) + "\n")

def save_nets(path, nets, cfg, vsizes, meta=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save({"cfg": asdict(cfg), "vsizes": vsizes, "state": {k: n.state_dict() for k, n in nets.items()},
                "heads": {k: n.heads for k, n in nets.items()}, "meta": meta or {}}, path)

def load_nets(path, device="cpu"):
    ck = torch.load(path, map_location=device, weights_only=False)
    cfg = Config(**ck["cfg"]); nets = {}
    for k, st in ck["state"].items():
        n = VTSeq(ck["vsizes"], cfg, ck["heads"][k]).to(device); n.load_state_dict(st); n.eval(); nets[k] = n
    return nets, cfg, ck

def run_oof_experiment(cfg, data, vocab, seed, outdir, root=".", device="cpu", max_batches=None):
    """Moc 2: OOF cho mot cau hinh x seed -> outdir/oof/<cfg>_s<seed>.jsonl + tom tat OOF + log fold. Khong cham test."""
    from evaluate import load_meta
    vs = vocab_sizes(vocab); tr = data["train"]
    meta_tr = load_meta(root, "train"); assert [m["window_id"] for m in meta_tr] == [w.wid for w in tr]
    folds = cv_folds(meta_tr, root=root)
    t0 = time.time()
    P_bin, P_ttp, finfo = run_cv(cfg, vs, tr, folds, seed, device, max_batches)
    sel = choose_on_oof(tr, P_bin, P_ttp, cfg)
    hn = np.array([m["window_class"] == "hard_negative" for m in meta_tr])
    summ = oof_summary(tr, P_bin, P_ttp, sel, hn)
    write_jsonl(os.path.join(outdir, "oof", f"{cfg.name}_s{seed}.jsonl"), preds_records(tr, "train", P_bin, P_ttp))
    rec = {"config": asdict(cfg), "seed": seed, "folds": finfo, "final_epochs": final_epochs(finfo),
           "n_hit_ceiling": sum(v["hit_ceiling"] for f in finfo for v in f.values()), "selection": sel, "oof": summ,
           "minutes": round((time.time() - t0) / 60, 2), "device": device, "torch": torch.__version__}
    os.makedirs(os.path.join(outdir, "logs"), exist_ok=True)
    with open(os.path.join(outdir, "logs", f"{cfg.name}_s{seed}.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, indent=1)
    return rec

# ---------------- moc 3: fit cuoi, du doan test MOT lan, phat hien som, ensemble ----------------
TEST_SPLITS = ("t_clean", "t_hard", "t_novel")
EARLY_KS = (4, 8, 16, 32)
# Ablation dac trung cho VT-Seq cuoi (M3): mat na ap CA khi train va khi test (nhu Buoc 5); (b) = M4b
PRESETS["M3c"] = replace(PRESETS["M3"], name="M3c", mask="c")
PRESETS["M3cp"] = replace(PRESETS["M3"], name="M3cp", mask="cp")

def chosen_score(P_bin, P_ttp, which):
    return P_bin if which == "p_bin" else np.maximum(P_bin, P_ttp.max(1))

def read_jsonl(path): return [json.loads(l) for l in open(path, encoding="utf-8")]

def early_inputs(w, cfg, k):
    """Cua so duong cat con k event tu event malicious dau tien (origin aux, nhu evaluate.early_starts), roi ap mat na
    ablation tren doan da cat (nhu B1/B3)."""
    i0 = w.first_own(); keep = set(w.base_idx(cfg.mask).tolist())
    return [i for i in range(i0, min(i0 + k, len(w))) if i in keep]

def early_raw(nets, data, cfg, device="cpu"):
    rows = []
    for s in ("t_clean", "t_novel"):
        pos = [w for w in data[s] if w.y_bin]
        for k in EARLY_KS:
            m = {w.wid: early_inputs(w, cfg, k) for w in pos}
            pb, pt, _ = predict(nets, pos, cfg, device, idx_fn=lambda w: m[w.wid])
            rows += [{"split": s, "k": k, "window_id": w.wid, "p_bin": float(pb[i]), "p_ttp": [float(x) for x in pt[i]]}
                     for i, w in enumerate(pos)]
    return rows

def raw_rows(ws, split, pb, pt):
    return [{"window_id": w.wid, "split": split, "p_bin": round(float(pb[i]), 7), "p_ttp": [round(float(x), 7) for x in pt[i]]}
            for i, w in enumerate(ws)]

def write_model_outputs(outdir, model, data, raw, early, sel, root="."):
    """raw: {split: (P_bin, P_ttp)} (train = OOF); early: list hang early_raw. Ghi preds dinh dang Buoc 5
    (<outdir>/reports/preds/<model>_<split>.jsonl, p_malicious = diem nhi phan da chon tren OOF), early da chon
    (<outdir>/early/<model>.json) va nguong (<outdir>/sel/<model>.json)."""
    from evaluate import load_meta, write_preds
    for s, (pb, pt) in raw.items():
        meta = load_meta(root, s); assert [m["window_id"] for m in meta] == [w.wid for w in data[s]]
        sc = chosen_score(pb, pt, sel["binary_score"])
        write_preds(outdir, model, s, meta, {w.wid: {"p": float(sc[i]), "p_ttp": {t: float(pt[i, j]) for j, t in enumerate(TTPS)}}
                                            for i, w in enumerate(data[s])})
    ech = {}
    for r in early:
        v = r["p_bin"] if sel["binary_score"] == "p_bin" else max(r["p_bin"], max(r["p_ttp"]))
        ech.setdefault(r["split"], {}).setdefault(str(r["k"]), {})[r["window_id"]] = v
    for d, obj in (("early", ech), ("sel", sel)):
        os.makedirs(os.path.join(outdir, d), exist_ok=True)
        with open(os.path.join(outdir, d, f"{model}.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(obj, f, indent=1)

def run_final(cfg, data, vocab, seed, outdir, root=".", device="cpu", oof_dir=None, max_batches=None):
    """OOF (lay tu oof_dir/moc 2 neu co, neu khong chay CV) -> nguong tu OOF -> fit toan Train (so epoch = trung vi fold)
    -> du doan t_clean/t_hard/t_novel MOT lan + phat hien som. Ghi raw/, reports/preds/, early/, sel/, ckpt/."""
    model = f"vtseq_{cfg.name}_s{seed}"; t0 = time.time(); tr = data["train"]
    lp = None if oof_dir is None else os.path.join(oof_dir, "logs", f"{cfg.name}_s{seed}.json")
    if lp is not None and os.path.exists(lp):
        log = json.load(open(lp, encoding="utf-8")); oof_path = os.path.join(oof_dir, "oof", f"{cfg.name}_s{seed}.jsonl"); src = oof_dir
    else:
        log = run_oof_experiment(cfg, data, vocab, seed, outdir, root, device, max_batches)
        oof_path = os.path.join(outdir, "oof", f"{cfg.name}_s{seed}.jsonl"); src = "chay CV tai moc 3"
    assert log["config"] == asdict(cfg), f"{model}: cau hinh khac log OOF"
    oof = {r["window_id"]: r for r in read_jsonl(oof_path)}
    P_bin = np.array([oof[w.wid]["p_malicious"] for w in tr]); P_ttp = np.array([[oof[w.wid]["p_ttp"][t] for t in TTPS] for w in tr])
    sel = log["selection"]                                          # nguong khoa tu OOF (xac suat day du)
    chk = choose_on_oof(tr, P_bin, P_ttp, cfg)                      # tinh lai tu file OOF (lam tron 6 so) phai khop
    assert chk["binary_score"] == sel["binary_score"] and abs(chk["binary"] - sel["binary"]) < 1e-5, (model, chk["binary"], sel["binary"])
    nets, info = fit_nets(cfg, vocab_sizes(vocab), tr, None, log["final_epochs"], seed, 0, device, max_batches)
    raw = {"train": (P_bin, P_ttp)}
    for s in TEST_SPLITS:
        pb, pt, _ = predict(nets, data[s], cfg, device); raw[s] = (pb, pt)
    er = early_raw(nets, data, cfg, device)
    for s, (pb, pt) in raw.items(): write_jsonl(os.path.join(outdir, "raw", f"{model}_{s}.jsonl"), raw_rows(data[s], s, pb, pt))
    write_jsonl(os.path.join(outdir, "raw", f"{model}_early.jsonl"), er)
    write_model_outputs(outdir, model, data, raw, er, {**sel, "oof_source": src, "final_epochs": log["final_epochs"]}, root)
    save_nets(os.path.join(outdir, "ckpt", f"{model}.pt"), nets, cfg, vocab_sizes(vocab), {"seed": seed, "final_epochs": log["final_epochs"]})
    return {"model": model, "final_epochs": log["final_epochs"], "binary_score": sel["binary_score"], "thr": sel["binary"],
            "oof_source": src, "minutes": round((time.time() - t0) / 60, 2)}

def build_ensemble(cfg_name, seeds, outdir, data, root="."):
    """VT-Seq-ens: trung binh xac suat (p_bin, p_ttp) cac seed - ca OOF (train), test va early; nguong + p_bin/p_bin'
    chon lai tren OOF trung binh (cung quy tac 4.3)."""
    model = f"vtseq_{cfg_name}_ens"; raw = {}
    for s in ("train",) + TEST_SPLITS:
        R = [read_jsonl(os.path.join(outdir, "raw", f"vtseq_{cfg_name}_s{sd}_{s}.jsonl")) for sd in seeds]
        assert all([r["window_id"] for r in x] == [w.wid for w in data[s]] for x in R)
        raw[s] = (np.mean([[r["p_bin"] for r in x] for x in R], 0), np.mean([[r["p_ttp"] for r in x] for x in R], 0))
    E = [read_jsonl(os.path.join(outdir, "raw", f"vtseq_{cfg_name}_s{sd}_early.jsonl")) for sd in seeds]
    early = [{**E[0][i], "p_bin": float(np.mean([e[i]["p_bin"] for e in E])), "p_ttp": list(np.mean([e[i]["p_ttp"] for e in E], 0))}
             for i in range(len(E[0]))]
    assert all((e[i]["window_id"], e[i]["k"]) == (early[i]["window_id"], early[i]["k"]) for e in E for i in range(len(early)))
    sel = choose_on_oof(data["train"], raw["train"][0], raw["train"][1], PRESETS[cfg_name])
    for s, (pb, pt) in raw.items(): write_jsonl(os.path.join(outdir, "raw", f"{model}_{s}.jsonl"), raw_rows(data[s], s, pb, pt))
    write_model_outputs(outdir, model, data, raw, early, {**sel, "members": [f"vtseq_{cfg_name}_s{sd}" for sd in seeds]}, root)
    return {"model": model, "binary_score": sel["binary_score"], "thr": sel["binary"], "oof_pr_auc": sel["oof_pr_auc"]}
