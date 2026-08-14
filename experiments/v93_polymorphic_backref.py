from __future__ import annotations

import hashlib
import json
import random
import shutil
import subprocess
from pathlib import Path

ROOT = Path.cwd()
NANODA = ROOT / "nanoda_lib"
CORPUS = ROOT / "v93-corpus"
OUT = ROOT / "results" / "v93"
NANODA_REV = "418320295890faed83a96fd97907b12a3b6728c2"


def run(cmd, cwd=None, check=True, capture=False):
    kwargs = {"cwd": cwd, "check": check}
    if capture:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return subprocess.run(cmd, **kwargs)


def clone_once():
    if NANODA.exists():
        shutil.rmtree(NANODA)
    run(["git", "clone", "-q", "https://github.com/ammkrn/nanoda_lib.git", str(NANODA)])
    run(["git", "checkout", "-q", NANODA_REV], cwd=NANODA)
    (NANODA / "config.json").write_text(json.dumps({
        "use_stdin": True,
        "nat_extension": True,
        "string_extension": True,
        "unpermitted_axiom_hard_error": False,
        "unsafe_permit_all_axioms": True,
        "num_threads": 4,
    }, indent=2) + "\n")
    run(["cargo", "build", "--release", "-q"], cwd=NANODA)


def make_corpus():
    if CORPUS.exists():
        shutil.rmtree(CORPUS)
    (CORPUS / "positive").mkdir(parents=True)
    (CORPUS / "negative").mkdir(parents=True)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    meta = {"meta": {
        "exporter": {"name": "v93-polymorphic-backref", "version": "0.1.0"},
        "format": {"version": "3.1.0"},
        "lean": {"githash": "2fcce7258eeb6e324366bc25f9058293b04b7547", "version": "4.29.1"},
    }}
    for seed in range(256):
        r = random.Random(seed)
        shared = r.randrange(1, 1_000_000)
        level_a = r.randrange(1, 1_000_000)
        while level_a == shared:
            level_a = r.randrange(1, 1_000_000)
        # The SAME external integer key is intentionally valid in all three namespaces:
        # Name(shared), Level(shared), Expr(shared).  Only the type tag distinguishes them.
        rows = [
            meta,
            {"in": shared, "str": {"pre": 0, "str": "foo"}},
            {"il": shared, "succ": 0},
            {"il": level_a, "succ": shared},
            {"ie": shared, "sort": level_a},
            {"axiom": {"isUnsafe": False, "levelParams": [], "name": shared, "type": shared}},
        ]
        p = CORPUS / "positive" / f"{seed:03d}.ndjson"
        p.write_text("\n".join(json.dumps(x, separators=(",", ":")) for x in rows) + "\n")
        manifest.append({"kind": "positive-cross-type-overlap", "seed": seed, "path": str(p),
                         "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})

        dangling = [dict(x) for x in rows]
        dangling[4] = {"ie": shared, "sort": 2_000_001 + seed}
        q = CORPUS / "negative" / f"{seed:03d}-dangling-level.ndjson"
        q.write_text("\n".join(json.dumps(x, separators=(",", ":")) for x in dangling) + "\n")
        manifest.append({"kind": "dangling-level", "seed": seed, "path": str(q),
                         "sha256": hashlib.sha256(q.read_bytes()).hexdigest()})

        # Same-type duplicate: both Expr definitions are locally meaningful, so the only defect
        # is rebinding the same external Expr key to two different Expr objects.
        duplicate = rows[:-1] + [{"ie": shared, "sort": shared}, rows[-1]]
        q = CORPUS / "negative" / f"{seed:03d}-duplicate-expr.ndjson"
        q.write_text("\n".join(json.dumps(x, separators=(",", ":")) for x in duplicate) + "\n")
        manifest.append({"kind": "duplicate-expr", "seed": seed, "path": str(q),
                         "sha256": hashlib.sha256(q.read_bytes()).hexdigest()})

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def patch_parser(mode: str):
    run(["git", "checkout", "-q", "--", "src/parser.rs"], cwd=NANODA)
    p = NANODA / "src" / "parser.rs"
    s = p.read_text()

    typed = mode != "TYPE_ERASED"
    guard = mode != "NO_INJECTIVITY"

    def rep(old: str, new: str, n: int = 1):
        nonlocal s
        c = s.count(old)
        if c != n:
            raise RuntimeError(f"anchor count {c}, expected {n}: {old[:100]!r}")
        s = s.replace(old, new, n)

    generic = r'''
struct BackRefTable<P: Copy> {
    map: FxHashMap<u32, P>,
}

impl<P: Copy> BackRefTable<P> {
    fn new() -> Self { Self { map: new_fx_hash_map() } }
    fn seed(&mut self, ext: u32, ptr: P) { self.map.insert(ext, ptr); }
    fn get(&self, ext: u32) -> P {
        *self.map.get(&ext).unwrap_or_else(|| panic!("unknown typed external back-reference {}", ext))
    }
    fn bind(&mut self, ext: u32, ptr: P, enforce_injective: bool) {
        if enforce_injective {
            if self.map.insert(ext, ptr).is_some() {
                panic!("duplicate typed external back-reference {}", ext);
            }
        } else {
            self.map.insert(ext, ptr);
        }
    }
}

'''
    rep("pub struct Parser<'a, R: BufRead> {", generic + "pub struct Parser<'a, R: BufRead> {")

    fields = """    mutual_block_sizes: FxHashMap<NamePtr<'a>, (usize, usize)>,
    name_backrefs: BackRefTable<NamePtr<'a>>,
    level_backrefs: BackRefTable<LevelPtr<'a>>,
    expr_backrefs: BackRefTable<ExprPtr<'a>>"""
    if not typed:
        fields += ",\n    untyped_seen: FxHashMap<u32, ()>"
    rep("    mutual_block_sizes: FxHashMap<NamePtr<'a>, (usize, usize)>\n}", fields + "\n}")

    old_new = """    pub fn new(buf_reader: R, config: Config) -> Self {
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
    init_untyped = "\n        let untyped_seen = new_fx_hash_map();" if not typed else ""
    field_untyped = ",\n            untyped_seen" if not typed else ""
    new_new = f"""    pub fn new(buf_reader: R, config: Config) -> Self {{
        let dag = LeanDag::new(&config);
        let mut name_backrefs = BackRefTable::new();
        let mut level_backrefs = BackRefTable::new();
        let expr_backrefs = BackRefTable::new();
        name_backrefs.seed(0, NamePtr::from(DagMarker::ExportFile, 0));
        level_backrefs.seed(0, LevelPtr::from(DagMarker::ExportFile, 0));{init_untyped}
        Self {{
            buf_reader,
            line_num: 0usize,
            dag,
            declars: new_fx_index_map(),
            notations: new_fx_hash_map(),
            config,
            skipped: Vec::new(),
            mutual_block_sizes: new_fx_hash_map(),
            name_backrefs,
            level_backrefs,
            expr_backrefs{field_untyped}
        }}
    }}"""
    rep(old_new, new_new)

    rep("""    fn get_name_ptr(&self, idx: u32) -> NamePtr<'a> {
        let out = crate::util::Ptr::from(DagMarker::ExportFile, idx as usize);
        assert!((idx as usize) < self.dag.names.len());
        out
    }""", """    fn get_name_ptr(&self, idx: u32) -> NamePtr<'a> {
        self.name_backrefs.get(idx)
    }""")
    rep("""    fn get_level_ptr(&self, idx: u32) -> LevelPtr<'a> {
        let out = crate::util::Ptr::from(DagMarker::ExportFile, idx as usize);
        assert!((idx as usize) < self.dag.levels.len());
        out
    }""", """    fn get_level_ptr(&self, idx: u32) -> LevelPtr<'a> {
        self.level_backrefs.get(idx)
    }""")
    rep("""    fn get_names(&self, idxs: &[u32]) -> Vec<NamePtr<'a>> {
        let mut names = Vec::new();
        for idx in idxs.iter().copied() {
            assert!(self.dag.names.get_index(idx as usize).is_some());
            names.push(NamePtr::from(DagMarker::ExportFile, idx as usize));
        }
        names
    }""", """    fn get_names(&self, idxs: &[u32]) -> Vec<NamePtr<'a>> {
        idxs.iter().copied().map(|idx| self.get_name_ptr(idx)).collect()
    }""")
    rep("""    fn get_levels_ptr(&mut self, idxs: &[u32]) -> LevelsPtr<'a> {
        let mut levels = Vec::new();
        for idx in idxs.iter().copied() {
            levels.push(LevelPtr::from(DagMarker::ExportFile, idx as usize));
        }
        LevelsPtr::from(DagMarker::ExportFile, self.dag.uparams.insert_full(Arc::from(levels)).0)
    }""", """    fn get_levels_ptr(&mut self, idxs: &[u32]) -> LevelsPtr<'a> {
        let levels = idxs.iter().copied().map(|idx| self.get_level_ptr(idx)).collect::<Vec<_>>();
        LevelsPtr::from(DagMarker::ExportFile, self.dag.uparams.insert_full(Arc::from(levels)).0)
    }""")
    rep("""    fn get_expr_ptr(&self, idx: u32) -> ExprPtr<'a> {
        let out = crate::util::Ptr::from(DagMarker::ExportFile, idx as usize);
        assert!((idx as usize) < self.dag.exprs.len());
        out
    }""", """    fn get_expr_ptr(&self, idx: u32) -> ExprPtr<'a> {
        self.expr_backrefs.get(idx)
    }""")

    global_check = "" if typed else """        if self.untyped_seen.insert(ext, ()).is_some() {
            panic!("type-erased external key collision {}", ext);
        }
"""
    guard_lit = "true" if guard else "false"

    def binder(kind: str, br: str, field: str, ptr: str):
        return f'''\n    fn bind_{kind.lower()}(&mut self, assigned: Option<BackRef>, (idx, _inserted): (usize, bool)) {{
        let ext = match assigned.expect("missing {kind} back-reference") {{
            BackRef::{br}(i) => i,
            other => panic!("wrong {kind} back-reference kind: {{:?}}", other),
        }};
{global_check}        self.{field}.bind(ext, {ptr}::from(DagMarker::ExportFile, idx), {guard_lit});
    }}\n'''

    anchor = "    fn has_fvars(&self, e: ExprPtr<'a>) -> bool { self.dag.exprs.get_index(e.idx()).unwrap().has_fvars() }\n"
    binders = binder("Name", "In", "name_backrefs", "NamePtr") + binder("Level", "Il", "level_backrefs", "LevelPtr") + binder("Expr", "Ie", "expr_backrefs", "ExprPtr")
    rep(anchor, anchor + binders)

    if s.count("assigned_idx.unwrap().assert_in(insert_result);") == 0:
        raise RuntimeError("missing Name bind calls")
    if s.count("assigned_idx.unwrap().assert_il(insert_result);") == 0:
        raise RuntimeError("missing Level bind calls")
    if s.count("assigned_idx.unwrap().assert_ie(insert_result);") == 0:
        raise RuntimeError("missing Expr bind calls")
    s = s.replace("assigned_idx.unwrap().assert_in(insert_result);", "self.bind_name(assigned_idx, insert_result);")
    s = s.replace("assigned_idx.unwrap().assert_il(insert_result);", "self.bind_level(assigned_idx, insert_result);")
    s = s.replace("assigned_idx.unwrap().assert_ie(insert_result);", "self.bind_expr(assigned_idx, insert_result);")

    p.write_text(s)
    return {
        "mode": mode,
        "typed": typed,
        "injective": guard,
        "generic_table_definitions": s.count("struct BackRefTable<P: Copy>"),
        "typed_instances": sum(s.count(x) for x in [
            "BackRefTable<NamePtr<'a>>", "BackRefTable<LevelPtr<'a>>", "BackRefTable<ExprPtr<'a>>"
        ]),
    }


def evaluate(label: str):
    exe = NANODA / "target" / "release" / "nanoda_bin"
    cfg = NANODA / "config.json"

    def one(p: Path):
        with p.open("rb") as f:
            return subprocess.run([str(exe), str(cfg)], stdin=f,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode

    pos = [one(p) for p in sorted((CORPUS / "positive").glob("*.ndjson"))]
    dangling = [one(p) for p in sorted((CORPUS / "negative").glob("*-dangling-level.ndjson"))]
    duplicate = [one(p) for p in sorted((CORPUS / "negative").glob("*-duplicate-expr.ndjson"))]
    row = {
        "label": label,
        "positive_total": len(pos),
        "positive_accepted": sum(x == 0 for x in pos),
        "dangling_total": len(dangling),
        "dangling_rejected": sum(x != 0 for x in dangling),
        "duplicate_total": len(duplicate),
        "duplicate_rejected": sum(x != 0 for x in duplicate),
        "all_positive_accept": all(x == 0 for x in pos),
        "all_dangling_reject": all(x != 0 for x in dangling),
        "all_duplicate_reject": all(x != 0 for x in duplicate),
    }
    (OUT / f"{label}.json").write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
    print(json.dumps(row, sort_keys=True), flush=True)
    return row


def main():
    clone_once()
    make_corpus()

    # Baseline is expected to reject arbitrary/non-contiguous external IDs.
    baseline = evaluate("BASELINE")

    rows = {}
    meta = {}
    for mode in ["POLYMORPHIC_TYPED", "TYPE_ERASED", "NO_INJECTIVITY"]:
        meta[mode] = patch_parser(mode)
        run(["cargo", "build", "--release", "-q"], cwd=NANODA)
        rows[mode] = evaluate(mode)

    good = rows["POLYMORPHIC_TYPED"]
    erased = rows["TYPE_ERASED"]
    noguard = rows["NO_INJECTIVITY"]

    result = {
        "nanoda_rev": NANODA_REV,
        "baseline": baseline,
        "variants": rows,
        "representation_metadata": meta,
        "gates": {
            "generic_schema_single_definition": meta["POLYMORPHIC_TYPED"]["generic_table_definitions"] == 1,
            "three_typed_instances_of_one_schema": meta["POLYMORPHIC_TYPED"]["typed_instances"] == 3,
            "polymorphic_schema_sufficient": good["all_positive_accept"] and good["all_dangling_reject"] and good["all_duplicate_reject"],
            "type_parameter_necessary": good["all_positive_accept"] and not erased["all_positive_accept"],
            "injectivity_law_necessary_for_boundary": good["all_duplicate_reject"] and not noguard["all_duplicate_reject"],
            "positive_closure_survives_without_injectivity": noguard["all_positive_accept"],
            "dangling_boundary_preserved_without_injectivity": noguard["all_dangling_reject"],
        },
    }
    result["verdict"] = "PASS_POLYMORPHIC_BACKREF_QUOTIENT_V93" if all(result["gates"].values()) else "MIXED_POLYMORPHIC_BACKREF_QUOTIENT_V93"
    (OUT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    if result["verdict"].startswith("MIXED"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
