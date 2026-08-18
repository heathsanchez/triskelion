#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
import hashlib
import json

MASK = 0xFF
ROWS = list(product((0, 1), repeat=3))
HEADLINE_SEED = "METALOGIC_EFFECTIVE_LANGUAGE_EXPANSION_V1"
SWEEP_PREFIX = "METALOGIC_DEVELOPMENTAL_LOOP_CAPSTONE_V1"

def truth_table(fn):
    out=0
    for i,args in enumerate(ROWS): out |= (fn(*args)&1)<<i
    return out
ZERO=0; ONE=MASK; X=truth_table(lambda x,y,z:x); Y=truth_table(lambda x,y,z:y); Z=truth_table(lambda x,y,z:z)
BASE={ZERO:"0",ONE:"1",X:"x",Y:"y",Z:"z"}
def bnot(a): return a^MASK
def bxor(a,b): return a^b
def band(a,b): return a&b
def bit(v,row): return (v>>row)&1

def apply3(k,a,b,c):
    out=0
    for idx,(av,bv,cv) in enumerate(ROWS):
        if bit(k,idx):
            out |= (a if av else bnot(a)) & (b if bv else bnot(b)) & (c if cv else bnot(c))
    return out

@dataclass(frozen=True)
class Expr:
    size:int; text:str; sem:int

def exact_l0_closure():
    s=set(BASE); changed=True
    while changed:
        changed=False
        for a in list(s):
            v=bnot(a)
            if v not in s: s.add(v); changed=True
        for a in list(s):
            for b in list(s):
                v=bxor(a,b)
                if v not in s: s.add(v); changed=True
    return s

def enumerate_u(max_size):
    best={v:Expr(1,t,v) for v,t in BASE.items()}; by={1:set(BASE)}
    for size in range(2,max_size+1):
        vals=set()
        if size-1 in by:
            for a in sorted(by[size-1]):
                v=bnot(a); t=f"~({best[a].text})"
                if v not in best: best[v]=Expr(size,t,v); vals.add(v)
                elif (size,t)<(best[v].size,best[v].text): best[v]=Expr(size,t,v)
        for s1 in range(1,size-1):
            s2=size-1-s1
            if s1 not in by or s2 not in by: continue
            for a in sorted(by[s1]):
                for b in sorted(by[s2]):
                    for sym,op in (("^",bxor),("&",band)):
                        v=op(a,b); t=f"({best[a].text}{sym}{best[b].text})"
                        if v not in best: best[v]=Expr(size,t,v); vals.add(v)
                        elif (size,t)<(best[v].size,best[v].text): best[v]=Expr(size,t,v)
        by[size]=vals
    return best

def enumerate_installed(k,max_size):
    best={v:Expr(1,t,v) for v,t in BASE.items()}; by={1:set(BASE)}
    for size in range(2,max_size+1):
        vals=set()
        if size-1 in by:
            for a in sorted(by[size-1]):
                v=bnot(a); t=f"~({best[a].text})"
                if v not in best: best[v]=Expr(size,t,v); vals.add(v)
        for s1 in range(1,size-1):
            s2=size-1-s1
            if s1 in by and s2 in by:
                for a in sorted(by[s1]):
                    for b in sorted(by[s2]):
                        v=bxor(a,b); t=f"({best[a].text}^{best[b].text})"
                        if v not in best: best[v]=Expr(size,t,v); vals.add(v)
        for s1 in range(1,size-2):
            for s2 in range(1,size-1-s1):
                s3=size-1-s1-s2
                if s1 not in by or s2 not in by or s3 not in by: continue
                for a in sorted(by[s1]):
                    for b in sorted(by[s2]):
                        for c in sorted(by[s3]):
                            v=apply3(k.sem,a,b,c); t=f"K({best[a].text},{best[b].text},{best[c].text})"
                            if v not in best: best[v]=Expr(size,t,v); vals.add(v)
        by[size]=vals
    return best

def rk(prefix,v): return hashlib.sha256(f"{prefix}:{v}".encode()).hexdigest()
def select_k(seed,l0,u7):
    xs=[e for sem,e in u7.items() if sem not in l0 and 5<=e.size<=7]; xs.sort(key=lambda e:rk(seed,e.sem)); return xs[0]
def coherent_cegis(target,u7):
    obs=[]; trace=[]; cs=sorted(u7.values(),key=lambda e:(e.size,e.text,e.sem))
    for rid in range(16):
        good=[e for e in cs if all(bit(e.sem,r)==y for r,y in obs)]
        if not good: raise RuntimeError("CEGIS empty")
        p=good[0]; mm=next((r for r in range(8) if bit(p.sem,r)!=bit(target.sem,r)),None)
        trace.append({"round":rid,"proposal":p.text,"proposal_sem":p.sem,"proposal_size":p.size,"consistent":len(good),"row":mm,"expected":None if mm is None else bit(target.sem,mm)})
        if mm is None: return p,trace
        obs.append((mm,bit(target.sem,mm)))
    raise RuntimeError("CEGIS budget exceeded")
def corrupted_candidate(trace,u7):
    obs=[(r["row"],r["expected"]) for r in trace if r["row"] is not None]
    rows=[r for r,_ in obs]; labels=[y for _,y in obs]; shifted=labels[1:]+labels[:1]; bad=list(zip(rows,shifted))
    good=[e for e in sorted(u7.values(),key=lambda e:(e.size,e.text,e.sem)) if all(bit(e.sem,r)==y for r,y in bad)]
    return (good[0] if good else None),bad
def select_o2(seed,l0,l1,k):
    xs=[e for sem,e in l1.items() if sem not in l0 and sem!=k.sem]; xs.sort(key=lambda e:rk(f"{seed}:O2",e.sem)); return xs[0]
def protected_l0(seed,l0,k):
    xs=[v for v in l0 if v!=k]; xs.sort(key=lambda v:rk(f"{seed}:PROTECTED",v)); return xs[0]
def scope_phase(k,p):
    scopes=["ANY","C_EQ_0","C_EQ_1","NEVER"]
    def applies(s,c): return {"ANY":True,"C_EQ_0":c==0,"C_EQ_1":c==1,"NEVER":False}[s]
    evidence=[(0,r,bit(k,r)) for r in range(8)]
    dr=next(r for r in range(8) if bit(k,r)!=bit(p,r)); evidence.append((1,dr,bit(p,dr)))
    def valid(s): return all((bit(k,r) if applies(s,c) else bit(p,r))==y for c,r,y in evidence)
    validity={s:valid(s) for s in scopes}; survivors=[s for s in scopes if validity[s]]; chosen=survivors[0] if survivors else "REVOKE"
    return {"protected_l0_sem":p,"counterexample_row":dr,"scope_validity":validity,"chosen_scope":chosen,"without_revision_scope":"ANY","without_revision_recreates_failure":not valid("ANY")}
def one_episode(seed):
    l0=exact_l0_closure(); u7=enumerate_u(7); kt=select_k(seed,l0,u7); k,trace=coherent_cegis(kt,u7)
    l17=enumerate_installed(k,7); o2=select_o2(seed,l0,l17,k); B=o2.size; l1B=enumerate_installed(k,B); uB=enumerate_u(B)
    cold=o2.sem in l0; dev=o2.sem in l1B; mem=o2.sem in uB
    corr,cobs=corrupted_candidate(trace,u7); cadmit=corr is not None and corr.sem==kt.sem; creach=cadmit and o2.sem in enumerate_installed(corr,B)
    abl=o2.sem in l0; rest=o2.sem in enumerate_installed(k,B); scope=scope_phase(k.sem,protected_l0(seed,l0,k.sem))
    gates={"G1_old_closure_obstruction":len(l0)==16 and kt.sem not in l0,"G2_nonpreenumerated_verified_synthesis":k.sem==kt.sem and k.sem not in l0,"G3_install_changes_reachability":dev and not cold,"G4_cold_fails_within_B":not cold,"G5_memory_fails_within_B":not mem,"G6_corrupted_does_not_match_downstream":not creach,"G7_ablate_restore":(not abl) and rest,"G8_counterevidence_refines_scope":not scope["scope_validity"]["ANY"] and scope["scope_validity"]["C_EQ_0"] and scope["chosen_scope"]=="C_EQ_0","G9_scope_ablation_recreates_failure":scope["without_revision_recreates_failure"],"G10_development_changes_development":o2.sem not in l0 and dev and not abl and rest}
    return {"seed":seed,"K":{"target_sem":kt.sem,"target_min_size":kt.size,"sealed_sem":k.sem,"sealed_expr":k.text,"cegis_rounds":len(trace),"trace":trace},"O2":{"sem":o2.sem,"installed_expr":o2.text,"B":B,"cold":cold,"memory_inline":mem,"development":dev,"corrupted":creach,"after_K_ablation":abl,"after_K_restore":rest},"corrupted":{"observations":cobs,"candidate":None if corr is None else corr.text,"candidate_sem":None if corr is None else corr.sem,"independently_admitted_as_K":cadmit},"scope":scope,"gates":gates,"pass":all(gates.values())}
def main():
    h=one_episode(HEADLINE_SEED); sweep=[]
    for i in range(100):
        try: sweep.append(one_episode(f"{SWEEP_PREFIX}:{i:03d}"))
        except Exception as e: sweep.append({"pass":False,"error":f"{type(e).__name__}: {e}"})
    def rate(k): return sum(1 for e in sweep if isinstance(e.get("gates"),dict) and e["gates"].get(k))
    summary={"episodes":100,"headline_pass":h["pass"],"full_capstone_passes":sum(1 for e in sweep if e.get("pass")),"G1":rate("G1_old_closure_obstruction"),"G2":rate("G2_nonpreenumerated_verified_synthesis"),"G3":rate("G3_install_changes_reachability"),"G4":rate("G4_cold_fails_within_B"),"G5_memory_separator":rate("G5_memory_fails_within_B"),"G6_corrupted_separator":rate("G6_corrupted_does_not_match_downstream"),"G7_ablate_restore":rate("G7_ablate_restore"),"G8_scope_revision":rate("G8_counterevidence_refines_scope"),"G9_scope_ablation":rate("G9_scope_ablation_recreates_failure"),"G10_development_changes_development":rate("G10_development_changes_development")}
    verdict="PASS_DEVELOPMENTAL_LOOP_CAPSTONE_V1" if h["pass"] else "VALID_NEGATIVE_DEVELOPMENTAL_LOOP_CAPSTONE_V1"
    out=Path("results/developmental_loop_capstone_v1"); out.mkdir(parents=True,exist_ok=True)
    result={"protocol":"DEVELOPMENTAL_LOOP_CAPSTONE_V1","verdict":verdict,"headline":{"K":h["K"],"O2":h["O2"],"corrupted":h["corrupted"],"scope":h["scope"],"gates":h["gates"]},"sweep":summary,"claim_boundary":"Integrated exact finite-world causal evidence only; no open-world natural-code autonomy, arbitrary ontology creation, representation-independent invention, neural learning, or broad generality."}
    (out/"summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("DEVELOPMENTAL LOOP CAPSTONE V1")
    print("K",h["K"]["sealed_expr"],"O2",h["O2"])
    print("scope",h["scope"])
    for g,ok in h["gates"].items(): print(g,"PASS" if ok else "FAIL")
    print("SWEEP",summary); print(verdict)
    return 0 if h["pass"] else 2
if __name__=="__main__": raise SystemExit(main())
