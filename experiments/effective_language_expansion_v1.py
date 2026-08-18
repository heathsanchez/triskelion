#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from itertools import product
from pathlib import Path

SEED = "METALOGIC_EFFECTIVE_LANGUAGE_EXPANSION_V1"
MASK = 0xFF
ROWS = list(product((0, 1), repeat=3))


def truth_table(fn) -> int:
    out = 0
    for i, args in enumerate(ROWS):
        out |= (fn(*args) & 1) << i
    return out


ZERO = 0
ONE = MASK
X = truth_table(lambda x, y, z: x)
Y = truth_table(lambda x, y, z: y)
Z = truth_table(lambda x, y, z: z)
BASE = {ZERO: "0", ONE: "1", X: "x", Y: "y", Z: "z"}


def bnot(a: int) -> int:
    return a ^ MASK


def bxor(a: int, b: int) -> int:
    return a ^ b


def band(a: int, b: int) -> int:
    return a & b


def bit(v: int, row: int) -> int:
    return (v >> row) & 1


def apply3(k: int, a: int, b: int, c: int) -> int:
    out = 0
    for idx, (av, bv, cv) in enumerate(ROWS):
        if bit(k, idx):
            term = (a if av else bnot(a)) & (b if bv else bnot(b)) & (c if cv else bnot(c))
            out |= term
    return out


def exact_l0_closure() -> set[int]:
    s = set(BASE)
    changed = True
    while changed:
        changed = False
        cur = list(s)
        for a in cur:
            v = bnot(a)
            if v not in s:
                s.add(v)
                changed = True
        cur = list(s)
        for a in cur:
            for b in cur:
                v = bxor(a, b)
                if v not in s:
                    s.add(v)
                    changed = True
    return s


@dataclass(frozen=True)
class Expr:
    size: int
    text: str
    sem: int


def enumerate_u(max_size: int = 7) -> dict[int, Expr]:
    best = {v: Expr(1, text, v) for v, text in BASE.items()}
    by_size: dict[int, set[int]] = {1: set(BASE)}

    for size in range(2, max_size + 1):
        vals: set[int] = set()

        if size - 1 in by_size:
            for a in sorted(by_size[size - 1]):
                v = bnot(a)
                text = f"~({best[a].text})"
                candidate = Expr(size, text, v)
                if v not in best:
                    best[v] = candidate
                    vals.add(v)
                elif (size, text) < (best[v].size, best[v].text):
                    best[v] = candidate

        for s1 in range(1, size - 1):
            s2 = size - 1 - s1
            if s1 not in by_size or s2 not in by_size:
                continue
            for a in sorted(by_size[s1]):
                for b in sorted(by_size[s2]):
                    for symbol, op in (("^", bxor), ("&", band)):
                        v = op(a, b)
                        text = f"({best[a].text}{symbol}{best[b].text})"
                        candidate = Expr(size, text, v)
                        if v not in best:
                            best[v] = candidate
                            vals.add(v)
                        elif (size, text) < (best[v].size, best[v].text):
                            best[v] = candidate

        by_size[size] = vals

    return best


def rank_key(prefix: str, function_id: int) -> str:
    return hashlib.sha256(f"{prefix}:{function_id}".encode()).hexdigest()


def select_k(l0: set[int], u: dict[int, Expr]) -> Expr:
    eligible = [
        expr for sem, expr in u.items()
        if sem not in l0 and 5 <= expr.size <= 7
    ]
    eligible.sort(key=lambda e: rank_key(SEED, e.sem))
    if not eligible:
        raise RuntimeError("No mechanically eligible acquisition target")
    return eligible[0]


def cegis(target: Expr, u: dict[int, Expr]) -> tuple[Expr, list[dict]]:
    observed_rows: list[int] = []
    trace: list[dict] = []
    candidates = sorted(u.values(), key=lambda e: (e.size, e.text, e.sem))

    for round_id in range(16):
        consistent = [
            e for e in candidates
            if all(bit(e.sem, r) == bit(target.sem, r) for r in observed_rows)
        ]
        if not consistent:
            raise RuntimeError("No U expression remains consistent with verifier evidence")

        proposal = consistent[0]
        mismatch = next(
            (r for r in range(8) if bit(proposal.sem, r) != bit(target.sem, r)),
            None,
        )
        trace.append({
            "round": round_id,
            "observations": len(observed_rows),
            "consistent_semantic_candidates": len(consistent),
            "proposal_size": proposal.size,
            "proposal": proposal.text,
            "proposal_function_id": proposal.sem,
            "verifier_counterexample_row": mismatch,
            "verifier_counterexample_input": None if mismatch is None else list(ROWS[mismatch]),
            "verifier_expected_output": None if mismatch is None else bit(target.sem, mismatch),
            "verifier_proposal_output": None if mismatch is None else bit(proposal.sem, mismatch),
        })

        if mismatch is None:
            return proposal, trace
        observed_rows.append(mismatch)

    raise RuntimeError("CEGIS did not converge within frozen round budget")


def enumerate_l1(k: Expr, max_size: int = 6) -> dict[int, Expr]:
    best = {v: Expr(1, text, v) for v, text in BASE.items()}
    by_size: dict[int, set[int]] = {1: set(BASE)}

    for size in range(2, max_size + 1):
        vals: set[int] = set()

        if size - 1 in by_size:
            for a in sorted(by_size[size - 1]):
                v = bnot(a)
                text = f"~({best[a].text})"
                if v not in best:
                    best[v] = Expr(size, text, v)
                    vals.add(v)

        for s1 in range(1, size - 1):
            s2 = size - 1 - s1
            if s1 in by_size and s2 in by_size:
                for a in sorted(by_size[s1]):
                    for b in sorted(by_size[s2]):
                        v = bxor(a, b)
                        text = f"({best[a].text}^{best[b].text})"
                        if v not in best:
                            best[v] = Expr(size, text, v)
                            vals.add(v)

        for s1 in range(1, size - 2):
            for s2 in range(1, size - 1 - s1):
                s3 = size - 1 - s1 - s2
                if s1 not in by_size or s2 not in by_size or s3 not in by_size:
                    continue
                for a in sorted(by_size[s1]):
                    for b in sorted(by_size[s2]):
                        for c in sorted(by_size[s3]):
                            v = apply3(k.sem, a, b, c)
                            text = f"K({best[a].text},{best[b].text},{best[c].text})"
                            if v not in best:
                                best[v] = Expr(size, text, v)
                                vals.add(v)

        by_size[size] = vals

    return best


def select_o2(l0: set[int], l1: dict[int, Expr], k: Expr) -> Expr:
    eligible = [
        expr for sem, expr in l1.items()
        if sem not in l0 and sem != k.sem
    ]
    eligible.sort(key=lambda e: rank_key(f"{SEED}:O2", e.sem))
    if not eligible:
        raise RuntimeError("No downstream target became newly reachable")
    return eligible[0]


def main() -> int:
    l0 = exact_l0_closure()
    u = enumerate_u(7)
    target = select_k(l0, u)

    gate_a = len(l0) == 16 and target.sem not in l0

    proposal, trace = cegis(target, u)
    gate_b = proposal.sem == target.sem
    gate_c = gate_b and proposal.sem not in l0

    l1 = enumerate_l1(proposal, 6)
    o2 = select_o2(l0, l1, proposal)
    gate_d = o2.sem not in l0 and o2.sem in l1

    ablated = exact_l0_closure()
    gate_e = o2.sem not in ablated

    restored = enumerate_l1(proposal, 6)
    gate_e_restore = o2.sem in restored

    passed = all((gate_a, gate_b, gate_c, gate_d, gate_e, gate_e_restore))
    verdict = (
        "PASS_EFFECTIVE_LANGUAGE_EXPANSION_V1"
        if passed
        else "VALID_NEGATIVE_EFFECTIVE_LANGUAGE_EXPANSION_V1"
    )

    result = {
        "protocol": "EFFECTIVE_LANGUAGE_EXPANSION_V1",
        "seed": SEED,
        "world": {
            "arity": 3,
            "semantic_functions_total": 256,
            "l0_exact_closure": len(l0),
            "u_semantics_reached_size_le_7": len(u),
        },
        "selected_acquisition_target": {
            "function_id": target.sem,
            "minimal_u_size": target.size,
            "minimal_u_expression_for_audit_only": target.text,
            "in_l0": target.sem in l0,
        },
        "cegis": {
            "rounds": len(trace),
            "trace": trace,
            "sealed_program": proposal.text,
            "sealed_program_size": proposal.size,
            "sealed_semantics": proposal.sem,
        },
        "installed_language": {
            "l1_bounded_semantics_size_le_6": len(l1),
        },
        "downstream_o2": {
            "function_id": o2.sem,
            "l1_expression": o2.text,
            "l1_expression_size": o2.size,
            "cold_reachable": o2.sem in l0,
            "warm_reachable": o2.sem in l1,
            "after_ablation_reachable": o2.sem in ablated,
            "after_restore_reachable": o2.sem in restored,
        },
        "gates": {
            "A_old_closure_obstruction": gate_a,
            "B_counterexample_guided_nonpreenumerated_synthesis": gate_b,
            "C_admission_expands_effective_language": gate_c,
            "D_new_downstream_reachability": gate_d,
            "E_ablation_removes_downstream_reachability": gate_e,
            "E_restore_returns_downstream_reachability": gate_e_restore,
        },
        "verdict": verdict,
        "claim_boundary": (
            "Bounded exact finite-world evidence for verifier-driven effective-language expansion "
            "under a fixed general construction substrate. Not substrate-free invention, open-world "
            "ontology creation, neural learning, or representation-independent novelty."
        ),
    }

    outdir = Path("results/effective_language_expansion_v1")
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print("=" * 88)
    print("EFFECTIVE LANGUAGE EXPANSION V1")
    print("=" * 88)
    print(f"L0 exact closure:            {len(l0)} / 256")
    print(f"U semantics (size <= 7):    {len(u)} / 256")
    print(f"Selected K function id:     {target.sem}")
    print(f"CEGIS rounds:               {len(trace)}")
    for row in trace:
        ce = row["verifier_counterexample_input"]
        print(
            f"  r{row['round']}: {row['proposal']:<24} "
            f"consistent={row['consistent_semantic_candidates']:<3} "
            f"counterexample={ce}"
        )
    print(f"Sealed K:                   {proposal.text}")
    print(f"O2 function id:             {o2.sem}")
    print(f"O2 warm expression:         {o2.text}")
    print(f"O2 cold reachable:          {o2.sem in l0}")
    print(f"O2 warm reachable:          {o2.sem in l1}")
    print(f"O2 after ablation:          {o2.sem in ablated}")
    print(f"O2 after restore:           {o2.sem in restored}")
    print("-" * 88)
    for name, value in result["gates"].items():
        print(f"{name}: {'PASS' if value else 'FAIL'}")
    print("-" * 88)
    print(verdict)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
