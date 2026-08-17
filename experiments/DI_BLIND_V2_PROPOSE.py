#!/usr/bin/env python3
import hashlib, json, os, re
from pathlib import Path
import river_client as river

BASE="Qwen/Qwen3.5-9B"; SEED=20260819; N=16; MAX_TOKENS=2200; TEMPERATURE=0.7
ROOT=Path("checker"); EXPOSED=Path("blind-di-v2/exposed.ndjson"); BASELINE=Path("blind-di-v2/exposed_baseline.json"); OUT=Path("blind-di-v2/candidates.json")
MAX_SOURCE=100_000; MAX_OLD_LINES=40; MAX_NEW_LINES=80; MAX_NEW_CHARS=12_000

def numbered(txt):
    return "\n".join(f"{i:05d}: {line}" for i,line in enumerate(txt.splitlines(),1))

def bundle_source():
    files=sorted((ROOT/"kernel").rglob("*.vow")); rows=[]; allowed=[]; total=0
    for p in files:
        txt=p.read_text(errors="replace"); rel=str(p.relative_to(ROOT)); chunk=f"\n===== FILE {rel} =====\n{numbered(txt)}\n"
        if total+len(chunk)>MAX_SOURCE: break
        rows.append(chunk); allowed.append(rel); total+=len(chunk)
    if not rows: raise SystemExit("no allowed source files")
    return "".join(rows),allowed

def extract_json(text):
    text=text.strip(); blocks=[text]
    blocks+=re.findall(r"```(?:json)?\s*(\{.*?\})\s*```",text,flags=re.S|re.I)
    a=text.find("{"); b=text.rfind("}")
    if a>=0 and b>a: blocks.append(text[a:b+1])
    for block in blocks:
        try:
            obj=json.loads(block)
            if isinstance(obj,dict): return obj
        except Exception: pass
    return None

def admissible(obj,allowed):
    need={"path","start_line","end_line","new_text"}
    if not isinstance(obj,dict): return False,"not_object"
    if need-set(obj): return False,"missing_fields"
    path=str(obj.get("path","")); new=str(obj.get("new_text",""))
    if path not in allowed: return False,"path_outside_allowed_surface"
    try: start=int(obj["start_line"]); end=int(obj["end_line"])
    except Exception: return False,"line_not_integer"
    lines=(ROOT/path).read_text(errors="replace").splitlines()
    if start<1 or end<start or end>len(lines): return False,"line_range_out_of_bounds"
    if end-start+1>MAX_OLD_LINES: return False,"too_many_replaced_lines"
    if len(new)>MAX_NEW_CHARS: return False,"replacement_too_large"
    if len(new.splitlines())>MAX_NEW_LINES: return False,"too_many_replacement_lines"
    old="\n".join(lines[start-1:end])
    if new.rstrip("\n")==old.rstrip("\n"): return False,"noop_edit"
    return True,"ok"

def main():
    key=os.environ.get("RIVER_API_KEY")
    if not key: raise SystemExit("RIVER_API_KEY is required")
    source,allowed=bundle_source(); case=EXPOSED.read_text(errors="replace"); baseline=json.loads(BASELINE.read_text())
    prompt=f'''You are the autonomous repair proposer in a preregistered blind software experiment.

You receive ONE naturally selected failing case and frozen source from an independent Lean proof checker. Protected cases exist but are physically unavailable to you. Infer a principled source-level correction only from the supplied evidence.

Return STRICT JSON only:
{{"hypothesis":"...","path":"kernel/...vow","start_line":123,"end_line":125,"new_text":"replacement source text"}}

Rules:
- Exactly one file and one inclusive line range may be replaced.
- The path must be in ALLOWED FILES.
- Replace at most {MAX_OLD_LINES} existing lines with at most {MAX_NEW_LINES} lines / {MAX_NEW_CHARS} characters.
- Line numbers are the 1-based numbers printed in FROZEN SOURCE, local to each file.
- Do not edit tests, harnesses, build scripts, or the input.
- No target-specific repair primitive or diagnosis has been supplied.
- Prefer a semantic/representation correction that could generalize, not a testcase special-case.
- `new_text` must contain the complete replacement for the selected line range.

ALLOWED FILES:
{json.dumps(allowed)}

BASELINE RESULT:
{json.dumps(baseline,indent=2)}

EXPOSED CASE:
{case}

FROZEN SOURCE:
{source}
'''
    prompt_sha=hashlib.sha256(prompt.encode()).hexdigest(); client=river.Client(api_key=key,timeout=240.0)
    if not client.health_check(): raise SystemExit("River health check failed")
    prompts=[prompt+f"\nIndependent candidate {i+1}/{N}. Diagnose afresh and return one JSON object only.\n" for i in range(N)]
    with client.session(project="di-blind-v2-linepatch") as s:
        model=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=8,seed=SEED))
        generations=model.sample(prompts=prompts,max_tokens=MAX_TOKENS,temperature=TEMPERATURE)
    rows=[]
    for i,gs in enumerate(generations):
        text=gs[0].text if gs else ""; obj=extract_json(text); ok,reason=admissible(obj,set(allowed))
        rows.append({"index":i,"raw_sha256":hashlib.sha256(text.encode()).hexdigest(),"raw":text,"parsed":obj,"admissible":ok,"admissibility_reason":reason})
    result={"protocol":"DI_BLIND_V2_AUTONOMOUS_CONSTRUCTION","base_model":BASE,"base_weight_updates":0,"seed":SEED,"candidate_count":N,"temperature":TEMPERATURE,"max_tokens":MAX_TOKENS,"prompt_sha256":prompt_sha,"allowed_files":allowed,"patch_schema":"single_line_range_replacement_v1","admissible_count":sum(r["admissible"] for r in rows),"candidates":rows}
    OUT.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="candidates"},indent=2))
    for r in rows: print("CANDIDATE",r["index"],"ADMISSIBLE",r["admissible"],r["admissibility_reason"],r["raw_sha256"])

if __name__=="__main__": main()
