#!/usr/bin/env python3
# VT-Guard labeler v2
# Gan nhan event da chuan hoa (normalize.py) theo manifest + cay tien trinh Sysmon EID1.
# Nguyen tac:
#   - Loai event cua chinh orchestrator (exclude_pids)            -> chong ro ri NHAN.
#   - Loai harness ART (hostname/whoami/conhost la con truc tiep  -> chong ro ri DAU VET CONG CU
#     cua orchestrator) cung cay con cua chung.                      (model khong hoc "ART fingerprint").
#   - Gan nhan cho event cua cac cay con EXECUTOR con lai trong cua so phien.
#   - Nhan o MUC CUA SO/PHIEN: label_ttps = tap TTP cua phien (multi-label), khong co gang
#     gan tung TTP cho tung event (vi 1 atomic chay nhieu lenh, gan theo thoi gian khong dang tin).
# Chay: python label.py <norm.jsonl> <manifests_dir> <out.jsonl>
import json, sys, glob, os
from datetime import datetime, timedelta

HARNESS = {"conhost.exe","hostname.exe","whoami.exe"}  # dau vet khung ART, khong phai TTP trong pham vi

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

def orch_guids(e1, exclude_pids, host, t0, t1):
    lo=t0-timedelta(seconds=300); hi=t1+timedelta(seconds=5); out=set()
    for r in e1:
        if r["host"]==host and r["process_id"] in exclude_pids:
            st=ts(r["ts"])
            if st and lo<=st<=hi: out.add(r["process_guid"])
    return out

def pid_to_guid(e1, host, pid, when, tol=180):
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
    stats={}
    for m in manifests:
        t0,t1=ts(m["t_start"]),ts(m["t_end"]); host=m["host"]; exclude=set(m.get("exclude_pids",[]))
        orch=orch_guids(e1, exclude, host, t0, t1)
        # harness = con truc tiep cua orchestrator co image trong HARNESS
        harness=set()
        for g in orch:
            for cg in children.get(g,[]):
                cr=by_guid.get(cg)
                if cr and (cr["image_name"] in HARNESS):
                    harness.add(cg); harness|=subtree(cg, children)
        # tap executor = cay con orchestrator, TRU harness
        atk=set()
        for g in orch: atk|=subtree(g, children)
        atk-=harness
        st=dict(run=m["run_id"],cls=m["class"],ttps=m["ttps"],dropped_orch=0,dropped_harness=0,labeled=0,bg=0)
        for r in rows:
            if r["host"]!=host: continue
            w=ts(r["ts"])
            if w is None or not (t0<=w<=t1): continue
            g=r.get("process_guid") or (pid_to_guid(e1,host,r["process_id"],w) if r["process_id"] is not None else None)
            if (r["process_id"] in exclude) or (g in orch):
                r.update(dropped=True,drop_reason="orchestrator",label_source="excluded"); st["dropped_orch"]+=1; continue
            if g in harness:
                r.update(dropped=True,drop_reason="art_harness",label_source="excluded"); st["dropped_harness"]+=1; continue
            if g in atk:
                r["run_id"]=m["run_id"]
                if m["class"]=="attack":
                    r.update(label_malicious=True,label_ttps=list(m["ttps"]),label_source="tree_attack")
                else:
                    r.update(label_malicious=False,label_ttps=[],label_source="tree_benign")
                st["labeled"]+=1
            else:
                st["bg"]+=1
        stats[m["run_id"]]=st
    return rows, stats

def main():
    norm,mdir,out=sys.argv[1],sys.argv[2],sys.argv[3]
    rows=load(norm)
    manifests=[json.load(open(f)) for f in glob.glob(os.path.join(mdir,"*.manifest.json"))]
    rows,stats=label(rows,manifests)
    with open(out,"w",encoding="utf-8") as w:
        for r in rows: w.write(json.dumps(r,ensure_ascii=False)+"\n")
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
