#!/usr/bin/env python3
"""Dependency-free calibration for the Developmental Intelligence demo.

This is NOT new scientific evidence. It is a transparent executable toy world that
shows the mechanics used by the public demo:

same executable experience -> compile an AST-role operator -> transfer to an unseen
program -> revert -> fail -> restore -> pass.

The scientific claims live in the frozen V54/V160/V161 experiment lineages.
"""
from __future__ import annotations

import ast
import copy
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Experience:
    id: str
    buggy: str
    fixed: str
    expected: list


@dataclass(frozen=True)
class Capability:
    id: str
    kind: str
    container_role: str
    item_role: str
    evidence_ids: tuple[str, ...]
    status: str = "active"


TRAIN = [
    Experience(
        id="E1",
        buggy="""def collect(values):\n    pile = []\n    for value in values:\n        pile + [value]\n    return pile\n""",
        fixed="""def collect(values):\n    pile = []\n    for value in values:\n        pile.append(value)\n    return pile\n""",
        expected=[2, 5, 8],
    ),
    Experience(
        id="E2",
        buggy="""def gather(tokens):\n    cache = []\n    for token in tokens:\n        cache + [token]\n    return cache\n""",
        fixed="""def gather(tokens):\n    cache = []\n    for token in tokens:\n        cache.append(token)\n    return cache\n""",
        expected=["a", "b"],
    ),
]

HELD_OUT = """def harvest(records):\n    reservoir = []\n    for record in records:\n        reservoir + [record]\n    return reservoir\n"""
HELD_INPUT = [11, 13, 17]
HELD_EXPECTED = [11, 13, 17]


def run(source: str, fn_name: str, arg):
    ns: dict = {}
    exec(compile(source, "<candidate>", "exec"), ns, ns)
    return ns[fn_name](arg)


def single_function(source: str) -> ast.FunctionDef:
    tree = ast.parse(source)
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    if len(fns) != 1:
        raise ValueError("expected exactly one function")
    return fns[0]


def role_signature(source: str) -> Optional[tuple[str, str, str]]:
    """Recognize the verifier-relevant structural failure, not identifier strings.

    Pattern:
      accumulator = []
      for item in iterable:
          accumulator + [item]      # expression result discarded

    Returns a neutral role signature if present.
    """
    fn = single_function(source)
    empty_lists = {
        n.targets[0].id
        for n in fn.body
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
        and isinstance(n.value, ast.List)
        and len(n.value.elts) == 0
    }
    for loop in [n for n in ast.walk(fn) if isinstance(n, ast.For)]:
        if not isinstance(loop.target, ast.Name):
            continue
        item = loop.target.id
        for stmt in loop.body:
            if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.BinOp) and isinstance(stmt.value.op, ast.Add)):
                continue
            left, right = stmt.value.left, stmt.value.right
            if (
                isinstance(left, ast.Name)
                and left.id in empty_lists
                and isinstance(right, ast.List)
                and len(right.elts) == 1
                and isinstance(right.elts[0], ast.Name)
                and right.elts[0].id == item
            ):
                return ("DISCARDED_LIST_ADD", "LOOP_ACCUMULATOR", "LOOP_ITEM")
    return None


def fixed_signature(source: str) -> Optional[tuple[str, str, str]]:
    fn = single_function(source)
    empty_lists = {
        n.targets[0].id
        for n in fn.body
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
        and isinstance(n.value, ast.List)
        and len(n.value.elts) == 0
    }
    for loop in [n for n in ast.walk(fn) if isinstance(n, ast.For)]:
        if not isinstance(loop.target, ast.Name):
            continue
        item = loop.target.id
        for stmt in loop.body:
            call = stmt.value if isinstance(stmt, ast.Expr) else None
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
                continue
            if (
                call.func.attr == "append"
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id in empty_lists
                and len(call.args) == 1
                and isinstance(call.args[0], ast.Name)
                and call.args[0].id == item
            ):
                return ("APPEND", "LOOP_ACCUMULATOR", "LOOP_ITEM")
    return None


def compile_capability(experiences: list[Experience]) -> Capability:
    bad = {role_signature(e.buggy) for e in experiences}
    good = {fixed_signature(e.fixed) for e in experiences}
    if bad != {("DISCARDED_LIST_ADD", "LOOP_ACCUMULATOR", "LOOP_ITEM")}:
        raise AssertionError(f"training failure signatures disagree: {bad}")
    if good != {("APPEND", "LOOP_ACCUMULATOR", "LOOP_ITEM")}:
        raise AssertionError(f"training repair signatures disagree: {good}")
    return Capability(
        id="C_APPEND_LOOP_ACCUMULATOR",
        kind="APPEND",
        container_role="LOOP_ACCUMULATOR",
        item_role="LOOP_ITEM",
        evidence_ids=tuple(e.id for e in experiences),
    )


class ApplyCapability(ast.NodeTransformer):
    def __init__(self):
        self.changed = 0
        self.empty_lists: set[str] = set()
        self.loop_item_stack: list[str] = []

    def visit_FunctionDef(self, node):
        self.empty_lists = {
            n.targets[0].id
            for n in node.body
            if isinstance(n, ast.Assign)
            and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name)
            and isinstance(n.value, ast.List)
            and len(n.value.elts) == 0
        }
        self.generic_visit(node)
        return node

    def visit_For(self, node):
        item = node.target.id if isinstance(node.target, ast.Name) else ""
        self.loop_item_stack.append(item)
        node.body = [self.visit(x) for x in node.body]
        self.loop_item_stack.pop()
        node.orelse = [self.visit(x) for x in node.orelse]
        return node

    def visit_Expr(self, node):
        if not self.loop_item_stack:
            return self.generic_visit(node)
        item = self.loop_item_stack[-1]
        v = node.value
        if isinstance(v, ast.BinOp) and isinstance(v.op, ast.Add):
            if (
                isinstance(v.left, ast.Name)
                and v.left.id in self.empty_lists
                and isinstance(v.right, ast.List)
                and len(v.right.elts) == 1
                and isinstance(v.right.elts[0], ast.Name)
                and v.right.elts[0].id == item
            ):
                self.changed += 1
                return ast.copy_location(
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Attribute(value=copy.deepcopy(v.left), attr="append", ctx=ast.Load()),
                            args=[copy.deepcopy(v.right.elts[0])],
                            keywords=[],
                        )
                    ),
                    node,
                )
        return self.generic_visit(node)


def apply_capability(source: str, capability: Optional[Capability]) -> str:
    if capability is None or capability.status != "active":
        return source
    tree = ast.parse(source)
    tx = ApplyCapability()
    tree = tx.visit(tree)
    ast.fix_missing_locations(tree)
    if tx.changed != 1:
        return source
    return ast.unparse(tree) + "\n"


def exact_episode_replay(source: str, experiences: list[Experience]) -> str:
    """A deliberately literal episodic baseline.

    It can replay an exact seen buggy program but cannot invent identifier-independent
    structure. This is a calibration control, NOT a claim about all possible RAG systems.
    """
    normalized = ast.dump(ast.parse(source), include_attributes=False)
    for e in experiences:
        if ast.dump(ast.parse(e.buggy), include_attributes=False) == normalized:
            return e.fixed
    return source


def main():
    # Verify the experiences are genuinely executable before compiling anything.
    training_checks = []
    for e in TRAIN:
        fn = single_function(e.buggy).name
        arg = e.expected
        bad_out = run(e.buggy, fn, arg)
        good_out = run(e.fixed, fn, arg)
        training_checks.append({"id": e.id, "buggy_fails": bad_out != e.expected, "fixed_passes": good_out == e.expected})
    assert all(x["buggy_fails"] and x["fixed_passes"] for x in training_checks)

    cap = compile_capability(TRAIN)
    held_name = single_function(HELD_OUT).name

    memory_source = exact_episode_replay(HELD_OUT, TRAIN)
    memory_pass = run(memory_source, held_name, HELD_INPUT) == HELD_EXPECTED

    developed_source = apply_capability(HELD_OUT, cap)
    developed_pass = run(developed_source, held_name, HELD_INPUT) == HELD_EXPECTED

    # Causal revert / restore.
    reverted_pass = run(apply_capability(HELD_OUT, None), held_name, HELD_INPUT) == HELD_EXPECTED
    restored_pass = run(apply_capability(HELD_OUT, cap), held_name, HELD_INPUT) == HELD_EXPECTED

    result = {
        "protocol": "DI_DEMO_CALIBRATION_V1",
        "claim_boundary": "Transparent local mechanism calibration only; not evidence that all memory/RAG systems fail and not a substitute for V54/V160/V161.",
        "same_experiences": [e.id for e in TRAIN],
        "compiled_capability": asdict(cap),
        "training_checks": training_checks,
        "held_out": {
            "identifier_overlap_with_training": False,
            "episodic_replay_pass": memory_pass,
            "development_pass": developed_pass,
            "revert_pass": reverted_pass,
            "restore_pass": restored_pass,
        },
        "gates": {
            "all_training_experiences_executable": all(x["buggy_fails"] and x["fixed_passes"] for x in training_checks),
            "literal_episode_replay_does_not_transfer": not memory_pass,
            "compiled_role_structure_transfers": developed_pass,
            "revert_removes_gain": not reverted_pass,
            "restore_returns_gain": restored_pass,
        },
    }
    result["verdict"] = "PASS_DI_DEMO_CALIBRATION_V1" if all(result["gates"].values()) else "FAIL_DI_DEMO_CALIBRATION_V1"
    (HERE / "calibration_result.json").write_text(json.dumps(result, indent=2) + "\n")

    print("\n" + "=" * 72)
    print("METALOGIC — DEVELOPMENTAL INTELLIGENCE CALIBRATION")
    print("=" * 72)
    print("Same verified experiences. Frozen code world. No learned weights.")
    print()
    print(f"EPISODIC REPLAY     {'PASS' if memory_pass else 'FAIL'}")
    print(f"DEVELOPMENT         {'PASS' if developed_pass else 'FAIL'}")
    print(f"REVERT DEVELOPMENT  {'PASS' if reverted_pass else 'FAIL'}")
    print(f"RESTORE DEVELOPMENT {'PASS' if restored_pass else 'FAIL'}")
    print()
    print("Compiled structure:")
    print(f"  {cap.kind}({cap.container_role}, {cap.item_role})")
    print(f"  evidence={','.join(cap.evidence_ids)}")
    print()
    print(result["verdict"])
    print("=" * 72)

    if result["verdict"].startswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
