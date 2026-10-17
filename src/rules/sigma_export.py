#!/usr/bin/env python3
"""VT-Guard Buoc 7 moc 2 - xuat Sigma (rules/sigma/<id>.yml) cho luat da duyet + validate bang pySigma.

Doc reports/step7/rules_provenance.json (CHI luat qua cong; khong doc tap test). Moi atom -> mot selection tren MOT event
process_creation (moi token cua luat chi khop o Sysmon EID 1 / Security 4688 tren Train):
  image=X        -> Image|endswith: '\\X'
  cmd~'T'        -> CommandLine|re: '(?i)(^|[^a-z0-9_.<>/\\-])T($|[^a-z0-9_.<>/\\-])'  (bien token = TOK_RE, khong khop System32)
  image=X & cmd~ -> ca hai trong CUNG selection (cung event)
Luat 1 atom -> mot luat Sigma. Luat nhieu atom (cac atom co the o event khac nhau) -> moi atom mot luat con (co `name`) +
mot luat correlation `type: temporal` (group-by Computer, timespan 1m; tren Train hai event cach nhau <= 0.07 s),
`generate: false`: luat con KHONG sinh truy van/canh bao rieng (spec Sigma correlation; pySigma disable_output).
Moi file co custom field `vtguard_provenance` tro ve reports/step7/rules_provenance.json.
Chay: python src/rules/sigma_export.py
"""
import json, os, re, sys, uuid
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../eval", "../dataset"): sys.path.insert(0, os.path.join(HERE, d))

OUT_DIR = os.path.join("rules", "sigma")
PROV = os.path.join("reports", "step7", "rules_provenance.json")
TOKCLS = r"a-z0-9_.<>/\\-"
TACTIC = {"T1016": "discovery", "T1018": "discovery", "T1087.002": "discovery", "T1654": "discovery", "T1003.003": "credential-access"}
NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/kaitokidc500/VT-Guard-2/rules")
DATE = "2026-10-17"
TIMESPAN = "1m"

def token_regex(t):
    # bien phai them \\" : log Wazuh giu dau nhay escape (\"Domain controllers\"); norm_cmd bo ca hai -> cung ranh gioi token
    return f"(?i)(^|[^{TOKCLS}]){re.escape(t)}($|[^{TOKCLS}]|\\\\\")"

def q(s):
    """YAML chuoi nhay don (khong escape backslash)."""
    return "'" + str(s).replace("'", "''") + "'"

def selection(atom):
    k, v = atom[0], atom[1]
    if k == "img": return [f"        Image|endswith: {q(chr(92) + v)}"]
    if k == "tok": return [f"        CommandLine|re: {q(token_regex(v))}"]
    if k == "imgtok": return [f"        Image|endswith: {q(chr(92) + v[0])}", f"        CommandLine|re: {q(token_regex(v[1]))}"]
    if k == "eid": return [f"        EventID: {int(v)}"]
    raise ValueError(k)

def tags_for(r, ttps_of):
    if r["target"] != "bin": ts = [r["target"]]
    else:                      # luat nhi phan: TTP chiem >= 50% cua so TP tren Train
        c = Counter(t for w in r["support_true_positive_windows"] for t in ttps_of[w]); n = len(r["support_true_positive_windows"])
        ts = sorted(t for t, x in c.items() if x / n >= 0.5)
    tac = sorted({TACTIC[t] for t in ts})
    return [f"attack.{a}" for a in tac] + [f"attack.{t.lower()}" for t in ts], ts

def prov_block(r, extra=None):
    o = r["oof"]; tr = r["train"]
    L = ["vtguard_provenance:", f"    rule_id: {r['id']}", f"    target: {q(r['target'])}", f"    provenance_file: {q(PROV.replace(os.sep, '/'))}",
         "    dataset: dataset-v1.2", "    induced_from: Train only (483 windows)", f"    engine: {q(r['source']['engine'])}",
         f"    train_support: {tr['support']}", f"    train_precision: {tr['precision']}", f"    oof_precision: {o['precision']}",
         f"    oof_windows: {o['tp'] + o['fp']}", f"    folds_rediscovered: {len(o['folds_rediscovered'])}",
         f"    window_semantics: {q('fires on a window (<= 64 events of one session) if every predicate matches >= 1 event')}"]
    if extra: L += [f"    {k}: {q(v)}" for k, v in extra.items()]
    return L

def single_rule(r, atom, title, rid, tags, ttps, name=None, sub=False):
    tr = r["train"]; o = r["oof"]
    desc = (f"VT-Guard auto-induced rule {r['id']} (RIPPER on Train, dataset-v1.2). Target: {r['target']}"
            + (f" ({', '.join(ttps)})" if ttps else "") + f". Train support {tr['support']} windows (precision {tr['precision']}), "
            f"OOF precision {o['precision']} on {o['tp'] + o['fp']} windows. Predicate: {' AND '.join(r['predicates'])}.")
    if sub: desc = f"Sub-rule of correlation {r['id']}: predicate {atom_txt(atom)}. " + desc
    L = [f"title: {q(title)}", f"id: {rid}"] + ([f"name: {name}"] if name else []) + [
        "status: experimental", f"description: {q(desc)}", "author: VT-Guard auto rule engine", f"date: {DATE}",
        "tags:"] + [f"    - {t}" for t in tags] + [
        "logsource:", "    category: process_creation", "    product: windows",
        "detection:", "    selection:"] + selection(atom) + ["    condition: selection",
        "fields:", "    - Image", "    - CommandLine", "    - ParentImage", "    - User", "    - Computer",
        "falsepositives:", "    - Administrative scripts running the same discovery / maintenance commands (see T-hard evaluation)",
        "level: medium" if r["target"] == "bin" else "level: high"] + ([] if sub else prov_block(r))
    return L

def atom_txt(a):
    k, v = a[0], a[1]
    return {"img": f"image={v}", "tok": f"cmd~{v}", "eid": f"event_id={v}"}.get(k, f"image={v[0]} & cmd~{v[1]}" if k == "imgtok" else str(a))

def export(root="."):
    P = json.load(open(os.path.join(root, PROV), encoding="utf-8"))
    from evaluate import load_meta
    ttps_of = {w["window_id"]: w["window_ttps"] for w in load_meta(root, "train")}
    os.makedirs(os.path.join(root, OUT_DIR), exist_ok=True)
    files = []
    for r in P["rules"]:
        atoms = [(a[0], tuple(a[1]) if a[0] == "imgtok" else a[1]) for a in r["atoms"]]
        tags, ttps = tags_for(r, ttps_of)
        rid = str(uuid.uuid5(NS, r["id"]))
        if len(atoms) == 1:
            doc = single_rule(r, atoms[0], f"VT-Guard {r['id']}: {' AND '.join(r['predicates'])}", rid, tags, ttps)
            text = "\n".join(doc) + "\n"
        else:
            docs, names = [], []
            for i, a in enumerate(atoms):
                nm = f"vtguard_{r['id'].lower().replace('-', '_')}_p{i + 1}"; names.append(nm)
                docs.append("\n".join(single_rule(r, a, f"VT-Guard {r['id']} part {i + 1}: {atom_txt(a)}", str(uuid.uuid5(NS, r["id"] + nm)),
                                                  tags, ttps, name=nm, sub=True)))
            corr = [f"title: {q('VT-Guard ' + r['id'] + ': ' + ' AND '.join(r['predicates']))}", f"id: {rid}", "status: experimental",
                    f"description: {q('VT-Guard auto-induced rule ' + r['id'] + ': all predicates within one session window (temporal correlation). Train: on 10/10 matched windows the two events are <= 0.07 s apart.')}",
                    "author: VT-Guard auto rule engine", f"date: {DATE}", "tags:"] + [f"    - {t}" for t in tags] + [
                    "correlation:", "    type: temporal", "    generate: false", "    rules:"] + [f"        - {n}" for n in names] + [
                    "    group-by:", "        - Computer", f"    timespan: {TIMESPAN}",
                    "falsepositives:", "    - Administrative scripts running the same discovery commands", "level: high"] + prov_block(r, {"timespan_note": f"{TIMESPAN} (Train gap <= 0.07 s)"})
            text = "\n---\n".join(docs + ["\n".join(corr)]) + "\n"
        fp = os.path.join(root, OUT_DIR, f"{r['id']}.yml")
        with open(fp, "w", encoding="ascii", newline="\n") as f: f.write(text)
        files.append(fp)
    return files

def validate(files):
    """pySigma: parse (SigmaCollection, ca correlation) + 31 validator mac dinh. Tra {file: {errors, issues}}."""
    from sigma.collection import SigmaCollection
    from sigma.validation import SigmaValidator
    from sigma.validators.core import validators
    import importlib.metadata as md
    V = SigmaValidator(validators.values())
    out = {}
    for f in files:
        c = SigmaCollection.from_yaml(open(f, encoding="ascii").read(), collect_errors=True)
        c.resolve_rule_references()
        errs = [str(e) for r in c.rules for e in getattr(r, "errors", [])] + [str(e) for e in getattr(c, "errors", [])]
        issues = Counter(type(i).__name__ for i in V.validate_rules(c))
        out[os.path.basename(f)] = {"n_documents": len(c.rules), "errors": errs, "validator_issues": dict(issues)}
    return {"tool": f"pySigma {md.version('pysigma')} (SigmaCollection + {len(validators)} validator mac dinh)", "files": out}

if __name__ == "__main__":
    fs = export("."); v = validate(fs)
    os.makedirs(os.path.join("reports", "step7"), exist_ok=True)
    with open(os.path.join("reports", "step7", "sigma_validation.json"), "w", encoding="utf-8", newline="\n") as f: json.dump(v, f, indent=1)
    print(v["tool"])
    for k, x in v["files"].items(): print(f"  {k}: {x['n_documents']} doc, loi {len(x['errors'])}, validator {x['validator_issues'] or 'sach'}")
