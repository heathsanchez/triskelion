#!/usr/bin/env python3
"""T1_WORLD_MAP_V1 — forest-first cartography for One Layer Deeper.

Uses public, already-executed exploration evidence from benjaminW2025/one-layer-deeper.
This is intentionally a map-building pass, not a new architecture intervention.
It inspects source column headers first, isolates T=1 cohorts, computes excess-over-chance,
and identifies the earliest empirically visible capability boundary.

Limits: the public results.csv is cohort-aggregate, so this V1 cannot yet split by per-example
carry/reduction/place-value structure. Those become explicit missing coordinates in the output.
"""
from __future__ import annotations

import csv
import io
import json
import math
import os
import statistics
import urllib.request
from collections import defaultdict
from pathlib import Path

CSV_URL = "https://raw.githubusercontent.com/benjaminW2025/one-layer-deeper/main/explorations/results/results.csv"
EXP0_URL = "https://raw.githubusercontent.com/benjaminW2025/one-layer-deeper/main/explorations/results/exp0_task_analysis.json"
OUT = Path("results/one_layer_deeper/t1_world_map_v1")


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "MathGraph-T1-World-Map/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def mean(xs):
    xs = [float(x) for x in xs if x is not None and not math.isnan(float(x))]
    return statistics.mean(xs) if xs else None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = fetch_text(CSV_URL)
    reader = csv.DictReader(io.StringIO(raw))
    headers = reader.fieldnames or []
    print("HEADERS:", headers)
    required = {"run_id", "exp", "regime", "seed", "budget_mode", "budget", "steps_completed",
                "eval_set", "T", "ood_n", "ood_t", "n_eval", "digit_acc", "exact_acc",
                "chance_digit", "chance_exact", "final_train_loss"}
    missing = sorted(required - set(headers))
    if missing:
        raise RuntimeError(f"missing required columns: {missing}")

    rows = list(reader)
    exp0 = json.loads(fetch_text(EXP0_URL))

    # Exact T=1 map only. Empty T is ID aggregate and deliberately excluded here.
    t1 = [r for r in rows if str(r.get("T", "")).strip() == "1"]
    for r in t1:
        for k in ("digit_acc", "exact_acc", "chance_digit", "chance_exact", "final_train_loss", "budget"):
            try:
                r[k] = float(r[k])
            except Exception:
                r[k] = math.nan
        try:
            r["steps_completed"] = int(float(r["steps_completed"]))
        except Exception:
            r["steps_completed"] = None
        r["ood_n_bool"] = str(r.get("ood_n", "")).lower() == "true"
        r["exact_excess"] = r["exact_acc"] - r["chance_exact"]
        r["digit_excess"] = r["digit_acc"] - r["chance_digit"]

    # Behavioral quotient at available resolution: same regime/budget/eval-axis -> one class.
    classes = defaultdict(list)
    for r in t1:
        key = (r["regime"], r["budget_mode"], r["budget"], r["ood_n_bool"])
        classes[key].append(r)

    class_rows = []
    for key, grp in classes.items():
        regime, budget_mode, budget, ood_n = key
        class_rows.append({
            "regime": regime,
            "budget_mode": budget_mode,
            "budget": budget,
            "ood_n": ood_n,
            "n_runs": len(grp),
            "mean_exact": mean([x["exact_acc"] for x in grp]),
            "mean_chance_exact": mean([x["chance_exact"] for x in grp]),
            "mean_exact_excess": mean([x["exact_excess"] for x in grp]),
            "mean_digit": mean([x["digit_acc"] for x in grp]),
            "mean_chance_digit": mean([x["chance_digit"] for x in grp]),
            "mean_digit_excess": mean([x["digit_excess"] for x in grp]),
            "mean_final_train_loss": mean([x["final_train_loss"] for x in grp]),
            "mean_steps": mean([x["steps_completed"] for x in grp if x["steps_completed"] is not None]),
        })

    class_rows.sort(key=lambda x: (x["regime"], x["budget_mode"], x["budget"], x["ood_n"]))

    # Global landmarks from available evidence.
    landmarks = []
    seen = [x for x in t1 if not x["ood_n_bool"]]
    ood = [x for x in t1 if x["ood_n_bool"]]
    seen_excess = mean([x["exact_excess"] for x in seen])
    ood_excess = mean([x["exact_excess"] for x in ood])
    landmarks.append({
        "name": "T1_fresh_x_seen_N",
        "coordinate": "fresh x with seen N at T=1",
        "mean_exact_excess_over_chance": seen_excess,
        "interpretation": "base modular-squaring generalization is upstream of depth",
    })
    landmarks.append({
        "name": "T1_fresh_x_OOD_N",
        "coordinate": "fresh x with unseen N at T=1",
        "mean_exact_excess_over_chance": ood_excess,
        "interpretation": "N-transfer is not interpretable unless fresh-x base operation is above chance",
    })

    # Does more optimization/training correlate with better T=1 generalization?
    finite = [x for x in t1 if x["steps_completed"] is not None and not math.isnan(x["exact_excess"])]
    if len(finite) >= 2:
        xs = [float(x["steps_completed"]) for x in finite]
        ys = [float(x["exact_excess"]) for x in finite]
        mx, my = statistics.mean(xs), statistics.mean(ys)
        num = sum((a-mx)*(b-my) for a,b in zip(xs,ys))
        den = math.sqrt(sum((a-mx)**2 for a in xs) * sum((b-my)**2 for b in ys))
        corr = num/den if den else None
    else:
        corr = None
    landmarks.append({
        "name": "compute_vs_T1_generalization",
        "coordinate": "optimizer steps vs exact excess over chance",
        "pearson": corr,
        "interpretation": "tests whether additional fitting is moving the capability frontier",
    })

    # Rank classes by evidence of real T=1 capability beyond chance.
    ranked = sorted(class_rows, key=lambda x: (x["mean_exact_excess"] if x["mean_exact_excess"] is not None else -999), reverse=True)

    # Missing coordinates required for true fine cartography.
    missing_coordinates = [
        "per-example x and N",
        "digit width of x and N",
        "whether x^2 < N (no modular reduction needed)",
        "quotient floor(x^2/N) / reduction complexity",
        "multiplication carry count",
        "longest carry chain",
        "answer width",
        "per-place prediction correctness",
        "positional alignment / field offsets",
        "same-example outcomes across competing representations",
    ]

    # Conservative boundary verdict.
    # If seen-N T=1 is at/below chance, earliest visible failure is fresh-x base operation.
    eps = 0.005
    if seen_excess is None:
        boundary = "UNRESOLVED_NO_T1_DATA"
    elif seen_excess <= eps:
        boundary = "FRESH_X_BASE_OPERATION"
    else:
        boundary = "DOWNSTREAM_OF_FRESH_X_BASE_OPERATION"

    result = {
        "experiment": "T1_WORLD_MAP_V1",
        "source": {
            "repo": "benjaminW2025/one-layer-deeper",
            "csv": CSV_URL,
            "exp0": EXP0_URL,
            "source_headers": headers,
            "n_rows": len(rows),
            "n_t1_rows": len(t1),
        },
        "method": "public-evidence behavioral cartography before intervention",
        "behavioral_classes": class_rows,
        "ranked_classes_by_exact_excess": ranked,
        "landmarks": landmarks,
        "earliest_visible_boundary": boundary,
        "missing_coordinates_for_v2": missing_coordinates,
        "exp0_keys": sorted(exp0.keys()) if isinstance(exp0, dict) else None,
        "claim_boundary": (
            "V1 maps only cohort-aggregate public evidence. It can locate broad upstream capability boundaries "
            "but cannot attribute failure to carry, reduction, or place-value without per-example predictions."
        ),
        "next_deciding_test": (
            "Run one trained model over a stratified per-example T=1 diagnostic population and join predictions "
            "to arithmetic descriptors; mine minimal success/failure contrasts before any architecture change."
        ),
    }

    (OUT / "map.json").write_text(json.dumps(result, indent=2, sort_keys=True))

    md = []
    md.append("# T1_WORLD_MAP_V1\n")
    md.append("Forest-first cartography for One Layer Deeper using public executed evidence.\n")
    md.append(f"- Source rows: **{len(rows)}**")
    md.append(f"- T=1 rows: **{len(t1)}**")
    md.append(f"- Earliest visible boundary: **{boundary}**")
    md.append(f"- Mean T=1 seen-N exact excess over chance: **{seen_excess}**")
    md.append(f"- Mean T=1 OOD-N exact excess over chance: **{ood_excess}**")
    md.append(f"- Steps/generalization Pearson: **{corr}**\n")
    md.append("## Ranked behavioral classes\n")
    md.append("| regime | budget | ood_n | exact | chance | excess | digit excess | runs |")
    md.append("|---|---:|:---:|---:|---:|---:|---:|---:|")
    for x in ranked:
        md.append(
            f"| {x['regime']} | {x['budget_mode']}={x['budget']} | {x['ood_n']} | "
            f"{x['mean_exact']:.5f} | {x['mean_chance_exact']:.5f} | {x['mean_exact_excess']:.5f} | "
            f"{x['mean_digit_excess']:.5f} | {x['n_runs']} |"
        )
    md.append("\n## Missing coordinates for the real per-example map\n")
    for m in missing_coordinates:
        md.append(f"- {m}")
    md.append("\n## Claim boundary\n")
    md.append(result["claim_boundary"])
    md.append("\n## Next deciding test\n")
    md.append(result["next_deciding_test"])
    (OUT / "README.md").write_text("\n".join(md) + "\n")

    print(json.dumps({
        "status": "PASS",
        "earliest_visible_boundary": boundary,
        "n_t1_rows": len(t1),
        "seen_exact_excess": seen_excess,
        "ood_exact_excess": ood_excess,
        "steps_corr": corr,
        "out": str(OUT),
    }, indent=2))


if __name__ == "__main__":
    main()
