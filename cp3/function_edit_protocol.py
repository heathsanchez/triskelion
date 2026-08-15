from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import structured_edit_protocol_v2 as json_transport


def visible_request(project: str, bug_id: int, failure: str, context: str) -> str:
    return (
        "Repair this independently authored Python repository bug. "
        "Return ONLY JSON in this exact schema: "
        "{\"edits\":[{\"path\":\"relative/path.py\",\"symbol\":\"function_name\",\"new\":\"complete replacement function definition\"}]}. "
        "Use 1-3 minimal function replacements. `symbol` must name an existing Python function in the chosen file. "
        "`new` must be the complete replacement `def` or `async def` for that same symbol. "
        "Do not edit tests, generated environments, or tooling. Do not include markdown or explanation. "
        "Use only the buggy source and failing native-test evidence below.\n\n"
        f"CASE: {project}/{bug_id}\n"
        f"NATIVE FAILURE:\n{failure[-12000:]}\n"
        f"BUGGY SOURCE CONTEXT:\n{context}"
    )


def _json_object(text: str) -> dict:
    # Reuse the syntax-only JSON recovery. It appends container closers only.
    return json_transport._json_object(text)


def extract_edits(text: str) -> str:
    value = _json_object(text)
    edits = value.get("edits")
    if not isinstance(edits, list) or not 1 <= len(edits) <= 3:
        raise ValueError("function edit must contain 1-3 edits")
    normalized = []
    for edit in edits:
        if not isinstance(edit, dict):
            raise ValueError("each edit must be an object")
        path = edit.get("path")
        symbol = edit.get("symbol")
        new = edit.get("new")
        if not all(isinstance(x, str) for x in (path, symbol, new)):
            raise ValueError("edit path/symbol/new must be strings")
        if not path or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol):
            raise ValueError("invalid function edit target")
        try:
            parsed = ast.parse(new)
        except SyntaxError as exc:
            raise ValueError(f"replacement function is not valid Python: {exc}") from exc
        if len(parsed.body) != 1 or not isinstance(parsed.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise ValueError("replacement must contain exactly one function definition")
        if parsed.body[0].name != symbol:
            raise ValueError("replacement function name must equal symbol")
        normalized.append({"path": path, "symbol": symbol, "new": new.rstrip() + "\n"})
    return json.dumps({"edits": normalized}, sort_keys=True, separators=(",", ":"))


def _safe_path(work: Path, raw: str) -> Path:
    return json_transport.base._safe_path(work, raw)


def _find_function(text: str, symbol: str) -> ast.AST:
    tree = ast.parse(text)
    matches = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol
    ]
    if len(matches) != 1:
        raise ValueError(f"symbol {symbol!r} must identify exactly one function; found {len(matches)}")
    node = matches[0]
    if not hasattr(node, "end_lineno") or node.end_lineno is None:
        raise ValueError("Python AST lacks end_lineno for deterministic function replacement")
    return node


def apply_edits(work: Path, payload: str) -> None:
    value = json.loads(payload)
    for edit in value["edits"]:
        path = _safe_path(work, edit["path"])
        text = path.read_text(encoding="utf-8", errors="strict")
        node = _find_function(text, edit["symbol"])
        lines = text.splitlines(keepends=True)
        start = node.lineno - 1
        end = node.end_lineno
        original_line = lines[start]
        indent = original_line[: len(original_line) - len(original_line.lstrip(" \t"))]
        new = edit["new"]
        new_lines = new.splitlines()
        # Model supplies a standalone function. Re-indent it to the original lexical scope.
        replacement = "".join((indent + line if line.strip() else line) + "\n" for line in new_lines)
        updated = "".join(lines[:start]) + replacement + "".join(lines[end:])
        # Fail closed if the resulting source is syntactically invalid.
        ast.parse(updated)
        path.write_text(updated, encoding="utf-8")


def changed_files(payload: str) -> list[str]:
    value = json.loads(payload)
    out: list[str] = []
    for edit in value.get("edits", []):
        path = edit.get("path")
        if isinstance(path, str) and path not in out:
            out.append(path)
    return out
