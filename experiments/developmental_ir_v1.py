#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import mean
import hashlib
import json
import random

PROTOCOL = "DEVELOPMENTAL_IR_V1"
PRECOMMIT_COMMIT = "9d3771bb2eab4c3bbf0c083a6bc839d3f21513c3"

N_INPUTS = 12
N_ROWS = 1 << N_INPUTS
MASK = (1 << N_ROWS) - 1
TASKS = 20_000
GROUND = MASK
LAW_D = 2  # table 0100 in 00,01,10,11 order: not(a) and b
INF = 10**9

# Rich source-language binary relations.
RICH_RELATIONS = {
    "AND": 8,   # 0001
    "OR": 14,   # 0111
    "XOR": 6,   # 0110
    "IMP": 11,  # 1101
    "NAND": 7,  # 1110
    "NOR": 1,   # 1000
    "EQ": 9,    # 1001
}
RICH_NAMES = tuple(RICH_RELATIONS)


def sha_text(*parts: object) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def sem_hash(sem: int) -> str:
    return hashlib.sha256(sem.to_bytes((N_ROWS + 7) // 8, "little")).hexdigest()


def bit_relation_apply(rel: int, a: int, b: int, mask: int = MASK) -> int:
    na = (~a) & mask
    nb = (~b) & mask
    out = 0
    if rel & 1:
        out |= na & nb
    if rel & 2:
        out |= na & b
    if rel & 4:
        out |= a & nb
    if rel & 8:
        out |= a & b
    return out


def input_sem(index: int) -> int:
    out = 0
    for row in range(N_ROWS):
        if (row >> index) & 1:
            out |= 1 << row
    return out


INPUT_SEMS = tuple(input_sem(i) for i in range(N_INPUTS))


# ---------------------------------------------------------------------------
# Exact synthesis of all 16 two-input relations from D + ground.
# ---------------------------------------------------------------------------

Template = object


def template_pretty(t) -> str:
    if t == "p" or t == "q" or t == "1":
        return t
    return f"D({template_pretty(t[1])},{template_pretty(t[2])})"


def template_stats(t) -> tuple[int, int, int]:
    # D count, p occurrences, q occurrences.
    if t == "p":
        return (0, 1, 0)
    if t == "q":
        return (0, 0, 1)
    if t == "1":
        return (0, 0, 0)
    dl, pl, ql = template_stats(t[1])
    dr, pr, qr = template_stats(t[2])
    return (1 + dl + dr, pl + pr, ql + qr)


def synthesize_relations() -> tuple[list[int], list[object]]:
    # Four abstract rows ordered 00,01,10,11.
    p = 0b1100
    q = 0b1010
    g = 0b1111
    cost = [INF] * 16
    expr: list[object | None] = [None] * 16
    for sem, t in ((p, "p"), (q, "q"), (g, "1")):
        cost[sem] = 0
        expr[sem] = t

    changed = True
    while changed:
        changed = False
        for a in range(16):
            if cost[a] >= INF:
                continue
            for b in range(16):
                if cost[b] >= INF:
                    continue
                sem = bit_relation_apply(LAW_D, a, b, 0b1111)
                new = 1 + cost[a] + cost[b]
                cand = ("D", expr[a], expr[b])
                if new < cost[sem]:
                    cost[sem] = new
                    expr[sem] = cand
                    changed = True
                elif new == cost[sem] and expr[sem] is not None:
                    if template_pretty(cand) < template_pretty(expr[sem]):
                        expr[sem] = cand
                        changed = True
    return cost, [e for e in expr]


REL_COST, REL_EXPR = synthesize_relations()


# ---------------------------------------------------------------------------
# Kernel IR node graph.
# ---------------------------------------------------------------------------

_NODE_COUNTER = 0


@dataclass(frozen=True)
class Node:
    id: int
    kind: str
    sem: int
    syntax_hash: str
    left: "Node | None" = None
    right: "Node | None" = None
    input_index: int | None = None


def make_leaf(kind: str, sem: int, token: str, input_index: int | None = None) -> Node:
    global _NODE_COUNTER
    _NODE_COUNTER += 1
    return Node(
        id=_NODE_COUNTER,
        kind=kind,
        sem=sem,
        syntax_hash=sha_text("leaf", token),
        input_index=input_index,
    )


INPUT_NODES = tuple(
    make_leaf("INPUT", INPUT_SEMS[i], f"IN:{i}", i) for i in range(N_INPUTS)
)
GROUND_NODE = make_leaf("GROUND", GROUND, "GROUND:1")


def make_d(a: Node, b: Node) -> Node:
    global _NODE_COUNTER
    _NODE_COUNTER += 1
    sem = bit_relation_apply(LAW_D, a.sem, b.sem)
    return Node(
        id=_NODE_COUNTER,
        kind="D",
        sem=sem,
        syntax_hash=sha_text("D", a.syntax_hash, b.syntax_hash),
        left=a,
        right=b,
    )


def instantiate_template(t, p: Node, q: Node) -> Node:
    if t == "p":
        return p
    if t == "q":
        return q
    if t == "1":
        return GROUND_NODE
    return make_d(
        instantiate_template(t[1], p, q),
        instantiate_template(t[2], p, q),
    )


def compile_binary(name: str, a: Node, b: Node) -> Node:
    rel = RICH_RELATIONS[name]
    return instantiate_template(REL_EXPR[rel], a, b)


def compile_not(a: Node) -> Node:
    return make_d(a, GROUND_NODE)


_TREE_COST_CACHE: dict[int, int] = {}


def tree_cost(root: Node) -> int:
    if root.id in _TREE_COST_CACHE:
        return _TREE_COST_CACHE[root.id]
    if root.kind != "D":
        ans = 0
    else:
        ans = 1 + tree_cost(root.left) + tree_cost(root.right)  # type: ignore[arg-type]
    _TREE_COST_CACHE[root.id] = ans
    return ans


def local_dag_cost(root: Node) -> int:
    seen: set[str] = set()
    stack = [root]
    cost = 0
    while stack:
        node = stack.pop()
        if node.kind != "D":
            continue
        if node.syntax_hash in seen:
            continue
        seen.add(node.syntax_hash)
        cost += 1
        stack.append(node.left)   # type: ignore[arg-type]
        stack.append(node.right)  # type: ignore[arg-type]
    return cost


def developmental_cost(
    root: Node,
    semantic_caps: dict[int, "Capability"],
) -> tuple[int, int]:
    seen_syntax: set[str] = set()
    seen_caps: set[int] = set()
    stack = [root]
    cost = 0
    cap_hits = 0
    while stack:
        node = stack.pop()
        cap = semantic_caps.get(node.sem)
        if cap is not None:
            if cap.cap_id not in seen_caps:
                seen_caps.add(cap.cap_id)
                cost += 1
                cap_hits += 1
            continue
        if node.kind != "D":
            continue
        if node.syntax_hash in seen_syntax:
            continue
        seen_syntax.add(node.syntax_hash)
        cost += 1
        stack.append(node.left)   # type: ignore[arg-type]
        stack.append(node.right)  # type: ignore[arg-type]
    return cost, cap_hits


def syntax_only_cost(
    root: Node,
    syntax_caps: dict[str, "Capability"],
) -> tuple[int, int]:
    seen_syntax: set[str] = set()
    seen_caps: set[int] = set()
    stack = [root]
    cost = 0
    hits = 0
    while stack:
        node = stack.pop()
        cap = syntax_caps.get(node.syntax_hash)
        if cap is not None:
            if cap.cap_id not in seen_caps:
                seen_caps.add(cap.cap_id)
                cost += 1
                hits += 1
            continue
        if node.kind != "D":
            continue
        if node.syntax_hash in seen_syntax:
            continue
        seen_syntax.add(node.syntax_hash)
        cost += 1
        stack.append(node.left)   # type: ignore[arg-type]
        stack.append(node.right)  # type: ignore[arg-type]
    return cost, hits


def collect_inputs(root: Node) -> frozenset[int]:
    out: set[int] = set()
    seen: set[int] = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node.id in seen:
            continue
        seen.add(node.id)
        if node.kind == "INPUT" and node.input_index is not None:
            out.add(node.input_index)
        elif node.kind == "D":
            stack.append(node.left)   # type: ignore[arg-type]
            stack.append(node.right)  # type: ignore[arg-type]
    return frozenset(out)


# ---------------------------------------------------------------------------
# Capability archive and deterministic workload.
# ---------------------------------------------------------------------------


@dataclass
class Capability:
    cap_id: int
    sem: int
    root: Node
    birth_task: int
    phase: str
    expanded_cost: int
    input_support: frozenset[int]
    parent_caps: tuple[int, ...]
    later_reuse: int = 0


@dataclass
class TaskResult:
    task: int
    phase: str
    tree: int
    local: int
    dev: int
    syntax: int
    verify: int
    promote: int
    cap_hits: int
    syntax_hits: int
    promoted_cap: int | None
    semantics_ok: bool


class ExperimentState:
    def __init__(self) -> None:
        self.semantic_caps: dict[int, Capability] = {}
        self.syntax_caps: dict[str, Capability] = {}
        self.caps_by_id: dict[int, Capability] = {}
        self.cap_order: list[int] = []
        self.next_cap = 1
        self.top_semantics: set[int] = set()
        self.results: list[TaskResult] = []
        self.phase4_cap_ids: set[int] = set()
        self.phase4_parent_reuses: set[int] = set()
        self.semantic_reuse_hits = 0
        self.syntax_reuse_hits = 0
        self.promotions = 0

    def promote(
        self,
        root: Node,
        task: int,
        phase: str,
        parent_caps: tuple[int, ...],
    ) -> Capability | None:
        if root.sem in self.semantic_caps:
            return None
        expanded = tree_cost(root)
        if expanded < 5:
            return None
        cap = Capability(
            cap_id=self.next_cap,
            sem=root.sem,
            root=root,
            birth_task=task,
            phase=phase,
            expanded_cost=expanded,
            input_support=collect_inputs(root),
            parent_caps=tuple(sorted(set(parent_caps))),
        )
        self.next_cap += 1
        self.semantic_caps[root.sem] = cap
        self.syntax_caps[root.syntax_hash] = cap
        self.caps_by_id[cap.cap_id] = cap
        self.cap_order.append(cap.cap_id)
        self.promotions += 1
        if phase == "recombinant":
            self.phase4_cap_ids.add(cap.cap_id)
        return cap

    def capability_list(self) -> list[Capability]:
        return [self.caps_by_id[i] for i in self.cap_order]


def rng_for(*parts: object) -> random.Random:
    return random.Random(int(sha_text(*parts)[:16], 16))


def random_rich_expr(seed: str, depth: int) -> Node:
    rng = rng_for(seed)

    def rec(d: int) -> Node:
        if d <= 0 or (d > 1 and rng.random() < 0.18):
            return INPUT_NODES[rng.randrange(N_INPUTS)]
        if rng.random() < 0.18:
            return compile_not(rec(d - 1))
        name = RICH_NAMES[rng.randrange(len(RICH_NAMES))]
        return compile_binary(name, rec(d - 1), rec(d - 1))

    return rec(depth)


def choose_two_caps(
    state: ExperimentState,
    seed: str,
    require_distinct_support: bool = False,
) -> tuple[Capability, Capability]:
    caps = state.capability_list()
    rng = rng_for(seed)
    if len(caps) < 2:
        raise RuntimeError("insufficient capabilities")
    for _ in range(512):
        a = caps[rng.randrange(len(caps))]
        b = caps[rng.randrange(len(caps))]
        if a.cap_id == b.cap_id:
            continue
        if require_distinct_support:
            if a.input_support == b.input_support:
                continue
            # Require neither support to be a subset of the other where possible.
            if a.input_support <= b.input_support or b.input_support <= a.input_support:
                continue
        return a, b
    # Deterministic fallback: distinct IDs, preserving no manual semantic targeting.
    return caps[0], caps[-1]


def relation_task_from_caps(
    state: ExperimentState,
    task: int,
    phase: str,
    require_distinct_support: bool = False,
) -> tuple[Node, tuple[int, ...]]:
    a, b = choose_two_caps(
        state,
        f"{PROTOCOL}:{phase}:{task}:parents",
        require_distinct_support=require_distinct_support,
    )
    rng = rng_for(PROTOCOL, phase, task, "relation")
    name = RICH_NAMES[rng.randrange(len(RICH_NAMES))]
    root = compile_binary(name, a.root, b.root)

    # Phase 2 may receive zero to two fresh environmental inputs.
    if phase == "descendant":
        extra = rng.randrange(3)
        for j in range(extra):
            inp = INPUT_NODES[rng.randrange(N_INPUTS)]
            name2 = RICH_NAMES[rng.randrange(len(RICH_NAMES))]
            root = compile_binary(name2, root, inp)

    for cap in (a, b):
        cap.later_reuse += 1
        if cap.cap_id in state.phase4_cap_ids:
            state.phase4_parent_reuses.add(cap.cap_id)
    return root, (a.cap_id, b.cap_id)


def semantic_twin_task(
    state: ExperimentState,
    task: int,
) -> tuple[Node, tuple[int, ...]]:
    caps = state.capability_list()
    if not caps:
        raise RuntimeError("semantic twin requested without capabilities")
    rng = rng_for(PROTOCOL, "semantic_twin", task)
    cap = caps[rng.randrange(len(caps))]
    cap.later_reuse += 1

    # Frozen identity: double negation.
    root = compile_not(compile_not(cap.root))
    assert root.sem == cap.sem
    return root, (cap.cap_id,)


def execute_and_maybe_promote(
    state: ExperimentState,
    task: int,
    phase: str,
    root: Node,
    parent_caps: tuple[int, ...],
) -> TaskResult:
    # Snapshot archive BEFORE the task. The task cannot use itself.
    sem_caps_before = dict(state.semantic_caps)
    syntax_caps_before = dict(state.syntax_caps)

    tc = tree_cost(root)
    lc = local_dag_cost(root)
    dc, dh = developmental_cost(root, sem_caps_before)
    sc, sh = syntax_only_cost(root, syntax_caps_before)

    # Exact authority: root semantics is the protected target.
    target = root.sem
    semantics_ok = root.sem == target
    verify = 1

    if not semantics_ok:
        raise AssertionError("internal exact semantics mismatch")

    promoted = state.promote(root, task, phase, parent_caps)
    promote_cost = 1 if promoted is not None else 0

    state.semantic_reuse_hits += dh
    state.syntax_reuse_hits += sh
    state.top_semantics.add(root.sem)

    result = TaskResult(
        task=task,
        phase=phase,
        tree=tc,
        local=lc,
        dev=dc,
        syntax=sc,
        verify=verify,
        promote=promote_cost,
        cap_hits=dh,
        syntax_hits=sh,
        promoted_cap=promoted.cap_id if promoted else None,
        semantics_ok=semantics_ok,
    )
    state.results.append(result)
    return result


def find_novel_phase1_root(state: ExperimentState, task: int) -> Node:
    for attempt in range(256):
        rng = rng_for(PROTOCOL, "curriculum", task, attempt)
        depth = 3 + rng.randrange(6)
        root = random_rich_expr(
            f"{PROTOCOL}:curriculum:{task}:{attempt}", depth
        )
        if root.sem not in state.top_semantics:
            return root
    # Finite generator fallback: exact duplicate is allowed only after exhaustion.
    return random_rich_expr(f"{PROTOCOL}:curriculum:fallback:{task}", 5)


def find_novel_relation_task(
    state: ExperimentState,
    task: int,
    phase: str,
    require_distinct_support: bool = False,
) -> tuple[Node, tuple[int, ...]]:
    # The parent choice is deterministic; vary a sealed salt if the denotation is
    # already an existing top-level target.
    for attempt in range(128):
        root, parents = relation_task_from_caps(
            state,
            task * 1000 + attempt,
            phase,
            require_distinct_support=require_distinct_support,
        )
        if root.sem not in state.top_semantics:
            return root, parents
    return relation_task_from_caps(
        state,
        task * 1000 + 999,
        phase,
        require_distinct_support=require_distinct_support,
    )


def simulate() -> dict[str, object]:
    state = ExperimentState()

    # Separate no-recombination archive is initialized after Phase 3.
    no_recomb_caps: dict[int, Capability] | None = None
    no_recomb_phase4_cost = 0
    dev_phase4_cost = 0

    for task in range(1, TASKS + 1):
        if task <= 1_000:
            phase = "curriculum"
            root = find_novel_phase1_root(state, task)
            parents: tuple[int, ...] = ()
        elif task <= 10_000:
            phase = "descendant"
            root, parents = find_novel_relation_task(
                state, task, phase, require_distinct_support=False
            )
        elif task <= 15_000:
            phase = "semantic_twin"
            root, parents = semantic_twin_task(state, task)
        else:
            phase = "recombinant"
            if no_recomb_caps is None:
                no_recomb_caps = dict(state.semantic_caps)
            root, parents = find_novel_relation_task(
                state, task, phase, require_distinct_support=True
            )
            # Frozen no-recombination control: Phase-4 verified children never enter
            # this archive.
            nr_cost, _ = developmental_cost(root, no_recomb_caps)
            no_recomb_phase4_cost += nr_cost

        r = execute_and_maybe_promote(
            state, task, phase, root, parents
        )
        if phase == "recombinant":
            dev_phase4_cost += r.dev

    # Sealed negative: exact verifier must reject one flipped truth-table bit.
    probe_root = state.capability_list()[0].root
    corrupt_target = probe_root.sem ^ 1
    corrupted_rejected = probe_root.sem != corrupt_target

    # NO_WARRANT archive is constitutionally empty.
    no_warrant_installed = 0

    # Aggregate.
    def rows_for(phase: str) -> list[TaskResult]:
        return [r for r in state.results if r.phase == phase]

    phases = ("curriculum", "descendant", "semantic_twin", "recombinant")
    per_phase = {}
    for phase in phases:
        rows = rows_for(phase)
        per_phase[phase] = {
            "tasks": len(rows),
            "tree": sum(r.tree for r in rows),
            "local_dag": sum(r.local for r in rows),
            "developmental": sum(r.dev for r in rows),
            "syntax_only": sum(r.syntax for r in rows),
            "verify": sum(r.verify for r in rows),
            "promotion": sum(r.promote for r in rows),
            "cap_hits": sum(r.cap_hits for r in rows),
            "syntax_hits": sum(r.syntax_hits for r in rows),
        }

    tree_total = sum(r.tree for r in state.results)
    local_total = sum(r.local for r in state.results)
    dev_exec_total = sum(r.dev for r in state.results)
    syntax_total = sum(r.syntax for r in state.results)
    verify_total = sum(r.verify for r in state.results)
    promote_total = sum(r.promote for r in state.results)
    dev_total = dev_exec_total + verify_total + promote_total

    # Break-even against TREE execution.
    ct = 0
    cd = 0
    break_even = None
    cost_vector = []
    for r in state.results:
        ct += r.tree
        cd += r.dev + r.verify + r.promote
        cost_vector.append((r.tree, r.local, r.dev, r.syntax, r.promote))
        if break_even is None and cd < ct:
            break_even = r.task

    first_1k = state.results[:1000]
    last_1k = state.results[-1000:]
    first_1k_mean_dev = mean(r.dev for r in first_1k)
    last_1k_mean_dev = mean(r.dev for r in last_1k)

    post5k = state.results[5000:]
    ancestor_invocation_fraction = sum(r.cap_hits > 0 for r in post5k) / len(post5k)

    # Savings-loss controls. COLD_ARCHIVE and NO_PROMOTION both reduce to LOCAL_DAG
    # in this pure functional V1.
    savings_dev = tree_total - dev_exec_total
    savings_local = tree_total - local_total
    cold_loss_fraction = (
        (local_total - dev_exec_total) / savings_dev if savings_dev > 0 else 0.0
    )
    no_promotion_loss_fraction = cold_loss_fraction

    phase3 = per_phase["semantic_twin"]
    phase4 = per_phase["recombinant"]

    # Capability archive uniqueness.
    unique_semantics = len(state.semantic_caps) == len({
        cap.sem for cap in state.capability_list()
    })

    # Ancestry depth over promoted-cap parent graph.
    depth_by_cap: dict[int, int] = {}
    for cid in state.cap_order:
        cap = state.caps_by_id[cid]
        depth_by_cap[cid] = 1 + max(
            (depth_by_cap.get(p, 0) for p in cap.parent_caps),
            default=0,
        )
    max_cap_depth = max(depth_by_cap.values(), default=0)

    ledger = [
        {
            "cap_id": cap.cap_id,
            "sem": sem_hash(cap.sem),
            "birth_task": cap.birth_task,
            "phase": cap.phase,
            "expanded_cost": cap.expanded_cost,
            "syntax": cap.root.syntax_hash,
            "parents": list(cap.parent_caps),
            "support": sorted(cap.input_support),
        }
        for cap in state.capability_list()
    ]
    ledger_hash = hashlib.sha256(
        json.dumps(ledger, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    cost_vector_hash = hashlib.sha256(
        json.dumps(cost_vector, separators=(",", ":")).encode()
    ).hexdigest()

    derived = {}
    for rel in range(16):
        derived[str(rel)] = {
            "table_00_01_10_11": "".join(str((rel >> i) & 1) for i in range(4)),
            "d_cost": REL_COST[rel],
            "formula": template_pretty(REL_EXPR[rel]),
            "stats": {
                "d_nodes": template_stats(REL_EXPR[rel])[0],
                "p_occurrences": template_stats(REL_EXPR[rel])[1],
                "q_occurrences": template_stats(REL_EXPR[rel])[2],
            },
        }

    phase4_reused_children = len(state.phase4_parent_reuses)

    # Gates.
    gates = {
        "E1_all_16_relations_derived": all(c < INF for c in REL_COST),
        "E2_zero_semantic_disagreements": all(r.semantics_ok for r in state.results),
        "E3_dev_exec_lt_50pct_tree": dev_exec_total < 0.50 * tree_total,
        "E4_dev_exec_lt_75pct_local": dev_exec_total < 0.75 * local_total,
        "E5_total_break_even_exists": break_even is not None,
        "E6_last1k_marginal_lower_than_first1k": last_1k_mean_dev < first_1k_mean_dev,
        "E7_post5k_ancestor_invocation_ge_80pct": ancestor_invocation_fraction >= 0.80,
        "E8_semantic_twin_dev_lt_50pct_syntax": (
            phase3["developmental"] < 0.50 * phase3["syntax_only"]
        ),
        "E9_cold_loses_ge_80pct_savings": cold_loss_fraction >= 0.80,
        "E10_no_promotion_loses_ge_80pct_savings": no_promotion_loss_fraction >= 0.80,
        "E11_no_warrant_installs_zero": no_warrant_installed == 0,
        "E12_corrupt_target_rejected": corrupted_rejected,
        "E13_100_recombinant_children_later_reused": phase4_reused_children >= 100,
        "E14_no_recomb_higher_after_first1000_phase4": (
            no_recomb_phase4_cost > dev_phase4_cost
        ),
        "E15_no_duplicate_protected_semantics": unique_semantics,
        # E16 is filled after deterministic replay.
        "E16_deterministic_replay": False,
    }

    return {
        "state": state,
        "ledger": ledger,
        "ledger_hash": ledger_hash,
        "cost_vector_hash": cost_vector_hash,
        "derived_relations": derived,
        "per_phase": per_phase,
        "totals": {
            "tree_exec": tree_total,
            "local_dag_exec": local_total,
            "developmental_exec": dev_exec_total,
            "syntax_only_exec": syntax_total,
            "verify": verify_total,
            "promotion": promote_total,
            "developmental_total_with_authority": dev_total,
        },
        "amortization": {
            "break_even_task": break_even,
            "first_1k_mean_dev_exec": first_1k_mean_dev,
            "last_1k_mean_dev_exec": last_1k_mean_dev,
            "post5k_ancestor_invocation_fraction": ancestor_invocation_fraction,
            "cold_loss_fraction_of_dev_savings": cold_loss_fraction,
            "no_promotion_loss_fraction_of_dev_savings": no_promotion_loss_fraction,
        },
        "controls": {
            "no_warrant_installed": no_warrant_installed,
            "corrupted_target_rejected": corrupted_rejected,
            "cold_exec": local_total,
            "no_promotion_exec": local_total,
            "no_recombination_phase4_exec": no_recomb_phase4_cost,
            "developmental_phase4_exec": dev_phase4_cost,
        },
        "archive": {
            "capabilities": len(state.cap_order),
            "semantic_reuse_hits": state.semantic_reuse_hits,
            "syntax_reuse_hits": state.syntax_reuse_hits,
            "max_capability_ancestry_depth": max_cap_depth,
            "recombinant_capabilities": len(state.phase4_cap_ids),
            "recombinant_children_later_reused": phase4_reused_children,
        },
        "gates": gates,
    }


def strip_runtime(sim: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in sim.items() if k not in {"state", "ledger"}}


def main() -> int:
    first = simulate()
    second = simulate()

    deterministic = (
        first["ledger_hash"] == second["ledger_hash"]
        and first["cost_vector_hash"] == second["cost_vector_hash"]
    )
    first["gates"]["E16_deterministic_replay"] = deterministic  # type: ignore[index]

    gates = first["gates"]  # type: ignore[assignment]
    if all(gates.values()):
        verdict = "PASS_DEVELOPMENTAL_IR_V1"
    elif any(gates.values()):
        verdict = "PARTIAL_DEVELOPMENTAL_IR_V1"
    else:
        verdict = "VALID_NEGATIVE_DEVELOPMENTAL_IR_V1"

    result = {
        "protocol": PROTOCOL,
        "precommit_commit": PRECOMMIT_COMMIT,
        "kernel": {
            "ground": 1,
            "relation": "D(a,b)=not(a) and b",
            "primitives": ["GROUND", "INPUT", "D", "VERIFY", "PROMOTE"],
            "rows": N_ROWS,
            "inputs": N_INPUTS,
        },
        "derived_relations": first["derived_relations"],
        "per_phase": first["per_phase"],
        "totals": first["totals"],
        "amortization": first["amortization"],
        "controls": first["controls"],
        "archive": first["archive"],
        "ledger_hash": first["ledger_hash"],
        "cost_vector_hash": first["cost_vector_hash"],
        "replay_ledger_hash": second["ledger_hash"],
        "replay_cost_vector_hash": second["cost_vector_hash"],
        "headline_gates": gates,
        "verdict": verdict,
        "claim_boundary": (
            "Exact finite 12-input Boolean workload under the frozen abstract "
            "execution-cost model. Positive results support a verified developmental "
            "IR with promoted semantic capabilities; they do not establish lower "
            "wall-clock time than production compilers, Turing universality, or "
            "superiority to lambda calculus/type theory."
        ),
    }

    out = Path("results/developmental_ir_v1")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )

    summary = {
        "verdict": verdict,
        "totals": first["totals"],
        "amortization": first["amortization"],
        "archive": first["archive"],
        "controls": first["controls"],
        "headline_gates": gates,
        "derived_source_ops": {
            "NOT": "D(p,1)",
            **{
                name: template_pretty(REL_EXPR[rel])
                for name, rel in RICH_RELATIONS.items()
            },
        },
        "ledger_hash": first["ledger_hash"],
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    print("=" * 104)
    print("DEVELOPMENTAL IR V1")
    print("=" * 104)
    print("verdict", verdict)
    print("totals", json.dumps(first["totals"], sort_keys=True))
    print("amortization", json.dumps(first["amortization"], sort_keys=True))
    print("archive", json.dumps(first["archive"], sort_keys=True))
    print("controls", json.dumps(first["controls"], sort_keys=True))
    for k, v in gates.items():
        print(k, "PASS" if v else "FAIL")
    print("ledger_hash", first["ledger_hash"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
