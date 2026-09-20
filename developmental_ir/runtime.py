from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import hashlib
import json


Expr = str | tuple[str, "Expr", "Expr"]


def _hash(*parts: object) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()


def parse_expr(text: str) -> Expr:
    """Parse canonical D-expression syntax: 1, x0..xN, D(a,b)."""
    s = text.strip()
    i = 0

    def rec() -> Expr:
        nonlocal i
        if s.startswith("D(", i):
            i += 2
            a = rec()
            if i >= len(s) or s[i] != ",":
                raise ValueError(f"expected comma at {i}")
            i += 1
            b = rec()
            if i >= len(s) or s[i] != ")":
                raise ValueError(f"expected close paren at {i}")
            i += 1
            return ("D", a, b)

        j = i
        while i < len(s) and (s[i].isalnum() or s[i] == "_"):
            i += 1
        token = s[j:i]
        if token == "1":
            return token
        if token.startswith("x") and token[1:].isdigit():
            return token
        raise ValueError(f"bad token {token!r}")

    out = rec()
    if i != len(s):
        raise ValueError(f"trailing input at {i}")
    return out


def expr_to_text(expr: Expr) -> str:
    if isinstance(expr, str):
        return expr
    return f"D({expr_to_text(expr[1])},{expr_to_text(expr[2])})"


def expr_cost(expr: Expr) -> int:
    if isinstance(expr, str):
        return 0
    return 1 + expr_cost(expr[1]) + expr_cost(expr[2])


def _var_semantics(arity: int, index: int) -> int:
    rows = 1 << arity
    out = 0
    for row in range(rows):
        if (row >> index) & 1:
            out |= 1 << row
    return out


def eval_truth(expr: Expr, arity: int) -> int:
    """Evaluate a D term as a complete 2^arity-row truth table."""
    mask = (1 << (1 << arity)) - 1
    if isinstance(expr, str):
        if expr == "1":
            return mask
        if expr.startswith("x"):
            idx = int(expr[1:])
            if idx >= arity:
                raise ValueError(f"argument x{idx} outside arity {arity}")
            return _var_semantics(arity, idx)
        raise ValueError(expr)

    a = eval_truth(expr[1], arity)
    b = eval_truth(expr[2], arity)
    return ((~a) & mask) & b


def eval_bitset(expr: Expr, args: tuple[int, ...], mask: int) -> int:
    """Evaluate an expression over arbitrary bitset arguments."""
    if isinstance(expr, str):
        if expr == "1":
            return mask
        if expr.startswith("x"):
            return args[int(expr[1:])]
        raise ValueError(expr)

    a = eval_bitset(expr[1], args, mask)
    b = eval_bitset(expr[2], args, mask)
    return ((~a) & mask) & b


def verifier_digest(cap_id: str, arity: int, table: int, expr: Expr) -> str:
    got = eval_truth(expr, arity)
    return _hash("DIRV0", cap_id, arity, table, expr_to_text(expr), got)


@dataclass(frozen=True)
class Capability:
    id: str
    arity: int
    table: int
    expansion: Expr
    digest: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def verified(
        cls,
        cap_id: str,
        arity: int,
        table: int,
        expansion: Expr | str,
        metadata: dict[str, Any] | None = None,
    ) -> "Capability":
        expr = parse_expr(expansion) if isinstance(expansion, str) else expansion
        got = eval_truth(expr, arity)
        if got != table:
            raise ValueError(
                f"capability {cap_id!r} failed verification: "
                f"expected table {table}, got {got}"
            )
        digest = verifier_digest(cap_id, arity, table, expr)
        return cls(cap_id, arity, table, expr, digest, metadata or {})

    def reverify(self) -> bool:
        return (
            eval_truth(self.expansion, self.arity) == self.table
            and verifier_digest(self.id, self.arity, self.table, self.expansion)
            == self.digest
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "arity": self.arity,
            "table": self.table,
            "expansion": expr_to_text(self.expansion),
            "digest": self.digest,
            "metadata": self.metadata,
        }

    @classmethod
    def from_json(cls, row: dict[str, Any]) -> "Capability":
        expr = parse_expr(row["expansion"])
        cap = cls(
            id=row["id"],
            arity=int(row["arity"]),
            table=int(row["table"]),
            expansion=expr,
            digest=row["digest"],
            metadata=dict(row.get("metadata", {})),
        )
        if not cap.reverify():
            raise ValueError(f"capability {cap.id!r} failed reload verification")
        return cap


class CapabilityArchive:
    """Persistent verified capability namespace.

    The archive is not trusted merely because a name exists. Every insert and
    reload re-verifies the transparent D+GROUND expansion.
    """

    def __init__(self, capabilities: list[Capability] | None = None):
        self._caps: dict[str, Capability] = {}
        if capabilities:
            for cap in capabilities:
                self.add(cap)

    def add(self, cap: Capability) -> None:
        if not cap.reverify():
            raise ValueError(f"unverified capability {cap.id!r}")
        self._caps[cap.id] = cap

    def get(self, cap_id: str) -> Capability:
        return self._caps[cap_id]

    def ids(self) -> list[str]:
        return sorted(self._caps)

    def pack_hash(self) -> str:
        payload = [self._caps[k].to_json() for k in self.ids()]
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def to_json(self) -> dict[str, Any]:
        return {
            "format": "developmental-ir-v0-capability-pack",
            "capabilities": [self._caps[k].to_json() for k in self.ids()],
            "pack_hash": self.pack_hash(),
        }

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> "CapabilityArchive":
        if obj.get("format") != "developmental-ir-v0-capability-pack":
            raise ValueError("unsupported capability pack")
        archive = cls([Capability.from_json(row) for row in obj["capabilities"]])
        expected = obj.get("pack_hash")
        if expected is not None and expected != archive.pack_hash():
            raise ValueError("capability pack hash mismatch")
        return archive

    @classmethod
    def load(cls, path: str | Path) -> "CapabilityArchive":
        return cls.from_json(json.loads(Path(path).read_text()))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_json(), indent=2, sort_keys=True) + "\n")


# Program IR:
# {"op":"one"}
# {"op":"arg","index":0}
# {"op":"d","a":..., "b":...}
# {"op":"cap","id":"...", "args":[...]}


def eval_term(term: dict[str, Any], args: tuple[int, ...], mask: int, archive: CapabilityArchive) -> int:
    op = term["op"]
    if op == "one":
        return mask
    if op == "arg":
        return args[int(term["index"])]
    if op == "d":
        a = eval_term(term["a"], args, mask, archive)
        b = eval_term(term["b"], args, mask, archive)
        return ((~a) & mask) & b
    if op == "cap":
        cap = archive.get(term["id"])
        actual = tuple(eval_term(x, args, mask, archive) for x in term["args"])
        if len(actual) != cap.arity:
            raise ValueError(f"{cap.id}: expected {cap.arity} args, got {len(actual)}")
        return eval_bitset(cap.expansion, actual, mask)
    raise ValueError(f"unknown term op {op!r}")


def expand_term(term: dict[str, Any], archive: CapabilityArchive) -> dict[str, Any]:
    """Erase capability calls by substituting their certified transparent expansion."""
    op = term["op"]
    if op in ("one", "arg"):
        return dict(term)
    if op == "d":
        return {
            "op": "d",
            "a": expand_term(term["a"], archive),
            "b": expand_term(term["b"], archive),
        }
    if op != "cap":
        raise ValueError(op)

    cap = archive.get(term["id"])
    actual = [expand_term(x, archive) for x in term["args"]]
    if len(actual) != cap.arity:
        raise ValueError(f"{cap.id}: arity mismatch")

    def subst(expr: Expr) -> dict[str, Any]:
        if isinstance(expr, str):
            if expr == "1":
                return {"op": "one"}
            if expr.startswith("x"):
                return actual[int(expr[1:])]
            raise ValueError(expr)
        return {"op": "d", "a": subst(expr[1]), "b": subst(expr[2])}

    return subst(cap.expansion)


def c_expr_from_expanded(term: dict[str, Any], arg_names: list[str]) -> str:
    op = term["op"]
    if op == "one":
        return "UINT64_MAX"
    if op == "arg":
        return arg_names[int(term["index"])]
    if op == "d":
        a = c_expr_from_expanded(term["a"], arg_names)
        b = c_expr_from_expanded(term["b"], arg_names)
        return f"((~({a})) & ({b}))"
    raise ValueError("term must be capability-expanded before C emission")


def compile_c_expr(term: dict[str, Any], archive: CapabilityArchive, arg_names: list[str]) -> str:
    """Default V0 lowering: transparent expansion, then native expression emission."""
    return c_expr_from_expanded(expand_term(term, archive), arg_names)


def archive_from_v6_result(path: str | Path) -> CapabilityArchive:
    """Convert the authoritative V6 learned language into a V0 capability pack."""
    data = json.loads(Path(path).read_text())
    rows = data["final_language"]
    caps = []
    for i, row in enumerate(rows):
        cap_id = f"v6_{i:02d}_a{row['arity']}_t{row['table']}"
        cap = Capability.verified(
            cap_id=cap_id,
            arity=int(row["arity"]),
            table=int(row["table"]),
            expansion=row["expression"],
            metadata={
                "source": "DEVELOPMENTAL_IR_V6_BLIND_GRAMMAR_EXPANSION",
                "admission_event": int(row["admission_event"]),
                "frozen_reuse": int(row["frozen_reuse"]),
                "utility": int(row["utility"]),
                "d_cost": int(row["cost"]),
            },
        )
        caps.append(cap)
    return CapabilityArchive(caps)
