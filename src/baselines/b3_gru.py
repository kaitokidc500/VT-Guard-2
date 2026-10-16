#!/usr/bin/env python3
"""VT-Guard Buoc 5 - B3: GRU thuan (docs/STEP5-BRIEF.md muc 4.4). PyTorch CPU.

- Chuoi event cua cua so (toi da 64, windows.jsonl dataset dong bang) -> moi event: embedding 7 truong categorical
  (vocab.json, fit tren Train) + nhanh command_line 256 chieu (featurize.hash_cmd, giong het featurize) qua
  Linear(256->32)+ReLU + 5 so (dt_log, has_network, has_dns, is_powershell_channel, is_security_channel, nhu featurize)
  -> Dropout -> GRU 1 lop (hidden 96) -> trang thai cuoi -> Dropout -> Linear. KHONG attention.
  Ma hoa duoc doi chieu voi cat/cmd/num cua file split (assert) -> dung dung featurizer dong bang.
- Hai bien the DON NHIEM, huan luyen RIENG (khong chung than, khong chung dau ra):
  B3-bin: 1 dau sigmoid (window_malicious); B3-ttp: 5 dau sigmoid da nhan (window_ttps).
  File ket qua b3_gru_<ab>_s<seed>: chi so nhi phan + phat hien som tu B3-bin, chi so TTP tu B3-ttp.
- Padding mask: pack_padded_sequence (GRU khong thay buoc pad). Random length crop khi train: moi epoch, moi cua so
  Train voi xac suat CROP_P bi cat mot doan LIEN TIEP do dai ~ U[4, n]; nhan cua doan = nhan cac event TRONG doan
  (label_malicious / label_ttps cua event, CHI tren Train - nhan huan luyen, khong phai feature). dt cua event dau = 0.
- Early stopping theo CV nhom (evaluate.cv_folds): moi fold dung tai epoch co val loss nho nhat (patience 6) -> OOF;
  mo hinh cuoi fit toan Train so epoch = trung vi epoch tot nhat cua 5 fold. Nguong khoa tren Train OOF moi seed.
- Ablation: (a) du; (b) bo embedding image_name + parent_image_name (giu dong lenh, nhu B1 (b));
  (c) chi event cay tien trinh (ro nhan theo cau truc - chi bao T-hard); (cp) che event nen mot-phia da biet.
- Du lieu nho (~484 cua so Train): chay SEEDS = 1337, 7, 42; summary.py gom trung binh +- do lech chuan.
- Khong dung n_events, tempo, variant, user_role, run_id, label_* (lam feature), wazuh_rule_*, text tho.
Chay: python src/baselines/b3_gru.py [--ablations a,b,c,cp] [--seeds 1337,7,42] [--threads 1]
"""
import argparse, json, math, os, sys, time

import numpy as np
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "eval")); sys.path.insert(0, os.path.join(HERE, "..", "dataset"))
from common import window_events, full_window_events, is_known_one_sided_bg
from evaluate import (check_dataset, load_all_meta, evaluate, render_markdown, write_preds, check_predictions,
                      cv_folds, choose_thresholds, early_starts, TTPS, SPLITS, TEST_SPLITS, EARLY_KS)
from featurize import token, hash_cmd, ts, CAT_FIELDS, CMD_DIM

SEEDS = (1337, 7, 42)
HP = {"hidden": 96, "emb_big": 16, "emb_small": 4, "cmd_dim": 32, "dropout": 0.3, "lr": 1e-3, "weight_decay": 1e-4,
      "batch": 32, "max_epochs": 60, "patience": 6, "crop_p": 0.5, "crop_min": 4}
BIG = {"event_id", "image_name", "parent_image_name"}
ABLATIONS = {"a": "du", "b": "bo image_name + parent_image_name", "c": "chi event cay tien trinh (ro nhan theo cau truc - chi bao T-hard)",
             "cp": "che event nen mot-phia da biet (ESENT/Directory Service, svchost->rundll32 COM)"}
NUM_DIM = 5

# ---------------- ma hoa event (giong featurize.py) ----------------
class Encoded:
    """Ma hoa san moi event cua mot cua so; seq(idx) dung chuoi con (dt tinh lai tren chuoi con)."""
    def __init__(self, ev, vocab):
        n = len(ev)
        self.cat = np.array([[vocab[f].get(token(f, e[f]), 1) for f in CAT_FIELDS] for e in ev], np.int64).reshape(n, len(CAT_FIELDS))
        self.cmd = np.zeros((n, CMD_DIM), np.float32)
        for i, e in enumerate(ev):
            for j, x in hash_cmd(e.get("command_line")): self.cmd[i, j] = x
        self.flag = np.array([[int(e["event_id"] == 3 or e.get("dst_port") is not None), int(e["event_id"] == 22 or bool(e.get("has_dns_query"))),
                               int("PowerShell" in (e.get("channel") or "")), int((e.get("channel") or "") == "Security")] for e in ev],
                             np.float32).reshape(n, 4)
        self.t = np.array([ts(e["ts"]).timestamp() for e in ev], np.float64)

    def seq(self, idx):
        idx = np.asarray(idx, np.int64)
        if len(idx) == 0:                     # chuoi rong (ablation c/cp): 1 buoc pad
            return np.zeros((1, len(CAT_FIELDS)), np.int64), np.zeros((1, CMD_DIM), np.float32), np.zeros((1, NUM_DIM), np.float32)
        t = self.t[idx]; dt = np.zeros(len(idx), np.float32)
        dt[1:] = np.log1p(np.maximum(0.0, np.diff(t)))
        return self.cat[idx], self.cmd[idx], np.concatenate([dt[:, None], self.flag[idx]], 1)

def keep_idx(ev, origin, ablation):
    return [i for i, (e, o) in enumerate(zip(ev, origin))
            if (ablation != "c" or o == "own") and not (ablation == "cp" and is_known_one_sided_bg(e, o))]

def verify_encoding(root, wev, encs):
    """Ma hoa cua so day du phai trung cat/cmd/num cua file split (dataset dong bang)."""
    bad = 0
    for s in SPLITS:
        with open(os.path.join(root, "data", "processed", "splits", f"{s}.jsonl"), encoding="utf-8") as fh:
            for l in fh:
                w = json.loads(l); en = encs[w["window_id"]]
                cat, cmd, num = en.seq(range(len(en.t)))
                ref_cmd = np.zeros_like(cmd)
                for i, c in enumerate(w["cmd"]):
                    for j, x in c: ref_cmd[i, j] = x
                ok = (np.array_equal(cat, np.array(w["cat"], np.int64)) and np.allclose(cmd, ref_cmd, atol=1e-5)
                      and np.allclose(num, np.array(w["num"], np.float32), atol=1e-4))
                bad += not ok
    if bad: sys.exit(f"LOI: ma hoa B3 lech file split o {bad} cua so. DUNG.")
    return True

# ---------------- mo hinh ----------------
class GRUNet(nn.Module):
    def __init__(self, vsizes, cols, n_out, hp):
        super().__init__()
        self.cols = cols
        dims = [hp["emb_big"] if CAT_FIELDS[c] in BIG else hp["emb_small"] for c in cols]
        self.embs = nn.ModuleList([nn.Embedding(vsizes[c], d, padding_idx=0) for c, d in zip(cols, dims)])
        self.cmd = nn.Sequential(nn.Linear(CMD_DIM, hp["cmd_dim"]), nn.ReLU())
        self.drop = nn.Dropout(hp["dropout"])
        self.gru = nn.GRU(sum(dims) + hp["cmd_dim"] + NUM_DIM, hp["hidden"], num_layers=1, batch_first=True)
        self.out = nn.Linear(hp["hidden"], n_out)

    def forward(self, cat, cmd, num, lens):
        x = torch.cat([emb(cat[:, :, c]) for emb, c in zip(self.embs, self.cols)] + [self.cmd(cmd), num], -1)
        packed = pack_padded_sequence(self.drop(x), lens, batch_first=True, enforce_sorted=False)   # padding mask
        _, h = self.gru(packed)
        return self.out(self.drop(h[-1]))

def collate(items):
    L = max(len(c) for c, _, _ in items); B = len(items)
    cat = np.zeros((B, L, len(CAT_FIELDS)), np.int64); cmd = np.zeros((B, L, CMD_DIM), np.float32); num = np.zeros((B, L, NUM_DIM), np.float32)
    lens = np.zeros(B, np.int64)
    for i, (c, m, n) in enumerate(items):
        k = len(c); cat[i, :k] = c; cmd[i, :k] = m; num[i, :k] = n; lens[i] = k
    return torch.from_numpy(cat), torch.from_numpy(cmd), torch.from_numpy(num), torch.from_numpy(lens)

def predict(net, seqs, bs=128):
    net.eval(); out = []
    with torch.no_grad():
        for i in range(0, len(seqs), bs):
            out.append(torch.sigmoid(net(*collate(seqs[i:i + bs]))).numpy())
    return np.concatenate(out, 0) if out else np.zeros((0, net.out.out_features))

class Trainer:
    """Mot bien the (bin | ttp) cho mot ablation + seed."""
    def __init__(self, kind, ablation, seed, vsizes, hp=HP):
        self.kind, self.ab, self.seed, self.hp, self.vsizes = kind, ablation, seed, hp, vsizes
        self.cols = [c for c, f in enumerate(CAT_FIELDS) if not (ablation == "b" and f in ("image_name", "parent_image_name"))]
        self.n_out = 1 if kind == "bin" else len(TTPS)

    def targets(self, ev_lab, idx):
        mal = [ev_lab[i] for i in idx]
        if self.kind == "bin": return np.array([float(any(m for m, _ in mal))], np.float32)
        tt = set(t for m, ts_ in mal if m for t in ts_)
        return np.array([float(t in tt) for t in TTPS], np.float32)

    def sample(self, rng, en, base, ev_lab):
        """Random length crop (lien tiep tren chuoi da ap ablation) + nhan cua doan."""
        idx = base
        if len(base) > self.hp["crop_min"] and rng.random() < self.hp["crop_p"]:
            L = int(rng.integers(self.hp["crop_min"], len(base) + 1)); s = int(rng.integers(0, len(base) - L + 1))
            idx = base[s:s + L]
        return en.seq(idx), self.targets(ev_lab, idx)

    def fit(self, tr_items, va_items=None, epochs=None, tag=0):
        """tr_items: [(Encoded, base_idx, ev_lab)]; va_items: [(seq, y)] -> early stopping theo val loss."""
        torch.manual_seed(self.seed * 1000 + tag)
        rng = np.random.default_rng([self.seed, tag, 0 if self.kind == "bin" else 1])
        net = GRUNet(self.vsizes, self.cols, self.n_out, self.hp)
        opt = torch.optim.Adam(net.parameters(), lr=self.hp["lr"], weight_decay=self.hp["weight_decay"])
        Yfull = np.stack([self.targets(lab, b) for _, b, lab in tr_items])
        pos = Yfull.sum(0); neg = len(Yfull) - pos
        pw = torch.tensor(np.where(pos > 0, neg / np.maximum(pos, 1), 1.0), dtype=torch.float32)
        lossf = nn.BCEWithLogitsLoss(pos_weight=pw); vlossf = nn.BCEWithLogitsLoss(pos_weight=pw)
        best, best_ep, best_state, wait = math.inf, 0, None, 0
        n_ep = epochs if epochs is not None else self.hp["max_epochs"]
        for ep in range(1, n_ep + 1):
            net.train()
            order = rng.permutation(len(tr_items))
            for i in range(0, len(order), self.hp["batch"]):
                b = [self.sample(rng, *tr_items[j]) for j in order[i:i + self.hp["batch"]]]
                cat, cmd, num, lens = collate([s for s, _ in b]); y = torch.from_numpy(np.stack([t for _, t in b]))
                opt.zero_grad(); loss = lossf(net(cat, cmd, num, lens), y); loss.backward()
                nn.utils.clip_grad_norm_(net.parameters(), 5.0); opt.step()
            if va_items is None: continue
            net.eval()
            with torch.no_grad():
                cat, cmd, num, lens = collate([s for s, _ in va_items])
                vl = float(vlossf(net(cat, cmd, num, lens), torch.from_numpy(np.stack([y for _, y in va_items]))))
            if vl < best - 1e-4:
                best, best_ep, wait = vl, ep, 0
                best_state = {k: v.clone() for k, v in net.state_dict().items()}
            else:
                wait += 1
                if wait >= self.hp["patience"]: break
        if va_items is not None and best_state is not None: net.load_state_dict(best_state)
        return net, best_ep, best

# ---------------- chay mot ablation x seed ----------------
def run(ablation, seed, root, meta, wev, encs, labs, folds, starts, vsizes):
    model = f"b3_gru_{ablation}_s{seed}"
    t0 = time.time()
    base = {wid: keep_idx(ev, origin, ablation) for wid, (ev, origin) in wev.items()}
    tr = meta["train"]
    tr_items = [(encs[w["window_id"]], base[w["window_id"]], labs[w["window_id"]]) for w in tr]
    full_seq = {wid: encs[wid].seq(b) for wid, b in base.items()}
    nets, log = {}, {}
    P = {k: np.zeros((len(tr), 1 if k == "bin" else len(TTPS))) for k in ("bin", "ttp")}
    for kind in ("bin", "ttp"):
        T = Trainer(kind, ablation, seed, vsizes)
        eps, vls = [], []
        for fi, (a_, va) in enumerate(folds):
            va_items = [(full_seq[tr[i]["window_id"]], T.targets(labs[tr[i]["window_id"]], base[tr[i]["window_id"]])) for i in va]
            net, ep, vl = T.fit([tr_items[i] for i in a_], va_items, tag=fi + 1)
            P[kind][va] = predict(net, [full_seq[tr[i]["window_id"]] for i in va])
            eps.append(ep); vls.append(round(vl, 4))
        n_final = max(1, int(np.median(eps)))
        nets[kind], _, _ = T.fit(tr_items, None, epochs=n_final, tag=0)
        log[kind] = {"best_epoch_per_fold": eps, "val_loss_per_fold": vls, "final_epochs": n_final,
                     "n_params": int(sum(p.numel() for p in nets[kind].parameters()))}
    pack = lambda pb, pt: {"p": float(pb[0]), "p_ttp": {t: float(pt[j]) for j, t in enumerate(TTPS)}}
    oof_pred = {w["window_id"]: pack(P["bin"][i], P["ttp"][i]) for i, w in enumerate(tr)}
    thr = choose_thresholds(tr, oof_pred)
    preds = {"train": oof_pred}
    for s in TEST_SPLITS:
        sq = [full_seq[w["window_id"]] for w in meta[s]]
        pb, pt = predict(nets["bin"], sq), predict(nets["ttp"], sq)
        preds[s] = {w["window_id"]: pack(pb[i], pt[i]) for i, w in enumerate(meta[s])}
    early = {}
    for s, st in starts.items():
        early[s] = {}
        for k in EARLY_KS:
            ids = list(st)
            sq = []
            for wid in ids:
                i0, _ = st[wid]; ev, origin = wev[wid]
                sl = list(range(i0, min(i0 + k, len(ev))))
                keep = [i for i in sl if (ablation != "c" or origin[i] == "own") and not (ablation == "cp" and is_known_one_sided_bg(ev[i], origin[i]))]
                sq.append(encs[wid].seq(keep))
            early[s][k] = dict(zip(ids, predict(nets["bin"], sq)[:, 0].astype(float)))
    res = evaluate(model, meta, {s: preds[s] for s in TEST_SPLITS}, thr, root=root, early=early)
    res.update(engine=f"torch {torch.__version__} (CPU, {torch.get_num_threads()} thread)", ablation=ablation,
               ablation_desc=ABLATIONS[ablation], seed=seed, hp=HP, train_log=log, minutes=round((time.time() - t0) / 60, 2),
               variants="p (nhi phan, phat hien som) tu B3-bin; p_ttp tu B3-ttp - hai mang huan luyen rieng",
               features_used=[CAT_FIELDS[c] for c in Trainer("bin", ablation, seed, vsizes).cols] + ["command_line (hash_cmd 256)", "dt_log + 4 co"],
               acceptance={"one_pred_per_window_no_leak": check_predictions(meta, {s: preds[s] for s in TEST_SPLITS})["ok"],
                           "vocab_from": "data/processed/vocab.json (fit Train, dataset dong bang)",
                           "encoding_matches_split_files": True})
    for s in SPLITS: write_preds(root, model, s, meta[s], preds[s])
    with open(os.path.join(root, "reports", "step5", f"{model}.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(root, "reports", "step5", f"{model}.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_markdown(res))
    return model, res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--ablations", default="a,b,c,cp")
    ap.add_argument("--seeds", default=",".join(map(str, SEEDS)))
    ap.add_argument("--threads", type=int, default=1)
    a = ap.parse_args()
    torch.set_num_threads(a.threads); torch.use_deterministic_algorithms(True)
    print("checksum dataset (so voi reports/dataset_stats.json):", check_dataset(a.root), "| torch", torch.__version__)
    meta = load_all_meta(a.root)
    vocab = json.load(open(os.path.join(a.root, "data", "processed", "vocab.json"), encoding="utf-8"))
    vsizes = [max(vocab[f].values()) + 1 for f in CAT_FIELDS]
    wev = window_events(a.root, [w["window_id"] for s in SPLITS for w in meta[s]])
    encs = {wid: Encoded(ev, vocab) for wid, (ev, _) in wev.items()}
    print("doi chieu ma hoa voi file split:", verify_encoding(a.root, wev, encs))
    # nhan tung event CHI cho Train (dung lam nhan cua doan cat ngau nhien) + doi chieu voi nhan cua so
    fe = full_window_events(a.root, [w["window_id"] for w in meta["train"]])
    labs = {wid: [(bool(e["label_malicious"]), tuple(e.get("label_ttps") or ())) for e in ev] for wid, ev in fe.items()}
    for w in meta["train"]:
        lb = labs[w["window_id"]]
        assert any(m for m, _ in lb) == bool(w["window_malicious"]), w["window_id"]
        assert set(t for m, tt in lb if m for t in tt) == set(w["window_ttps"]), w["window_id"]
    folds = cv_folds(meta["train"], root=a.root); starts = early_starts(a.root, meta)
    for ab in a.ablations.split(","):
        for sd in map(int, a.seeds.split(",")):
            model, res = run(ab, sd, a.root, meta, wev, encs, labs, folds, starts, vsizes)
            S = res["splits"]
            print(f"[{model}] {res['minutes']} ph | epoch bin {res['train_log']['bin']['best_epoch_per_fold']} -> {res['train_log']['bin']['final_epochs']}"
                  f" | ttp {res['train_log']['ttp']['best_epoch_per_fold']} -> {res['train_log']['ttp']['final_epochs']}"
                  f" | T-clean F1 {S['t_clean']['tuned']['f1']['point']:.3f} | T-hard FP {S['t_hard']['tuned']['fp']}"
                  f" | T-novel F1 {S['t_novel']['tuned']['f1']['point']:.3f} | kiem tra {res['acceptance']['one_pred_per_window_no_leak']}", flush=True)

if __name__ == "__main__":
    main()
