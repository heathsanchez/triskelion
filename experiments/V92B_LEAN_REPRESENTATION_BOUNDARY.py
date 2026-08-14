#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("v92", HERE / "V92_LEAN_REPRESENTATION_FACTORIZATION.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def make_corpus():
    manifest = []
    meta = {"meta": {"exporter": {"name": "v92b-boundary", "version": "0.1.0"},
                     "format": {"version": "3.1.0"},
                     "lean": {"githash": "2fcce7258eeb6e324366bc25f9058293b04b7547", "version": "4.29.1"}}}
    for seed in range(256):
        r = random.Random(seed)
        name_id = r.randrange(1, 1_000_000)
        level_a = r.randrange(1, 1_000_000)
        level_b = r.randrange(1, 1_000_000)
        while level_b == level_a:
            level_b = r.randrange(1, 1_000_000)
        expr_id = r.randrange(1, 1_000_000)
        rows = [meta,
                {"in": name_id, "str": {"pre": 0, "str": "foo"}},
                {"il": level_b, "succ": 0},
                {"il": level_a, "succ": level_b},
                {"ie": expr_id, "sort": level_a},
                {"axiom": {"isUnsafe": False, "levelParams": [], "name": name_id, "type": expr_id}}]
        p = v.CORPUS / "positive" / f"{seed:03d}.ndjson"
        p.write_text("\n".join(json.dumps(x, separators=(",", ":")) for x in rows) + "\n")
        manifest.append({"kind": "positive", "seed": seed, "path": str(p),
                         "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})

        dangling = [dict(x) for x in rows]
        dangling[4] = {"ie": expr_id, "sort": 1_000_001 + seed}
        q = v.CORPUS / "negative" / f"{seed:03d}-dangling-level.ndjson"
        q.write_text("\n".join(json.dumps(x, separators=(",", ":")) for x in dangling) + "\n")
        manifest.append({"kind": "dangling-level", "seed": seed, "path": str(q),
                         "sha256": hashlib.sha256(q.read_bytes()).hexdigest()})

        # Boundary-isolating duplicate: both individual expressions are valid Sort expressions.
        # The only intended defect is reuse of the same external expression key for a distinct
        # second expression. If duplicate-key rejection is removed, last-write-wins can otherwise
        # produce a semantically valid axiom and should expose the lost representation invariant.
        duplicate = rows[:-1] + [{"ie": expr_id, "sort": level_b}, rows[-1]]
        q = v.CORPUS / "negative" / f"{seed:03d}-duplicate-expr.ndjson"
        q.write_text("\n".join(json.dumps(x, separators=(",", ":")) for x in duplicate) + "\n")
        manifest.append({"kind": "duplicate-expr-valid-overwrite", "seed": seed, "path": str(q),
                         "sha256": hashlib.sha256(q.read_bytes()).hexdigest()})
    (v.OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))


v.make_corpus = make_corpus
v.main()
p = v.OUT / "RESULT.json"
r = json.loads(p.read_text())
r["protocol"] = "V92B_LEAN_REPRESENTATION_BOUNDARY"
r["qualification"] = "Boundary-isolating correction of V92. Positive and dangling-reference families are unchanged in structure. The duplicate-expression negative now binds the same external expression key twice to two individually valid Sort expressions, isolating external-key injectivity from downstream semantic invalidity. All 2^3 Name/Level/Expr map subsets and the duplicate-guard ablation remain frozen as in V92."
r["verdict"] = "PASS_MINIMUM_CAUSAL_REPRESENTATION_BOUNDARY_V92B" if all(r["gates"].values()) else "MIXED_REPRESENTATION_BOUNDARY_V92B"
p.write_text(json.dumps(r, indent=2, sort_keys=True))
print(json.dumps(r, indent=2, sort_keys=True))
