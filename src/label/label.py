#!/usr/bin/env python3
# VT-Guard labeler v1
# Gan nhan event da chuan hoa (normalize.py) theo manifest + cay tien trinh Sysmon EID1.
# Nguyen tac:
#   - Loai event cua chinh orchestrator (process_id in exclude_pids) -> chong ro ri nhan.
#   - Gan nhan TTP cho event cua cac tien trinh LA CON CHAU cua orchestrator trong cua so phien.
#   - Event benign/nen: label_malicious=false, label_ttps=[].
# Chay: python label.py <norm.jsonl> <manifests_dir> <out.jsonl>
import json, sys, glob, os
from datetime import datetime, timedelta

def ts(s):
    if not s: return None
    s=s.replace("Z","+00:00")
    # cat micro giay toi 6 chu so
    if "." in s:
        head,rest=s.split(".",1)
        digs="".join(c for c in rest if c.isdigit())[:6]
        tz=rest[len(digs):] if not rest[len(digs):].startswith("+") else rest[len(digs):]
        off=rest[rest.find("+"):] if "+" in rest else "+00:00"
        s=f"{head}.{digs}{off}"
    return datetime.fromisoformat(s)

def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]

def build_tree(rows):
    # Sysmon EID1: guid -> row, va guid -> list con
    e1=[r for r in rows if r["event_id"]==1 and r["process_guid"]]
    by_guid={r["process_guid"]:r for r in e1}
    children={}
    for r in e1:
        p=r.get("parent_process_guid")
        if p: children.setdefault(p,[]).append(r["process_guid"])
    return by_guid, children, e1

def descendants(root_guid, children):
    seen=set(); stack=list(children.get(root_guid,[]))
    while stack:
        g=stack.pop()
        if g in seen: continue
        seen.add(g); stack+=children.get(g,[])
    return seen

def orchestrator_guids(e1, exclude_pids, host, t0, t1, pad=5):
    # tim process guid cua orchestrator: Sysmon EID1 co process_id in exclude_pids,
    # tren dung host, khoi tao gan cua so phien
    lo=t0-timedelta(seconds=300); hi=t1+timedelta(seconds=pad)
    out=set()
    for r in e1:
        if r["host"]==host and r["process_id"] in exclude_pids:
            st=ts(r["ts"])
            if st and lo<=st<=hi: out.add(r["process_guid"])
    return out

def pid_to_guid_at(rows_e1, host, pid, when, tol=120):
    # map (host,pid,time) -> process_guid gan nhat (cho 4688/PowerShell khong co guid)
    best=None; bestdt=None
    for r in rows_e1:
        if r["host"]==host and r["process_id"]==pid:
            st=ts(r["ts"])
            if st is None: continue
            dt=abs((when-st).total_seconds())
            if dt<=tol and (bestdt is None or dt<bestdt):
                best=r["process_guid"]; bestdt=dt
    return best

def label(rows, manifests):
    by_guid, children, e1 = build_tree(rows)
    # khoi tao nhan mac dinh
    for r in rows:
        r["label_malicious"]=False; r["label_ttps"]=[]; r["label_source"]=None; r["run_id"]=None; r["dropped"]=False
    stats={}
    for m in manifests:
        t0,t1=ts(m["t_start"]),ts(m["t_end"])
        host=m["host"]; exclude=set(m.get("exclude_pids",[]))
        orch=orchestrator_guids(e1, exclude, host, t0, t1)
        # tap guid cua cay con orchestrator (KHONG gom orchestrator)
        atk=set()
        for g in orch: atk|=descendants(g, children)
        st={"run":m["run_id"],"class":m["class"],"ttps":m["ttps"],"dropped":0,"labeled":0,"benign_in_win":0}
        for r in rows:
            if r["host"]!=host: continue
            w=ts(r["ts"])
            if w is None or not (t0<=w<=t1): continue
            # xac dinh guid cua event
            g=r.get("process_guid")
            if not g and r["process_id"] is not None:
                g=pid_to_guid_at(e1, host, r["process_id"], w)
            # 1) loai event cua chinh orchestrator (ro ri)
            if (r["process_id"] in exclude) or (g in orch):
                r["dropped"]=True; r["label_source"]="excluded_orchestrator"; st["dropped"]+=1; continue
            # 2) event cua cay con orchestrator -> gan nhan phien
            if g in atk:
                r["run_id"]=m["run_id"]
                if m["class"]=="attack":
                    r["label_malicious"]=True; r["label_ttps"]=list(m["ttps"]); r["label_source"]="tree_attack"
                else:
                    r["label_malicious"]=False; r["label_ttps"]=[]; r["label_source"]="tree_benign"
                st["labeled"]+=1
            else:
                st["benign_in_win"]+=1  # nhieu nen trong cua so, giu benign
        stats[m["run_id"]]=st
    return rows, stats

def main():
    norm, mdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
    rows=load(norm)
    manifests=[json.load(open(f)) for f in glob.glob(os.path.join(mdir,"*.manifest.json"))]
    rows, stats = label(rows, manifests)
    with open(out,"w",encoding="utf-8") as w:
        for r in rows: w.write(json.dumps(r,ensure_ascii=False)+"\n")
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
