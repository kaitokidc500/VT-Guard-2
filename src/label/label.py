#!/usr/bin/env python3
# VT-Guard labeler v4 (ho tro nhieu orchestrator chay song song tren cung host)
# Gan nhan event da chuan hoa (normalize.py) theo manifest + cay tien trinh Sysmon EID1.
# Nguyen tac:
#   - Orchestrator = tien trinh chay Invoke-VTSession/Batch (pid in exclude_pids). Event cua no -> LOAI (chong ro ri NHAN).
#   - Executor-root = con truc tiep cua orchestrator (EID1 co parent_process_id in exclude_pids).
#       Gan tung root vao PHIEN theo THOI DIEM sinh ra (dung moc bat dau cac phien lam ranh gioi),
#       KHONG loc tung event theo [t_start,t_end] (chong tre log + phien sat nhau).
#   - Harness ART (hostname/whoami/conhost la executor-root) + cay con cua chung -> LOAI (chong ro ri DAU VET CONG CU).
#   - Cac executor-root con lai + cay con -> gan nhan theo class phien (attack: label_ttps = ttps cua phien).
#   - Nhan o MUC CUA SO/PHIEN (multi-label), khong gan tung TTP cho tung event.
# Chay: python label.py <norm.jsonl> <manifests_dir> <out.jsonl>
import json, sys, glob, os
from collections import defaultdict
from datetime import datetime, timedelta

HARNESS = {"conhost.exe","hostname.exe","whoami.exe"}

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

def pid_to_guid(e1, host, pid, when, tol=300):
    best=None; bd=None
    for r in e1:
        if r["host"]==host and r["process_id"]==pid:
            st=ts(r["ts"])
            if st is None: continue
            dt=abs((when-st).total_seconds())
            if dt<=tol and (bd is None or dt<bd): best=r["process_guid"]; bd=dt
    return best

def label(rows, manifests):
    by_guid, children, e1 = build_tree(rows)
    for r in rows:
        r.update(label_malicious=False,label_ttps=[],label_source=None,run_id=None,dropped=False,drop_reason=None)

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

    man_by_id={m["run_id"]:m for m in manifests}
    stats={m["run_id"]:dict(run=m["run_id"],cls=m["class"],ttps=m["ttps"],
                            dropped_orch=0,dropped_harness=0,labeled=0,bg=0) for m in manifests}

    for r in rows:
        h=r["host"]; w=ts(r["ts"])
        if w is None: continue
        g=r.get("process_guid") or (pid_to_guid(e1,h,r["process_id"],w) if r["process_id"] is not None else None)
        # 1) event cua chinh orchestrator -> loai (chong ro ri)
        if r["process_id"] in excl_by_host.get(h,set()):
            m=find_session(h,w,r["process_id"])
            r.update(dropped=True,drop_reason="orchestrator",label_source="excluded")
            if m: stats[m["run_id"]]["dropped_orch"]+=1
            continue
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
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
