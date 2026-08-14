#!/usr/bin/env python3
import hashlib
import json
import os
import random
import shutil
import subprocess
from pathlib import Path

ROOT = Path(os.environ.get("NANODA_DIR", "nanoda_lib"))
OUT = Path(os.environ.get("OUT_DIR", "results/v92"))
CORPUS = Path(os.environ.get("CORPUS_DIR", "v92-corpus"))
OUT.mkdir(parents=True, exist_ok=True)
(CORPUS / "positive").mkdir(parents=True, exist_ok=True)
(CORPUS / "negative").mkdir(parents=True, exist_ok=True)

NANODA_REV = "418320295890faed83a96fd97907b12a3b6728c2"


def sh(*args, cwd=None, check=True):
    return subprocess.run(args, cwd=cwd, check=check)


def make_corpus():
    manifest = []
    meta = {"meta": {"exporter": {"name": "v92-factorization", "version": "0.1.0"},
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
        p = CORPUS / "positive" / f"{seed:03d}.ndjson"
        p.write_text("\n".join(json.dumps(x, separators=(",", ":")) for x in rows) + "\n")
        manifest.append({"kind": "positive", "seed": seed, "path": str(p),
                         "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})

        bad = [dict(x) for x in rows]
        bad[4] = {"ie": expr_id, "sort": 1_000_001 + seed}
        q = CORPUS / "negative" / f"{seed:03d}-dangling-level.ndjson"
        q.write_text("\n".join(json.dumps(x, separators=(",", ":")) for x in bad) + "\n")
        manifest.append({"kind": "dangling-level", "seed": seed, "path": str(q),
                         "sha256": hashlib.sha256(q.read_bytes()).hexdigest()})

        dup = rows[:-1] + [{"ie": expr_id, "bvar": 0}, rows[-1]]
        q = CORPUS / "negative" / f"{seed:03d}-duplicate-expr.ndjson"
        q.write_text("\n".join(json.dumps(x, separators=(",", ":")) for x in dup) + "\n")
        manifest.append({"kind": "duplicate-expr", "seed": seed, "path": str(q),
                         "sha256": hashlib.sha256(q.read_bytes()).hexdigest()})
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))


def rep(s, old, new, n=1):
    c = s.count(old)
    if c != n:
        raise RuntimeError(f"anchor count {c}, expected {n}: {old[:120]!r}")
    return s.replace(old, new, n)


def apply_factor(enabled, guard=True):
    p = ROOT / "src/parser.rs"
    s = p.read_text()
    fields = []
    if "NAME" in enabled:
        fields.append("    name_backrefs: FxHashMap<u32, NamePtr<'a>>")
    if "LEVEL" in enabled:
        fields.append("    level_backrefs: FxHashMap<u32, LevelPtr<'a>>")
    if "EXPR" in enabled:
        fields.append("    expr_backrefs: FxHashMap<u32, ExprPtr<'a>>")
    if fields:
        s = rep(s,
                "    mutual_block_sizes: FxHashMap<NamePtr<'a>, (usize, usize)>\n}",
                "    mutual_block_sizes: FxHashMap<NamePtr<'a>, (usize, usize)>,\n" + ",\n".join(fields) + "\n}")
        pre = []
        extra = []
        if "NAME" in enabled:
            pre += ["        let mut name_backrefs = new_fx_hash_map();",
                    "        name_backrefs.insert(0, NamePtr::from(DagMarker::ExportFile, 0));"]
            extra.append("            name_backrefs")
        if "LEVEL" in enabled:
            pre += ["        let mut level_backrefs = new_fx_hash_map();",
                    "        level_backrefs.insert(0, LevelPtr::from(DagMarker::ExportFile, 0));"]
            extra.append("            level_backrefs")
        if "EXPR" in enabled:
            pre += ["        let expr_backrefs = new_fx_hash_map();"]
            extra.append("            expr_backrefs")
        old = """    pub fn new(buf_reader: R, config: Config) -> Self {
        Self {
            buf_reader,
            line_num: 0usize,
            dag: LeanDag::new(&config),
            declars: new_fx_index_map(),
            notations: new_fx_hash_map(),
            config,
            skipped: Vec::new(),
            mutual_block_sizes: new_fx_hash_map()
        }
    }"""
        new = ("    pub fn new(buf_reader: R, config: Config) -> Self {\n" + "\n".join(pre) +
               "\n        Self {\n            buf_reader,\n            line_num: 0usize,\n            dag: LeanDag::new(&config),\n"
               "            declars: new_fx_index_map(),\n            notations: new_fx_hash_map(),\n            config,\n"
               "            skipped: Vec::new(),\n            mutual_block_sizes: new_fx_hash_map(),\n" +
               ",\n".join(extra) + "\n        }\n    }")
        s = rep(s, old, new)

    if "NAME" in enabled:
        s = rep(s, """    fn get_name_ptr(&self, idx: u32) -> NamePtr<'a> {
        let out = crate::util::Ptr::from(DagMarker::ExportFile, idx as usize);
        assert!((idx as usize) < self.dag.names.len());
        out
    }""", """    fn get_name_ptr(&self, idx: u32) -> NamePtr<'a> {
        *self.name_backrefs.get(&idx).unwrap_or_else(|| panic!("unknown Name back-reference {}", idx))
    }""")
        s = rep(s, """    fn get_names(&self, idxs: &[u32]) -> Vec<NamePtr<'a>> {
        let mut names = Vec::new();
        for idx in idxs.iter().copied() {
            assert!(self.dag.names.get_index(idx as usize).is_some());
            names.push(NamePtr::from(DagMarker::ExportFile, idx as usize));
        }
        names
    }""", """    fn get_names(&self, idxs: &[u32]) -> Vec<NamePtr<'a>> {
        idxs.iter().copied().map(|idx| self.get_name_ptr(idx)).collect()
    }""")
    if "LEVEL" in enabled:
        s = rep(s, """    fn get_level_ptr(&self, idx: u32) -> LevelPtr<'a> {
        let out = crate::util::Ptr::from(DagMarker::ExportFile, idx as usize);
        assert!((idx as usize) < self.dag.levels.len());
        out
    }""", """    fn get_level_ptr(&self, idx: u32) -> LevelPtr<'a> {
        *self.level_backrefs.get(&idx).unwrap_or_else(|| panic!("unknown Level back-reference {}", idx))
    }""")
        s = rep(s, """    fn get_levels_ptr(&mut self, idxs: &[u32]) -> LevelsPtr<'a> {
        let mut levels = Vec::new();
        for idx in idxs.iter().copied() {
            levels.push(LevelPtr::from(DagMarker::ExportFile, idx as usize));
        }
        LevelsPtr::from(DagMarker::ExportFile, self.dag.uparams.insert_full(Arc::from(levels)).0)
    }""", """    fn get_levels_ptr(&mut self, idxs: &[u32]) -> LevelsPtr<'a> {
        let levels = idxs.iter().copied().map(|idx| self.get_level_ptr(idx)).collect::<Vec<_>>();
        LevelsPtr::from(DagMarker::ExportFile, self.dag.uparams.insert_full(Arc::from(levels)).0)
    }""")
    if "EXPR" in enabled:
        s = rep(s, """    fn get_expr_ptr(&self, idx: u32) -> ExprPtr<'a> {
        let out = crate::util::Ptr::from(DagMarker::ExportFile, idx as usize);
        assert!((idx as usize) < self.dag.exprs.len());
        out
    }""", """    fn get_expr_ptr(&self, idx: u32) -> ExprPtr<'a> {
        *self.expr_backrefs.get(&idx).unwrap_or_else(|| panic!("unknown Expr back-reference {}", idx))
    }""")

    def binder(kind, br, mapname, ptr):
        if guard:
            body = (f"        if self.{mapname}.insert(ext, {ptr}::from(DagMarker::ExportFile, idx)).is_some() {{\n"
                    f"            panic!(\"duplicate {kind} back-reference {{}}\", ext);\n        }}")
        else:
            body = f"        self.{mapname}.insert(ext, {ptr}::from(DagMarker::ExportFile, idx));"
        return (f"\n    fn bind_{kind.lower()}(&mut self, assigned: Option<BackRef>, (idx, _inserted): (usize, bool)) {{\n"
                f"        let ext = match assigned.expect(\"missing {kind} back-reference\") {{\n"
                f"            BackRef::{br}(i) => i,\n            other => panic!(\"wrong {kind} back-reference kind: {{:?}}\", other),\n        }};\n"
                f"{body}\n    }}\n")

    binders = []
    if "NAME" in enabled:
        binders.append(binder("Name", "In", "name_backrefs", "NamePtr"))
    if "LEVEL" in enabled:
        binders.append(binder("Level", "Il", "level_backrefs", "LevelPtr"))
    if "EXPR" in enabled:
        binders.append(binder("Expr", "Ie", "expr_backrefs", "ExprPtr"))
    if binders:
        anchor = "    fn has_fvars(&self, e: ExprPtr<'a>) -> bool { self.dag.exprs.get_index(e.idx()).unwrap().has_fvars() }\n"
        s = rep(s, anchor, anchor + "".join(binders))
    if "NAME" in enabled:
        if s.count("assigned_idx.unwrap().assert_in(insert_result);") == 0:
            raise RuntimeError("no NAME bind sites")
        s = s.replace("assigned_idx.unwrap().assert_in(insert_result);", "self.bind_name(assigned_idx, insert_result);")
    if "LEVEL" in enabled:
        if s.count("assigned_idx.unwrap().assert_il(insert_result);") == 0:
            raise RuntimeError("no LEVEL bind sites")
        s = s.replace("assigned_idx.unwrap().assert_il(insert_result);", "self.bind_level(assigned_idx, insert_result);")
    if "EXPR" in enabled:
        if s.count("assigned_idx.unwrap().assert_ie(insert_result);") == 0:
            raise RuntimeError("no EXPR bind sites")
        s = s.replace("assigned_idx.unwrap().assert_ie(insert_result);", "self.bind_expr(assigned_idx, insert_result);")
    p.write_text(s)


def build():
    sh("cargo", "build", "--release", "-q", cwd=ROOT)


def run_one(path):
    with path.open("rb") as f:
        return subprocess.run([str((ROOT / "target/release/nanoda_bin").resolve()), str((ROOT / "config.json").resolve())],
                              stdin=f, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode


def eval_variant(label):
    pos = [run_one(p) for p in sorted((CORPUS / "positive").glob("*.ndjson"))]
    dang = [run_one(p) for p in sorted((CORPUS / "negative").glob("*-dangling-level.ndjson"))]
    dup = [run_one(p) for p in sorted((CORPUS / "negative").glob("*-duplicate-expr.ndjson"))]
    row = {"label": label,
           "positive_total": len(pos), "positive_accepted": sum(x == 0 for x in pos),
           "dangling_total": len(dang), "dangling_rejected": sum(x != 0 for x in dang),
           "duplicate_total": len(dup), "duplicate_rejected": sum(x != 0 for x in dup),
           "all_positive_accept": all(x == 0 for x in pos),
           "all_dangling_reject": all(x != 0 for x in dang),
           "all_duplicate_reject": all(x != 0 for x in dup)}
    (OUT / f"{label}.json").write_text(json.dumps(row, indent=2, sort_keys=True))
    print(json.dumps(row, sort_keys=True), flush=True)
    return row


def reset_parser():
    sh("git", "checkout", "-q", "--", "src/parser.rs", cwd=ROOT)


def main():
    make_corpus()
    build()
    rows = [eval_variant("NONE")]
    variants = [
        ("NAME", {"NAME"}, True),
        ("LEVEL", {"LEVEL"}, True),
        ("EXPR", {"EXPR"}, True),
        ("NAME_LEVEL", {"NAME", "LEVEL"}, True),
        ("NAME_EXPR", {"NAME", "EXPR"}, True),
        ("LEVEL_EXPR", {"LEVEL", "EXPR"}, True),
        ("NAME_LEVEL_EXPR", {"NAME", "LEVEL", "EXPR"}, True),
        ("NAME_LEVEL_EXPR_NO_GUARD", {"NAME", "LEVEL", "EXPR"}, False),
    ]
    for label, enabled, guard in variants:
        reset_parser()
        apply_factor(enabled, guard)
        build()
        rows.append(eval_variant(label))

    proper = {"NONE": set(), "NAME": {"NAME"}, "LEVEL": {"LEVEL"}, "EXPR": {"EXPR"},
              "NAME_LEVEL": {"NAME", "LEVEL"}, "NAME_EXPR": {"NAME", "EXPR"},
              "LEVEL_EXPR": {"LEVEL", "EXPR"}, "NAME_LEVEL_EXPR": {"NAME", "LEVEL", "EXPR"}}
    successful = [r["label"] for r in rows if r["all_positive_accept"] and r["all_dangling_reject"] and r["all_duplicate_reject"]]
    exact = [x for x in successful if x in proper]
    minimal = [x for x in exact if not any(proper[y] < proper[x] for y in exact)]
    by = {r["label"]: r for r in rows}
    full = by["NAME_LEVEL_EXPR"]
    nog = by["NAME_LEVEL_EXPR_NO_GUARD"]
    necessity = {"NAME": not by["LEVEL_EXPR"]["all_positive_accept"],
                 "LEVEL": not by["NAME_EXPR"]["all_positive_accept"],
                 "EXPR": not by["NAME_LEVEL"]["all_positive_accept"]}
    result = {
        "protocol": "V92_LEAN_REPRESENTATION_FACTORIZATION",
        "nanoda_rev": NANODA_REV,
        "corpus": {"positive": 256, "dangling_level_negative": 256, "duplicate_expr_negative": 256},
        "rows": rows,
        "successful_representations": successful,
        "minimal_successful_subsets": minimal,
        "component_necessity_for_positive_closure": necessity,
        "duplicate_guard_boundary_effect": {
            "full_guard_duplicate_rejected": full["duplicate_rejected"],
            "no_guard_duplicate_rejected": nog["duplicate_rejected"],
            "guard_required_for_duplicate_boundary": nog["duplicate_rejected"] < full["duplicate_rejected"]},
        "gates": {
            "full_representation_768_of_768": full["all_positive_accept"] and full["all_dangling_reject"] and full["all_duplicate_reject"],
            "all_three_backref_classes_individually_necessary_for_positive_closure": all(necessity.values()),
            "full_is_unique_minimal_subset": minimal == ["NAME_LEVEL_EXPR"],
            "duplicate_binding_guard_has_independent_boundary_value": nog["duplicate_rejected"] < full["duplicate_rejected"]},
        "qualification": "Finite causal factorization of the already-demonstrated Lean Kernel Arena external-ID representation capability. Tests all 2^3 subsets of Name/Level/Expr external back-reference maps on 256 positive and 512 hostile metamorphic cases, plus a duplicate-binding-guard ablation. Establishes minimum sufficiency only for this frozen corpus and representation family."
    }
    result["verdict"] = "PASS_MINIMUM_CAUSAL_REPRESENTATION_V92" if all(result["gates"].values()) else "MIXED_REPRESENTATION_FACTORIZATION_V92"
    (OUT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
