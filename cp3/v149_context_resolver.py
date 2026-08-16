from __future__ import annotations

import re
from pathlib import Path
from typing import Any

MAX_FILES = 6
MAX_CHARS = 36000


def _excluded(rel: Path) -> bool:
    parts = [p.lower() for p in rel.parts]
    name = rel.name.lower()
    if '.git' in parts or 'site-packages' in parts or 'env' in parts or '.venv' in parts or 'venv' in parts:
        return True
    if 'test' in parts or 'tests' in parts or 'testing' in parts or 'fixtures' in parts:
        return True
    if name.startswith('test_') or name.endswith('_test.py'):
        return True
    return False


def visible_test_names(output: str) -> list[str]:
    names: list[str] = []
    # pytest node ids: path.py::Class::test_name or path.py::test_name
    for m in re.finditer(r'::(test_[A-Za-z0-9_]+)', output):
        n = m.group(1)
        if n not in names:
            names.append(n)
    # unittest dotted names: Class.test_name or module.Class.test_name
    for m in re.finditer(r'\.((?:test_)[A-Za-z0-9_]+)', output):
        n = m.group(1)
        if n not in names:
            names.append(n)
    return names


def identifier_candidates(test_names: list[str]) -> list[str]:
    scored: dict[str, tuple[int, int, str]] = {}
    for ti, raw in enumerate(test_names):
        stem = raw[5:] if raw.startswith('test_') else raw
        toks = [t for t in stem.split('_') if t]
        # Longest prefixes first, e.g. strip_jsonp, xs_datetimelike_wrapping,
        # xs_datetimelike, xs. Individual tokens follow.
        seqs: list[str] = []
        for end in range(len(toks), 0, -1):
            seqs.append('_'.join(toks[:end]))
        seqs.extend(toks)
        for s in seqs:
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', s):
                continue
            # Ignore generic test-language tokens unless they occur in a compound identifier.
            if '_' not in s and s.lower() in {'returns','return','value','values','error','errors','case','cases','data','object','result','results','wrapping','like'}:
                continue
            key = (len(s), -ti, s)
            if s not in scored or key > scored[s]:
                scored[s] = key
    return [s for s,_ in sorted(scored.items(), key=lambda kv: (-kv[1][0], -kv[1][1], kv[0]))]


def _project_py(work: Path) -> list[Path]:
    out: list[Path] = []
    root = work.resolve()
    for p in sorted(work.rglob('*.py')):
        try:
            rel = p.resolve().relative_to(root)
        except Exception:
            continue
        if _excluded(rel):
            continue
        if p.is_file():
            out.append(p)
    return out


def resolve_context(work: Path, baseline_output: str, *, max_files: int = MAX_FILES, max_chars: int = MAX_CHARS) -> tuple[str, list[str], dict[str, Any]]:
    root = work.resolve()
    tests = visible_test_names(baseline_output)
    identifiers = identifier_candidates(tests)
    project_files = _project_py(work)
    hits: list[tuple[int, str, str, Path]] = []

    for p in project_files:
        try:
            text = p.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        rel = str(p.resolve().relative_to(root))
        for ident in identifiers:
            pat = re.compile(r'(?m)^\s*(?:async\s+)?def\s+' + re.escape(ident) + r'\s*\(')
            if pat.search(text):
                hits.append((-len(ident), ident, rel, p))
    hits.sort(key=lambda x: (x[0], x[2], x[1]))

    chosen: list[Path] = []
    match_meta: list[dict[str, str]] = []
    for _, ident, rel, p in hits:
        if p not in chosen:
            chosen.append(p)
            match_meta.append({'identifier': ident, 'path': rel})
        if len(chosen) >= max_files:
            break

    # Add project source explicitly referenced by native traceback, but never tests/envs.
    for raw in re.findall(r'File ["\']([^"\']+\.py)["\']', baseline_output):
        p = Path(raw)
        if not p.is_absolute():
            p = work / p
        try:
            rp = p.resolve(); relp = rp.relative_to(root)
        except Exception:
            continue
        if _excluded(relp) or not rp.is_file() or rp in chosen:
            continue
        chosen.append(rp)
        if len(chosen) >= max_files:
            break

    # Deterministic non-test fallback only after symbol/traceback resolution.
    for p in project_files:
        if p not in chosen:
            chosen.append(p)
        if len(chosen) >= max_files:
            break

    chunks: list[str] = []
    used: list[str] = []
    remaining = max_chars
    for p in chosen[:max_files]:
        text = p.read_text(encoding='utf-8', errors='replace')
        rel = str(p.resolve().relative_to(root))
        # If a relevant exact definition is in a very large file, center a bounded
        # excerpt on the first matched definition rather than dropping the file.
        chunk_text = text
        if len(text) > 16000:
            pos = None
            for mm in match_meta:
                if mm['path'] == rel:
                    m = re.search(r'(?m)^\s*(?:async\s+)?def\s+' + re.escape(mm['identifier']) + r'\s*\(', text)
                    if m:
                        pos = m.start(); break
            if pos is not None:
                lo=max(0,pos-5000); hi=min(len(text),pos+11000); chunk_text=text[lo:hi]
            else:
                chunk_text=text[:16000]
        chunk=f"\n### FILE {rel}\n```python\n{chunk_text}\n```\n"
        if len(chunk) > remaining:
            continue
        chunks.append(chunk); used.append(rel); remaining -= len(chunk)

    audit = {
        'visible_test_names': tests,
        'identifier_candidates': identifiers,
        'exact_definition_matches': match_meta,
        'selected_files': used,
        'eligible_exact_hit': bool(match_meta),
    }
    return ''.join(chunks), used, audit
