from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

# Generic repository/source exclusions. These are representation hygiene rules,
# not case-specific knowledge and do not encode any protected or reference fix.
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".tox", ".nox", ".venv", "venv", "env",
    "site-packages", "dist-packages", "__pycache__", "node_modules",
    "build", "dist", ".eggs", ".cp3_tools", "devscripts",
}

STOP = {
    "file", "line", "python", "pytest", "assert", "assertionerror", "error",
    "failed", "failure", "failures", "traceback", "test", "tests", "self",
    "none", "true", "false", "return", "import", "from", "with", "class",
    "function", "value", "expected", "actual", "where", "when", "then",
}


def _excluded(path: Path, work: Path) -> bool:
    try:
        rel = path.resolve().relative_to(work.resolve())
    except Exception:
        return True
    lower_parts = {p.lower() for p in rel.parts}
    if lower_parts & EXCLUDED_DIRS:
        return True
    return any(part.startswith(".") and part not in {"."} for part in rel.parts[:-1])


def _tokens(text: str) -> list[str]:
    raw = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{3,}\b", text)
    out: list[str] = []
    for token in raw:
        low = token.lower()
        if low in STOP:
            continue
        if low.startswith("test_") and len(low) > 5:
            out.append(low[5:])
        out.append(low)
    return out


def _trace_paths(work: Path, baseline_output: str) -> list[Path]:
    out: list[Path] = []
    patterns = [
        r'File ["\']([^"\']+\.py)["\']',
        r'(?m)^\s*([^\s:][^:\n]*\.py):\d+',
    ]
    for pattern in patterns:
        for raw in re.findall(pattern, baseline_output):
            p = Path(raw)
            if not p.is_absolute():
                p = work / p
            try:
                p = p.resolve()
                p.relative_to(work.resolve())
            except Exception:
                continue
            if p.is_file() and not _excluded(p, work) and p not in out:
                out.append(p)
    return out


def _candidate_files(work: Path) -> list[Path]:
    files: list[Path] = []
    for p in work.rglob("*.py"):
        if _excluded(p, work):
            continue
        try:
            if p.stat().st_size > 250_000:
                continue
        except OSError:
            continue
        files.append(p)
    return files


def _score_file(path: Path, work: Path, token_counts: Counter[str], traced: set[Path]) -> tuple[int, str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return (-1, str(path))
    low = text.lower()
    rel = str(path.relative_to(work))
    score = 10_000 if path.resolve() in traced else 0
    rel_low = rel.lower()
    if "/test" in "/" + rel_low or rel_low.startswith("test"):
        score -= 150
    for token, count in token_counts.most_common(80):
        if token not in low:
            continue
        occurrences = min(low.count(token), 8)
        score += min(count, 8) * occurrences
        if re.search(rf"(?m)^\s*(?:async\s+)?def\s+{re.escape(token)}\b", low):
            score += 700
        if re.search(rf"(?m)^\s*class\s+{re.escape(token)}\b", low):
            score += 500
        if token in path.stem.lower():
            score += 120
    return score, rel


def _focused_excerpt(path: Path, tokens: list[str], max_chars: int = 6500) -> str:
    """Return exact source substrings only; never decorate lines.

    Structured-edit transport requires the model's `old` field to be an exact
    substring of the repository file. Display-only line-number prefixes would
    corrupt that contract, so long-file windows preserve source bytes/text as
    presented, apart from joining disjoint windows with a sentinel between them.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= max_chars:
        return text
    lines = text.splitlines()
    hits: list[int] = []
    token_set = [t for t in tokens[:50] if len(t) >= 4]
    for i, line in enumerate(lines):
        low = line.lower()
        if any(t in low for t in token_set):
            hits.append(i)
            if len(hits) >= 6:
                break
    if not hits:
        return "\n".join(lines[:180])[:max_chars]
    ranges: list[tuple[int, int]] = []
    for i in hits:
        start, end = max(0, i - 35), min(len(lines), i + 70)
        if ranges and start <= ranges[-1][1] + 5:
            ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
        else:
            ranges.append((start, end))
    chunks: list[str] = []
    remaining = max_chars
    for start, end in ranges:
        exact = "\n".join(lines[start:end])
        if len(exact) > remaining:
            exact = exact[:remaining]
        chunks.append(exact)
        remaining -= len(exact)
        if remaining <= 0:
            break
    return "\n# ... CP3 CONTEXT WINDOW GAP ...\n".join(chunks)


def collect_context(work: Path, baseline_output: str, *, max_files: int = 6, max_chars: int = 36000) -> tuple[str, list[str]]:
    """Select buggy repository source using only the failing native-test evidence.

    This intentionally ignores generated virtual environments and tooling trees.
    Selection is based on repository traceback frames plus identifier overlap with
    the failure text. It never reads BugsInPy reference patches or fixed source.
    """
    traced_paths = _trace_paths(work, baseline_output)
    traced = {p.resolve() for p in traced_paths}
    token_counts = Counter(_tokens(baseline_output))
    candidates = _candidate_files(work)
    ranked = sorted((_score_file(p, work, token_counts, traced), p) for p in candidates)
    ranked.reverse()

    chosen: list[Path] = []
    for p in traced_paths:
        if p not in chosen:
            chosen.append(p)
    for (score, _), p in ranked:
        if score <= 0 and chosen:
            continue
        if p not in chosen:
            chosen.append(p)
        if len(chosen) >= max_files:
            break
    if not chosen:
        chosen = [p for (_, p) in ranked[:max_files]]

    chunks: list[str] = []
    used: list[str] = []
    remaining = max_chars
    ranked_tokens = [t for t, _ in token_counts.most_common(80)]
    for p in chosen[:max_files]:
        rel = str(p.relative_to(work))
        excerpt = _focused_excerpt(p, ranked_tokens, max_chars=min(6500, remaining))
        chunk = f"\n### FILE {rel}\n```python\n{excerpt}\n```\n"
        if len(chunk) > remaining:
            break
        chunks.append(chunk)
        used.append(rel)
        remaining -= len(chunk)
        if remaining < 800:
            break
    return "".join(chunks), used
