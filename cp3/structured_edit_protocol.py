from __future__ import annotations

import json
import re
from pathlib import Path


def visible_request(project: str, bug_id: int, failure: str, context: str) -> str:
    return (
        "Repair this independently authored Python repository bug. "
        "Return ONLY JSON in this exact schema: "
        "{\"edits\":[{\"path\":\"relative/path.py\",\"old\":\"exact existing source text\",\"new\":\"replacement source text\"}]}. "
        "Use 1-3 minimal edits. The `old` text must be copied exactly from the provided buggy source and must occur exactly once. "
        "Do not edit tests, generated environments, or tooling. Do not include markdown, explanation, or a unified diff. "
        "Use only the buggy source and failing native-test evidence below.\n\n"
        f"CASE: {project}/{bug_id}\n"
        f"NATIVE FAILURE:\n{failure[-12000:]}\n"
        f"BUGGY SOURCE CONTEXT:\n{context}"
    )


def _json_object(text: str) -> dict:
    blocks = re.findall(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    candidates = blocks + [text]
    last = None
    for candidate in candidates:
        candidate = candidate.strip()
        try:
            value = json.loads(candidate)
            if isinstance(value, dict):
                return value
        except Exception as exc:
            last = exc
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start >= 0 and end > start:
            try:
                value = json.loads(candidate[start:end + 1])
                if isinstance(value, dict):
                    return value
            except Exception as exc:
                last = exc
    raise ValueError(f"model output is not valid structured-edit JSON: {last}")


def extract_edits(text: str) -> str:
    value = _json_object(text)
    edits = value.get("edits")
    if not isinstance(edits, list) or not 1 <= len(edits) <= 3:
        raise ValueError("structured edit must contain 1-3 edits")
    normalized = []
    for edit in edits:
        if not isinstance(edit, dict):
            raise ValueError("each edit must be an object")
        path = edit.get("path")
        old = edit.get("old")
        new = edit.get("new")
        if not all(isinstance(x, str) for x in (path, old, new)):
            raise ValueError("edit path/old/new must be strings")
        if not path or not old or old == new:
            raise ValueError("edit must have nonempty path/old and make a real change")
        normalized.append({"path": path, "old": old, "new": new})
    return json.dumps({"edits": normalized}, sort_keys=True, separators=(",", ":"))


def _safe_path(work: Path, raw: str) -> Path:
    path = (work / raw).resolve()
    try:
        rel = path.relative_to(work.resolve())
    except Exception as exc:
        raise ValueError(f"edit escapes repository: {raw}") from exc
    lower = [part.lower() for part in rel.parts]
    if any(part in {"env", ".venv", "venv", "site-packages", ".git", "devscripts"} for part in lower):
        raise ValueError(f"edit targets forbidden generated/tooling path: {raw}")
    if lower and (lower[0] in {"test", "tests"} or path.name.lower().startswith("test_")):
        raise ValueError(f"editing tests is forbidden: {raw}")
    if path.suffix != ".py" or not path.is_file():
        raise ValueError(f"edit target is not an existing Python source file: {raw}")
    return path


def apply_edits(work: Path, payload: str) -> None:
    value = json.loads(payload)
    for edit in value["edits"]:
        path = _safe_path(work, edit["path"])
        text = path.read_text(encoding="utf-8", errors="strict")
        count = text.count(edit["old"])
        if count != 1:
            raise ValueError(f"old text must occur exactly once in {edit['path']}; found {count}")
        path.write_text(text.replace(edit["old"], edit["new"], 1), encoding="utf-8")


def changed_files(payload: str) -> list[str]:
    value = json.loads(payload)
    out = []
    for edit in value.get("edits", []):
        path = edit.get("path")
        if isinstance(path, str) and path not in out:
            out.append(path)
    return out
