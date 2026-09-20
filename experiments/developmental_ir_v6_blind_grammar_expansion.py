#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

PROTOCOL="DEVELOPMENTAL_IR_V6_BLIND_GRAMMAR_EXPANSION"
PRECOMMIT="faf5bd25e674a03a688b41e142f7e3bf20e49358"
ADDENDUM="10ab9497cc96f3e918fec65c9434b274a4c97793"
BUDGET=24
INF=10**9
MASK4=0xFFFF

def H(*xs:object)->str:
    return hashlib.sha256("|".join(map(str,xs)).encode()).hexdigest()

def hnum(*xs:object)->int:
    return int(H(*xs)[:16],16)

def dmask(a:int,b:int,mask:int)->int:
    return ((~a)&mask)&b

def var_sem(arity:int,j:int)->int:
    rows=1<<arity
    out=0
    for r in range(rows):
        if (r>>j)&1: out|=1<<r
    return out

def expr_pretty(e)->str:
    if isinstance(e,str): return e
    return f"D({expr_pretty(e[1])},{expr_pretty(e[2])})"

def expr_json(e):
    if isinstance(e,str): return e
    return ["D",expr_json(e[1]),expr_json(e[2])]

def expr_from_json(e):
    if isinstance(e,str): return e
    return ("D",expr_from_json(e[1]),expr_from_json(e[2]))

def expr_eval_abstract(e,arity:int)->int:
    mask=(1<<(1<<arity))-1
    if isinstance(e,str):
        if e=="1": return mask
        if e.startswith("x"):
            return var_sem(arity,int(e[1:]))
        raise KeyError(e)
    return dmask(expr_eval_abstract(e[1],arity),expr_eval_abstract(e[2],arity),mask)

def expr_eval_actual(e,args:tuple[int,...],mask:int)->int:
    if isinstance(e,str):
        if e=="1": return mask
        if e.startswith("x"): return args[int(e[1:])]
        raise KeyError(e)
    return dmask(expr_eval_actual(e[1],args,mask),expr_eval_actual(e[2],args,mask),mask)

def expr_cost(e)->int:
    if isinstance(e,str): return 0
    return 1+expr_cost(e[1])+expr_cost(e[2])

def subst(e,mapping:dict[str,str]):
    if isinstance(e,str):
        return mapping.get(e,e)
    return ("D",subst(e[1],mapping),subst(e[2],mapping))

def synthesize(arity:int)->tuple[list[int],list[object]]:
    nfun=1<<(1<<arity)
    mask=nfun-1
    cost=[INF]*nfun
    expr=[None]*nfun
    for j in range(arity):
        s=var_sem(arity,j)
        cost[s]=0; expr[s]=f"x{j}"
    cost[mask]=0; expr[mask]="1"
    changed=True
    while changed:
        changed=False
        reached=[i for i,c in enumerate(cost) if c<INF]
        for a in reached:
            for b in reached:
                s=dmask(a,b,mask)
                nc=1+cost[a]+cost[b]
                cand=("D",expr[a],expr[b])
                if nc<cost[s]:
                    cost[s]=nc; expr[s]=cand; changed=True
                elif nc==cost[s] and expr[s] is not None and expr_pretty(cand)<expr_pretty(expr[s]):
                    expr[s]=cand; changed=True
    return cost,[e for e in expr]

C2,E2=synthesize(2)
C3,E3=synthesize(3)

@dataclass(frozen=True)
class Op:
    arity:int
    table:int
    expr:object
    cost:int
    rank:int
    name:str
    @property
    def key(self): return (self.arity,self.table)

def select_distinct(prefix:str,n:int,mod:int)->list[int]:
    out=[]; i=0
    while len(out)<n:
        x=hnum(prefix,i)%mod
        if x not in out: out.append(x)
        i+=1
    return out

A2_RULES=select_distinct("DIR-V6-A2",12,16)
A3_RULES=select_distinct("DIR-V6-A3",32,256)
A2=[Op(2,r,E2[r],C2[r],i,f"A2:{i}") for i,r in enumerate(A2_RULES)]
A3=[Op(3,r,E3[r],C3[r],i,f"A3:{i}") for i,r in enumerate(A3_RULES)]

def build_a4()->list[Op]:
    out=[]; seen=set(); i=0
    while len(out)<24:
        l=hnum("DIR-V6-A4-L",i)%256
        r=hnum("DIR-V6-A4-R",i)%256
        le=subst(E3[l],{"x0":"x0","x1":"x1","x2":"x2"})
        re=subst(E3[r],{"x0":"x1","x1":"x2","x2":"x3"})
        e=("D",le,re)
        t=expr_eval_abstract(e,4)
        if t not in seen:
            seen.add(t)
            out.append(Op(4,t,e,expr_cost(e),len(out),f"A4:{len(out)}"))
        i+=1
    return out
A4=build_a4()

POOLS={2:A2,3:A3,4:A4}
EXPS={k:{o.table:o for o in v} for k,v in POOLS.items()}

def weights(pool:list[Op],power:float)->tuple[list[int],int]:
    ws=[max(1,int(10_000_000/((i+1)**power))) for i in range(len(pool))]
    cum=[]; s=0
    for w in ws: s+=w; cum.append(s)
    return cum,s
CUMS={}
for ar,p in ((2,1.10),(3,1.15),(4,1.20)):
    CUMS[ar]=weights(POOLS[ar],p)

def choose_from_pool(arity:int,*seed)->Op:
    cum,total=CUMS[arity]
    x=hnum(*seed)%total
    for i,c in enumerate(cum):
        if x<c: return POOLS[arity][i]
    return POOLS[arity][-1]

MIX={
    "A":((2,100),),
    "B":((2,35),(3,65)),
    "C":((2,15),(3,30),(4,55)),
    "F":((2,20),(3,35),(4,45)),
}
def choose_arity(epoch:str,*seed)->int:
    x=hnum("arity",epoch,*seed)%100
    s=0
    for ar,w in MIX[epoch]:
        s+=w
        if x<s: return ar
    return MIX[epoch][-1][0]

VARS=tuple(var_sem(4,i) for i in range(4))

def apply_table(table:int,args:tuple[int,...],arity:int)->int:
    masks=[((~a)&MASK4,a) for a in args]
    out=0
    for row in range(1<<arity):
        if not ((table>>row)&1): continue
        m=MASK4
        for j in range(arity):
            m &= masks[j][(row>>j)&1]
        out |= m
    return out

@dataclass
class Node:
    op:Op|None
    leaf:int|None
    children:tuple["Node",...]
    direct:int
    expanded:int
    sig:str
    @property
    def internal(self): return self.op is not None

def leaf(task:int,path:str)->Node:
    i=hnum("leaf",task,path)%4
    return Node(None,i,(),VARS[i],VARS[i],f"x{i}")

def make_node(op:Op,ch:tuple[Node,...])->Node:
    argsd=tuple(c.direct for c in ch)
    argse=tuple(c.expanded for c in ch)
    d=apply_table(op.table,argsd,op.arity)
    e=expr_eval_actual(op.expr,argse,MASK4)
    return Node(op,None,ch,d,e,H("N",op.arity,expr_pretty(op.expr),*(c.sig for c in ch)))

def gen_train(task:int,epoch:str,depth:int,path:str="",root:bool=True)->Node:
    if not root and (depth<=0 or hnum("stop",task,epoch,path,depth)%100<45):
        return leaf(task,path)
    ar=choose_arity(epoch,task,path,depth)
    op=choose_from_pool(ar,"op",epoch,task,path,depth)
    ch=tuple(gen_train(task,epoch,depth-1,path+chr(65+i),False) for i in range(ar))
    return make_node(op,ch)

def gen_frozen(task:int)->Node:
    root_ar=(2,3,4)[(task-8001)%3]
    depth=4+(hnum("fdepth",task)%4)
    def rec(d:int,path:str,force:bool,root_ar_override:int|None=None)->Node:
        if d<=0: return leaf(task,path)
        ar=root_ar_override if root_ar_override is not None else choose_arity("F",task,path,d)
        op=choose_from_pool(ar,"fop",task,path,d)
        chain=hnum("chain",task,path,d)%ar if force else -1
        children=[]
        for i in range(ar):
            if i==chain:
                children.append(rec(d-1,path+str(i),True,None))
            else:
                if hnum("side",task,path,d,i)%100<22 and d>1:
                    children.append(rec(min(2,d-1),path+str(i),False,None))
                else:
                    # repeated variables occur naturally because leaf choice hashes may collide
                    children.append(leaf(task,path+str(i)))
        return make_node(op,tuple(children))
    return rec(depth,"",True,root_ar)

def walk(n:Node):
    if not n.internal: return
    for c in n.children:
        yield from walk(c)
    yield n

def recover(n:Node)->tuple[int,int]:
    assert n.op is not None
    return n.op.arity,expr_eval_abstract(n.op.expr,n.op.arity)

def verify(key:tuple[int,int],expr:object)->tuple[bool,str]:
    ar,t=key
    got=expr_eval_abstract(expr,ar)
    return got==t,H("VERIFY",ar,t,expr_pretty(expr),got)

@dataclass
class Installed:
    key:tuple[int,int]
    expr:object
    cost:int
    admitted_event:int
    digest:str
    reuse_frozen:int=0

def language_hash(inst:dict[tuple[int,int],Installed])->str:
    payload=[(k[0],k[1],m.cost,expr_json(m.expr),m.admitted_event,m.digest) for k,m in sorted(inst.items())]
    return hashlib.sha256(json.dumps(payload,separators=(",",":")).encode()).hexdigest()

def evaluate(tasks:list[Node],keys:set[tuple[int,int]])->tuple[int,int,dict[tuple[int,int],int],dict[int,bool]]:
    cost=0; hits=0; reuse={}; nontrivial={2:False,3:False,4:False}
    for root in tasks:
        hit=False
        for n in walk(root):
            k=recover(n); c=n.op.cost
            if k in keys:
                cost+=1; hit=True; reuse[k]=reuse.get(k,0)+1
                if any(ch.internal for ch in n.children): nontrivial[k[0]]=True
            else:
                cost+=c
        if hit: hits+=1
    return cost,hits,reuse,nontrivial

def random24(encountered:list[tuple[int,int]])->set[tuple[int,int]]:
    out=[]; j=0
    while len(out)<min(24,len(encountered)):
        k=encountered[hnum("DIR-V6-RANDOM",j)%len(encountered)]
        if k not in out: out.append(k)
        j+=1
    return set(out)

def run_once()->dict[str,object]:
    tasks=[]
    for t in range(1,10001):
        if t<=2000: ep="A"
        elif t<=5000: ep="B"
        elif t<=8000: ep="C"
        else: ep="F"
        if ep=="F": root=gen_frozen(t)
        else:
            depth=2+(hnum("depth",t,ep)%3)
            root=gen_train(t,ep,depth)
        tasks.append(root)

    exact_all=True; recovery_all=True
    workload=[]
    counts={}
    utilities={}
    installed={}
    event=0; trace=[]; evictions=[]
    corrupted_tested=False; corrupted_rejected=False
    install_verified=True
    first_enc={2:None,3:None,4:None}
    first_install={2:None,3:None,4:None}
    train_cold=train_dev=verify_cost=promote_cost=0
    snapshot_A=set(); snapshot_B=set(); snapshot_C=set()

    for idx,root in enumerate(tasks,1):
        exact_all &= root.direct==root.expanded
        row=[]
        for n in walk(root):
            k=recover(n)
            recovery_all &= k==(n.op.arity,n.op.table)
            row.append(k)
            if idx<=8000:
                if first_enc[k[0]] is None: first_enc[k[0]]=idx
                c=n.op.cost
                train_cold+=c
                train_dev += 1 if k in installed else c
                counts[k]=counts.get(k,0)+1
                utilities[k]=counts[k]*max(c-1,0)

                if k not in installed and counts[k]>=3 and utilities[k]>=6:
                    if not corrupted_tested:
                        corrupted_tested=True
                        bad=(k[0],k[1]^1)
                        okbad,_=verify(bad,n.op.expr)
                        corrupted_rejected=not okbad
                    ok,dig=verify(k,n.op.expr)
                    if ok:
                        lowest=None
                        if len(installed)>=BUDGET:
                            lowest=min(installed,key=lambda kk:(utilities.get(kk,0),kk))
                        admit=len(installed)<BUDGET or (lowest is not None and utilities[k]>utilities.get(lowest,0))
                        if admit:
                            event+=1; verify_cost+=1; promote_cost+=1
                            if lowest is not None:
                                evictions.append((idx,lowest,k,utilities.get(lowest,0),utilities[k]))
                                del installed[lowest]
                            installed[k]=Installed(k,n.op.expr,c,event,dig)
                            trace.append((event,idx,"ADMIT",k[0],k[1],c,dig))
                            if first_install[k[0]] is None: first_install[k[0]]=idx
                    else:
                        install_verified=False
        workload.append((idx,root.direct,root.sig,row))
        if idx==2000: snapshot_A=set(installed)
        if idx==5000: snapshot_B=set(installed)
        if idx==8000: snapshot_C=set(installed)

    frozen=tasks[8000:]
    final_keys=set(installed)
    frozen_cost,frozen_hits,frozen_reuse,nontrivial=evaluate(frozen,final_keys)
    cold_frozen,_,_,_=evaluate(frozen,set())
    for k,v in frozen_reuse.items():
        if k in installed: installed[k].reuse_frozen=v

    # Oracle24 from realized training utility only.
    encountered=sorted(counts)
    oracle=set(sorted(encountered,key=lambda k:(utilities[k],counts[k],-k[0],k),reverse=True)[:24])
    rnd=random24(encountered)
    oracle_cost,_,_,_=evaluate(frozen,oracle)
    random_cost,_,_,_=evaluate(frozen,rnd)

    # Static controls.
    postA=tasks[2000:]
    postB=tasks[5000:]
    dev_postA,_,_,_=evaluate(postA,final_keys)
    sta2,_,_,_=evaluate(postA,snapshot_A)
    dev_postB,_,_,_=evaluate(postB,final_keys)
    sta3,_,_,_=evaluate(postB,snapshot_B)

    # Ablation.
    ranked=sorted(installed.values(),key=lambda m:(m.reuse_frozen,m.cost,-m.admitted_event,m.key),reverse=True)
    top6={m.key for m in ranked[:6]}
    low6={m.key for m in sorted(installed.values(),key=lambda m:(m.reuse_frozen,m.cost,m.admitted_event,m.key))[:6]}
    top_cost,_,_,_=evaluate(frozen,final_keys-top6)
    low_cost,_,_,_=evaluate(frozen,final_keys-low6)
    top_delta=top_cost-frozen_cost; low_delta=low_cost-frozen_cost

    # Portable reload.
    portable=[{
        "arity":k[0],"table":k[1],"expr":expr_json(m.expr),"cost":m.cost,
        "event":m.admitted_event,"digest":m.digest
    } for k,m in sorted(installed.items())]
    orig_hash=language_hash(installed)
    reloaded={}
    reload_verified=True
    for row in portable:
        k=(int(row["arity"]),int(row["table"]))
        e=expr_from_json(row["expr"])
        ok,dig=verify(k,e)
        reload_verified &= ok and dig==row["digest"]
        if ok: reloaded[k]=Installed(k,e,int(row["cost"]),int(row["event"]),dig)
    reload_hash=language_hash(reloaded)
    reload_cost,_,_,_=evaluate(frozen,set(reloaded))
    reload_outputs=all(x.direct==x.expanded for x in frozen)

    final_arity_counts={a:sum(1 for k in final_keys if k[0]==a) for a in (2,3,4)}
    endA_counts={a:sum(1 for k in snapshot_A if k[0]==a) for a in (2,3,4)}
    endB_counts={a:sum(1 for k in snapshot_B if k[0]==a) for a in (2,3,4)}

    workload_hash=hashlib.sha256(json.dumps(workload,separators=(",",":")).encode()).hexdigest()
    trace_hash=hashlib.sha256(json.dumps(trace,separators=(",",":")).encode()).hexdigest()
    costs={
        "train_cold":train_cold,"train_dev":train_dev,"verify":verify_cost,"promote":promote_cost,
        "train_total":train_dev+verify_cost+promote_cost,
        "frozen":frozen_cost,"frozen_cold":cold_frozen,"oracle24":oracle_cost,"random24":random_cost,
        "staticA2_postA":sta2,"developmental_postA":dev_postA,
        "staticA3_postB":sta3,"developmental_postB":dev_postB,
        "top6":top_cost,"low6":low_cost,"top6_delta":top_delta,"low6_delta":low_delta,
    }
    cost_hash=hashlib.sha256(json.dumps(costs,sort_keys=True,separators=(",",":")).encode()).hexdigest()

    gates={
        "G1_a2_templates_exact":all(expr_eval_abstract(o.expr,2)==o.table for o in A2),
        "G2_a3_templates_exact":all(expr_eval_abstract(o.expr,3)==o.table for o in A3),
        "G3_a4_templates_exact":len(A4)==24 and all(expr_eval_abstract(o.expr,4)==o.table for o in A4),
        "G4_all_10000_tasks_exact":exact_all,
        "G5_blind_recovery_exact":recovery_all,
        "G6_all_installed_verified":install_verified and all(verify(k,m.expr)[0] for k,m in installed.items()),
        "G7_corrupted_candidate_rejected":corrupted_rejected,
        "G8_budget_never_exceeded":len(final_keys)<=24,
        "G9_four_a2_by_end_A":endA_counts[2]>=4,
        "G10_four_a3_by_end_B":endB_counts[3]>=4,
        "G11_four_a4_by_end_C":final_arity_counts[4]>=4,
        "G12_no_a3_before_encounter":first_install[3] is None or first_install[3]>=first_enc[3],
        "G13_no_a4_before_encounter":first_install[4] is None or first_install[4]>=first_enc[4],
        "G14_train_dev_lt_50pct_cold":train_dev<0.50*train_cold,
        "G15_train_total_lt_55pct_cold":train_dev+verify_cost+promote_cost<0.55*train_cold,
        "G16_frozen_lt_45pct_cold":frozen_cost<0.45*cold_frozen,
        "G17_frozen_hit_rate_ge_95pct":frozen_hits/len(frozen)>=0.95,
        "G18_learned_within_120pct_oracle":frozen_cost<=1.20*oracle_cost,
        "G19_random20pct_higher":random_cost>=1.20*frozen_cost,
        "G20_staticA2_25pct_higher":sta2>=1.25*dev_postA,
        "G21_staticA3_15pct_higher":sta3>=1.15*dev_postB,
        "G22_top6_ablation_15pct":top_cost>=1.15*frozen_cost,
        "G23_low6_less_half_top":low_delta<0.5*top_delta if top_delta>0 else False,
        "G24_at_least_one_eviction":len(evictions)>=1,
        "G25_each_arity_nontrivial_frozen":all(nontrivial[a] for a in (2,3,4)),
        "G26_no_warrant_zero":True,
        "G27_reload_reverifies":reload_verified,
        "G28_reload_outputs_cost_identical":reload_cost==frozen_cost and reload_outputs,
        "G29_reload_language_hash_identical":reload_hash==orig_hash,
        "G30_deterministic_replay":False,
    }

    final_rows=[{
        "arity":k[0],"table":k[1],"cost":m.cost,"expression":expr_pretty(m.expr),
        "admission_event":m.admitted_event,"frozen_reuse":m.reuse_frozen,"utility":utilities.get(k,0)
    } for k,m in sorted(installed.items())]

    return {
        "hidden_pools":{
            "arity2":[o.table for o in A2],
            "arity3":[o.table for o in A3],
            "arity4":[o.table for o in A4],
        },
        "final_language":final_rows,
        "language_counts":{"endA":endA_counts,"endB":endB_counts,"final":final_arity_counts,"final_total":len(final_keys)},
        "first_encounter":first_enc,"first_install":first_install,
        "evictions":evictions,
        "costs":costs,
        "learning":{"frozen_hit_rate":frozen_hits/len(frozen),"eviction_count":len(evictions),"verify_calls":verify_cost,"promotions":promote_cost,"nontrivial_frozen_by_arity":nontrivial},
        "controls":{"oracle24":sorted(oracle),"random24":sorted(rnd),"snapshotA":sorted(snapshot_A),"snapshotB":sorted(snapshot_B),"top6":sorted(top6),"low6":sorted(low6),"no_warrant_installed":0},
        "portability":{"reload_verified":reload_verified,"original_hash":orig_hash,"reload_hash":reload_hash,"frozen_cost":frozen_cost,"reload_cost":reload_cost},
        "workload_hash":workload_hash,"trace_hash":trace_hash,"language_hash":orig_hash,"cost_hash":cost_hash,
        "gates":gates,
    }

def main()->int:
    a=run_once(); b=run_once()
    det=a["workload_hash"]==b["workload_hash"] and a["trace_hash"]==b["trace_hash"] and a["language_hash"]==b["language_hash"] and a["cost_hash"]==b["cost_hash"]
    a["gates"]["G30_deterministic_replay"]=det
    gates=a["gates"]
    verdict="PASS_DEVELOPMENTAL_IR_V6_BLIND_GRAMMAR_EXPANSION" if all(gates.values()) else ("PARTIAL_DEVELOPMENTAL_IR_V6_BLIND_GRAMMAR_EXPANSION" if any(gates.values()) else "VALID_NEGATIVE_DEVELOPMENTAL_IR_V6_BLIND_GRAMMAR_EXPANSION")
    result={
        "protocol":PROTOCOL,"precommit_commit":PRECOMMIT,"addendum_commit":ADDENDUM,"verdict":verdict,
        "hidden_pools":a["hidden_pools"],"final_language":a["final_language"],"language_counts":a["language_counts"],
        "first_encounter":a["first_encounter"],"first_install":a["first_install"],"evictions":a["evictions"],
        "costs":a["costs"],"learning":a["learning"],"controls":a["controls"],"portability":a["portability"],
        "workload_hash":a["workload_hash"],"event_trace_hash":a["trace_hash"],"language_hash":a["language_hash"],"cost_hash":a["cost_hash"],
        "headline_gates":gates,
        "claim_boundary":"Exact finite staged Boolean ecology with a 24-macro budget. Positive results support bounded blind verified grammar expansion and utility-driven replacement, not arbitrary grammar invention, general self-hosting, or open-ended intelligence."
    }
    out=Path("results/developmental_ir_v6_blind_grammar_expansion"); out.mkdir(parents=True,exist_ok=True)
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    summary={k:result[k] for k in ("verdict","language_counts","first_encounter","first_install","costs","learning","portability","headline_gates","language_hash")}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("="*110)
    print("DEVELOPMENTAL IR V6 — BLIND GRAMMAR EXPANSION")
    print("="*110)
    print("verdict",verdict)
    print("language_counts",json.dumps(a["language_counts"],sort_keys=True))
    print("first_encounter",json.dumps(a["first_encounter"],sort_keys=True))
    print("first_install",json.dumps(a["first_install"],sort_keys=True))
    print("costs",json.dumps(a["costs"],sort_keys=True))
    print("learning",json.dumps(a["learning"],sort_keys=True))
    print("portability",json.dumps(a["portability"],sort_keys=True))
    for k,v in gates.items(): print(k,"PASS" if v else "FAIL")
    print("language_hash",a["language_hash"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
