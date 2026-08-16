#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, tempfile
from pathlib import Path
from typing import Any
import bugsinpy_four_arm as base
import structured_edit_protocol_v2 as sed

T2=("youtube-dl",32)
ARMS=["D_COLD","D_PLUS_O1_COMPILED","D_PLUS_RAW_T1","D_PLUS_SHAM_O1","D_PLUS_SHAM_RAW"]
def sha(s:str)->str:return hashlib.sha256(s.encode()).hexdigest()

def parse_exact(text:str, prior_sha:str|None):
    obj=sed._json_object(text)
    alts=obj.get("alternatives")
    if not isinstance(alts,list): return [],None
    seen=set(); rows=[]; selected=None
    for rank,alt in enumerate(alts[:3],1):
        r={"rank":rank}
        try:
            if not isinstance(alt,dict): raise ValueError("not object")
            p=sed.extract_edits(json.dumps({"edits":alt.get("edits")},ensure_ascii=False)); h=sha(p)
            dup1=prior_sha is not None and h==prior_sha; dupe=h in seen; seen.add(h)
            r.update(status="VALID",payload=p,payload_sha256=h,duplicates_call1=dup1,duplicates_earlier=dupe)
            if selected is None and not dup1 and not dupe:
                selected={"rank":rank,"payload":p,"payload_sha256":h}; r["selected"]=True
            else:r["selected"]=False
        except Exception as e:r.update(status="INVALID",error=f"{type(e).__name__}: {e}")
        rows.append(r)
    return rows,selected

def paths(payloads):
    out=set()
    for p in payloads:
        for e in json.loads(p)["edits"]:out.add(e["path"])
    return out

def load(work,ps):
    return {r:((work/r).read_text(encoding="utf-8") if (work/r).is_file() else None) for r in ps}
def sim(st0,p):
    st=dict(st0)
    for i,e in enumerate(json.loads(p)["edits"],1):
        t=st.get(e["path"])
        if t is None:return False,{"edit_index":i,"path":e["path"],"reason":"MISSING_FILE","old_count":None}
        n=t.count(e["old"])
        if n!=1:return False,{"edit_index":i,"path":e["path"],"reason":"OLD_COUNT_NOT_ONE","old_count":n,"old_sha256":sha(e["old"])}
        st[e["path"]]=t.replace(e["old"],e["new"],1)
    return True,None

def main():
    a=argparse.ArgumentParser();a.add_argument("--v154-result",type=Path,required=True);a.add_argument("--bugsinpy",type=Path,required=True);a.add_argument("--out",type=Path,required=True);x=a.parse_args()
    if x.out.exists():raise SystemExit("output exists")
    x.out.mkdir(parents=True)
    b=x.v154_result.read_bytes(); src=json.loads(b)
    res={"canonical_id":"V154B_EXACT_PARSER_ACTUAL_STATE_RIVAL_AUDIT","protocol":"protocols/V154B_EXACT_PARSER_ACTUAL_STATE_RIVAL_AUDIT.md","source_v154_sha256":hashlib.sha256(b).hexdigest(),"model_calls":0,"verifier_calls":0,"rows":[]}
    if res["source_v154_sha256"]!="bb076d3f18d6eddd78b8093fb392280c012c9b69f526856bbb0e114abf8f2881":
        res.update(verdict="R10_DIAGNOSTIC_INCONCLUSIVE",reason="source hash mismatch"); return finish(x.out,res)
    missed=mixed=actual_exec=valid=pm=0
    for arm in ARMS:
      for rr in src.get("rows",{}).get(arm,[]):
        seed=rr.get("seed"); ats=rr.get("attempts",[]); c1=next((z for z in ats if z.get("call")==1),None); c2=next((z for z in ats if z.get("call")==2),None)
        row={"arm":arm,"seed":seed,"alternatives":[]}
        if not c2 or not isinstance((c2.get("response")or{}).get("text"),str): row["status"]="NO_CALL2";res["rows"].append(row);continue
        c1p=None; c1ap=bool(c1 and isinstance(c1.get("verdict"),dict))
        if c1ap:c1p=sed.extract_edits(c1["response"]["text"])
        prior=sha(c1p) if c1p else None
        try: alts,sel=parse_exact(c2["response"]["text"],prior)
        except Exception as e: row.update(status="PARSE_ERROR",error=f"{type(e).__name__}: {e}");res["rows"].append(row);continue
        rec_rank=c2.get("selected_rank"); rec_sha=c2.get("selected_payload_sha256")
        if (sel.get("rank") if sel else None)!=rec_rank or (sel.get("payload_sha256") if sel else None)!=rec_sha:
            pm+=1;row["parser_replay_mismatch"]={"recomputed_rank":sel.get("rank") if sel else None,"recorded_rank":rec_rank,"recomputed_sha":sel.get("payload_sha256") if sel else None,"recorded_sha":rec_sha}
        ps=[q["payload"] for q in alts if q.get("status")=="VALID"]+([c1p] if c1p else [])
        with tempfile.TemporaryDirectory(prefix=f"v154b-{arm}-{seed}-") as td:
            work=base.checkout_buggy(x.bugsinpy,T2[0],T2[1],Path(td)); clean=load(work,paths(ps))
        actual=dict(clean)
        if c1p:
            ok,fail=sim(actual,c1p)
            if not ok: res.update(verdict="R10_DIAGNOSTIC_INCONCLUSIVE",reason=f"call1 reconstruction {arm}/{seed}: {fail}");return finish(x.out,res)
            for e in json.loads(c1p)["edits"]:actual[e["path"]]=actual[e["path"]].replace(e["old"],e["new"],1)
        nonsel=False; selected_actual=None
        for q in alts:
            ar={k:v for k,v in q.items() if k!="payload"}
            if q.get("status")=="VALID":
                valid+=1; cok,cf=sim(clean,q["payload"]); aok,af=sim(actual,q["payload"]); ar.update(clean_applies=cok,clean_failure=cf,actual_applies=aok,actual_failure=af)
                if aok and not q.get("duplicates_call1"): actual_exec+=1
                if aok and not q.get("selected") and not q.get("duplicates_call1"):nonsel=True
                if q.get("selected"):selected_actual=aok
                if (not aok) and cok and c1ap:mixed+=1
            row["alternatives"].append(ar)
        reached=isinstance(c2.get("verdict"),dict)
        if not reached and nonsel: missed+=1;row["missed_executable_rival"]=True
        else:row["missed_executable_rival"]=False
        row.update(actual_state="POST_CALL1" if c1ap else "CLEAN",recorded_selected_rank=rec_rank,recorded_selected_sha=rec_sha,selected_reached_verifier=reached,status="AUDITED")
        res["rows"].append(row)
    res["summary"]={"valid_projected_alternatives":valid,"actual_state_executable_alternatives":actual_exec,"missed_executable_rival_arm_seeds":missed,"clean_only_while_actual_post_call1":mixed,"parser_replay_mismatches":pm}
    if pm:v="R10_V154_PARSER_REPLAY_MISMATCH"
    elif missed:v="DIAGNOSTIC_V154_SELECTION_POLICY_MISSES_EXECUTABLE_RIVAL"
    elif mixed:v="DIAGNOSTIC_V154_STATE_SEMANTICS_STILL_MIXED"
    elif valid and actual_exec==0:v="DIAGNOSTIC_V154_CANDIDATE_SET_NOT_EXECUTABLE_ON_ACTUAL_STATE"
    elif actual_exec:v="DIAGNOSTIC_V154_EXECUTABLE_RIVALS_EXIST_BUT_NO_SELECTION_MISS"
    else:v="R10_DIAGNOSTIC_INCONCLUSIVE"
    res["verdict"]=v;finish(x.out,res)
def finish(out,res):
    p=out/"V154B_RESULT.json";p.write_text(json.dumps(res,indent=2,sort_keys=True)+"\n");print(p.read_text())
if __name__=="__main__":main()
