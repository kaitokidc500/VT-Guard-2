#!/usr/bin/env python3
"""VT-Guard Buoc 7 - vi tu (atom) cua luat, DANH SACH CAM (docs/STEP7-BRIEF.md muc 2-3) va matcher noi bo.

Atom = "trong cua so co >= 1 event thoa ...", chi tren telemetry quan sat duoc (brief muc 2):
  ("img", X)          image_name == X
  ("par", X)          parent_image_name == X (da gop <launcher>)
  ("eid", E)          event_id == E
  ("tok", T)          command_line (featurize.norm_cmd, tach token nhu B1) chua token T
  ("imgtok", (X, T))  CUNG MOT event: image_name == X va command_line chua token T
Khong doc truong nao khac cua event (EVENT_KEYS). Truong cam (wazuh_rule_*, label_*, run_id, window_id, process_guid,
n_events, tempo, variant, user_role, duong dan day du) khong bao gio la atom.

Danh sach cam theo canh bao scaffold (brief muc 3; reports/step6/m4_explain.md):
  S1 duong dan mac dinh / ma ky thuat ART (ntds_T1003 -> ntds_t0 sau norm, \\windows\\temp\\, atomic, t<so>)
  S2 vo cmd: image cmd.exe, token "cmd" / "/c", parent cmd.exe / <launcher>
  S3 PowerShell (ART chay test trong powershell con): image powershell.exe/pwsh.exe, parent powershell.exe, token
     "powershell", event_id kenh PowerShell (4103/4104/4105/4106/40961/40962/53504/400/403/600/800)
  S4 event nen mot-phia cua T1003.003: ESENT/Directory Service event_id, vssvc.exe, rundll32 SHCreateLocalServerRunDll
  S5 (de xuat them) ten mien lab (vtlab / corp.vtlab.test): khong khai quat ra moi truong khac
Them cong ky thuat (khong phai scaffold): G-sigma - token co chu so (norm_cmd doi so -> 0) hoac <guid>/<hex> khong anh
xa nguyen van sang CommandLine|contains cua Sigma.
"""
import re

TOK_RE = re.compile(r"[a-z0-9_.<>/\\-]+")
EVENT_KEYS = ("image_name", "parent_image_name", "event_id", "command_line")   # duy nhat cac truong event duoc doc

NTDS_SIDE_EFFECT_EIDS = {98, 102, 103, 105, 216, 300, 301, 302, 325, 326, 327, 330, 2001, 2002, 2003, 2004, 2005, 2006}
PS_EIDS = {4103, 4104, 4105, 4106, 40961, 40962, 53504, 400, 403, 600, 800}

FORBIDDEN_ATOMS = {
    ("img", "cmd.exe"): "S2 vo cmd", ("tok", "cmd"): "S2 vo cmd", ("tok", "/c"): "S2 vo cmd",
    ("par", "cmd.exe"): "S2 vo cmd", ("par", "<launcher>"): "S2/S3 launcher (cmd|powershell)",
    ("img", "powershell.exe"): "S3 powershell", ("img", "pwsh.exe"): "S3 powershell", ("par", "powershell.exe"): "S3 powershell",
    ("tok", "powershell"): "S3 powershell",
    ("img", "vssvc.exe"): "S4 nen T1003 (VSS service)", ("tok", "shell32.dll"): "S4 nen COM",
}
FORBIDDEN_TOKEN_RES = [
    (re.compile(r"ntds_t0|\\windows\\temp\\|atomic|pathtoatomics|(?<![a-z0-9])t0(?![a-z0-9])"), "S1 duong dan/ma ky thuat ART"),
    (re.compile(r"shcreatelocalserverrundll"), "S4 nen COM (svchost->rundll32)"),
    (re.compile(r"vtlab"), "S5 ten mien lab"),
]
NON_SIGMA_TOKEN_RE = re.compile(r"0|<guid>|<hex>")

def tokens(cmd):
    from featurize import norm_cmd
    return set(TOK_RE.findall(norm_cmd(cmd))) if cmd else set()

def forbidden_reason(atom):
    """Ly do cam (chuoi) hoac None. Ap cho moi loai atom (ke ca thanh phan cua imgtok)."""
    kind, v = atom
    if atom in FORBIDDEN_ATOMS: return FORBIDDEN_ATOMS[atom]
    if kind == "eid":
        if int(v) in PS_EIDS: return "S3 kenh PowerShell"
        if int(v) in NTDS_SIDE_EFFECT_EIDS: return "S4 nen T1003 (ESENT/Directory Service)"
    if kind == "imgtok":
        return forbidden_reason(("img", v[0])) or forbidden_reason(("tok", v[1]))
    if kind == "tok":
        for rx, why in FORBIDDEN_TOKEN_RES:
            if rx.search(v): return why
    return None

def sigma_reason(atom):
    """Ly do khong anh xa Sigma nguyen van, hoac None."""
    kind, v = atom
    t = v[1] if kind == "imgtok" else (v if kind == "tok" else None)
    if t is not None and NON_SIGMA_TOKEN_RE.search(t): return "G-sigma: token co chu so/<guid>/<hex> (da chuan hoa)"
    return None

def event_atoms(e):
    """Tap atom cua mot event (chi doc EVENT_KEYS)."""
    img, par, eid, cmd = (e.get(k) for k in EVENT_KEYS)
    out = {("img", img or "<none>"), ("eid", int(eid))}
    if par: out.add(("par", par))
    for t in tokens(cmd):
        out.add(("tok", t)); out.add(("imgtok", (img or "<none>", t)))
    return out

# ---------------- matcher noi bo (doc lap voi ma tran dac trung) ----------------
def _event_has(e, atom):
    kind, v = atom
    if kind == "img": return (e.get("image_name") or "<none>") == v
    if kind == "par": return e.get("parent_image_name") == v
    if kind == "eid": return int(e.get("event_id")) == int(v)
    toks = tokens(e.get("command_line"))
    if kind == "tok": return v in toks
    if kind == "imgtok": return (e.get("image_name") or "<none>") == v[0] and v[1] in toks
    raise ValueError(kind)

def match(literals, events):
    """literals: [(atom, True|False)]; True = co >= 1 event thoa atom trong cua so, False = khong event nao thoa."""
    return all(any(_event_has(e, a) for e in events) == pol for a, pol in literals)
