# VT-Guard Buoc 7 moc 1 - luat ung vien (CHI Train; chua Sigma, chua test)

Engine (macro-F1 TTP OOF, du doan cua chinh engine): tree3 = 0.6584; tree4 = 0.6751; ripper = 0.7558 -> chon **ripper** (wittgenstein RIPPER (k=2, prune_size 0.33)), seed 1337. Atom: 706 (>= 3 phien Train); bi chan o luot rang buoc: 446 {'S4 nen T1003 (ESENT/Directory Service)': 16, 'S4-auto nen mot-phia (40% khop trong cay tien trinh < 50%, Train)': 1, 'S4-auto nen mot-phia (5% khop trong cay tien trinh < 50%, Train)': 1, 'S3 kenh PowerShell': 5, 'S4-auto nen mot-phia (0% khop trong cay tien trinh < 50%, Train)': 314, 'S4-auto nen mot-phia (32% khop trong cay tien trinh < 50%, Train)': 1, 'S4-auto nen mot-phia (16% khop trong cay tien trinh < 50%, Train)': 1, 'S2 vo cmd': 70, 'S3 powershell': 24, 'S4 nen T1003 (VSS service)': 2, 'S1 duong dan/ma ky thuat ART': 3, 'S5 ten mien lab': 4, 'S4-auto nen mot-phia (42% khop trong cay tien trinh < 50%, Train)': 1, 'S4 nen COM (svchost->rundll32)': 2, 'S2/S3 launcher (cmd|powershell)': 1}.

Ngu nghia: cua so khop luat neu moi vi tu co >= 1 event thoa; `cmd~'x'` = command line (norm_cmd) chua token x. Luat = cac literal DUONG cua mot luat/la cua engine (literal vang mat bi bo vi Sigma khong bieu dien duoc), da rut gon. OOF: luat duoc quy nap lai boi engine tren 4/5 Train va do tren fold con lai; precision OOF can >= 10 cua so khop.

## Luat giu lai: 11

| id | Muc tieu | Vi tu | Support Train (TP/FP) | Precision Train | Recall Train | Precision OOF (TP/FP) | Fold tai lap | Hat giong lien quan (TTP: lift) |
|---|---|---|---|---|---|---|---|---|
| VTR-BIN-01 | bin | `cmd~'userdnsdomain'` | 35 (35/0) | 1.000 | 0.199 | 1.000 (24/0) | 4/5 | cmd~'userdnsdomain': T1018 74.78 |
| VTR-BIN-02 | bin | `cmd~'create'` | 26 (26/0) | 1.000 | 0.148 | 1.000 (18/0) | 4/5 | cmd~'create': T1003.003 182.74 |
| VTR-BIN-03 | bin | `cmd~'enum-logs'` | 25 (25/0) | 1.000 | 0.142 | 1.000 (25/0) | 5/5 | cmd~'enum-logs': T1016 72.24, T1087.002 42.01, T1654 92.47 |
| VTR-BIN-04 | bin | `cmd~'.findall'` | 19 (19/0) | 1.000 | 0.108 | 1.000 (15/0) | 4/5 | - |
| VTR-BIN-05 | bin | `image=net.exe & cmd~'administrator'` | 18 (18/0) | 1.000 | 0.102 | 1.000 (10/0) | 3/5 | image=net.exe: T1016 2.27, T1018 2.11, T1087.002 2.27, T1654 1.78 |
| VTR-BIN-06 | bin | `cmd~'controllers'` | 17 (17/0) | 1.000 | 0.097 | 1.000 (10/0) | 4/5 | cmd~'controllers': T1018 66.91 |
| VTR-T1018-01 | T1018 | `cmd~'controllers'` | 17 (17/0) | 1.000 | 0.218 | 1.000 (13/0) | 4/5 | cmd~'controllers': T1018 66.91 |
| VTR-T1018-02 | T1018 | `image=nltest.exe` AND `cmd~'userdnsdomain'` | 10 (10/0) | 1.000 | 0.128 | 1.000 (10/0) | 4/5 | image=nltest.exe: T1016 0.52, T1018 1.12, T1087.002 0.46, T1654 0.53; cmd~'userdnsdomain': T1018 74.78 |
| VTR-T1654-01 | T1654 | `cmd~'system'` | 25 (25/0) | 1.000 | 0.301 | 1.000 (11/0) | 3/5 | - |
| VTR-T1654-02 | T1654 | `cmd~'enum-logs'` | 25 (25/0) | 1.000 | 0.301 | 1.000 (25/0) | 5/5 | cmd~'enum-logs': T1016 72.24, T1087.002 42.01, T1654 92.47 |
| VTR-T1003003-01 | T1003.003 | `cmd~'create'` | 26 (26/0) | 1.000 | 0.619 | 1.000 (18/0) | 4/5 | cmd~'create': T1003.003 182.74 |

**TTP khong co luat rieng:** T1016 va T1087.002 KHONG co luat theo TTP: ket qua cua cac cong (khong ha cong). Phien mixed gan nhieu TTP cho cung cua so nen token cua TTP khac xuat hien trong cua so mang nhan TTP do -> precision OOF thap; cac luat T1087.002 chinh xac (cmd~'.findall' 9 cua so OOF, image=cmd.exe & cmd~'user' bi cam S2) khong qua cong. Hanh vi T1087.002 chi duoc phu o muc nhi phan (VTR-BIN-04 .findall, VTR-BIN-05 net administrator).

## Sai khac so voi brief (va ly do)

1. **vi tu CO MAT (cua so co >= 1 event thoa atom) thay cho nguong ti le dac trung B2 (brief 4.1/4.2)** - chi dang nay anh xa CHINH XAC sang Sigma ('co >= 1 event thoa ...'); nguong ti le > 0 cua B2 tuong duong co mat, nguong ti le khac 0 khong bieu dien duoc trong Sigma -> matcher Sigma se lech dieu kien luat.
2. **engine = RIPPER (wittgenstein), khong phai cay** - brief 4.1 yeu cau chon bang macro-F1 TTP OOF; RIPPER 0.756 > cay sau 4 0.675 > cay sau 3 0.658 (du doan cua chinh engine, literal day du, luot rang buoc). Cay van duoc chay va bao cao.
3. **them cong S5 (ten mien lab vtlab) va S4-auto (atom co < 50% lan khop tren cua so duong Train nam trong cay tien trinh)** - S5: token ten mien lab khong khai quat ra moi truong khac. S4-auto: tong quat hoa canh bao 4 (event nen mot-phia) - bat duoc svchost dsmsvc / rundll32 -embedding (tac dong phu nen cua T1003, 0% trong cay tien trinh) ma danh sach tay bo sot; event_origin chi dung cho cong nay tren Train, khong bao gio la dac trung.
4. **cong phu: precision OOF phai tinh tren >= 10 cua so OOF khop (them vao G3)** - precision OOF tren 3-9 cua so khong co y nghia thong ke (vd cmd~'system' cho T1087.002: 3 cua so, precision Train 0.72). Cong dat TRUOC khi cham test, CHI dua tren Train; nguoi dung duyet giu nguong 10 (khong ha de lay them luat).

## Luat bi loai theo cong

| Cong | So luat | Mo ta |
|---|---|---|
| G0 | 0 | luat khong co literal duong |
| G1 | 18 | vi tu cam (scaffold S1-S5 / nen mot-phia S4-auto) |
| G2 | 0 | khong anh xa Sigma nguyen van |
| G3 | 24 | support Train >= 10, precision OOF >= 0.9 tren >= 10 cua so OOF (can tai lap tren fold) |
| G4 | 1 | khu trung (Jaccard >= 0.8, cung TTP) |

**G1** (vi tu cam (scaffold S1-S5 / nen mot-phia S4-auto)) - 18 luat

| Luot | Muc tieu | Vi tu | Ly do | Support / precision Train | Precision OOF |
|---|---|---|---|---|---|
| khong_rang_buoc | bin | `image=cmd.exe` AND `cmd~'c'` | vi tu cam: image=cmd.exe [S2 vo cmd]; cmd~'c' [S4-auto nen mot-phia (42% khop trong cay tien trinh < 50%, Train)] | 72 / 1.0 | 1.0 |
| khong_rang_buoc | bin | `image=cmd.exe` AND `image=net1.exe` | vi tu cam: image=cmd.exe [S2 vo cmd] | 57 / 1.0 | 1.0 |
| khong_rang_buoc | bin | `image=cmd.exe` | vi tu cam: image=cmd.exe [S2 vo cmd] | 166 / 0.8434 | 0.871 |
| khong_rang_buoc | bin | `event_id=40961` | vi tu cam: event_id=40961 [S3 kenh PowerShell] | 43 / 0.9302 | 0.9302 |
| khong_rang_buoc | T1016 | `cmd~'cmd'` AND `cmd~'config'` | vi tu cam: cmd~'cmd' [S2 vo cmd] | 24 / 1.0 | 1.0 |
| khong_rang_buoc | T1018 | `image=cmd.exe & cmd~'-a'` AND `cmd~'cmd'` | vi tu cam: image=cmd.exe & cmd~'-a' [S2 vo cmd]; cmd~'cmd' [S2 vo cmd] | 34 / 0.6471 | 0.6667 |
| khong_rang_buoc | T1018 | `image=cmd.exe` AND `cmd~'/domain'` AND `cmd~'controllers'` | vi tu cam: image=cmd.exe [S2 vo cmd] | 17 / 1.0 | 1.0 |
| khong_rang_buoc | T1018 | `image=<none>` AND `cmd~'cmd'` AND `cmd~'userdnsdomain'` | vi tu cam: image=<none> [S4-auto nen mot-phia (16% khop trong cay tien trinh < 50%, Train)]; cmd~'cmd' [S2 vo cmd] | 14 / 0.8571 | None |
| khong_rang_buoc | T1018 | `image=microsoft.activedirectory.webservices.exe` AND `cmd~'cmd'` AND `cmd~'enum-logs'` | vi tu cam: image=microsoft.activedirectory.webservices.exe [S4-auto nen mot-phia (0% khop trong cay tien trinh < 50%, Train)]; cmd~'cmd' [S2 vo cmd] | 8 / 0.875 | - |
| khong_rang_buoc | T1018 | `image=cmd.exe & cmd~'net'` AND `image=powershell.exe & cmd~'-c'` | vi tu cam: image=cmd.exe & cmd~'net' [S2 vo cmd]; image=powershell.exe & cmd~'-c' [S3 powershell] | 9 / 1.0 | - |
| khong_rang_buoc | T1018 | `image=cmd.exe & cmd~'/dclist'` | vi tu cam: image=cmd.exe & cmd~'/dclist' [S2 vo cmd] | 10 / 1.0 | 1.0 |
| khong_rang_buoc | T1087.002 | `image=cmd.exe & cmd~'net'` AND `cmd~'user'` | vi tu cam: image=cmd.exe & cmd~'net' [S2 vo cmd] | 41 / 1.0 | 1.0 |
| khong_rang_buoc | T1087.002 | `event_id=40961` AND `cmd~'user'` | vi tu cam: event_id=40961 [S3 kenh PowerShell] | 26 / 1.0 | 1.0 |
| khong_rang_buoc | T1087.002 | `image=cmd.exe` AND `image=microsoft.activedirectory.webservices.exe` | vi tu cam: image=cmd.exe [S2 vo cmd]; image=microsoft.activedirectory.webservices.exe [S4-auto nen mot-phia (0% khop trong cay tien trinh < 50%, Train)] | 36 / 0.7222 | 0.5455 |
| khong_rang_buoc | T1654 | `cmd~'cmd'` AND `cmd~'enum-logs'` | vi tu cam: cmd~'cmd' [S2 vo cmd] | 25 / 1.0 | 1.0 |
| khong_rang_buoc | T1654 | `image=microsoft.activedirectory.webservices.exe` AND `cmd~'cmd'` | vi tu cam: image=microsoft.activedirectory.webservices.exe [S4-auto nen mot-phia (0% khop trong cay tien trinh < 50%, Train)]; cmd~'cmd' [S2 vo cmd] | 34 / 0.7353 | 0.5455 |
| khong_rang_buoc | T1003.003 | `image=svchost.exe & cmd~'dsmsvc'` | vi tu cam: image=svchost.exe & cmd~'dsmsvc' [S4-auto nen mot-phia (0% khop trong cay tien trinh < 50%, Train)] | 38 / 1.0 | - |
| khong_rang_buoc | T1003.003 | `event_id=103` | vi tu cam: event_id=103 [S4 nen T1003 (ESENT/Directory Service)] | 38 / 1.0 | 1.0 |

**G3** (support Train >= 10, precision OOF >= 0.9 tren >= 10 cua so OOF (can tai lap tren fold)) - 24 luat

| Luot | Muc tieu | Vi tu | Ly do | Support / precision Train | Precision OOF |
|---|---|---|---|---|---|
| khong_rang_buoc | bin | `cmd~'-n'` | support Train 49 (>= 10) / precision OOF 0.7917 (>= 0.9) tren 24 cua so OOF khop (>= 10) | 49 / 0.8163 | 0.7917 |
| khong_rang_buoc | T1016 | `cmd~'userdnsdomain'` | support Train 35 (>= 10) / precision OOF 0.8571 (>= 0.9) tren 7 cua so OOF khop (>= 10) | 35 / 0.9429 | 0.8571 |
| khong_rang_buoc | T1016 | `cmd~'enum-logs'` | support Train 25 (>= 10) / precision OOF 0.8 (>= 0.9) tren 15 cua so OOF khop (>= 10) | 25 / 0.8 | 0.8 |
| khong_rang_buoc | T1016 | `cmd~'controllers'` | support Train 17 (>= 10) / precision OOF 0.6667 (>= 0.9) tren 3 cua so OOF khop (>= 10) | 17 / 0.7059 | 0.6667 |
| khong_rang_buoc | T1018 | `cmd~'-n'` | support Train 49 (>= 10) / precision OOF 0.5 (>= 0.9) tren 30 cua so OOF khop (>= 10) | 49 / 0.5714 | 0.5 |
| khong_rang_buoc | T1087.002 | `cmd~'system'` | khong tai lap tren fold nao (khong co OOF) | 25 / 0.72 | - |
| khong_rang_buoc | T1654 | `cmd~'-n'` | khong tai lap tren fold nao (khong co OOF) | 49 / 0.449 | - |
| rang_buoc | bin | `cmd~'-n'` | support Train 49 (>= 10) / precision OOF 0.8205 (>= 0.9) tren 39 cua so OOF khop (>= 10) | 49 / 0.8163 | 0.8205 |
| rang_buoc | bin | `image=ntdsutil.exe` | support Train 47 (>= 10) / precision OOF 0.8085 (>= 0.9) tren 47 cua so OOF khop (>= 10) | 47 / 0.8085 | 0.8085 |
| rang_buoc | bin | `cmd~'system'` | support Train 25 (>= 10) / precision OOF 1.0 (>= 0.9) tren 5 cua so OOF khop (>= 10) | 25 / 1.0 | 1.0 |
| rang_buoc | bin | `image=net1.exe & cmd~'group'` | support Train 81 (>= 10) / precision OOF 0.4615 (>= 0.9) tren 13 cua so OOF khop (>= 10) | 81 / 0.3827 | 0.4615 |
| rang_buoc | T1016 | `image=ipconfig.exe` AND `cmd~'-n'` | support Train 23 (>= 10) / precision OOF 1.0 (>= 0.9) tren 8 cua so OOF khop (>= 10) | 23 / 1.0 | 1.0 |
| rang_buoc | T1016 | `cmd~'userdnsdomain'` | support Train 35 (>= 10) / precision OOF 0.8571 (>= 0.9) tren 7 cua so OOF khop (>= 10) | 35 / 0.9429 | 0.8571 |
| rang_buoc | T1016 | `cmd~'controllers'` AND `cmd~'system'` | khong tai lap tren fold nao (khong co OOF) | 5 / 1.0 | - |
| rang_buoc | T1018 | `cmd~'-n'` | support Train 49 (>= 10) / precision OOF 0.5714 (>= 0.9) tren 49 cua so OOF khop (>= 10) | 49 / 0.5714 | 0.5714 |
| rang_buoc | T1018 | `image=arp.exe` AND `cmd~'administrator'` | khong tai lap tren fold nao (khong co OOF) | 7 / 0.8571 | - |
| rang_buoc | T1018 | `cmd~'enum-logs'` | support Train 25 (>= 10) / precision OOF 0.3333 (>= 0.9) tren 9 cua so OOF khop (>= 10) | 25 / 0.44 | 0.3333 |
| rang_buoc | T1018 | `image=arp.exe` | support Train 142 (>= 10) / precision OOF 0.1549 (>= 0.9) tren 142 cua so OOF khop (>= 10) | 142 / 0.1549 | 0.1549 |
| rang_buoc | T1018 | `image=net.exe & cmd~'administrator'` | support Train 18 (>= 10) / precision OOF 0.5 (>= 0.9) tren 4 cua so OOF khop (>= 10) | 18 / 0.7222 | 0.5 |
| rang_buoc | T1087.002 | `cmd~'net'` AND `cmd~'user'` | support Train 92 (>= 10) / precision OOF 0.2381 (>= 0.9) tren 21 cua so OOF khop (>= 10) | 92 / 0.4457 | 0.2381 |
| rang_buoc | T1087.002 | `cmd~'.findall'` | support Train 19 (>= 10) / precision OOF 1.0 (>= 0.9) tren 9 cua so OOF khop (>= 10) | 19 / 1.0 | 1.0 |
| rang_buoc | T1654 | `cmd~'-n'` | khong tai lap tren fold nao (khong co OOF) | 49 / 0.449 | - |
| rang_buoc | T1654 | `image=net.exe & cmd~'administrator'` | support Train 18 (>= 10) / precision OOF 0.6 (>= 0.9) tren 5 cua so OOF khop (>= 10) | 18 / 0.5556 | 0.6 |
| rang_buoc | T1003.003 | `image=ntdsutil.exe` | support Train 47 (>= 10) / precision OOF 0.8085 (>= 0.9) tren 47 cua so OOF khop (>= 10) | 47 / 0.8085 | 0.8085 |

**G4** (khu trung (Jaccard >= 0.8, cung TTP)) - 1 luat

| Luot | Muc tieu | Vi tu | Ly do | Support / precision Train | Precision OOF |
|---|---|---|---|---|---|
| rang_buoc | T1654 | `cmd~'system'` | trung khoa voi luat cua luot khac | 25 / 1.0 | 1.0 |
