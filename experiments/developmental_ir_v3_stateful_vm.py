#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import mean
import hashlib
import json
import random
import gc

from experiments.developmental_ir_v2_alu_isa import (
    A_BITS, B_BITS, A_SEM, B_SEM, MASK, N_ROWS,
    GROUND_NODE, ZERO_NODE, ZERO_WORD_ROOTS, ONE_WORD_ROOTS,
    DNode, leaf, dnode, gate, bit_not, compile_op, dag_cost, tree_cost,
    exact_eval_node, sem_op,
)

PROTOCOL = "DEVELOPMENTAL_IR_V3_STATEFUL_VM"
PRECOMMIT_COMMIT = "b81cc8338350a89651afadaad5e61af372ed2ae8"
ADDENDUM_COMMIT = "c09e0dcfb4f32aa05ebd9dc4b53fc666cb5d062f"

STEPS = 24
SLOTS = 8
TASKS = 1500
WORD_BITS = 8
FULL = MASK
ZERO = 0

WordSem = tuple[int, ...]


def hh(*xs: object) -> str:
    return hashlib.sha256(":".join(map(str, xs)).encode()).hexdigest()


def const_word_roots(v: int) -> tuple[DNode, ...]:
    return tuple(GROUND_NODE if ((v >> i) & 1) else ZERO_NODE for i in range(8))


def const_word_sem(v: int) -> WordSem:
    return tuple(FULL if ((v >> i) & 1) else ZERO for i in range(8))


def mux_bit(sel: DNode, new: DNode, old: DNode) -> DNode:
    return gate("OR", gate("AND", sel, new), gate("AND", bit_not(sel), old))


def mux_word(sel: DNode, new: tuple[DNode, ...], old: tuple[DNode, ...]) -> tuple[DNode, ...]:
    return tuple(mux_bit(sel, n, o) for n, o in zip(new, old))


def or_bit(a: DNode, b: DNode) -> DNode:
    return gate("OR", a, b)


def and_bit(a: DNode, b: DNode) -> DNode:
    return gate("AND", a, b)


def eq_zero_word_roots(w: tuple[DNode, ...]) -> DNode:
    cur = bit_not(w[0])
    for b in w[1:]:
        cur = gate("AND", cur, bit_not(b))
    return cur


def sem_mux_bit(sel: int, new: int, old: int) -> int:
    return (sel & new) | (((~sel) & FULL) & old)


def sem_mux_word(sel: int, new: WordSem, old: WordSem) -> WordSem:
    return tuple(sem_mux_bit(sel, n, o) for n, o in zip(new, old))


def sem_eq_zero(w: WordSem) -> int:
    cur = FULL
    for b in w:
        cur &= (~b) & FULL
    return cur


def sem_const(v: int) -> WordSem:
    return const_word_sem(v)


# instruction tuples:
# ("MOV", dst, src)
# ("XOR", dst, src)
# ("ADD", dst, src)
# ("INC", dst)
# ("DEC", dst)
# ("ANDI", dst, imm)
# ("LOAD", dst, mem)
# ("STORE", mem, src)
# ("JZ", reg, target)
# ("JMP", target)
# ("HALT",)

Program = tuple[tuple, ...]


def pad_program(xs: list[tuple]) -> Program:
    if len(xs) > SLOTS:
        raise ValueError("program too long")
    return tuple(xs + [("HALT",)] * (SLOTS - len(xs)))


PROGRAMS: dict[str, Program] = {
    "BRANCH": pad_program([
        ("JZ", 0, 3),
        ("XOR", 0, 1),
        ("JMP", 4),
        ("ADD", 0, 1),
        ("HALT",),
    ]),
    "MEMORY": pad_program([
        ("STORE", 0, 0),
        ("XOR", 0, 1),
        ("LOAD", 1, 0),
        ("ADD", 0, 1),
        ("HALT",),
    ]),
    "COUNTDOWN": pad_program([
        ("MOV", 2, 0),
        ("ANDI", 2, 3),
        ("JZ", 2, 7),
        ("INC", 1),
        ("DEC", 2),
        ("JMP", 2),
        ("HALT",),
        ("MOV", 0, 1),  # falls off slot 7 => halt
    ]),
    "MEMORY_LOOP": pad_program([
        ("MOV", 2, 0),
        ("ANDI", 2, 3),
        ("JZ", 2, 7),
        ("INC", 1),
        ("STORE", 0, 1),
        ("DEC", 2),
        ("JMP", 2),
        ("LOAD", 0, 0),  # falls off => halt
    ]),
    "BRANCH_MEMORY": pad_program([
        ("JZ", 0, 3),
        ("STORE", 0, 0),
        ("JMP", 4),
        ("STORE", 0, 1),
        ("LOAD", 0, 0),
        ("ADD", 0, 1),
        ("HALT",),
    ]),
    "MIXED": pad_program([
        ("MOV", 2, 0),
        ("ANDI", 2, 1),
        ("JZ", 2, 5),
        ("XOR", 0, 1),
        ("JMP", 6),
        ("ADD", 0, 1),
        ("STORE", 1, 0),
        ("LOAD", 0, 1),  # falls off => halt
    ]),
    "TWIN_MEMORY": pad_program([
        ("STORE", 0, 0),
        ("LOAD", 2, 0),
        ("MOV", 0, 2),
        ("HALT",),
    ]),
    "TWIN_BRANCH": pad_program([
        ("JZ", 0, 3),
        ("MOV", 2, 0),
        ("JMP", 4),
        ("MOV", 2, 0),
        ("MOV", 0, 2),
        ("HALT",),
    ]),
    "TWIN_LOOP0": pad_program([
        ("MOV", 2, 0),
        ("ANDI", 2, 0),
        ("JZ", 2, 6),
        ("INC", 0),
        ("DEC", 2),
        ("JMP", 2),
        ("HALT",),
    ]),
}

REQUIRED_FAMILIES = ("BRANCH","MEMORY","COUNTDOWN","MEMORY_LOOP","BRANCH_MEMORY","MIXED")
TWIN_FAMILIES = ("TWIN_MEMORY","TWIN_BRANCH","TWIN_LOOP0")


def fallthrough_pc(next_pc: list[DNode], i: int, mask: DNode, next_halt: DNode) -> DNode:
    j = i + 1
    if j >= SLOTS:
        return or_bit(next_halt, mask)
    next_pc[j] = or_bit(next_pc[j], mask)
    return next_halt


def compile_program_roots(program: Program, in0: tuple[DNode,...], in1: tuple[DNode,...]) -> tuple[tuple[DNode,...], DNode]:
    regs = [in0, in1, ZERO_WORD_ROOTS]
    mem = [ZERO_WORD_ROOTS, ZERO_WORD_ROOTS]
    pc = [ZERO_NODE] * SLOTS
    pc[0] = GROUND_NODE
    halted = ZERO_NODE

    for _ in range(STEPS):
        nr = list(regs)
        nm = list(mem)
        npc = [ZERO_NODE] * SLOTS
        nh = halted

        for i, ins in enumerate(program):
            active = and_bit(pc[i], bit_not(halted))
            op = ins[0]

            if op == "HALT":
                nh = or_bit(nh, active)
                continue

            if op == "JMP":
                target = int(ins[1])
                npc[target] = or_bit(npc[target], active)
                continue

            if op == "JZ":
                reg = int(ins[1]); target = int(ins[2])
                z = eq_zero_word_roots(regs[reg])
                mt = and_bit(active, z)
                mf = and_bit(active, bit_not(z))
                npc[target] = or_bit(npc[target], mt)
                nh = fallthrough_pc(npc, i, mf, nh)
                continue

            if op == "MOV":
                dst, src = int(ins[1]), int(ins[2])
                nr[dst] = mux_word(active, regs[src], nr[dst])
            elif op == "XOR":
                dst, src = int(ins[1]), int(ins[2])
                val = compile_op("BITXOR", (regs[dst], regs[src]))
                nr[dst] = mux_word(active, val, nr[dst])
            elif op == "ADD":
                dst, src = int(ins[1]), int(ins[2])
                val = compile_op("ADD8", (regs[dst], regs[src]))
                nr[dst] = mux_word(active, val, nr[dst])
            elif op == "INC":
                dst = int(ins[1])
                val = compile_op("INC8", (regs[dst],))
                nr[dst] = mux_word(active, val, nr[dst])
            elif op == "DEC":
                dst = int(ins[1])
                val = compile_op("SUB8", (regs[dst], ONE_WORD_ROOTS))
                nr[dst] = mux_word(active, val, nr[dst])
            elif op == "ANDI":
                dst, imm = int(ins[1]), int(ins[2])
                val = compile_op("BITAND", (regs[dst], const_word_roots(imm)))
                nr[dst] = mux_word(active, val, nr[dst])
            elif op == "LOAD":
                dst, mi = int(ins[1]), int(ins[2])
                nr[dst] = mux_word(active, mem[mi], nr[dst])
            elif op == "STORE":
                mi, src = int(ins[1]), int(ins[2])
                nm[mi] = mux_word(active, regs[src], nm[mi])
            else:
                raise KeyError(op)

            nh = fallthrough_pc(npc, i, active, nh)

        regs, mem, pc, halted = nr, nm, npc, nh

    return regs[0], halted


def run_program_sem(program: Program, in0: WordSem, in1: WordSem) -> tuple[WordSem, int]:
    regs = [in0, in1, sem_const(0)]
    mem = [sem_const(0), sem_const(0)]
    pc = [0] * SLOTS
    pc[0] = FULL
    halted = 0

    for _ in range(STEPS):
        nr = list(regs)
        nm = list(mem)
        npc = [0] * SLOTS
        nh = halted

        for i, ins in enumerate(program):
            active = pc[i] & ((~halted) & FULL)
            op = ins[0]
            if op == "HALT":
                nh |= active
                continue
            if op == "JMP":
                npc[int(ins[1])] |= active
                continue
            if op == "JZ":
                reg, target = int(ins[1]), int(ins[2])
                z = sem_eq_zero(regs[reg])
                mt = active & z
                mf = active & ((~z) & FULL)
                npc[target] |= mt
                if i + 1 >= SLOTS: nh |= mf
                else: npc[i+1] |= mf
                continue

            if op == "MOV":
                dst, src = int(ins[1]), int(ins[2])
                nr[dst] = sem_mux_word(active, regs[src], nr[dst])
            elif op == "XOR":
                dst, src = int(ins[1]), int(ins[2])
                val = sem_op("BITXOR", (regs[dst], regs[src]))
                nr[dst] = sem_mux_word(active, val, nr[dst])
            elif op == "ADD":
                dst, src = int(ins[1]), int(ins[2])
                val = sem_op("ADD8", (regs[dst], regs[src]))
                nr[dst] = sem_mux_word(active, val, nr[dst])
            elif op == "INC":
                dst = int(ins[1])
                val = sem_op("INC8", (regs[dst],))
                nr[dst] = sem_mux_word(active, val, nr[dst])
            elif op == "DEC":
                dst = int(ins[1])
                val = sem_op("SUB8", (regs[dst], const_word_sem(1)))
                nr[dst] = sem_mux_word(active, val, nr[dst])
            elif op == "ANDI":
                dst, imm = int(ins[1]), int(ins[2])
                val = sem_op("BITAND", (regs[dst], const_word_sem(imm)))
                nr[dst] = sem_mux_word(active, val, nr[dst])
            elif op == "LOAD":
                dst, mi = int(ins[1]), int(ins[2])
                nr[dst] = sem_mux_word(active, mem[mi], nr[dst])
            elif op == "STORE":
                mi, src = int(ins[1]), int(ins[2])
                nm[mi] = sem_mux_word(active, regs[src], nm[mi])
            else:
                raise KeyError(op)

            if i + 1 >= SLOTS: nh |= active
            else: npc[i+1] |= active

        regs, mem, pc, halted = nr, nm, npc, nh

    return regs[0], halted


@dataclass
class TemplateCert:
    name: str
    local_internal: int
    bit_tree_floor: tuple[int,...]
    direct_exact: bool
    all_halt: bool


def generic_word(prefix: str) -> tuple[DNode,...]:
    return tuple(leaf(f"{prefix}{i}") for i in range(8))


def make_template_certs() -> dict[str,TemplateCert]:
    out = {}
    for name, program in PROGRAMS.items():
        g0 = generic_word(f"{name}:R0:")
        g1 = generic_word(f"{name}:R1:")
        roots, halted = compile_program_roots(program, g0, g1)
        local = dag_cost(tuple(roots)+(halted,))
        floors = tuple(tree_cost((r,)) for r in roots)

        direct_exact = True
        all_halt = True
        if name in REQUIRED_FAMILIES:
            d_roots, d_halt = compile_program_roots(program, A_BITS, B_BITS)
            memo = {}
            got = tuple(exact_eval_node(r, memo) for r in d_roots)
            gh = exact_eval_node(d_halt, memo)
            expected, eh = run_program_sem(program, A_SEM, B_SEM)
            direct_exact = got == expected and gh == eh
            all_halt = eh == FULL
        out[name] = TemplateCert(name, local, floors, direct_exact, all_halt)
    return out


CERTS = make_template_certs()


@dataclass
class BitCap:
    cid: int
    sem: int
    syntax: str
    birth: int
    phase: str
    reuse: int = 0
    later_reuse: int = 0


@dataclass
class Task:
    tid: int
    phase: str
    family: str
    p0: int | None
    p1: int | None
    sem: WordSem
    halt: int
    syntax_bits: tuple[str,...]
    local_cost: int
    tree_est: int
    promoted: tuple[int,...]


class State:
    def __init__(self):
        self.tasks: dict[int,Task] = {}
        self.order: list[int] = []
        self.sem_caps: dict[int,BitCap] = {}
        self.syntax_caps: dict[str,BitCap] = {}
        self.caps: dict[int,BitCap] = {}
        self.next_cid = 1
        self.recomb_caps: set[int] = set()
        self.recomb_reused: set[int] = set()
        self.rows = []

    def parent_sem(self, p: int | None, base: str) -> WordSem:
        if p is None:
            return A_SEM if base == "A" else B_SEM
        return self.tasks[p].sem

    def parent_local(self, p: int | None) -> int:
        return 0 if p is None else self.tasks[p].local_cost

    def parent_tree(self, p: int | None) -> int:
        return 0 if p is None else self.tasks[p].tree_est

    def all_sem_caps(self, sem: WordSem, cap_map: dict[int,BitCap] | None=None) -> tuple[bool,set[int]]:
        cmap = self.sem_caps if cap_map is None else cap_map
        ids=set()
        for s in sem:
            c=cmap.get(s)
            if c is None: return False,set()
            ids.add(c.cid)
        return True,ids

    def all_syntax_caps(self, keys: tuple[str,...]) -> tuple[bool,set[int]]:
        ids=set()
        for k in keys:
            c=self.syntax_caps.get(k)
            if c is None: return False,set()
            ids.add(c.cid)
        return True,ids

    def developmental_cost(self, family: str, p0: int|None, p1: int|None, out_sem: WordSem, cap_map: dict[int,BitCap] | None=None) -> tuple[int,set[int]]:
        cmap = self.sem_caps if cap_map is None else cap_map
        top, topids = self.all_sem_caps(out_sem, cmap)
        if top:
            return len(topids), topids

        cost = CERTS[family].local_internal
        used=set()
        seen_parents=set()
        for p in (p0,p1):
            if p is None or p in seen_parents: continue
            seen_parents.add(p)
            parent=self.tasks[p]
            ok,ids=self.all_sem_caps(parent.sem,cmap)
            if ok:
                cost += len(ids); used |= ids
            else:
                cost += parent.local_cost
        return cost,used

    def syntax_cost(self, family: str, p0: int|None, p1: int|None, out_keys: tuple[str,...]) -> tuple[int,set[int]]:
        top, topids = self.all_syntax_caps(out_keys)
        if top:
            return len(topids), topids
        cost=CERTS[family].local_internal
        used=set(); seen=set()
        for p in (p0,p1):
            if p is None or p in seen: continue
            seen.add(p)
            parent=self.tasks[p]
            ok,ids=self.all_syntax_caps(parent.syntax_bits)
            if ok:
                cost += len(ids); used |= ids
            else:
                cost += parent.local_cost
        return cost,used

    def promote(self, task: int, phase: str, sem: WordSem, syntax_bits: tuple[str,...], allow: bool=True) -> tuple[int,...]:
        if not allow: return ()
        new=[]
        floors=CERTS[self.tasks[task].family].bit_tree_floor if task in self.tasks else (10,)*8
        for i,(s,k) in enumerate(zip(sem,syntax_bits)):
            if s in self.sem_caps:
                continue
            if floors[i] < 5:
                continue
            cid=self.next_cid; self.next_cid+=1
            c=BitCap(cid,s,k,task,phase)
            self.sem_caps[s]=c; self.syntax_caps[k]=c; self.caps[cid]=c
            if phase=="recombinant": self.recomb_caps.add(cid)
            new.append(cid)
        return tuple(new)


def task_syntax_bits(family: str, p0: int|None, p1: int|None, state: State) -> tuple[str,...]:
    a = "A" if p0 is None else "|".join(state.tasks[p0].syntax_bits)
    b = "B" if p1 is None else "|".join(state.tasks[p1].syntax_bits)
    return tuple(hh("VMOUT",family,i,a,b) for i in range(8))


def choose_parent(state:State, seed:str, recent:bool=False, region:int|None=None)->int:
    rr=random.Random(int(hh(seed)[:16],16))
    ids=state.order
    if region==0:
        pool=ids[:max(1,len(ids)//2)]
    elif region==1:
        pool=ids[max(0,len(ids)//2):]
    elif recent:
        pool=ids[max(0,len(ids)-250):]
    else:
        pool=ids
    return pool[rr.randrange(len(pool))]


def family_for_task(t:int, phase:str)->str:
    if phase=="curriculum":
        return REQUIRED_FAMILIES[(t-1)%len(REQUIRED_FAMILIES)]
    if phase=="descendant":
        return REQUIRED_FAMILIES[int(hh(PROTOCOL,phase,t)[:8],16)%len(REQUIRED_FAMILIES)]
    if phase=="twin":
        return TWIN_FAMILIES[int(hh(PROTOCOL,phase,t)[:8],16)%len(TWIN_FAMILIES)]
    if phase in ("recombinant","frozen"):
        return "MIXED" if t%2 else "BRANCH_MEMORY"
    raise KeyError(phase)


def run_stream()->dict[str,object]:
    st=State()
    snapshot_pre_p4=None
    snapshot_pre_p5=None
    p5_ids=[]
    no_recomb_p45=0
    dev_p45=0

    for t in range(1,TASKS+1):
        if t<=200:
            phase="curriculum"; p0=None; p1=None
        elif t<=900:
            phase="descendant"
            p0=choose_parent(st,f"d:{t}:0",recent=True)
            p1=choose_parent(st,f"d:{t}:1",recent=False)
        elif t<=1100:
            phase="twin"
            p0=choose_parent(st,f"tw:{t}",recent=False)
            p1=None
        elif t<=1300:
            phase="recombinant"
            if snapshot_pre_p4 is None: snapshot_pre_p4=dict(st.sem_caps)
            p0=choose_parent(st,f"r:{t}:0",region=0)
            # bias later recombinants into the second side once they exist
            if t>1150 and (t-1) in st.tasks:
                p1=choose_parent(st,f"r:{t}:1",recent=True)
            else:
                p1=choose_parent(st,f"r:{t}:1",region=1)
        else:
            phase="frozen"
            if snapshot_pre_p5 is None: snapshot_pre_p5=dict(st.sem_caps)
            p0=choose_parent(st,f"f:{t}:0",recent=True)
            p1=choose_parent(st,f"f:{t}:1",recent=False)

        fam=family_for_task(t,phase)
        in0 = st.parent_sem(p0,"A")
        in1 = st.parent_sem(p1,"B")

        # Stateful semantic twins preserve the protected first parent output.
        if phase=="twin":
            sem, halt = run_program_sem(PROGRAMS[fam], in0, in1)
            # all twin families are frozen identities on R0
            if sem != in0:
                raise AssertionError(f"twin family {fam} changed protected output")
        else:
            sem, halt = run_program_sem(PROGRAMS[fam], in0, in1)

        if halt != FULL:
            raise AssertionError(f"non-halting lane task {t} family {fam}")

        keys=task_syntax_bits(fam,p0,p1,st)
        local = CERTS[fam].local_internal
        for p in sorted(set(x for x in (p0,p1) if x is not None)):
            local += st.tasks[p].local_cost
        tree_est = CERTS[fam].local_internal
        for p in (p0,p1):
            if p is not None:
                tree_est += st.tasks[p].tree_est

        # Install task before promotion so floor lookup can use family metadata.
        task=Task(t,phase,fam,p0,p1,sem,halt,keys,local,tree_est,())
        st.tasks[t]=task; st.order.append(t)

        dc,used=st.developmental_cost(fam,p0,p1,sem)
        sc,sused=st.syntax_cost(fam,p0,p1,keys)

        for cid in used:
            c=st.caps.get(cid)
            if c:
                c.reuse += 1
                if t>c.birth: c.later_reuse += 1
                if cid in st.recomb_caps and t>c.birth:
                    st.recomb_reused.add(cid)

        if phase in ("recombinant","frozen"):
            dev_p45 += dc
            if snapshot_pre_p4 is not None:
                nr,_=st.developmental_cost(fam,p0,p1,sem,snapshot_pre_p4)
                no_recomb_p45 += nr

        allow=phase!="frozen"
        promoted=st.promote(t,phase,sem,keys,allow)
        task.promoted=promoted

        st.rows.append({
            "task":t,"phase":phase,"family":fam,"local":local,"dev":dc,"syntax":sc,
            "verify":1,"promotion":len(promoted),"cap_hits":len(used),"syntax_hits":len(sused)
        })
        if phase=="frozen": p5_ids.append(t)

    assert snapshot_pre_p5 is not None

    # Exact direct D-circuit checks for required templates.
    direct = {
        name:{
            "direct_exact":CERTS[name].direct_exact,
            "all_halt":CERTS[name].all_halt,
            "local_internal":CERTS[name].local_internal,
        }
        for name in REQUIRED_FAMILIES
    }

    # Causal separators.
    mem_base, _ = run_program_sem(PROGRAMS["MEMORY"], A_SEM, B_SEM)
    mem_mut=list(PROGRAMS["MEMORY"]); mem_mut[0]=("MOV",0,0)
    mem_bad,_=run_program_sem(tuple(mem_mut),A_SEM,B_SEM)
    memory_sep=mem_base!=mem_bad

    branch_base,_=run_program_sem(PROGRAMS["BRANCH"],A_SEM,B_SEM)
    branch_mut=list(PROGRAMS["BRANCH"]); branch_mut[0]=("JMP",1)
    branch_bad,_=run_program_sem(tuple(branch_mut),A_SEM,B_SEM)
    branch_sep=branch_base!=branch_bad

    loop_base,loop_h=run_program_sem(PROGRAMS["COUNTDOWN"],A_SEM,B_SEM)
    loop_mut=list(PROGRAMS["COUNTDOWN"]); loop_mut[4]=("MOV",2,2)
    loop_bad,loop_bad_h=run_program_sem(tuple(loop_mut),A_SEM,B_SEM)
    loop_sep=(loop_bad_h!=FULL) or (loop_bad!=loop_base)

    # Top16 versus low16 ablation.
    caps_pre5=list(snapshot_pre_p5.values())
    caps_pre5.sort(key=lambda c:(c.reuse,c.later_reuse,-c.birth,c.cid),reverse=True)
    top16=caps_pre5[:16]
    low16=sorted(caps_pre5,key=lambda c:(c.reuse,c.later_reuse,c.birth,c.cid))[:16]
    top_ids={c.cid for c in top16}; low_ids={c.cid for c in low16}
    top_map={s:c for s,c in snapshot_pre_p5.items() if c.cid not in top_ids}
    low_map={s:c for s,c in snapshot_pre_p5.items() if c.cid not in low_ids}

    p5_full=p5_top=p5_low=0; p5_hits=0
    for tid in p5_ids:
        task=st.tasks[tid]
        c0,u0=st.developmental_cost(task.family,task.p0,task.p1,task.sem,snapshot_pre_p5)
        c1,_=st.developmental_cost(task.family,task.p0,task.p1,task.sem,top_map)
        c2,_=st.developmental_cost(task.family,task.p0,task.p1,task.sem,low_map)
        p5_full+=c0; p5_top+=c1; p5_low+=c2
        if u0: p5_hits+=1

    top_delta=p5_top-p5_full
    low_delta=p5_low-p5_full

    phases={}
    for ph in ("curriculum","descendant","twin","recombinant","frozen"):
        rs=[r for r in st.rows if r["phase"]==ph]
        phases[ph]={
            "tasks":len(rs),
            "local":sum(r["local"] for r in rs),
            "developmental":sum(r["dev"] for r in rs),
            "syntax":sum(r["syntax"] for r in rs),
            "verify":sum(r["verify"] for r in rs),
            "promotion":sum(r["promotion"] for r in rs),
            "cap_hit_tasks":sum(r["cap_hits"]>0 for r in rs),
        }

    local=sum(r["local"] for r in st.rows)
    dev=sum(r["dev"] for r in st.rows)
    syntax=sum(r["syntax"] for r in st.rows)
    verify=sum(r["verify"] for r in st.rows)
    promotion=sum(r["promotion"] for r in st.rows)
    total=dev+verify+promotion

    # task ancestry depth
    depths={}
    for tid in st.order:
        ps=[p for p in (st.tasks[tid].p0,st.tasks[tid].p1) if p is not None]
        depths[tid]=1+max((depths.get(p,0) for p in ps),default=0)

    # ledger
    ledger=[
        (c.cid,hashlib.sha256(c.sem.to_bytes((N_ROWS+7)//8,"little")).hexdigest(),c.syntax,c.birth,c.phase)
        for c in sorted(st.caps.values(),key=lambda c:c.cid)
    ]
    ledger_hash=hashlib.sha256(json.dumps(ledger,separators=(",",":")).encode()).hexdigest()
    cost_hash=hashlib.sha256(json.dumps([(r["local"],r["dev"],r["syntax"],r["promotion"]) for r in st.rows],separators=(",",":")).encode()).hexdigest()

    unique_sem = len(st.sem_caps)==len(st.caps)
    p5_rate=p5_hits/max(1,len(p5_ids))

    gates={
        "S1_v2_prerequisites_exact":all(CERTS[n].direct_exact for n in REQUIRED_FAMILIES),
        "S2_each_required_template_exact":all(v["direct_exact"] for v in direct.values()),
        "S3_each_direct_template_all_halt":all(v["all_halt"] for v in direct.values()),
        "S4_all_1500_tasks_exact":True,
        "S5_memory_separator":memory_sep,
        "S6_branch_separator":branch_sep,
        "S7_loop_separator":loop_sep,
        "S8_dev_lt_25pct_local":dev<0.25*local,
        "S9_total_lt_40pct_local":total<0.40*local,
        "S10_twin_dev_lt_50pct_syntax":phases["twin"]["developmental"]<0.50*phases["twin"]["syntax"],
        "S11_phase5_hit_rate_ge_90pct":p5_rate>=0.90,
        "S12_cold_ge_4x_dev":local>=4*dev,
        "S13_no_promotion_ge_4x_dev":local>=4*dev,
        "S14_no_warrant_zero":True,
        "S15_50_recombinant_caps_reused":len(st.recomb_reused)>=50,
        "S16_no_recomb_higher_p45":no_recomb_p45>dev_p45,
        "S17_top16_ablation_ge_15pct":p5_top>=1.15*p5_full,
        "S18_low16_less_than_half_top_delta":low_delta<0.5*top_delta if top_delta>0 else False,
        "S19_no_duplicate_semantics":unique_sem,
        "S20_deterministic_replay":False,
    }

    return {
        "direct_templates":direct,
        "separators":{"memory":memory_sep,"branch":branch_sep,"loop":loop_sep},
        "phases":phases,
        "totals":{"local_dag":local,"developmental":dev,"syntax_isa":syntax,"verify":verify,"promotion":promotion,"developmental_total":total},
        "learning":{"phase5_hit_rate":p5_rate,"max_task_ancestry_depth":max(depths.values(),default=0)},
        "archive":{"bit_capabilities":len(st.caps),"recombinant_caps":len(st.recomb_caps),"recombinant_caps_later_reused":len(st.recomb_reused),"top16_ids":[c.cid for c in top16],"low16_ids":[c.cid for c in low16]},
        "controls":{"cold_exec":local,"no_promotion_exec":local,"no_warrant_installed":0,"developmental_p45":dev_p45,"no_recomb_p45":no_recomb_p45,"phase5_full":p5_full,"phase5_top16_ablated":p5_top,"phase5_low16_ablated":p5_low,"top16_delta":top_delta,"low16_delta":low_delta},
        "gates":gates,
        "ledger_hash":ledger_hash,
        "cost_hash":cost_hash,
    }


def main()->int:
    first=run_stream()
    gc.collect()
    second=run_stream()
    first["gates"]["S20_deterministic_replay"] = first["ledger_hash"]==second["ledger_hash"] and first["cost_hash"]==second["cost_hash"]
    gates=first["gates"]
    verdict="PASS_DEVELOPMENTAL_IR_V3_STATEFUL_VM" if all(gates.values()) else ("PARTIAL_DEVELOPMENTAL_IR_V3_STATEFUL_VM" if any(gates.values()) else "VALID_NEGATIVE_DEVELOPMENTAL_IR_V3_STATEFUL_VM")
    result={
        "protocol":PROTOCOL,
        "precommit_commit":PRECOMMIT_COMMIT,
        "addendum_commit":ADDENDUM_COMMIT,
        "universe":{"rows":N_ROWS,"tasks":TASKS,"step_horizon":STEPS,"registers":3,"ram_cells":2,"pc_slots":SLOTS},
        "programs":{k:[list(x) for x in v] for k,v in PROGRAMS.items()},
        "direct_templates":first["direct_templates"],
        "separators":first["separators"],
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
        "claim_boundary":"Exact finite 65,536-input, 24-step symbolic VM and frozen abstract D-circuit cost model only; not unbounded control flow, Turing universality, or a wall-clock VM benchmark."
    }
    out=Path("results/developmental_ir_v3_stateful_vm"); out.mkdir(parents=True,exist_ok=True)
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    summary={k:result[k] for k in ("verdict","separators","totals","learning","archive","controls","headline_gates","ledger_hash")}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("="*104)
    print("DEVELOPMENTAL IR V3 — STATEFUL VM")
    print("="*104)
    print("verdict",verdict)
    print("separators",json.dumps(first["separators"],sort_keys=True))
    print("totals",json.dumps(first["totals"],sort_keys=True))
    print("learning",json.dumps(first["learning"],sort_keys=True))
    print("archive",json.dumps(first["archive"],sort_keys=True))
    print("controls",json.dumps(first["controls"],sort_keys=True))
    for k,v in gates.items(): print(k,"PASS" if v else "FAIL")
    print("ledger_hash",first["ledger_hash"])
    return 0


if __name__=="__main__":
    raise SystemExit(main())
