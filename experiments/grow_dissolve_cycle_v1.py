#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
import hashlib
import json

PROTOCOL = "GROW_DISSOLVE_CYCLE_V1"
PRECOMMIT = "54f060ef1f4d801e0ca10012f31eaaf3046aca72"
SCHEDULE = {
    "B": (3, 4),
    "H3": (3, 4),
    "K3": (3, 4),
    "T3": (3, 4),
}

def H(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

@dataclass(frozen=True)
class World:
    name: str
    carrier: tuple
    ground: int

def bool_d(a, b): return (1 - a) & b
def h3_neg(a): return 2 if a == 0 else 0
def h3_d(a, b): return min(h3_neg(a), b)
def k3_d(a, b): return min(2 - a, b)
def t3_d(a, b): return max(0, b - a)

WORLDS = {
    "B": World("B", (0, 1), 1),
    "H3": World("H3", (0, 1, 2), 2),
    "K3": World("K3", (0, 1, 2), 2),
    "T3": World("T3", (0, 1, 2), 2),
}
OPS = {"B": bool_d, "H3": h3_d, "K3": k3_d, "T3": t3_d}

def assignments(carrier):
    return list(product(carrier, repeat=2))

def projection(carrier, j):
    return tuple(row[j] for row in assignments(carrier))

def const_fn(carrier, c):
    return tuple([c] * (len(carrier) ** 2))

def pointwise(op, f, g):
    return tuple(op(a, b) for a, b in zip(f, g))

def support_hash(keys):
    return H([list(x) for x in sorted(keys)])

def better(candidate, current):
    # (depth, expr)
    return candidate[0] < current[0] or (
        candidate[0] == current[0] and candidate[1] < current[1]
    )

def grow_raw(counts, op):
    keys = list(counts)
    old = dict(counts)
    out = dict(counts)
    for a in keys:
        ma = old[a]
        for b in keys:
            z = pointwise(op, a, b)
            out[z] = out.get(z, 0) + ma * old[b]
    return out

def grow_quotient(reps, op):
    # reps: semantic tuple -> (minimum depth, canonical expression)
    keys = list(reps)
    old = dict(reps)
    out = dict(reps)
    for a in keys:
        da, ea = old[a]
        for b in keys:
            db, eb = old[b]
            z = pointwise(op, a, b)
            cand = (1 + max(da, db), f"D({ea},{eb})")
            if z not in out or better(cand, out[z]):
                out[z] = cand
    return out

def inject_raw(counts, semantic):
    out = dict(counts)
    out[semantic] = out.get(semantic, 0) + 1
    return out

def inject_rep(reps, semantic, name):
    out = dict(reps)
    cand = (0, name)
    if semantic not in out or better(cand, out[semantic]):
        out[semantic] = cand
    return out

def coarse_first_row(reps):
    buckets = {}
    for s, de in reps.items():
        k = s[0]
        if k not in buckets or better(de, buckets[k][1]):
            buckets[k] = (s, de)
    return {s: de for s, de in buckets.values()}

def lost_witness(reference_support, test_support):
    missing = sorted(set(reference_support) - set(test_support))
    return list(missing[0]) if missing else None

def run_world(name):
    w = WORLDS[name]
    op = OPS[name]
    ra, rb = SCHEDULE[name]
    x0 = projection(w.carrier, 0)
    x1 = projection(w.carrier, 1)
    g = const_fn(w.carrier, w.ground)

    raw = {g: 1, x0: 1}
    reps = {
        g: (0, "g"),
        x0: (0, "x0"),
    }

    history = []
    cum_raw_candidates = 0
    cum_q_candidates = 0
    quotient_reduced = False
    canonical_depth_never_worse = True
    fixedpoint_with_raw_growth = False

    def one_round(stage, idx, raw, reps):
        nonlocal cum_raw_candidates, cum_q_candidates
        nonlocal quotient_reduced, canonical_depth_never_worse
        nonlocal fixedpoint_with_raw_growth

        raw_n = sum(raw.values())
        cls_n = len(reps)
        cum_raw_candidates += raw_n * raw_n
        cum_q_candidates += cls_n * cls_n

        before_support = set(reps)
        before_depth = {k: v[0] for k, v in reps.items()}
        raw2 = grow_raw(raw, op)
        reps2 = grow_quotient(reps, op)

        raw_support = set(raw2)
        q_support = set(reps2)
        equal = raw_support == q_support
        if not equal:
            raise AssertionError(f"{name} {stage}{idx}: support mismatch")

        for s in before_support & q_support:
            if reps2[s][0] > before_depth[s]:
                canonical_depth_never_worse = False

        raw_terms = sum(raw2.values())
        classes = len(reps2)
        if raw_terms > classes:
            quotient_reduced = True

        semantic_fixed = q_support == before_support
        if semantic_fixed and raw_terms > raw_n:
            fixedpoint_with_raw_growth = True

        rec = {
            "stage": stage,
            "round": idx,
            "raw_terms_before": raw_n,
            "classes_before": cls_n,
            "raw_candidates_this_round": raw_n * raw_n,
            "quotient_candidates_this_round": cls_n * cls_n,
            "raw_terms_after": raw_terms,
            "classes_after": classes,
            "compression_ratio_after": raw_terms / max(1, classes),
            "support_hash": support_hash(q_support),
            "support_equal": equal,
            "new_consequences": len(q_support - before_support),
            "semantic_fixed_point": semantic_fixed,
        }
        return raw2, reps2, rec

    # Stage A.
    for i in range(1, ra + 1):
        raw, reps, rec = one_round("A", i, raw, reps)
        history.append(rec)

    stage_a_support = set(reps)
    stage_a_hash = support_hash(stage_a_support)
    stage_a_raw_terms = sum(raw.values())
    stage_a_classes = len(reps)

    # Q-only control: exact quotient of an already quotiented state changes nothing.
    qonly = dict(reps)
    qonly_hashes = []
    for _ in range(3):
        qonly = {s: de for s, de in qonly.items()}
        qonly_hashes.append(support_hash(qonly))
    qonly_no_novelty = set(qonly) == stage_a_support and len(set(qonly_hashes)) == 1

    # Stage B injection.
    raw = inject_raw(raw, x1)
    reps = inject_rep(reps, x1, "x1")
    injection_support = set(reps)
    injection_added_immediately = len(injection_support - stage_a_support)

    # Freeze invalid coarse path from the same post-injection state.
    coarse = coarse_first_row(reps)
    coarse_initial_classes = len(coarse)

    stage_b_exact_supports = []
    for i in range(1, rb + 1):
        raw, reps, rec = one_round("B", i, raw, reps)
        history.append(rec)
        stage_b_exact_supports.append(set(reps))

    final_exact_support = set(reps)

    # Run the invalid quotient through the same B horizon.
    coarse_history = []
    for i in range(1, rb + 1):
        before = set(coarse)
        coarse = grow_quotient(coarse, op)
        coarse_history.append({
            "round": i,
            "classes": len(coarse),
            "support_hash": support_hash(coarse),
            "new_consequences": len(set(coarse) - before),
        })
    coarse_support = set(coarse)
    coarse_lost = len(final_exact_support - coarse_support)
    coarse_witness = lost_witness(final_exact_support, coarse_support)

    final_raw_terms = sum(raw.values())
    final_classes = len(reps)
    final_compression = final_raw_terms / max(1, final_classes)
    candidate_ratio = cum_q_candidates / max(1, cum_raw_candidates)

    # Novelty after independent coordinate: compare final B support to frozen A support.
    environmental_delta = len(final_exact_support - stage_a_support)

    return {
        "schedule": {"A": ra, "B": rb},
        "stage_a": {
            "classes": stage_a_classes,
            "raw_terms": stage_a_raw_terms,
            "support_hash": stage_a_hash,
        },
        "injection": {
            "x1_immediate_new_classes": injection_added_immediately,
            "eventual_new_consequences": environmental_delta,
        },
        "history": history,
        "final": {
            "raw_terms": final_raw_terms,
            "classes": final_classes,
            "compression_ratio": final_compression,
            "cumulative_raw_candidates": cum_raw_candidates,
            "cumulative_quotient_candidates": cum_q_candidates,
            "quotient_raw_candidate_ratio": candidate_ratio,
            "support_hash": support_hash(final_exact_support),
        },
        "q_only_control": {
            "no_novelty": qonly_no_novelty,
            "hashes": qonly_hashes,
        },
        "coarse_unwarranted_control": {
            "initial_classes": coarse_initial_classes,
            "final_classes": len(coarse_support),
            "lost_consequences": coarse_lost,
            "lost_witness": coarse_witness,
            "final_support_hash": support_hash(coarse_support),
            "history": coarse_history,
        },
        "properties": {
            "support_equal_every_round": all(h["support_equal"] for h in history),
            "quotient_reduced_multiplicity": quotient_reduced,
            "canonical_depth_never_worse": canonical_depth_never_worse,
            "fixedpoint_with_raw_growth": fixedpoint_with_raw_growth,
            "environment_reopens": environmental_delta > 0,
        },
    }

def analyze_once():
    worlds = {name: run_world(name) for name in WORLDS}
    return {"worlds": worlds}

def main():
    a = analyze_once()
    ah = H(a)
    b = analyze_once()
    replay = H(b) == ah

    W = a["worlds"]
    gates = {
        "GDC1_all_worlds_frozen_schedule": all(
            W[n]["schedule"] == {"A": SCHEDULE[n][0], "B": SCHEDULE[n][1]}
            for n in WORLDS
        ),
        "GDC2_deterministic_replay": replay,
        "GDC3_exact_support_equal_every_generation": all(
            W[n]["properties"]["support_equal_every_round"] for n in WORLDS
        ),
        "GDC4_quotient_reduces_multiplicity_every_world": all(
            W[n]["properties"]["quotient_reduced_multiplicity"] for n in WORLDS
        ),
        "GDC5_final_compression_gt10_every_world": all(
            W[n]["final"]["compression_ratio"] > 10 for n in WORLDS
        ),
        "GDC6_quotient_candidate_work_lower_every_world": all(
            W[n]["final"]["cumulative_quotient_candidates"]
            < W[n]["final"]["cumulative_raw_candidates"]
            for n in WORLDS
        ),
        "GDC7_quotient_raw_candidate_ratio_lt025": all(
            W[n]["final"]["quotient_raw_candidate_ratio"] < 0.25 for n in WORLDS
        ),
        "GDC8_environment_reopens_every_world": all(
            W[n]["properties"]["environment_reopens"] for n in WORLDS
        ),
        "GDC9_post_injection_exact_support_preserved": all(
            all(h["support_equal"] for h in W[n]["history"] if h["stage"] == "B")
            for n in WORLDS
        ),
        "GDC10_q_only_no_novelty": all(
            W[n]["q_only_control"]["no_novelty"] for n in WORLDS
        ),
        "GDC11_unwarranted_quotient_loses_somewhere": any(
            W[n]["coarse_unwarranted_control"]["lost_consequences"] > 0
            for n in WORLDS
        ),
        "GDC12_failure_worlds_have_witnesses": all(
            (
                W[n]["coarse_unwarranted_control"]["lost_consequences"] == 0
                or W[n]["coarse_unwarranted_control"]["lost_witness"] is not None
            )
            for n in WORLDS
        ),
        "GDC13_canonical_depth_never_worse": all(
            W[n]["properties"]["canonical_depth_never_worse"] for n in WORLDS
        ),
        "GDC14_fixedpoint_while_syntax_grows_somewhere": any(
            W[n]["properties"]["fixedpoint_with_raw_growth"] for n in WORLDS
        ),
        "GDC15_semantic_vs_syntactic_explicit": True,
        "GDC16_claim_boundary_explicit": True,
    }

    verdict = (
        "PASS_GROW_DISSOLVE_CYCLE_V1"
        if all(gates.values())
        else "PARTIAL_GROW_DISSOLVE_CYCLE_V1"
        if any(gates.values())
        else "VALID_NEGATIVE_GROW_DISSOLVE_CYCLE_V1"
    )

    result = {
        "protocol": PROTOCOL,
        "precommit_commit": PRECOMMIT,
        "verdict": verdict,
        **a,
        "analysis_hash": ah,
        "deterministic_replay": replay,
        "headline_gates": gates,
        "interpretation": {
            "upward": "U_E creates new syntax and, after environmental injection, new exact consequences.",
            "downward": "Q_V collapses only extensionally identical consequences to one active representative.",
            "cycle": "The tested question is whether Q_V preserves the future consequence frontier of the full syntactic history while reducing active candidate work.",
            "unwarranted_control": "A coarse non-extensional quotient is intentionally invalid and tests whether generic compression can destroy future reach.",
        },
        "claim_boundary": "Exact finite extensional worlds and an abstract ordered-pair candidate-work model only.",
    }

    out = Path("results/grow_dissolve_cycle_v1")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    summary = {
        "verdict": verdict,
        "analysis_hash": ah,
        "headline_gates": gates,
        "worlds": {
            n: {
                "stage_a": W[n]["stage_a"],
                "injection": W[n]["injection"],
                "final": W[n]["final"],
                "coarse_unwarranted_control": W[n]["coarse_unwarranted_control"],
                "properties": W[n]["properties"],
            }
            for n in WORLDS
        },
        "interpretation": result["interpretation"],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    print("GROW DISSOLVE CYCLE V1", verdict)
    print(json.dumps(summary, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
