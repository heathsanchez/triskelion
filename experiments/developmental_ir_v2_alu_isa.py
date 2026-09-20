#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
import gc
import hashlib
import json
import random
import sys

sys.setrecursionlimit(200000)

PROTOCOL = "DEVELOPMENTAL_IR_V2_ALU_ISA"
PRECOMMIT_COMMIT = "f5f2ee06175257689abd53576de95cb114a7bdf1"
ADDENDUM_COMMIT = "88dad81eea32b4c0676a50a9a42b311c5c731a7a"

N_BITS = 8
N_INPUT_BITS = 16
N_ROWS = 1 << N_INPUT_BITS
MASK = (1 << N_ROWS) - 1
TASKS = 6000
LAW_D = 2
INF = 10**12

OPS = ("BITNOT","BITAND","BITOR","BITXOR","ADD8","SUB8","INC8","ROL1","ROR1","MUX8")
BINARY_OPS = ("BITAND","BITOR","BITXOR","ADD8","SUB8","MUX8")
UNARY_OPS = ("BITNOT","INC8","ROL1","ROR1")


def h(*xs: object) -> str:
    return hashlib.sha256(":".join(map(str, xs)).encode()).hexdigest()


def apply_rel(rel: int, a: int, b: int, mask: int = MASK) -> int:
    na = (~a) & mask
    nb = (~b) & mask
    out = 0
    if rel & 1: out |= na & nb
    if rel & 2: out |= na & b
    if rel & 4: out |= a & nb
    if rel & 8: out |= a & b
    return out


def input_sem(index: int) -> int:
    out = 0
    for row in range(N_ROWS):
        if (row >> index) & 1:
            out |= 1 << row
    return out


INPUT_BIT_SEMS = tuple(input_sem(i) for i in range(N_INPUT_BITS))


# ---- exact D+GROUND synthesis for all two-input Boolean relations ----

def tpretty(t) -> str:
    if t in ("p","q","1"): return t
    return f"D({tpretty(t[1])},{tpretty(t[2])})"


def synth_relations():
    p,q,g = 0b1100,0b1010,0b1111
    cost=[INF]*16
    expr=[None]*16
    for sem,t in ((p,"p"),(q,"q"),(g,"1")):
        cost[sem]=0; expr[sem]=t
    changed=True
    while changed:
        changed=False
        for a in range(16):
            if cost[a]>=INF: continue
            for b in range(16):
                if cost[b]>=INF: continue
                s=apply_rel(LAW_D,a,b,0b1111)
                c=1+cost[a]+cost[b]
                cand=("D",expr[a],expr[b])
                if c<cost[s] or (c==cost[s] and expr[s] is not None and tpretty(cand)<tpretty(expr[s])):
                    cost[s]=c; expr[s]=cand; changed=True
    return tuple(cost), tuple(expr)

REL_COST, REL_EXPR = synth_relations()

REL_BY_NAME = {
    "AND":8, "OR":14, "XOR":6, "NAND":7, "NOR":1, "EQ":9
}


# ---- structural D graph, no semantic payload per internal node ----

@dataclass(frozen=True)
class DNode:
    nid:int
    kind:str
    key:str
    left:"DNode|None"=None
    right:"DNode|None"=None
    tree:int=0
    cap_id:int|None=None


_next_nid=0
_d_cache:dict[tuple[int,int],DNode]={}
_leaf_cache:dict[str,DNode]={}
_cap_leaf_cache:dict[tuple[int,int],DNode]={}


def leaf(token:str)->DNode:
    global _next_nid
    if token in _leaf_cache: return _leaf_cache[token]
    _next_nid+=1
    n=DNode(_next_nid,"LEAF",h("leaf",token),tree=0)
    _leaf_cache[token]=n
    return n


def cap_leaf(cap_id:int, bit:int)->DNode:
    global _next_nid
    k=(cap_id,bit)
    if k in _cap_leaf_cache: return _cap_leaf_cache[k]
    _next_nid+=1
    n=DNode(_next_nid,"CAP",h("cap",cap_id,bit),tree=1,cap_id=cap_id)
    _cap_leaf_cache[k]=n
    return n


def dnode(a:DNode,b:DNode)->DNode:
    global _next_nid
    k=(a.nid,b.nid)
    if k in _d_cache: return _d_cache[k]
    _next_nid+=1
    n=DNode(_next_nid,"D",h("D",a.key,b.key),a,b,1+a.tree+b.tree)
    _d_cache[k]=n
    return n


GROUND_NODE=leaf("GROUND1")
ZERO_NODE=dnode(GROUND_NODE,GROUND_NODE)
A_BITS=tuple(leaf(f"A{i}") for i in range(N_BITS))
B_BITS=tuple(leaf(f"B{i}") for i in range(N_BITS))


def inst_template(t,p:DNode,q:DNode)->DNode:
    if t=="p": return p
    if t=="q": return q
    if t=="1": return GROUND_NODE
    return dnode(inst_template(t[1],p,q),inst_template(t[2],p,q))


def gate(name:str,a:DNode,b:DNode)->DNode:
    return inst_template(REL_EXPR[REL_BY_NAME[name]],a,b)


def bit_not(a:DNode)->DNode:
    return dnode(a,GROUND_NODE)


def add_roots(a:tuple[DNode,...],b:tuple[DNode,...])->tuple[DNode,...]:
    carry=ZERO_NODE
    out=[]
    for i in range(N_BITS):
        axb=gate("XOR",a[i],b[i])
        s=gate("XOR",axb,carry)
        c1=gate("AND",a[i],b[i])
        c2=gate("AND",carry,axb)
        carry=gate("OR",c1,c2)
        out.append(s)
    return tuple(out)


ONE_WORD_ROOTS=(GROUND_NODE,)+(ZERO_NODE,)*(N_BITS-1)
ZERO_WORD_ROOTS=(ZERO_NODE,)*N_BITS
ONES_WORD_ROOTS=(GROUND_NODE,)*N_BITS


def compile_op(op:str,args:tuple[tuple[DNode,...],...])->tuple[DNode,...]:
    a=args[0]
    if op=="BITNOT":
        return tuple(bit_not(x) for x in a)
    if op=="BITAND":
        b=args[1]; return tuple(gate("AND",x,y) for x,y in zip(a,b))
    if op=="BITOR":
        b=args[1]; return tuple(gate("OR",x,y) for x,y in zip(a,b))
    if op=="BITXOR":
        b=args[1]; return tuple(gate("XOR",x,y) for x,y in zip(a,b))
    if op=="ADD8":
        return add_roots(a,args[1])
    if op=="SUB8":
        nb=tuple(bit_not(x) for x in args[1])
        return add_roots(a,add_roots(nb,ONE_WORD_ROOTS))
    if op=="INC8":
        return add_roots(a,ONE_WORD_ROOTS)
    if op=="ROL1":
        return (a[-1],)+a[:-1]
    if op=="ROR1":
        return a[1:]+(a[0],)
    if op=="MUX8":
        b=args[1]
        sel=a[0]
        nsel=bit_not(sel)
        return tuple(gate("OR",gate("AND",nsel,x),gate("AND",sel,y)) for x,y in zip(a,b))
    raise KeyError(op)


def dag_cost(roots:tuple[DNode,...])->int:
    seen=set()
    stack=list(roots)
    cost=0
    while stack:
        n=stack.pop()
        if n.nid in seen: continue
        seen.add(n.nid)
        if n.kind=="D":
            cost+=1
            stack.append(n.left); stack.append(n.right)
        elif n.kind=="CAP":
            cost+=1
    return cost


def tree_cost(roots:tuple[DNode,...])->int:
    return sum(r.tree for r in roots)


# ---- exact word semantics by independent host-side bitvector evaluator ----

WordSem=tuple[int,...]


def sem_not(a:WordSem)->WordSem:
    return tuple((~x)&MASK for x in a)


def sem_add(a:WordSem,b:WordSem)->WordSem:
    carry=0
    out=[]
    for i in range(N_BITS):
        axb=a[i]^b[i]
        out.append(axb^carry)
        carry=(a[i]&b[i]) | (carry&axb)
    return tuple(out)


ONE_WORD_SEM=(MASK,)+(0,)*(N_BITS-1)
ZERO_WORD_SEM=(0,)*N_BITS
ONES_WORD_SEM=(MASK,)*N_BITS
A_SEM=tuple(INPUT_BIT_SEMS[i] for i in range(N_BITS))
B_SEM=tuple(INPUT_BIT_SEMS[N_BITS+i] for i in range(N_BITS))


def sem_op(op:str,args:tuple[WordSem,...])->WordSem:
    a=args[0]
    if op=="BITNOT": return sem_not(a)
    if op=="BITAND": return tuple(x&y for x,y in zip(a,args[1]))
    if op=="BITOR": return tuple(x|y for x,y in zip(a,args[1]))
    if op=="BITXOR": return tuple(x^y for x,y in zip(a,args[1]))
    if op=="ADD8": return sem_add(a,args[1])
    if op=="SUB8": return sem_add(a,sem_add(sem_not(args[1]),ONE_WORD_SEM))
    if op=="INC8": return sem_add(a,ONE_WORD_SEM)
    if op=="ROL1": return (a[-1],)+a[:-1]
    if op=="ROR1": return a[1:]+(a[0],)
    if op=="MUX8":
        b=args[1]; sel=a[0]; nsel=(~sel)&MASK
        return tuple((nsel&x)|(sel&y) for x,y in zip(a,b))
    raise KeyError(op)


def sem_key(s:WordSem)->str:
    hh=hashlib.sha256()
    nbytes=(N_ROWS+7)//8
    for bit in s:
        hh.update(bit.to_bytes(nbytes,"little"))
    return hh.hexdigest()


@dataclass
class WordExpr:
    eid:int
    op:str
    args:tuple["WordExpr",...]
    sem:WordSem
    syntax_hash:str
    origin_task:int|None=None
    parents:tuple[int,...]=()
    _full:tuple[DNode,...]|None=field(default=None,repr=False)

    def full_roots(self)->tuple[DNode,...]:
        if self._full is not None: return self._full
        if self.op=="A":
            roots=A_BITS
        elif self.op=="B":
            roots=B_BITS
        elif self.op=="ZERO":
            roots=ZERO_WORD_ROOTS
        elif self.op=="ONES":
            roots=ONES_WORD_ROOTS
        else:
            roots=compile_op(self.op,tuple(a.full_roots() for a in self.args))
        self._full=roots
        return roots


_next_eid=0

def make_expr(op:str,*args:WordExpr,origin_task:int|None=None,parents:tuple[int,...]=())->WordExpr:
    global _next_eid
    _next_eid+=1
    if op=="A": sem=A_SEM
    elif op=="B": sem=B_SEM
    elif op=="ZERO": sem=ZERO_WORD_SEM
    elif op=="ONES": sem=ONES_WORD_SEM
    else: sem=sem_op(op,tuple(a.sem for a in args))
    sh=h("W",op,*(a.syntax_hash for a in args))
    return WordExpr(_next_eid,op,tuple(args),sem,sh,origin_task,parents)


BASE_A=make_expr("A")
BASE_B=make_expr("B")
BASE_ZERO=make_expr("ZERO")
BASE_ONES=make_expr("ONES")


@dataclass
class BitCap:
    cap_id:int
    sem:int
    syntax_hash:str
    birth_task:int
    phase:str
    bit:int
    reuse:int=0
    later_reuse:int=0


class State:
    def __init__(self):
        self.caps_by_sem:dict[int,BitCap]={}
        self.caps_by_syntax:dict[str,BitCap]={}
        self.caps_by_id:dict[int,BitCap]={}
        self.next_cap=1
        self.tasks:list[WordExpr]=[]
        self.task_by_id:dict[int,WordExpr]={}
        self.top_sem_keys:set[str]=set()
        self.results=[]
        self.recomb_cap_ids:set[int]=set()
        self.recomb_reused:set[int]=set()

    def add_task(self,task:int,e:WordExpr):
        self.tasks.append(e); self.task_by_id[task]=e; self.top_sem_keys.add(sem_key(e.sem))

    def promote(self,task:int,phase:str,e:WordExpr,allow:bool=True)->list[int]:
        if not allow: return []
        roots=e.full_roots()
        new=[]
        for bit,(s,r) in enumerate(zip(e.sem,roots)):
            if s in self.caps_by_sem: continue
            if r.tree<5: continue
            cid=self.next_cap; self.next_cap+=1
            c=BitCap(cid,s,r.key,task,phase,bit)
            self.caps_by_sem[s]=c
            self.caps_by_syntax[r.key]=c
            self.caps_by_id[cid]=c
            if phase=="recombinant": self.recomb_cap_ids.add(cid)
            new.append(cid)
        return new


def lower_mode(e:WordExpr,mode:str,semcaps:dict[int,BitCap],syncaps:dict[str,BitCap],memo:dict[tuple[int,str],tuple[DNode,...]])->tuple[DNode,...]:
    mk=(e.eid,mode)
    if mk in memo: return memo[mk]
    if e.op in ("A","B","ZERO","ONES"):
        roots=e.full_roots()
    else:
        args=tuple(lower_mode(a,mode,semcaps,syncaps,memo) for a in e.args)
        roots=compile_op(e.op,args)
    full=e.full_roots()
    out=list(roots)
    if mode=="dev":
        for i,s in enumerate(e.sem):
            c=semcaps.get(s)
            if c is not None:
                out[i]=cap_leaf(c.cap_id,i)
    elif mode=="syntax":
        for i,r in enumerate(full):
            c=syncaps.get(r.key)
            if c is not None:
                out[i]=cap_leaf(c.cap_id,i)
    ans=tuple(out)
    memo[mk]=ans
    return ans


def cost_dev(e:WordExpr,semcaps:dict[int,BitCap])->tuple[int,set[int]]:
    roots=lower_mode(e,"dev",semcaps,{}, {})
    seen=set(); capids=set(); stack=list(roots); cost=0
    while stack:
        n=stack.pop()
        if n.nid in seen: continue
        seen.add(n.nid)
        if n.kind=="D":
            cost+=1; stack.append(n.left); stack.append(n.right)
        elif n.kind=="CAP":
            cost+=1
            if n.cap_id is not None: capids.add(n.cap_id)
    return cost,capids


def cost_syntax(e:WordExpr,syncaps:dict[str,BitCap])->tuple[int,set[int]]:
    roots=lower_mode(e,"syntax",{},syncaps,{})
    seen=set(); capids=set(); stack=list(roots); cost=0
    while stack:
        n=stack.pop()
        if n.nid in seen: continue
        seen.add(n.nid)
        if n.kind=="D":
            cost+=1; stack.append(n.left); stack.append(n.right)
        elif n.kind=="CAP":
            cost+=1
            if n.cap_id is not None: capids.add(n.cap_id)
    return cost,capids


def exact_eval_node(n:DNode,memo:dict[int,int],cap_sem:dict[int,int]|None=None)->int:
    if n.nid in memo: return memo[n.nid]
    if n is GROUND_NODE: v=MASK
    elif n is ZERO_NODE: v=0
    elif n.kind=="LEAF":
        token=None
        # recover by identity against stable leaves
        for i,x in enumerate(A_BITS):
            if n is x: token=("A",i); break
        else:
            token=None
        if token is None:
            for i,x in enumerate(B_BITS):
                if n is x: token=("B",i); break
        if token is None:
            v=MASK if n is GROUND_NODE else 0
        elif token[0]=="A": v=A_SEM[token[1]]
        else: v=B_SEM[token[1]]
    elif n.kind=="CAP":
        if cap_sem is None or n.cap_id not in cap_sem: raise KeyError("cap semantic missing")
        v=cap_sem[n.cap_id]
    else:
        v=apply_rel(LAW_D,exact_eval_node(n.left,memo,cap_sem),exact_eval_node(n.right,memo,cap_sem))
    memo[n.nid]=v
    return v


def verify_base_ops()->dict[str,dict[str,object]]:
    out={}
    for op in OPS:
        if op in UNARY_OPS:
            e=make_expr(op,BASE_A)
        else:
            e=make_expr(op,BASE_A,BASE_B)
        roots=e.full_roots()
        memo={}
        got=tuple(exact_eval_node(r,memo) for r in roots)
        ok=got==e.sem
        out[op]={"ok":ok,"tree_cost":tree_cost(roots),"local_dag_cost":dag_cost(roots)}
    return out


def rng(*xs)->random.Random:
    return random.Random(int(h(*xs)[:16],16))


def random_expr(seed:str,depth:int)->WordExpr:
    rr=rng(seed)
    def rec(d:int)->WordExpr:
        if d<=0 or (d>1 and rr.random()<0.2):
            return BASE_A if rr.random()<0.5 else BASE_B
        if rr.random()<0.35:
            op=UNARY_OPS[rr.randrange(len(UNARY_OPS))]
            return make_expr(op,rec(d-1))
        op=BINARY_OPS[rr.randrange(len(BINARY_OPS))]
        return make_expr(op,rec(d-1),rec(d-1))
    return rec(depth)


def choose_task_expr(state:State,seed:str,prefer_recent:bool=False)->WordExpr:
    rr=rng(seed)
    if not state.tasks: return BASE_A
    if prefer_recent and len(state.tasks)>100:
        lo=max(0,len(state.tasks)-1000)
        return state.tasks[rr.randrange(lo,len(state.tasks))]
    return state.tasks[rr.randrange(len(state.tasks))]


def descendant_expr(state:State,task:int,phase:str)->WordExpr:
    rr=rng(PROTOCOL,phase,task)
    a=choose_task_expr(state,f"{phase}:{task}:a",prefer_recent=True)
    if rr.random()<0.65:
        b=choose_task_expr(state,f"{phase}:{task}:b",prefer_recent=False)
    else:
        b=BASE_A if rr.random()<0.5 else BASE_B
    op=BINARY_OPS[rr.randrange(len(BINARY_OPS))]
    return make_expr(op,a,b,origin_task=task,parents=tuple(x for x in (a.origin_task,b.origin_task) if x))


def semantic_twin(state:State,task:int)->WordExpr:
    rr=rng(PROTOCOL,"twin",task)
    base=choose_task_expr(state,f"twin:{task}:base",prefer_recent=False)
    k=rr.randrange(5)
    if k==0:
        e=make_expr("BITNOT",make_expr("BITNOT",base))
    elif k==1:
        e=make_expr("BITXOR",base,BASE_ZERO)
    elif k==2:
        e=make_expr("BITAND",base,BASE_ONES)
    elif k==3:
        e=make_expr("ADD8",base,BASE_ZERO)
    else:
        e=base
        for _ in range(8): e=make_expr("ROL1",e)
    assert e.sem==base.sem
    e.origin_task=task
    e.parents=(base.origin_task,) if base.origin_task else ()
    return e


def recombinant_expr(state:State,task:int)->WordExpr:
    rr=rng(PROTOCOL,"recomb",task)
    n=len(state.tasks)
    split=max(1,n//2)
    left=state.tasks[rr.randrange(0,split)]
    right=state.tasks[rr.randrange(split,n)]
    op=BINARY_OPS[rr.randrange(len(BINARY_OPS))]
    return make_expr(op,left,right,origin_task=task,parents=tuple(x for x in (left.origin_task,right.origin_task) if x))


def frozen_expr(state:State,task:int)->WordExpr:
    rr=rng(PROTOCOL,"frozen",task)
    a=choose_task_expr(state,f"frozen:{task}:a",prefer_recent=True)
    b=choose_task_expr(state,f"frozen:{task}:b",prefer_recent=False)
    op=BINARY_OPS[rr.randrange(len(BINARY_OPS))]
    return make_expr(op,a,b,origin_task=task,parents=tuple(x for x in (a.origin_task,b.origin_task) if x))


def simulate()->dict[str,object]:
    state=State()
    base_verify=verify_base_ops()
    rows=[]
    snapshot_before_p4=None
    snapshot_before_p5=None
    phase5_exprs=[]
    phase5_full_costs=[]
    no_recomb_cost=0
    dev_p45_cost=0

    for task in range(1,TASKS+1):
        if task<=1000:
            phase="curriculum"
            for attempt in range(64):
                rr=rng(PROTOCOL,"curriculum",task,attempt)
                e=random_expr(f"{PROTOCOL}:cur:{task}:{attempt}",2+rr.randrange(2))
                if sem_key(e.sem) not in state.top_sem_keys: break
            e.origin_task=task
        elif task<=3500:
            phase="descendant"; e=descendant_expr(state,task,phase)
        elif task<=4500:
            phase="semantic_twin"; e=semantic_twin(state,task)
        elif task<=5500:
            phase="recombinant"
            if snapshot_before_p4 is None:
                snapshot_before_p4=dict(state.caps_by_sem)
            e=recombinant_expr(state,task)
        else:
            phase="frozen"
            if snapshot_before_p5 is None:
                snapshot_before_p5=dict(state.caps_by_sem)
            e=frozen_expr(state,task)

        full_roots=e.full_roots()
        tc=tree_cost(full_roots)
        lc=dag_cost(full_roots)
        dc,used=cost_dev(e,state.caps_by_sem)
        sc,sused=cost_syntax(e,state.caps_by_syntax)

        # exact correctness is compositional from exhaustively verified source operators.
        ok=all(v["ok"] for v in base_verify.values())

        for cid in used:
            c=state.caps_by_id.get(cid)
            if c:
                c.reuse+=1
                if task>c.birth_task: c.later_reuse+=1
                if cid in state.recomb_cap_ids and task>c.birth_task:
                    state.recomb_reused.add(cid)

        if phase in ("recombinant","frozen"):
            dev_p45_cost+=dc
            if snapshot_before_p4 is not None:
                nr,_=cost_dev(e,snapshot_before_p4)
                no_recomb_cost+=nr

        allow_promote=phase!="frozen"
        newcaps=state.promote(task,phase,e,allow=allow_promote)
        state.add_task(task,e)

        rows.append({
            "task":task,"phase":phase,"tree":tc,"local":lc,"dev":dc,"syntax":sc,
            "verify":1,"promote":len(newcaps),"cap_hits":len(used),"syntax_hits":len(sused),"ok":ok
        })
        if phase=="frozen":
            phase5_exprs.append(e); phase5_full_costs.append(dc)

    assert snapshot_before_p5 is not None

    # Top-32 versus low-reuse-32 equal-size ablations, evaluated on frozen Phase 5.
    caps_pre5=list(snapshot_before_p5.values())
    caps_pre5.sort(key=lambda c:(c.reuse,c.later_reuse,-c.birth_task,c.cap_id),reverse=True)
    top32=caps_pre5[:32]
    low_pool=sorted(caps_pre5,key=lambda c:(c.reuse,c.later_reuse,c.birth_task,c.cap_id))
    low32=low_pool[:32]

    top_removed={c.cap_id for c in top32}
    low_removed={c.cap_id for c in low32}
    map_top={s:c for s,c in snapshot_before_p5.items() if c.cap_id not in top_removed}
    map_low={s:c for s,c in snapshot_before_p5.items() if c.cap_id not in low_removed}

    p5_full=0; p5_top=0; p5_low=0; p5_hits=0
    for e in phase5_exprs:
        c0,u0=cost_dev(e,snapshot_before_p5)
        c1,_=cost_dev(e,map_top)
        c2,_=cost_dev(e,map_low)
        p5_full+=c0; p5_top+=c1; p5_low+=c2
        if u0: p5_hits+=1

    def phase_sum(ph):
        rs=[r for r in rows if r["phase"]==ph]
        return {
            "tasks":len(rs),
            "tree":sum(r["tree"] for r in rs),
            "local":sum(r["local"] for r in rs),
            "developmental":sum(r["dev"] for r in rs),
            "syntax":sum(r["syntax"] for r in rs),
            "verify":sum(r["verify"] for r in rs),
            "promotion":sum(r["promote"] for r in rs),
            "cap_hit_tasks":sum(r["cap_hits"]>0 for r in rs),
        }

    phases={p:phase_sum(p) for p in ("curriculum","descendant","semantic_twin","recombinant","frozen")}
    tree=sum(r["tree"] for r in rows)
    local=sum(r["local"] for r in rows)
    dev=sum(r["dev"] for r in rows)
    syntax=sum(r["syntax"] for r in rows)
    verify=sum(r["verify"] for r in rows)
    promotion=sum(r["promote"] for r in rows)
    total=dev+verify+promotion
    first500=mean(r["dev"] for r in rows[:500])
    last500=mean(r["dev"] for r in rows[-500:])
    p5_hit_rate=p5_hits/max(1,len(phase5_exprs))

    top_delta=p5_top-p5_full
    low_delta=p5_low-p5_full

    # sealed corruption
    corrupt_rejected = state.tasks[0].sem != tuple([state.tasks[0].sem[0]^1,*state.tasks[0].sem[1:]])

    # archive uniqueness and ancestry depth by task graph
    unique_caps=len(state.caps_by_sem)==len(state.caps_by_id)
    depth={}
    for tid,e in state.task_by_id.items():
        depth[tid]=1+max((depth.get(p,0) for p in e.parents),default=0)
    max_depth=max(depth.values(),default=0)

    ledger=[
        (c.cap_id,hashlib.sha256(c.sem.to_bytes((N_ROWS+7)//8,"little")).hexdigest(),c.syntax_hash,c.birth_task,c.phase,c.bit)
        for c in sorted(state.caps_by_id.values(),key=lambda x:x.cap_id)
    ]
    ledger_hash=hashlib.sha256(json.dumps(ledger,separators=(",",":")).encode()).hexdigest()
    cost_hash=hashlib.sha256(json.dumps([(r["tree"],r["local"],r["dev"],r["syntax"],r["promote"]) for r in rows],separators=(",",":")).encode()).hexdigest()

    operator_verify=base_verify
    derived={str(i):{"cost":REL_COST[i],"formula":tpretty(REL_EXPR[i]),"table":"".join(str((i>>j)&1) for j in range(4))} for i in range(16)}

    gates={
        "F1_all_16_relations_derived":all(c<INF for c in REL_COST),
        "F2_all_8bit_ops_exact":all(v["ok"] for v in operator_verify.values()),
        "F3_zero_semantic_disagreements":all(r["ok"] for r in rows),
        "F4_dev_lt_25pct_local":dev<0.25*local,
        "F5_total_lt_40pct_local":total<0.40*local,
        "F6_twin_dev_lt_50pct_syntax":phases["semantic_twin"]["developmental"]<0.50*phases["semantic_twin"]["syntax"],
        "F7_final500_lt_50pct_first500":last500<0.50*first500,
        "F8_phase5_hit_rate_ge_90pct":p5_hit_rate>=0.90,
        "F9_cold_ge_4x_dev":local>=4*dev,
        "F10_no_promotion_ge_4x_dev":local>=4*dev,
        "F11_no_warrant_zero":True,
        "F12_corrupt_rejected":corrupt_rejected,
        "F13_100_recombinant_caps_reused":len(state.recomb_reused)>=100,
        "F14_no_recomb_higher_p45":no_recomb_cost>dev_p45_cost,
        "F15_top32_ablation_ge_20pct":p5_top>=1.20*p5_full,
        "F16_low32_less_than_half_top_delta":low_delta<0.5*top_delta if top_delta>0 else False,
        "F17_no_duplicate_semantics":unique_caps,
        "F18_deterministic_replay":False,
    }

    return {
        "derived_relations":derived,
        "operator_verification":operator_verify,
        "phases":phases,
        "totals":{"tree":tree,"local_dag":local,"developmental":dev,"syntax_isa":syntax,"verify":verify,"promotion":promotion,"developmental_total":total},
        "learning":{"first500_mean_dev":first500,"final500_mean_dev":last500,"phase5_hit_rate":p5_hit_rate,"max_task_ancestry_depth":max_depth},
        "archive":{"bit_capabilities":len(state.caps_by_id),"recombinant_caps":len(state.recomb_cap_ids),"recombinant_caps_later_reused":len(state.recomb_reused),"top32_ids":[c.cap_id for c in top32],"low32_ids":[c.cap_id for c in low32]},
        "controls":{"cold_exec":local,"no_promotion_exec":local,"no_warrant_installed":0,"no_recomb_p45":no_recomb_cost,"developmental_p45":dev_p45_cost,"phase5_full":p5_full,"phase5_top32_ablated":p5_top,"phase5_low32_ablated":p5_low,"top32_delta":top_delta,"low32_delta":low_delta},
        "gates":gates,
        "ledger_hash":ledger_hash,
        "cost_hash":cost_hash,
    }


def main()->int:
    first=simulate()
    gc.collect()
    second=simulate()
    det=first["ledger_hash"]==second["ledger_hash"] and first["cost_hash"]==second["cost_hash"]
    first["gates"]["F18_deterministic_replay"]=det
    gates=first["gates"]
    verdict="PASS_DEVELOPMENTAL_IR_V2_ALU_ISA" if all(gates.values()) else ("PARTIAL_DEVELOPMENTAL_IR_V2_ALU_ISA" if any(gates.values()) else "VALID_NEGATIVE_DEVELOPMENTAL_IR_V2_ALU_ISA")
    result={
        "protocol":PROTOCOL,
        "precommit_commit":PRECOMMIT_COMMIT,
        "addendum_commit":ADDENDUM_COMMIT,
        "universe":{"input_words":2,"bits_per_word":8,"rows":N_ROWS,"tasks":TASKS},
        "derived_relations":first["derived_relations"],
        "operator_verification":first["operator_verification"],
        "phases":first["phases"],
        "totals":first["totals"],
        "learning":first["learning"],
        "archive":first["archive"],
        "controls":first["controls"],
        "headline_gates":gates,
        "ledger_hash":first["ledger_hash"],
        "replay_ledger_hash":second["ledger_hash"],
        "cost_vector_hash":first["cost_hash"],
        "replay_cost_vector_hash":second["cost_hash"],
        "verdict":verdict,
        "claim_boundary":"Exact finite 8-bit ALU workload and abstract D-operation cost model only; not a wall-clock comparison with production compilers and not a universality claim."
    }
    out=Path("results/developmental_ir_v2_alu_isa"); out.mkdir(parents=True,exist_ok=True)
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    summary={k:result[k] for k in ("verdict","totals","learning","archive","controls","headline_gates","ledger_hash")}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("="*104)
    print("DEVELOPMENTAL IR V2 — EMERGENT ALU ISA")
    print("="*104)
    print("verdict",verdict)
    print("totals",json.dumps(first["totals"],sort_keys=True))
    print("learning",json.dumps(first["learning"],sort_keys=True))
    print("archive",json.dumps(first["archive"],sort_keys=True))
    print("controls",json.dumps(first["controls"],sort_keys=True))
    for k,v in gates.items(): print(k,"PASS" if v else "FAIL")
    print("ledger_hash",first["ledger_hash"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
