# VT-Guard Buoc 8 moc 1 - fusion AI + luat: CHI OOF Train (chua cham test)

Nguon OOF: AI `reports/preds/vtseq_M3_ens_train.jsonl` (trung binh 5 seed M3, OOF Buoc 6; nguong khoa tau = 0.8692, diem p_bin_max), luat `reports/preds/rules_oof_train.jsonl` (luat quy nap lai trong tung fold, Buoc 7). KHONG dung `reports/preds/rules_train.jsonl` de hoc/chon (chi cho do nhay mo ta). Train 483 cua so (176 duong, 109 hard_negative). Seed 1337.

F0 chi-AI, F1 chi-luat: tham chieu. F2 OR (0 tham so). F3 s = p + beta*r (beta chon tren OOF trong {0.1, 0.2, 0.3}; nguong FPR <= 1% am OOF, TTP max-F1 OOF). F4 LR 7 dac trung, diem OOF bang CV long theo nhom phien.

## Bien the A: tat ca kenh luat theo TTP (dinh nghia brief)

**OOF F0-F4**

| Cau hinh | macro-F1 TTP | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | PR-AUC bin | FPR hard_neg | FPR am | Recall | F1 bin |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F0: chi-AI (nguong Buoc 6) | 0.830 | 0.752 | 0.776 | 0.791 | 0.828 | 1.000 | 0.997 | 0.037 | 0.013 | 0.994 | 0.986 |
| F1: chi-luat (nguong 0.5) | 0.545 | 0.707 | 0.286 | 0.257 | 0.712 | 0.765 | 0.801 | 0.018 | 0.007 | 0.705 | 0.821 |
| F2: OR | 0.831 | 0.752 | 0.791 | 0.791 | 0.820 | 1.000 | 0.982 | 0.055 | 0.020 | 0.994 | 0.980 |
| F3: boost beta = 0.1 | 0.847 | 0.816 | 0.791 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.010 | 0.994 | 0.989 |
| F4: stacking LR (CV long) | 0.832 | 0.785 | 0.751 | 0.793 | 0.830 | 1.000 | 0.995 | 0.028 | 0.010 | 0.994 | 0.989 |

**F3 - luoi beta (OOF)**

| Cau hinh | macro-F1 TTP | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | PR-AUC bin | FPR hard_neg | FPR am | Recall | F1 bin |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F3 beta = 0.1 | 0.847 | 0.816 | 0.791 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.010 | 0.994 | 0.989 |
| F3 beta = 0.2 | 0.847 | 0.816 | 0.791 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.010 | 0.994 | 0.989 |
| F3 beta = 0.3 | 0.846 | 0.810 | 0.791 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.010 | 0.994 | 0.989 |

**Chon theo muc 4 (ung vien F2-F4; ngang nhau neu |chenh| <= DLC bootstrap hieu so -> it tham so hon)**

| Tieu chi | Tot nhat | So voi | |chenh| | DLC bootstrap | Ngang nhau? |
|---|---|---|---|---|---|
| macro_f1_ttp | F3 | F2 | 0.0166 | 0.0087 | khong |
| macro_f1_ttp | F3 | F4 | 0.0155 | 0.0082 | khong |

-> chon **F3** (boost beta = 0.1).

**Do nhay (CHI mo ta): thay luat fold bang luat cuoi tren Train (in-sample)** - r khac o 11/483 cua so, r_k: {'T1016': 48, 'T1018': 14, 'T1087.002': 14, 'T1654': 5, 'T1003.003': 0}; giu nguyen tham so/nguong da hoc (F4: mo hinh fit toan OOF -> in-sample).

| Cau hinh | macro-F1 TTP | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | PR-AUC bin | FPR hard_neg | FPR am | Recall | F1 bin |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F2 OOF (luat fold) | 0.831 | 0.752 | 0.791 | 0.791 | 0.820 | 1.000 | 0.982 | 0.055 | 0.020 | 0.994 | 0.980 |
| F2 luat cuoi (mo ta) | 0.834 | 0.752 | 0.798 | 0.791 | 0.828 | 1.000 | 0.997 | 0.037 | 0.013 | 0.994 | 0.986 |
| F3 OOF (luat fold) | 0.847 | 0.816 | 0.791 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.010 | 0.994 | 0.989 |
| F3 luat cuoi (mo ta) | 0.813 | 0.636 | 0.798 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.010 | 0.994 | 0.989 |
| F4 OOF (luat fold) | 0.832 | 0.785 | 0.751 | 0.793 | 0.830 | 1.000 | 0.995 | 0.028 | 0.010 | 0.994 | 0.989 |
| F4 luat cuoi (mo ta) | 0.816 | 0.727 | 0.748 | 0.790 | 0.815 | 1.000 | 0.997 | 0.000 | 0.000 | 0.909 | 0.952 |

## Bien the B: chi kenh luat theo TTP co trong bo luat cuoi: ['T1003.003', 'T1018', 'T1654']

**OOF F0-F4**

| Cau hinh | macro-F1 TTP | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | PR-AUC bin | FPR hard_neg | FPR am | Recall | F1 bin |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F0: chi-AI (nguong Buoc 6) | 0.830 | 0.752 | 0.776 | 0.791 | 0.828 | 1.000 | 0.997 | 0.037 | 0.013 | 0.994 | 0.986 |
| F1: chi-luat (nguong 0.5) | 0.353 | 0.000 | 0.286 | 0.000 | 0.712 | 0.765 | 0.801 | 0.018 | 0.007 | 0.705 | 0.821 |
| F2: OR | 0.831 | 0.752 | 0.791 | 0.791 | 0.820 | 1.000 | 0.982 | 0.055 | 0.020 | 0.994 | 0.980 |
| F3: boost beta = 0.1 | 0.835 | 0.752 | 0.791 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.010 | 0.994 | 0.989 |
| F4: stacking LR (CV long) | 0.836 | 0.798 | 0.758 | 0.793 | 0.830 | 1.000 | 0.995 | 0.028 | 0.010 | 0.994 | 0.989 |

**F3 - luoi beta (OOF)**

| Cau hinh | macro-F1 TTP | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | PR-AUC bin | FPR hard_neg | FPR am | Recall | F1 bin |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F3 beta = 0.1 | 0.835 | 0.752 | 0.791 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.010 | 0.994 | 0.989 |
| F3 beta = 0.2 | 0.835 | 0.752 | 0.791 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.010 | 0.994 | 0.989 |
| F3 beta = 0.3 | 0.835 | 0.752 | 0.791 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.010 | 0.994 | 0.989 |

**Chon theo muc 4 (ung vien F2-F4; ngang nhau neu |chenh| <= DLC bootstrap hieu so -> it tham so hon)**

| Tieu chi | Tot nhat | So voi | |chenh| | DLC bootstrap | Ngang nhau? |
|---|---|---|---|---|---|
| macro_f1_ttp | F4 | F2 | 0.005 | 0.0108 | co |
| macro_f1_ttp | F4 | F3 | 0.0011 | 0.0111 | co |
| pr_auc | F3 | F2 | 0.015 | 0.0109 | khong |
| pr_auc | F3 | F4 | 0.0015 | 0.0013 | khong |

-> chon **F3** (boost beta = 0.1).

**Do nhay (CHI mo ta): thay luat fold bang luat cuoi tren Train (in-sample)** - r khac o 11/483 cua so, r_k: {'T1016': 0, 'T1018': 14, 'T1087.002': 0, 'T1654': 5, 'T1003.003': 0}; giu nguyen tham so/nguong da hoc (F4: mo hinh fit toan OOF -> in-sample).

| Cau hinh | macro-F1 TTP | T1016 | T1018 | T1087.002 | T1654 | T1003.003 | PR-AUC bin | FPR hard_neg | FPR am | Recall | F1 bin |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F2 OOF (luat fold) | 0.831 | 0.752 | 0.791 | 0.791 | 0.820 | 1.000 | 0.982 | 0.055 | 0.020 | 0.994 | 0.980 |
| F2 luat cuoi (mo ta) | 0.834 | 0.752 | 0.798 | 0.791 | 0.828 | 1.000 | 0.997 | 0.037 | 0.013 | 0.994 | 0.986 |
| F3 OOF (luat fold) | 0.835 | 0.752 | 0.791 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.010 | 0.994 | 0.989 |
| F3 luat cuoi (mo ta) | 0.836 | 0.752 | 0.798 | 0.797 | 0.834 | 1.000 | 0.997 | 0.028 | 0.010 | 0.994 | 0.989 |
| F4 OOF (luat fold) | 0.836 | 0.798 | 0.758 | 0.793 | 0.830 | 1.000 | 0.995 | 0.028 | 0.010 | 0.994 | 0.989 |
| F4 luat cuoi (mo ta) | 0.822 | 0.762 | 0.743 | 0.790 | 0.815 | 1.000 | 0.997 | 0.000 | 0.000 | 0.915 | 0.955 |
