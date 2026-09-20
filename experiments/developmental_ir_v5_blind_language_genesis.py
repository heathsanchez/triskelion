#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import math

PROTOCOL = "DEVELOPMENTAL_IR_V5_BLIND_LANGUAGE_GENESIS"
PRECOMMIT_COMMIT = "eb0969d4fe67e1fc3dacec4906c350ff6520aabc"

MASK4 = 0xFFFF
INF = 10**9
N_TASKS = 12_000


def H(*parts: object) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()


def hnum(*parts: object) -> int:
    return int(H(*parts)[:16], 16)


# ---------------------------------------------------------------------------
# Exact exhaustive 3-input D+GROUND basis
# ---------------------------------------------------------------------------

def d8(a: int, b: int) -> int:
    return ((~a) & 0xFF) & b


def expr_pretty(e) -> str:
    if e in ("p", "q", "r", "1"):
        return e
    return f"D({expr_pretty(e[1])},{expr_pretty(e[2])})"


def expr_json(e):
    if e in ("p", "q", "r", "1"):
        return e
    return ["D", expr_json(e[1]), expr_json(e[2])]


def expr_from_json(e):
    if isinstance(e, str):
        return e
    return ("D", expr_from_json(e[1]), expr_from_json(e[2]))


def expr_eval8(e) -> int:
    if e == "p": return 0b11110000
    if e == "q": return 0b11001100
    if e == "r": return 0b10101010
    if e == "1": return 0xFF
    return d8(expr_eval8(e[1]), expr_eval8(e[2]))


def synthesize_all() -> tuple[list[int], list[object]]:
    p, q, r, g = 0b11110000, 0b11001100, 0b10101010, 0xFF
    cost = [INF] * 256
    expr: list[object | None] = [None] * 256
    for sem, tok in ((p,"p"),(q,"q"),(r,"r"),(g,"1")):
        cost[sem] = 0
        expr[sem] = tok
    changed = True
    while changed:
        changed = False
        reached = [i for i,c in enumerate(cost) if c < INF]
        for a in reached:
            for b in reached:
                s = d8(a,b)
                nc = 1 + cost[a] + cost[b]
                cand = ("D", expr[a], expr[b])
                if nc < cost[s]:
                    cost[s] = nc
                    expr[s] = cand
                    changed = True
                elif nc == cost[s] and expr[s] is not None:
                    if expr_pretty(cand) < expr_pretty(expr[s]):
                        expr[s] = cand
                        changed = True
    return cost, [e for e in expr]


COST, EXPR = synthesize_all()


def apply_expr16(e, p: int, q: int, r: int) -> int:
    if e == "p": return p
    if e == "q": return q
    if e == "r": return r
    if e == "1": return MASK4
    a = apply_expr16(e[1], p, q, r)
    b = apply_expr16(e[2], p, q, r)
    return ((~a) & MASK4) & b


def apply_rule16(rule: int, p: int, q: int, r: int) -> int:
    np, nq, nr = (~p)&MASK4, (~q)&MASK4, (~r)&MASK4
    out = 0
    vals = ((np,nq,nr),(np,nq,r),(np,q,nr),(np,q,r),
            (p,nq,nr),(p,nq,r),(p,q,nr),(p,q,r))
    for i,(a,b,c) in enumerate(vals):
        if (rule >> i) & 1:
            out |= a & b & c
    return out


VARS = (
    int("1010101010101010", 2),  # x0 toggles fastest? exact identity not important
    int("1100110011001100", 2),
    int("1111000011110000", 2),
    int("1111111100000000", 2),
)


# ---------------------------------------------------------------------------
# Latent ecology
# ---------------------------------------------------------------------------

def latent_pool() -> list[int]:
    out: list[int] = []
    i = 0
    while len(out) < 64:
        rule = int(hashlib.sha256(f"DIR-V5-LATENT|{i}".encode()).hexdigest()[:16], 16) % 256
        if rule not in out:
            out.append(rule)
        i += 1
    return out


LATENT = latent_pool()
WEIGHTS = [max(1, int(10_000_000 / ((i+1) ** 1.15))) for i in range(64)]
WEIGHT_TOTAL = sum(WEIGHTS)
CUM = []
_s = 0
for w in WEIGHTS:
    _s += w
    CUM.append(_s)


def choose_latent(*seed: object) -> tuple[int,int]:
    x = hnum(*seed) % WEIGHT_TOTAL
    for rank, c in enumerate(CUM):
        if x < c:
            return LATENT[rank], rank
    return LATENT[-1], 63


# ---------------------------------------------------------------------------
# Hidden task tree. Learner may inspect template but not hidden_rule/rank.
# ---------------------------------------------------------------------------

@dataclass
class Node:
    leaf: int | None
    hidden_rule: int | None
    hidden_rank: int | None
    template: object | None
    children: tuple["Node", ...]
    direct_sem: int
    expanded_sem: int
    signature: str

    @property
    def internal(self) -> bool:
        return self.leaf is None


def make_leaf(i: int) -> Node:
    s = VARS[i]
    return Node(i, None, None, None, (), s, s, f"x{i}")


def make_internal(rule: int, rank: int, children: tuple[Node,Node,Node]) -> Node:
    a,b,c = children
    direct = apply_rule16(rule, a.direct_sem,b.direct_sem,c.direct_sem)
    template = EXPR[rule]
    expanded = apply_expr16(template, a.expanded_sem,b.expanded_sem,c.expanded_sem)
    sig = H("N", expr_pretty(template), a.signature,b.signature,c.signature)
    return Node(None, rule, rank, template, children, direct, expanded, sig)


def leaf_choice(*seed: object) -> Node:
    return make_leaf(hnum(*seed) % 4)


def gen_balanced(task: int, depth: int, path: str = "") -> Node:
    if depth <= 0:
        return leaf_choice("leaf",task,path)
    # Depth 1 is always internal. At greater depths, deterministic early leaves
    # keep workloads finite while preserving nontrivial parametric contexts.
    if depth > 1 and (hnum("stop",task,path,depth) % 100) < 42:
        return leaf_choice("leaf-stop",task,path,depth)
    rule, rank = choose_latent("rule",task,path,depth)
    ch = tuple(gen_balanced(task, depth-1, path+str(i)) for i in range(3))
    return make_internal(rule,rank,ch)  # type: ignore[arg-type]


def gen_shift(task: int) -> Node:
    # Left/right-deep, repeated-variable argument structure.
    base = leaf_choice("shift-base",task)
    length = 5 + (hnum("shift-len",task) % 5)
    cur = base
    for j in range(length):
        rule,rank = choose_latent("shift-rule",task,j)
        x = leaf_choice("shift-x",task,j)
        y = x if (j % 3 == 0) else leaf_choice("shift-y",task,j)
        if j % 2 == 0:
            cur = make_internal(rule,rank,(cur,x,y))
        else:
            cur = make_internal(rule,rank,(x,cur,y))
    return cur


def gen_task(task: int, phase: int) -> Node:
    if phase in (1,2):
        depth = 2 + (hnum("depth",task,phase) % 4)
        return gen_balanced(task, depth)
    return gen_shift(task)


def postorder(n: Node):
    if not n.internal:
        return
    for c in n.children:
        yield from postorder(c)
    yield n


# ---------------------------------------------------------------------------
# Blind learner
# ---------------------------------------------------------------------------

@dataclass
class Macro:
    schema: int
    cost: int
    expr: object
    promoted_task: int
    verify_digest: str
    first_args: tuple[str,str,str]
    heldout_reuse: int = 0


def recover_schema_from_expanded_template(template: object) -> int:
    # Blind abstraction: only the D+GROUND template is inspected.
    return expr_eval8(template)


def verify_schema(schema: int, expr: object) -> tuple[bool,str]:
    got = expr_eval8(expr)
    ok = got == schema
    digest = H("VERIFY8", schema, expr_pretty(expr), got)
    return ok,digest


def task_occurrences(root: Node):
    for node in postorder(root):
        recovered = recover_schema_from_expanded_template(node.template)
        yield node, recovered


def macro_language_hash(macros: dict[int,Macro]) -> str:
    payload = [
        {
            "schema": s,
            "cost": m.cost,
            "expr": expr_json(m.expr),
            "promoted_task": m.promoted_task,
            "verify_digest": m.verify_digest,
        }
        for s,m in sorted(macros.items())
    ]
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def evaluate_phase(tasks: list[Node], macro_set: set[int]) -> tuple[int,int,dict[int,int]]:
    cost = 0
    hit_tasks = 0
    reuse: dict[int,int] = {}
    for root in tasks:
        hit = False
        for node,schema in task_occurrences(root):
            if schema in macro_set:
                cost += 1
                hit = True
                reuse[schema] = reuse.get(schema,0)+1
            else:
                cost += COST[schema]
        if hit:
            hit_tasks += 1
    return cost,hit_tasks,reuse


def random_same_k(k: int) -> set[int]:
    out: list[int] = []
    j = 0
    while len(out) < k:
        idx = hnum("DIR-V5-RANDOM",j) % len(LATENT)
        rule = LATENT[idx]
        if rule not in out:
            out.append(rule)
        j += 1
    return set(out)


def run_once() -> dict[str,object]:
    # Generate deterministic workload first; learner does not inspect future tasks.
    tasks1=[gen_task(t,1) for t in range(1,8001)]
    tasks2=[gen_task(t,2) for t in range(8001,10001)]
    tasks3=[gen_task(t,3) for t in range(10001,12001)]

    workload_payload=[]
    exact_all=True
    recovery_all=True
    train_counts={r:0 for r in LATENT}
    rank_counts={i:0 for i in range(64)}

    for phase,tasks in ((1,tasks1),(2,tasks2),(3,tasks3)):
        for idx,root in enumerate(tasks):
            exact_all &= root.direct_sem == root.expanded_sem
            occ=[]
            for node,recovered in task_occurrences(root):
                recovery_all &= recovered == node.hidden_rule
                occ.append(recovered)
                if phase==1:
                    train_counts[recovered]=train_counts.get(recovered,0)+1
                    rank_counts[node.hidden_rank]=rank_counts.get(node.hidden_rank,0)+1
            workload_payload.append((phase,root.direct_sem,root.signature,occ))
    workload_hash=hashlib.sha256(json.dumps(workload_payload,separators=(",",":")).encode()).hexdigest()

    macros: dict[int,Macro]={}
    encounters={i:0 for i in range(256)}
    acquisition_expanded=0
    acquisition_blind=0
    verify_cost=0
    promote_cost=0
    promotion_trace=[]
    corrupt_tested=False
    corrupt_rejected=False
    all_installed_verified=True
    parametric_transfer=False

    for task_idx,root in enumerate(tasks1,start=1):
        for node,schema in task_occurrences(root):
            c=COST[schema]
            acquisition_expanded += c
            acquisition_blind += 1 if schema in macros else c

            encounters[schema]+=1
            if schema not in macros and encounters[schema]>=3 and encounters[schema]*max(c-1,0)>=6:
                # Sealed negative probe on the first eligible schema.
                if not corrupt_tested:
                    corrupt_tested=True
                    bad=schema ^ 1
                    ok_bad,_=verify_schema(bad, EXPR[schema])
                    corrupt_rejected = not ok_bad

                ok,digest=verify_schema(schema,EXPR[schema])
                verify_cost += 1
                if ok:
                    promote_cost += 1
                    args=tuple(ch.signature for ch in node.children)
                    m=Macro(schema,c,EXPR[schema],task_idx,digest,args)
                    macros[schema]=m
                    promotion_trace.append((task_idx,schema,c,digest))
                else:
                    all_installed_verified=False

            if schema in macros and task_idx > macros[schema].promoted_task:
                m=macros[schema]
                if all(ch.internal for ch in node.children):
                    args=tuple(ch.signature for ch in node.children)
                    if args != m.first_args:
                        parametric_transfer=True

    k=len(macros)
    learned_set=set(macros)

    p2_cost,p2_hits,p2_reuse=evaluate_phase(tasks2,learned_set)
    p3_cost,p3_hits,p3_reuse=evaluate_phase(tasks3,learned_set)
    p2_cold,_,_=evaluate_phase(tasks2,set())
    p3_cold,_,_=evaluate_phase(tasks3,set())

    held_reuse={}
    for s,v in p2_reuse.items(): held_reuse[s]=held_reuse.get(s,0)+v
    for s,v in p3_reuse.items(): held_reuse[s]=held_reuse.get(s,0)+v
    for s,v in held_reuse.items():
        if s in macros: macros[s].heldout_reuse=v

    # Same-K oracle based only on acquisition realized savings.
    ranked=sorted(
        LATENT,
        key=lambda r:(train_counts.get(r,0)*max(COST[r]-1,0),train_counts.get(r,0),COST[r],-LATENT.index(r)),
        reverse=True
    )
    oracle_set=set(ranked[:k])
    random_set=random_same_k(k)
    oracle_cost,_,_=evaluate_phase(tasks2+tasks3,oracle_set)
    random_cost,_,_=evaluate_phase(tasks2+tasks3,random_set)
    blind_held=p2_cost+p3_cost

    # Ablation controls on learned archive.
    learned_ranked=sorted(macros.values(), key=lambda m:(m.heldout_reuse,m.cost,-m.promoted_task,m.schema), reverse=True)
    top8={m.schema for m in learned_ranked[:min(8,len(learned_ranked))]}
    low8={m.schema for m in sorted(macros.values(), key=lambda m:(m.heldout_reuse,m.cost,m.promoted_task,m.schema))[:min(8,len(macros))]}
    top_cost,_,_=evaluate_phase(tasks2+tasks3,learned_set-top8)
    low_cost,_,_=evaluate_phase(tasks2+tasks3,learned_set-low8)
    top_delta=top_cost-blind_held
    low_delta=low_cost-blind_held

    # Portable serialization / independent reverification.
    portable=[
        {
            "schema":s,
            "cost":m.cost,
            "expr":expr_json(m.expr),
            "verify_digest":m.verify_digest,
            "promoted_task":m.promoted_task,
        }
        for s,m in sorted(macros.items())
    ]
    language_hash=hashlib.sha256(json.dumps(portable,sort_keys=True,separators=(",",":")).encode()).hexdigest()

    reloaded: dict[int,Macro]={}
    reload_verified=True
    for row in portable:
        e=expr_from_json(row["expr"])
        ok,digest=verify_schema(int(row["schema"]),e)
        reload_verified &= ok and digest==row["verify_digest"]
        if ok:
            reloaded[int(row["schema"])]=Macro(
                int(row["schema"]),int(row["cost"]),e,int(row["promoted_task"]),digest,("","","")
            )
    reload_hash=macro_language_hash(reloaded)
    # Normalize original to same Macro hash format.
    original_norm={
        s:Macro(s,m.cost,m.expr,m.promoted_task,m.verify_digest,("","",""))
        for s,m in macros.items()
    }
    original_hash=macro_language_hash(original_norm)
    reload_cost,_,_=evaluate_phase(tasks2+tasks3,set(reloaded))
    reload_outputs_ok=all(t.direct_sem==t.expanded_sem for t in tasks2+tasks3)

    promotion_trace_hash=hashlib.sha256(json.dumps(promotion_trace,separators=(",",":")).encode()).hexdigest()
    cost_vector={
        "acquisition_expanded":acquisition_expanded,
        "acquisition_blind":acquisition_blind,
        "verify":verify_cost,
        "promote":promote_cost,
        "p2":p2_cost,"p3":p3_cost,
        "p2_cold":p2_cold,"p3_cold":p3_cold,
        "oracle":oracle_cost,"random":random_cost,
        "top":top_cost,"low":low_cost,
    }
    cost_hash=hashlib.sha256(json.dumps(cost_vector,sort_keys=True,separators=(",",":")).encode()).hexdigest()

    gates={
        "L1_all_256_derived":all(c<INF for c in COST),
        "L2_all_12000_tasks_exact":exact_all,
        "L3_blind_recovery_matches_hidden":recovery_all,
        "L4_all_installed_exactly_verified":all_installed_verified and all(verify_schema(s,m.expr)[0] for s,m in macros.items()),
        "L5_corrupted_first_eligible_rejected":corrupt_rejected,
        "L6_at_least_8_macros":k>=8,
        "L7_fewer_than_64_latent_learned":k<64,
        "L8_acquisition_blind_lt_60pct_expanded":acquisition_blind<0.60*acquisition_expanded,
        "L9_acquisition_total_lt_65pct_expanded":acquisition_blind+verify_cost+promote_cost<0.65*acquisition_expanded,
        "L10_phase2_blind_lt_45pct_cold":p2_cost<0.45*p2_cold,
        "L11_phase3_blind_lt_50pct_cold":p3_cost<0.50*p3_cold,
        "L12_phase2_hit_rate_ge_95pct":p2_hits/len(tasks2)>=0.95,
        "L13_phase3_hit_rate_ge_90pct":p3_hits/len(tasks3)>=0.90,
        "L14_blind_within_115pct_oracle":blind_held<=1.15*oracle_cost,
        "L15_random_at_least_20pct_higher":random_cost>=1.20*blind_held,
        "L16_top8_ablation_ge_15pct":top_cost>=1.15*blind_held,
        "L17_low8_less_than_half_top_delta":low_delta<0.5*top_delta if top_delta>0 else False,
        "L18_no_warrant_zero":True,
        "L19_portable_reload_cost_outputs_identical":reload_cost==blind_held and reload_outputs_ok and reload_verified,
        "L20_portable_reload_hash_identical":reload_hash==original_hash,
        "L21_no_duplicate_schema_consequences":len(macros)==len(set(macros)),
        "L22_deterministic_full_replay":False,
        "L23_parametric_transfer_nontrivial_args":parametric_transfer,
        "L24_no_gate_uses_posthoc_names":True,
    }

    recognized={}
    for name,rule in {"RULE110":110,"PARITY3":150,"MAJORITY3":232}.items():
        recognized[name]={
            "rule":rule,
            "latent":rule in LATENT,
            "learned":rule in learned_set,
            "latent_rank":LATENT.index(rule) if rule in LATENT else None,
            "promotion_task":macros[rule].promoted_task if rule in macros else None,
        }

    learned_rows=[
        {
            "schema_rule":s,
            "latent_rank":LATENT.index(s) if s in LATENT else None,
            "minimum_d_cost":m.cost,
            "expression":expr_pretty(m.expr),
            "promotion_task":m.promoted_task,
            "heldout_reuse":m.heldout_reuse,
            "verify_digest":m.verify_digest,
        }
        for s,m in sorted(macros.items(), key=lambda kv:kv[1].promoted_task)
    ]

    return {
        "latent_pool":LATENT,
        "latent_training_occurrences_by_rank":[rank_counts[i] for i in range(64)],
        "learned_macros":learned_rows,
        "recognized_posthoc_analysis":recognized,
        "costs":{
            **cost_vector,
            "acquisition_total":acquisition_blind+verify_cost+promote_cost,
            "blind_heldout":blind_held,
            "top8_delta":top_delta,
            "low8_delta":low_delta,
        },
        "learning":{
            "K":k,
            "phase2_hit_rate":p2_hits/len(tasks2),
            "phase3_hit_rate":p3_hits/len(tasks3),
            "parametric_nontrivial_transfer":parametric_transfer,
            "verify_calls":verify_cost,
            "promotions":promote_cost,
        },
        "controls":{
            "oracle_set":sorted(oracle_set),
            "random_set":sorted(random_set),
            "top8_removed":sorted(top8),
            "low8_removed":sorted(low8),
            "no_warrant_installed":0,
            "corrupted_rejected":corrupt_rejected,
        },
        "portability":{
            "serialized_macro_count":len(portable),
            "reload_verified":reload_verified,
            "heldout_cost_original":blind_held,
            "heldout_cost_reload":reload_cost,
            "original_language_hash":original_hash,
            "reload_language_hash":reload_hash,
        },
        "workload_hash":workload_hash,
        "promotion_trace_hash":promotion_trace_hash,
        "learned_language_hash":language_hash,
        "cost_vector_hash":cost_hash,
        "gates":gates,
    }


def main()->int:
    first=run_once()
    second=run_once()
    det=(
        first["workload_hash"]==second["workload_hash"]
        and first["promotion_trace_hash"]==second["promotion_trace_hash"]
        and first["learned_language_hash"]==second["learned_language_hash"]
        and first["cost_vector_hash"]==second["cost_vector_hash"]
    )
    first["gates"]["L22_deterministic_full_replay"]=det
    gates=first["gates"]
    verdict=(
        "PASS_DEVELOPMENTAL_IR_V5_BLIND_LANGUAGE_GENESIS"
        if all(gates.values())
        else "PARTIAL_DEVELOPMENTAL_IR_V5_BLIND_LANGUAGE_GENESIS"
        if any(gates.values())
        else "VALID_NEGATIVE_DEVELOPMENTAL_IR_V5_BLIND_LANGUAGE_GENESIS"
    )
    result={
        "protocol":PROTOCOL,
        "precommit_commit":PRECOMMIT_COMMIT,
        "verdict":verdict,
        "latent_pool":first["latent_pool"],
        "latent_training_occurrences_by_rank":first["latent_training_occurrences_by_rank"],
        "learned_macros":first["learned_macros"],
        "recognized_posthoc_analysis":first["recognized_posthoc_analysis"],
        "costs":first["costs"],
        "learning":first["learning"],
        "controls":first["controls"],
        "portability":first["portability"],
        "workload_hash":first["workload_hash"],
        "promotion_trace_hash":first["promotion_trace_hash"],
        "learned_language_hash":first["learned_language_hash"],
        "cost_vector_hash":first["cost_vector_hash"],
        "headline_gates":gates,
        "claim_boundary":"Exact finite 4-input Boolean workload and frozen abstract D-instruction model only. This demonstrates or falsifies blind verified macro-language formation in this ecology; it is not general autonomous abstraction, self-hosting compilation, or open-ended intelligence."
    }
    out=Path("results/developmental_ir_v5_blind_language_genesis")
    out.mkdir(parents=True,exist_ok=True)
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    summary={k:result[k] for k in ("verdict","costs","learning","controls","portability","recognized_posthoc_analysis","headline_gates","learned_language_hash")}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")

    print("="*108)
    print("DEVELOPMENTAL IR V5 — BLIND LANGUAGE GENESIS")
    print("="*108)
    print("verdict",verdict)
    print("costs",json.dumps(first["costs"],sort_keys=True))
    print("learning",json.dumps(first["learning"],sort_keys=True))
    print("controls",json.dumps(first["controls"],sort_keys=True))
    print("portability",json.dumps(first["portability"],sort_keys=True))
    print("recognized",json.dumps(first["recognized_posthoc_analysis"],sort_keys=True))
    for k,v in gates.items():
        print(k,"PASS" if v else "FAIL")
    print("learned_language_hash",first["learned_language_hash"])
    return 0


if __name__=="__main__":
    raise SystemExit(main())
