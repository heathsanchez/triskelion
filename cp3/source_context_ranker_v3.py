from __future__ import annotations

from pathlib import Path

import source_context_ranker as base


def _number_if_needed(text: str) -> str:
    lines = text.splitlines()
    if lines and all((not line.strip()) or (len(line) >= 6 and line[:5].isdigit() and line[5:6] == ':') for line in lines[:min(8,len(lines))]):
        return text
    return "\n".join(f"{i+1:05d}: {line}" for i, line in enumerate(lines))


def collect_context(work: Path, baseline_output: str, *, max_files: int = 6, max_chars: int = 36000) -> tuple[str, list[str]]:
    # Reuse the frozen acquisition ranker to choose files solely from the failing
    # native-test evidence, then expose deterministic original-source line numbers
    # so edit transport never depends on copying an exact old string.
    _, used = base.collect_context(work, baseline_output, max_files=max_files, max_chars=max_chars)
    tokens = base._tokens(baseline_output)
    chunks: list[str] = []
    final_used: list[str] = []
    remaining = max_chars
    for rel in used:
        p = work / rel
        if not p.is_file():
            continue
        excerpt = base._focused_excerpt(p, tokens, max_chars=min(6500, remaining))
        excerpt = _number_if_needed(excerpt)
        chunk = f"\n### FILE {rel}\n```python\n{excerpt}\n```\n"
        if len(chunk) > remaining:
            break
        chunks.append(chunk)
        final_used.append(rel)
        remaining -= len(chunk)
        if remaining < 800:
            break
    return "".join(chunks), final_used
