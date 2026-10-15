#!/usr/bin/env python3
# VT-Guard labeler v6 (v5 + ghep PID->tien trinh theo vong doi, gio ts_system)
# Gan nhan event da chuan hoa (normalize.py) theo manifest + cay tien trinh Sysmon EID1.
# Nguyen tac:
#   - Orchestrator = tien trinh chay Invoke-VTSession/Batch (pid in exclude_pids). Event cua no -> LOAI (chong ro ri NHAN).
#   - Executor-root = con truc tiep cua orchestrator (EID1 co parent_process_id in exclude_pids).
#       Gan tung root vao PHIEN theo THOI DIEM sinh ra (dung moc bat dau cac phien lam ranh gioi),
#       KHONG loc tung event theo [t_start,t_end] (chong tre log + phien sat nhau).
#   - Harness ART (hostname/whoami/conhost la executor-root) + cay con cua chung -> LOAI (chong ro ri DAU VET CONG CU).
#   - Cac executor-root con lai + cay con -> gan nhan theo class phien (attack: label_ttps = ttps cua phien).
#   - Nhan o MUC CUA SO/PHIEN (multi-label), khong gan tung TTP cho tung event.
# Bo sung v5:
#   - "ps_fragment": event khong co channel/event_id/record_id (Wazuh cat vo message 4103,
#       noi dung la pipeline Invoke-AtomicTest, mat PID) -> LOAI.
#   - "harness_upload": scp/ssh day manifest len server (scp.exe, ssh.exe la executor-root,
#       hoac EID1 co dong lenh chua .manifest.json / VT-Guard-runs) + cay con -> LOAI,
#       uu tien hon gan nhan phien (v4 gan nham thanh malicious T1003.003 o ntds).
#   - "operator_console": console PowerShell cua nguoi van hanh (khong nam trong exclude_pids)
#       co script block goi khung ART/VT -> LOAI moi event cua tien trinh do + cay con truc tiep
#       (runas, w32tm...). Vong doi tien trinh = giua 2 lan EID1 cung PID; KHONG dung EID5 lam
#       moc ket thuc vi khoi phuc snapshot (ntds) lam tien trinh "song lai" ma khong co EID1.
#       Event thuoc cay phien (exec) van uu tien hon quy tac nay.
# Bo sung v6:
#   - Event khong co process_guid (PowerShell 4103/4104, Security...) ghep vao tien trinh theo
#       (host, PID) va ts_system (gio that cua event), CHI khi event nam trong vong doi tien trinh:
#       [EID1, EID5] cua guid do (+-2 s); thieu EID5 -> den EID1 ke tiep cung PID (hoac mo).
#       v5 dung `ts` cua Wazuh +-300 s: sau khi khoi phuc snapshot dong ho DC01 lech ~55 phut,
#       PowerShell pid 1112 (07:47) bi ghep nham vao conhost.exe 1112 cua phien ntds2 084208 (08:42)
#       -> 204 event malicious T1003.003 sai.
# Chay: python label.py <norm.jsonl> <manifests_dir> <out.jsonl>
import json, sys, glob, os, re
from bisect import bisect_right
from collections import defaultdict, Counter
from datetime import datetime, timedelta

LABEL_VERSION = "v6"
HARNESS = {"conhost.exe","hostname.exe","whoami.exe","scp.exe","ssh.exe"}
UPLOAD_RE = re.compile(r"\.manifest\.json|VT-Guard-runs", re.I)
OPERATOR_RE = re.compile(r"Invoke-AtomicTest|Invoke-VT\w*|AtomicRedTeam|PathToAtomicsFolder|Get-AtomicTechnique|VT-Guard", re.I)

def ts(s):
    if not s: return None
    s=s.replace("Z","+00:00")
    if "." in s:
        head,rest=s.split(".",1)
        digs="".join(c for c in rest if c.isdigit())[:6]
        off=rest[rest.find("+"):] if "+" in rest else "+00:00"
        s=f"{head}.{digs}{off}"
    return datetime.fromisoformat(s)

def load(path): return [json.loads(l) for l in open(path, encoding="utf-8")]

def load_manifest(f):
    try:
        with open(f, encoding="utf-8-sig") as fh: txt=fh.read().strip()
        return json.loads(txt) if txt else None
    except (json.JSONDecodeError, OSError) as e:
        sys.stderr.write(f"CANH BAO: bo qua manifest loi {os.path.basename(f)}: {e}\n"); return None

def build_tree(rows):
    e1=[r for r in rows if r["event_id"]==1 and r["process_guid"]]
    by_guid={r["process_guid"]:r for r in e1}
    children={}
    for r in e1:
        p=r.get("parent_process_guid")
        if p: children.setdefault(p,[]).append(r["process_guid"])
    return by_guid, children, e1

def subtree(root, children):
    seen=set(); stack=list(children.get(root,[]))
    while stack:
        g=stack.pop()
        if g in seen: continue
        seen.add(g); stack+=children.get(g,[])
    return seen

LIFE_SLACK = timedelta(seconds=2)

def build_lifetimes(rows, e1):
    """(host, pid) -> [(start, end|None, guid)] theo ts_system; end = EID5 cung guid, hoac EID1 ke tiep cung PID."""
    end_by_guid={}
    for r in rows:
        if r["event_id"]==5 and r.get("process_guid"):
            t=ts(r.get("ts_system"))
            if t: end_by_guid[r["process_guid"]]=t
    life=defaultdict(list)
    for r in e1:
        t=ts(r.get("ts_system"))
        if t: life[(r["host"],r["process_id"])].append([t,end_by_guid.get(r["process_guid"]),r["process_guid"]])
    for k,v in life.items():
        v.sort(key=lambda x: x[0])
        for i,x in enumerate(v):
            if x[1] is None and i+1<len(v): x[1]=v[i+1][0]
    return life

def pid_to_guid(life, host, pid, when):
    """Tien trinh (host, pid) dang song tai `when` (ts_system); None neu khong co."""
    if when is None: return None
    best=None
    for st,en,g in life.get((host,pid),[]):
        if st-LIFE_SLACK<=when and (en is None or when<=en+LIFE_SLACK): best=g   # lay tien trinh moi nhat
    return best

def is_fragment(r):
    return r.get("channel") is None and r.get("event_id") is None and r.get("record_id") is None

def console_segments(rows, excl_by_host):
    """(host, pid, seg) cua console nguoi van hanh; seg = so lan EID1 cung PID truoc thoi diem do."""
    starts=defaultdict(list)
    for r in rows:
        if r["event_id"]==1 and r["process_id"] is not None and ts(r["ts"]):
            starts[(r["host"],r["process_id"])].append(ts(r["ts"]))
    for k in starts: starts[k].sort()
    def seg(host,pid,t): return bisect_right(starts.get((host,pid),[]),t)
    cons=set()
    for r in rows:
        pid=r["process_id"]; t=ts(r["ts"])
        if pid is None or t is None or pid in excl_by_host.get(r["host"],set()): continue
        txt=(r.get("script_block_text") or "")+"\n"+(r.get("ps_payload") or "")
        if r["event_id"] in (4103,4104) and OPERATOR_RE.search(txt):
            cons.add((r["host"],pid,seg(r["host"],pid,t)))
    return cons, seg

def label(rows, manifests):
    by_guid, children, e1 = build_tree(rows)
    life = build_lifetimes(rows, e1)
    for r in rows:
        r.update(label_malicious=False,label_ttps=[],label_source=None,run_id=None,dropped=False,drop_reason=None,
                 label_version=LABEL_VERSION)

    # manifest theo host, sap xep theo t_start
    man_by_host=defaultdict(list)
    for m in manifests: man_by_host[m["host"]].append(m)
    for h in man_by_host: man_by_host[h].sort(key=lambda m: ts(m["t_start"]))
    excl_by_host=defaultdict(set)
    for m in manifests: excl_by_host[m["host"]] |= set(m.get("exclude_pids",[]))

    # Phan nhom phien theo (host, orchestrator pid): nhieu cua so batch co the chay SONG SONG
    # tren cung host; ranh gioi phien chi xet cac phien cua CUNG orchestrator.
    man_by_orch=defaultdict(list)
    for m in manifests:
        for pid in m.get("exclude_pids",[]): man_by_orch[(m["host"],pid)].append(m)
    for k in man_by_orch: man_by_orch[k].sort(key=lambda m: ts(m["t_start"]))

    def find_session(host, t, pid=None):
        # phien co t_start <= t < t_start phien ke tiep (phien cuoi: den t_end + 10 phut)
        ms=man_by_orch.get((host,pid),[]) if pid is not None else man_by_host.get(host,[])
        for i,m in enumerate(ms):
            st=ts(m["t_start"])
            en=ts(ms[i+1]["t_start"]) if i+1<len(ms) else ts(m["t_end"])+timedelta(seconds=600)
            if st-timedelta(seconds=5) <= t < en: return m
        return None

    # gan moi executor-root (va cay con) vao 1 phien theo thoi diem sinh
    guid_session={}  # guid -> (run_id, kind)  kind in {"exec","harness"}
    for r in e1:
        h=r["host"]; pp=r.get("parent_process_id")
        if pp in excl_by_host.get(h,set()):
            m=find_session(h, ts(r["ts"]), pp)
            if not m: continue
            kind="harness" if r["image_name"] in HARNESS else "exec"
            for gg in [r["process_guid"]]+list(subtree(r["process_guid"],children)):
                # uu tien 'exec' neu da gan; harness khong ghi de exec
                if gg in guid_session and guid_session[gg][1]=="exec": continue
                guid_session[gg]=(m["run_id"], kind)

    # v5: upload manifest (scp/ssh) o bat ky dau -> cay con bi loai, uu tien hon gan phien
    upload_guids=set()
    for r in e1:
        if UPLOAD_RE.search(r.get("command_line") or ""):
            upload_guids |= {r["process_guid"]} | subtree(r["process_guid"],children)
    # v5: console nguoi van hanh + cay con truc tiep (khong ghi de cay phien)
    cons, seg = console_segments(rows, excl_by_host)
    console_child_guids=set()
    for r in e1:
        pp=r.get("parent_process_id"); t=ts(r["ts"])
        if pp is not None and t and (r["host"],pp,seg(r["host"],pp,t)) in cons:
            console_child_guids |= {r["process_guid"]} | subtree(r["process_guid"],children)

    man_by_id={m["run_id"]:m for m in manifests}
    stats={m["run_id"]:dict(run=m["run_id"],cls=m["class"],ttps=m["ttps"],
                            dropped_orch=0,dropped_harness=0,dropped_tool=0,labeled=0,bg=0) for m in manifests}

    def drop_tool(r, reason, h, w):
        r.update(dropped=True,drop_reason=reason,label_source="excluded")
        m=find_session(h,w)
        if m: stats[m["run_id"]]["dropped_tool"]+=1

    for r in rows:
        h=r["host"]; w=ts(r["ts"])
        if w is None: continue
        # 0) manh vo 4103 khong co dinh danh -> loai
        if is_fragment(r):
            drop_tool(r, "ps_fragment", h, w); continue
        g=r.get("process_guid") or (pid_to_guid(life,h,r["process_id"],ts(r.get("ts_system"))) if r["process_id"] is not None else None)
        # 1) event cua chinh orchestrator -> loai (chong ro ri)
        if r["process_id"] in excl_by_host.get(h,set()):
            m=find_session(h,w,r["process_id"])
            r.update(dropped=True,drop_reason="orchestrator",label_source="excluded")
            if m: stats[m["run_id"]]["dropped_orch"]+=1
            continue
        # 1b) upload manifest (scp/ssh) -> loai
        if g in upload_guids:
            drop_tool(r, "harness_upload", h, w); continue
        # 2) thuoc cay con da gan phien?
        if g in guid_session:
            rid,kind=guid_session[g]; m=man_by_id[rid]
            if kind=="harness":
                r.update(dropped=True,drop_reason="art_harness",label_source="excluded")
                stats[rid]["dropped_harness"]+=1
            else:
                r["run_id"]=rid
                if m["class"]=="attack":
                    r.update(label_malicious=True,label_ttps=list(m["ttps"]),label_source="tree_attack")
                else:
                    r.update(label_malicious=False,label_ttps=[],label_source="tree_benign")
                stats[rid]["labeled"]+=1
            continue
        # 2b) console nguoi van hanh (va cay con truc tiep) -> loai
        pid=r["process_id"]
        if (pid is not None and (h,pid,seg(h,pid,w)) in cons) or g in console_child_guids:
            drop_tool(r, "operator_console", h, w); continue
        # 3) nhieu nen -> gan phien theo thoi gian (chi de thong ke)
        m=find_session(h,w)
        if m: stats[m["run_id"]]["bg"]+=1
    return rows, stats

def main():
    norm,mdir,out=sys.argv[1],sys.argv[2],sys.argv[3]
    rows=load(norm)
    manifests=[m for m in (load_manifest(f) for f in glob.glob(os.path.join(mdir,"*.manifest.json"))) if m]
    print(f"Doc {len(manifests)} manifest hop le.", file=sys.stderr)
    rows,stats=label(rows,manifests)
    with open(out,"w",encoding="utf-8") as w:
        for r in rows: w.write(json.dumps(r,ensure_ascii=False)+"\n")
    dr=Counter(r["drop_reason"] for r in rows if r["dropped"])
    print(f"labeler {LABEL_VERSION}: {len(rows)} event, dropped theo ly do: {dict(dr)}", file=sys.stderr)
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
