#!/usr/bin/env python3
"""VT-Guard Buoc 6 moc 1 - unit test nhanh cho src/models/vtseq.py (host, CPU, vai batch, 2 epoch).
Kiem: (1) du lieu & ma hoa khop file split, (2) khong doc truong cam, (3) shape, (4) mask + attention tong = 1 + bat bien
padding, (5) nhan crop tinh lai dung, (6) name dropout, (7) huan luyen 2 epoch + CV/OOF, (8) nguong FPR,
(9) checkpoint, (10) tat dinh. Chay: python src/models/test_vtseq.py
"""
import json, os, re, sys, tempfile, time
from dataclasses import replace

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "eval"))
import vtseq as V                                      # noqa: E402
from evaluate import check_model_sources, load_meta, cv_folds, TTPS   # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FORBIDDEN = ["wazuh_rule_id", "wazuh_rule_level", "wazuh_rule_mitre", "label_malicious", "label_ttps", "run_id", "event_uid",
             "process_guid", "parent_process_guid", "script_block_text", "ps_payload", "image", "parent_image", "n_events",
             "tempo", "variant", "user_role", "batch", "revert_control", "window_class", "session_windows_total", "host", "t0", "t1"]
RESULTS = []

def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond))); print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""), flush=True)
    return cond

class TrackDict(dict):
    seen = set()
    def __getitem__(self, k): TrackDict.seen.add(k); return dict.__getitem__(self, k)
    def get(self, k, d=None): TrackDict.seen.add(k); return dict.get(self, k, d)

def main():
    t0 = time.time(); torch.set_num_threads(2)
    # ---- 1. du lieu ----
    data, vocab = V.load_data(ROOT); vs = V.vocab_sizes(vocab)
    check("1a checksum dataset-v1.2 + aux sha256", True, f"{ {s: len(v) for s, v in data.items()} }")
    raw = {}
    for s in V.SPLITS:
        for l in open(os.path.join(ROOT, "data", "processed", "splits", f"{s}.jsonl"), encoding="utf-8"):
            r = json.loads(l); raw[r["window_id"]] = r
    bad = 0; maxdt = 0.0
    for s in V.SPLITS:
        for w in data[s]:
            r = raw[w.wid]; cat, cmd, num = w.seq(np.arange(len(w)))
            ref = np.zeros_like(cmd)
            for i, c in enumerate(r["cmd"]):
                for j, x in c: ref[i, j] = x
            d = float(np.abs(num - np.array(r["num"], np.float32)).max())
            maxdt = max(maxdt, d)
            bad += not (np.array_equal(cat, np.array(r["cat"])) and np.array_equal(cmd, ref) and d < 1e-4)
    check("1b seq(toan cua so) tai tao dung cat/cmd/num cua split (809 cua so)", bad == 0, f"lech {bad}, max |num| sai {maxdt:.2e}")
    w = max(data["train"], key=len); s0, L = 7, 20; idx = np.arange(s0, s0 + L)
    _, _, num = w.seq(idx)
    check("1c crop lien tiep: dt event dau = 0, cac event sau giu nguyen dt goc",
          num[0, 0] == 0 and np.allclose(num[1:, 0], w.num[idx[1:], 0], atol=1e-4))
    # ---- 2. truong cam ----
    TrackDict.seen = set(); orig = V.json.loads
    V.json.loads = lambda s, *a, **k: TrackDict(orig(s, *a, **k))
    try: V.load_split(ROOT, "t_hard")
    finally: V.json.loads = orig
    check("2a load_split chi doc ALLOWED_KEYS", TrackDict.seen <= set(V.ALLOWED_KEYS), f"doc: {sorted(TrackDict.seen)}")
    check("2b khong doc truong cam nao", not (TrackDict.seen & set(FORBIDDEN)))
    src = open(os.path.join(HERE, "vtseq.py"), encoding="utf-8").read()
    lit = [f for f in FORBIDDEN if f != "window_class" and re.search(r"""["']%s["']""" % re.escape(f), src)]   # window_class: chi chon tren OOF (FPR HN)
    check("2c vtseq.py khong co chuoi ten truong cam", not lit, f"{lit}")
    check("2d evaluate.check_model_sources (src/baselines + src/models) sach", not check_model_sources(ROOT))
    check("2e nhan event (ev_mal) chi co o Train", all(w.ev_mal is not None for w in data["train"])
          and all(w.ev_mal is None for s in ("t_clean", "t_hard", "t_novel") for w in data[s]))
    # ---- 3. shape ----
    cfg = V.PRESETS["M3"]; torch.manual_seed(0)
    net = V.VTSeq(vs, cfg).eval()
    ws = sorted(data["t_clean"], key=len)[:3] + sorted(data["t_clean"], key=len)[-2:]
    cat, cmd, num, lens = V.collate([V.eval_seq(w, cfg) for w in ws])
    with torch.no_grad(): o = net(cat, cmd, num, lens)
    B, T = cat.shape[:2]
    check("3a shape logit_bin (B,), logit_ttp (B,5), alpha (B,T)",
          o["logit_bin"].shape == (B,) and o["logit_ttp"].shape == (B, 5) and o["alpha"].shape == (B, T),
          f"B={B} T={T} lens={lens.tolist()}")
    nl = V.VTSeq(vs, replace(cfg, pooling="last"), ("bin",)).eval()
    with torch.no_grad(): ol = nl(cat, cmd, num, lens)
    check("3b pooling last / mot dau: chi logit_bin, alpha None", "logit_ttp" not in ol and ol["alpha"] is None)
    # ---- 4. mask + attention ----
    a = o["alpha"]; m = o["mask"]
    check("4a alpha = 0 tren buoc pad", float(a[~m].abs().max()) == 0.0 if (~m).any() else True)
    check("4b tong alpha tren event that = 1", torch.allclose(a.sum(1), torch.ones(B), atol=1e-6), f"{a.sum(1).tolist()}")
    single = []
    with torch.no_grad():
        for w_ in ws:
            c1, m1, n1, l1 = V.collate([V.eval_seq(w_, cfg)]); single.append(net(c1, m1, n1, l1)["logit_bin"][0])
    check("4c bat bien padding: cua so mot minh == trong batch co pad", torch.allclose(torch.stack(single), o["logit_bin"], atol=1e-5))
    g = torch.Generator().manual_seed(1)
    cat2, cmd2, num2 = cat.clone(), cmd.clone(), num.clone()
    padm = ~m
    cat2[padm] = torch.randint(1, 5, (int(padm.sum()), cat.shape[2]), generator=g)
    cmd2[padm] = torch.randn(int(padm.sum()), cmd.shape[2], generator=g); num2[padm] = torch.randn(int(padm.sum()), num.shape[2], generator=g)
    with torch.no_grad(): o2 = net(cat2, cmd2, num2, lens)
    check("4d gia tri rac o vung pad khong doi dau ra", torch.allclose(o2["logit_bin"], o["logit_bin"], atol=1e-6)
          and torch.allclose(o2["logit_ttp"], o["logit_ttp"], atol=1e-6))
    # ---- 5. nhan crop ----
    aux = V.load_aux(ROOT)
    rng = np.random.default_rng(1337); n_chk = n_neg_from_pos = 0; ok = True; lens_cls = {0: [], 1: []}
    for cfg_c in (V.PRESETS["M2"], V.PRESETS["M3"]):
        for _ in range(3000):
            w_ = data["train"][int(rng.integers(len(data["train"])))]
            idx = V.crop_idx(w_.base_idx(cfg_c.mask), cfg_c, rng)
            yb, yt = w_.targets(idx)
            ax = aux[w_.wid]                                             # tinh lai DOC LAP tu chuoi trong aux
            exp_b = float(any(ax["ev_mal"][i] == "1" for i in idx))
            exp_t = np.array([float(any(j in ax["ev_ttps"][i] for i in idx)) for j in range(len(TTPS))], np.float32)
            ok &= (yb == exp_b) and np.array_equal(yt, exp_t); n_chk += 1
            if w_.y_bin == 1 and yb == 0: n_neg_from_pos += 1
            if cfg_c.name == "M3": lens_cls[int(w_.y_bin)].append(len(idx))
            ok &= (len(idx) == len(w_) or (cfg_c.crop_min <= len(idx) <= len(w_)))
            ok &= bool(np.all(np.diff(idx) == 1)) if len(idx) > 1 else True
    check("5a nhan doan crop == tinh lai doc lap tu nhan tung event (aux)", ok, f"{n_chk} doan")
    check("5b co doan cat tu cua so duong ma khong con event malicious -> nhan 0", n_neg_from_pos > 0, f"{n_neg_from_pos} doan")
    full_ok = all(w_.targets(np.arange(len(w_)))[0] == w_.y_bin and np.array_equal(w_.targets(np.arange(len(w_)))[1], w_.y_ttp)
                  for w_ in data["train"])
    check("5c khong crop: nhan == window_malicious / window_ttps (483 cua so)", full_ok)
    for mode in ("b3", "uniform"):
        cm = replace(V.PRESETS["M3"], crop=mode); lc = {0: [], 1: []}; rr = np.random.default_rng(5)
        for _ in range(5): 
            for w_ in data["train"]: lc[int(w_.y_bin)].append(len(V.crop_idx(w_.base_idx("a"), cm, rr)))
        print(f"     crop={mode:7s}: do dai doan duong mean {np.mean(lc[1]):.1f} / am mean {np.mean(lc[0]):.1f}, "
              f"ti le {np.mean(lc[1]) / np.mean(lc[0]):.2f}; ti le doan 64 event duong {np.mean(np.array(lc[1]) == 64):.2f} / am {np.mean(np.array(lc[0]) == 64):.2f}")
    print("     do dai doan M3 (uniform) theo lop cua so goc: duong mean %.1f / am mean %.1f; goc: duong %.1f / am %.1f" % (
        np.mean(lens_cls[1]), np.mean(lens_cls[0]),
        np.mean([len(w_) for w_ in data["train"] if w_.y_bin]), np.mean([len(w_) for w_ in data["train"] if not w_.y_bin])))
    # ---- 6. name dropout ----
    w_ = data["train"][0]; c0 = w_.seq(np.arange(len(w_)))[0]
    c1 = V.apply_names(c0, replace(cfg, name_drop=1.0), np.random.default_rng(0), True)
    c2 = V.apply_names(c0, replace(cfg, name_drop=1.0), None, False)
    c3 = V.apply_names(c0, replace(cfg, drop_names=True), None, False)
    oth = [i for i in range(7) if i not in V.NAME_COLS]
    check("6a name_drop p=1 khi train: image/parent = <unk>, cot khac giu nguyen",
          (c1[:, list(V.NAME_COLS)] == V.UNK).all() and np.array_equal(c1[:, oth], c0[:, oth]))
    check("6b luc suy luan khong drop (p>0)", np.array_equal(c2, c0))
    check("6c drop_names (b): luon <unk> ca luc suy luan", (c3[:, list(V.NAME_COLS)] == V.UNK).all())
    # ---- 7. huan luyen 2 epoch ----
    meta_tr = load_meta(ROOT, "train"); folds = cv_folds(meta_tr, root=ROOT)[:2]
    for pname in ("M1", "M4"):
        c = replace(V.PRESETS[pname], max_epochs=2)
        t1 = time.time()
        P_bin, P_ttp, finfo = V.run_cv(c, vs, data["train"], folds, seed=1337, max_batches=4)
        va = np.concatenate([f[1] for f in folds])
        good = np.isfinite(P_bin[va]).all() and (0 <= P_bin[va]).all() and (P_bin[va] <= 1).all() and np.isfinite(P_ttp[va]).all()
        keys = sorted(finfo[0])
        check(f"7 {pname}: CV 2 fold x 2 epoch x 4 batch, OOF hop le", good and keys == (["bin", "ttp"] if pname == "M1" else ["joint"]),
              f"mang {keys}, epoch tot nhat {[[f[k]['best_epoch'] for k in keys] for f in finfo]}, {time.time() - t1:.1f}s")
    lg = []
    V.fit(replace(V.PRESETS["M3"], max_epochs=2), vs, data["train"][:96], data["train"][96:160], seed=7, log=lg)
    check("7c log co train_loss/val_loss huu han", all(np.isfinite(e["train_loss"]) and np.isfinite(e["val_loss"]) for e in lg),
          f"{[(e['epoch'], round(e['train_loss'], 3), round(e['val_loss'], 3)) for e in lg]}")
    # ---- 8. nguong ----
    r = np.random.default_rng(3); y = r.random(500) < 0.3; s = r.random(500) + y * 0.5
    thr = V.threshold_at_fpr(y, s, 0.01)
    check("8a threshold_at_fpr: FPR am <= 1%", float((s[~y] >= thr).mean()) <= 0.01, f"FPR {(s[~y] >= thr).mean():.4f}, thr {thr:.3f}")
    sel = V.choose_on_oof(data["train"], P_bin, P_ttp, V.PRESETS["M4"])
    check("8b choose_on_oof: chon p_bin / p_bin' + nguong TTP", sel["binary_score"] in ("p_bin", "p_bin_max") and len(sel["ttp"]) == 5,
          f"{sel['binary_score']} {sel['oof_pr_auc']}")
    # ---- 9. checkpoint ----
    nets, _ = V.fit_nets(replace(V.PRESETS["M4"], max_epochs=1), vs, data["train"][:64], max_batches=2, epochs={"joint": 1})
    pb1, pt1, al1 = V.predict(nets, data["t_novel"][:20], V.PRESETS["M4"])
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.pt"); V.save_nets(p, nets, V.PRESETS["M4"], vs); nets2, cfg2, _ = V.load_nets(p)
        pb2, pt2, al2 = V.predict(nets2, data["t_novel"][:20], cfg2)
    check("9 save/load checkpoint: du doan + alpha giong het", np.array_equal(pb1, pb2) and np.array_equal(pt1, pt2)
          and all(np.array_equal(x, y_) for x, y_ in zip(al1, al2)) and all(abs(x.sum() - 1) < 1e-5 for x in al1))
    # ---- 11. aux cua tap test khong bao gio vao forward ----
    import copy, inspect
    fwd = list(inspect.signature(V.VTSeq.forward).parameters)
    check("11a forward chi nhan (cat, cmd, num, lens)", fwd == ["self", "cat", "cmd", "num", "lens"], f"{fwd}")
    nets_t, _ = V.fit_nets(replace(V.PRESETS["M4"], max_epochs=1), vs, data["train"][:64], max_batches=2, epochs={"joint": 1})
    same = True
    for sp in ("t_clean", "t_hard", "t_novel"):
        ws0 = data[sp][:40]; stripped = []
        for w0 in ws0:                                          # xoa han mat na aux -> neu bi doc se loi
            w1 = copy.copy(w0); w1.origin = None; w1.one_sided = None; w1.ev_mal = None; w1.ev_ttp = None; stripped.append(w1)
        for pn in ("M3", "M4", "M4b"):
            a1 = V.predict(nets_t, ws0, V.PRESETS[pn]); a2 = V.predict(nets_t, stripped, V.PRESETS[pn])
            same &= np.array_equal(a1[0], a2[0]) and np.array_equal(a1[1], a2[1]) and all(np.array_equal(x, y_) for x, y_ in zip(a1[2], a2[2]))
    check("11b tap test, mat na (a)/(b): xoa origin/one_sided/nhan aux -> du doan + alpha giong het (aux khong vao forward)", same)
    w0 = data["t_novel"][0]; w1 = copy.copy(w0); w1.origin = ~w0.origin; w1.one_sided = ~w0.one_sided
    s0 = V.eval_seq(w0, V.PRESETS["M3"]); s1 = V.eval_seq(w1, V.PRESETS["M3"])
    check("11c dao nguoc mat na aux tap test -> chuoi dau vao (a) khong doi", all(np.array_equal(x, y_) for x, y_ in zip(s0, s1)))
    cp_ = replace(V.PRESETS["M3"], mask="c"); sc = V.eval_seq(w0, cp_)
    check("11d mat na (c) chi chon chi so event (dau vao = tap con cua event that, khong them kenh)",
          sc[0].shape[1] == len(V.CAT_FIELDS) and sc[2].shape[1] == V.NUM_DIM and len(sc[0]) == max(1, int(w0.origin.sum())))
    wt = data["train"][5]; wt2 = copy.copy(wt); wt2.ev_mal = ~wt.ev_mal; wt2.ev_ttp = 1 - wt.ev_ttp
    x1 = V.train_sample(wt, V.PRESETS["M4"], np.random.default_rng(9)); x2 = V.train_sample(wt2, V.PRESETS["M4"], np.random.default_rng(9))
    check("11e Train: doi nhan event -> dau vao giong het, chi nhan doan doi (nhan chi la target)",
          all(np.array_equal(a_, b_) for a_, b_ in zip(x1[0], x2[0])) and (x1[1] != x2[1] or not np.array_equal(x1[2], x2[2])))
    # ---- 10. tat dinh ----
    sd = []
    for _ in range(2):
        n_, _, _, _ = V.fit(replace(V.PRESETS["M4"], max_epochs=1), vs, data["train"][:64], seed=42, max_batches=2)
        sd.append(torch.cat([p_.flatten() for p_ in n_.parameters()]))
    check("10 cung seed -> trong so giong het", torch.equal(sd[0], sd[1]))
    n_pass = sum(ok for _, ok in RESULTS)
    print(f"\nKET QUA: {n_pass}/{len(RESULTS)} PASS trong {time.time() - t0:.1f}s | torch {torch.__version__}")
    sys.exit(0 if n_pass == len(RESULTS) else 1)

if __name__ == "__main__":
    main()
