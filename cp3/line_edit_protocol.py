from __future__ import annotations

import ast
import json
from pathlib import Path

import structured_edit_protocol_v2 as json_transport


def visible_request(project: str, bug_id: int, failure: str, context: str) -> str:
    return (
        "Repair this independently authored Python repository bug. Return ONLY JSON in this exact schema: "
        "{\"edits\":[{\"path\":\"relative/path.py\",\"start_line\":1,\"end_line\":1,\"new\":\"replacement source text\"}]}. "
        "Use 1-3 minimal edits. start_line/end_line are inclusive ORIGINAL source line numbers shown in the context. "
        "Replace exactly that line range with `new`; use an empty `new` only to delete the selected range. "
        "Do not edit tests, generated environments, or tooling. Do not include markdown or explanation. "
        "Use only the buggy source and frozen failing-test evidence below.\n\n"
        f"CASE: {project}/{bug_id}\n"
        f"NATIVE FAILURE:\n{failure[-12000:]}\n"
        f"BUGGY SOURCE CONTEXT:\n{context}"
    )


def extract_edits(text: str) -> str:
    value = json_transport._json_object(text)
    edits = value.get("edits")
    if not isinstance(edits, list) or not 1 <= len(edits) <= 3:
        raise ValueError("line edit must contain 1-3 edits")
    normalized = []
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"path","start_line","end_line","new"}:
            raise ValueError("each line edit must contain exactly path/start_line/end_line/new")
        path=edit["path"]; start=edit["start_line"]; end=edit["end_line"]; new=edit["new"]
        if not isinstance(path,str) or not isinstance(new,str) or not isinstance(start,int) or not isinstance(end,int):
            raise ValueError("invalid line edit types")
        if start < 1 or end < start:
            raise ValueError("invalid line range")
        normalized.append({"path":path,"start_line":start,"end_line":end,"new":new})
    return json.dumps({"edits":normalized},sort_keys=True,separators=(",",":"))


def _safe_path(work: Path, raw: str) -> Path:
    return json_transport.base._safe_path(work, raw)


def _is_test_path(raw: str) -> bool:
    p=Path(raw)
    parts={x.lower() for x in p.parts}
    n=p.name.lower()
    return "test" in parts or "tests" in parts or n.startswith("test_") or n.endswith("_test.py")


def apply_edits(work: Path, payload: str) -> None:
    value=json.loads(payload)
    grouped: dict[str,list[dict]]={}
    for edit in value["edits"]:
        if _is_test_path(edit["path"]):
            raise ValueError(f"refusing test edit: {edit['path']}")
        grouped.setdefault(edit["path"],[]).append(edit)
    for raw, edits in grouped.items():
        path=_safe_path(work,raw)
        if path.suffix != '.py':
            raise ValueError("CP3 line transport edits Python source only")
        text=path.read_text(encoding="utf-8",errors="strict")
        lines=text.splitlines(keepends=True)
        # Descending ranges preserve original line coordinates for all edits.
        edits=sorted(edits,key=lambda e:(e["start_line"],e["end_line"]),reverse=True)
        last_start=len(lines)+1
        for edit in edits:
            start,end=edit["start_line"],edit["end_line"]
            if end > len(lines):
                raise ValueError(f"line range exceeds file: {raw}:{start}-{end}/{len(lines)}")
            if end >= last_start:
                raise ValueError("overlapping line edits are forbidden")
            replacement=edit["new"]
            if replacement and not replacement.endswith("\n"):
                replacement += "\n"
            lines[start-1:end]=[replacement] if replacement else []
            last_start=start
        updated="".join(lines)
        ast.parse(updated)
        path.write_text(updated,encoding="utf-8")


def changed_files(payload: str) -> list[str]:
    value=json.loads(payload)
    out=[]
    for edit in value.get("edits",[]):
        p=edit.get("path")
        if isinstance(p,str) and p not in out:
            out.append(p)
    return out
