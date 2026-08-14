from pathlib import Path
import subprocess, json, random, shutil, sys

ROOT=Path.cwd(); NANODA=ROOT/'nanoda_lib'; OUT=ROOT/'results/v92c'; CORP=ROOT/'v92c-corpus'
OUT.mkdir(parents=True,exist_ok=True); (CORP/'positive').mkdir(parents=True,exist_ok=True); (CORP/'negative').mkdir(parents=True,exist_ok=True)
meta={"meta":{"exporter":{"name":"v92c","version":"0.1.0"},"format":{"version":"3.1.0"},"lean":{"githash":"2fcce7258eeb6e324366bc25f9058293b04b7547","version":"4.29.1"}}}
for seed in range(128):
    r=random.Random(seed); k=r.randrange(10,1_000_000); l2=r.randrange(10,1_000_000)
    while l2==k: l2=r.randrange(10,1_000_000)
    # Deliberately reuse k across Name/Level/Expr namespaces.
    rows=[meta,{"in":k,"str":{"pre":0,"str":"foo"}},{"il":l2,"succ":0},{"il":k,"succ":l2},{"ie":k,"sort":k},{"axiom":{"isUnsafe":False,"levelParams":[],"name":k,"type":k}}]
    p=CORP/'positive'/f'{seed:03}.ndjson'; p.write_text('\n'.join(json.dumps(x,separators=(',',':')) for x in rows)+'\n')
    # Same-type duplicate Expr key, both values otherwise valid.
    bad=rows[:-1]+[{"ie":k,"sort":l2},rows[-1]]
    q=CORP/'negative'/f'{seed:03}-duplicate-expr.ndjson'; q.write_text('\n'.join(json.dumps(x,separators=(',',':')) for x in bad)+'\n')

orig=(NANODA/'src/parser.rs').read_text()

def patch(mode):
    s=orig
    def rep(a,b,n=1):
        nonlocal s
        if s.count(a)!=n: raise RuntimeError(f'anchor {s.count(a)} != {n}: {a[:80]}')
        s=s.replace(a,b,n)
    typed = mode!='UNTYPED'
    guard = mode!='NO_GUARD'
    enum="""\n#[derive(Copy, Clone)]\nenum ExternalPtr<'a> {\n    Name(NamePtr<'a>),\n    Level(LevelPtr<'a>),\n    Expr(ExprPtr<'a>),\n}\n"""
    keyty="(u8, u32)" if typed else "u32"
    rep("pub struct Parser<'a, R: BufRead> {",enum+"\npub struct Parser<'a, R: BufRead> {")
    rep("    mutual_block_sizes: FxHashMap<NamePtr<'a>, (usize, usize)>\n}",f"    mutual_block_sizes: FxHashMap<NamePtr<'a>, (usize, usize)>,\n    backrefs: FxHashMap<{keyty}, ExternalPtr<'a>>\n}}")
    pre="""        let mut backrefs = new_fx_hash_map();\n"""
    if typed:
        pre += "        backrefs.insert((0,0), ExternalPtr::Name(NamePtr::from(DagMarker::ExportFile,0)));\n        backrefs.insert((1,0), ExternalPtr::Level(LevelPtr::from(DagMarker::ExportFile,0)));\n"
    else:
        pre += "        backrefs.insert(0, ExternalPtr::Level(LevelPtr::from(DagMarker::ExportFile,0)));\n"
    old="""    pub fn new(buf_reader: R, config: Config) -> Self {\n        Self {\n            buf_reader,\n            line_num: 0usize,\n            dag: LeanDag::new(&config),\n            declars: new_fx_index_map(),\n            notations: new_fx_hash_map(),\n            config,\n            skipped: Vec::new(),\n            mutual_block_sizes: new_fx_hash_map()\n        }\n    }"""
    new="    pub fn new(buf_reader: R, config: Config) -> Self {\n"+pre+"        Self {\n            buf_reader,\n            line_num: 0usize,\n            dag: LeanDag::new(&config),\n            declars: new_fx_index_map(),\n            notations: new_fx_hash_map(),\n            config,\n            skipped: Vec::new(),\n            mutual_block_sizes: new_fx_hash_map(),\n            backrefs\n        }\n    }"
    rep(old,new)
    def key(tag): return f"({tag}, idx)" if typed else "idx"
    rep("""    fn get_name_ptr(&self, idx: u32) -> NamePtr<'a> {\n        let out = crate::util::Ptr::from(DagMarker::ExportFile, idx as usize);\n        assert!((idx as usize) < self.dag.names.len());\n        out\n    }""",f"""    fn get_name_ptr(&self, idx: u32) -> NamePtr<'a> {{\n        match self.backrefs.get(&{key(0)}) {{ Some(ExternalPtr::Name(p)) => *p, _ => panic!(\"unknown/wrong Name back-reference {{}}\", idx) }}\n    }}""")
    rep("""    fn get_level_ptr(&self, idx: u32) -> LevelPtr<'a> {\n        let out = crate::util::Ptr::from(DagMarker::ExportFile, idx as usize);\n        assert!((idx as usize) < self.dag.levels.len());\n        out\n    }""",f"""    fn get_level_ptr(&self, idx: u32) -> LevelPtr<'a> {{\n        match self.backrefs.get(&{key(1)}) {{ Some(ExternalPtr::Level(p)) => *p, _ => panic!(\"unknown/wrong Level back-reference {{}}\", idx) }}\n    }}""")
    rep("""    fn get_expr_ptr(&self, idx: u32) -> ExprPtr<'a> {\n        let out = crate::util::Ptr::from(DagMarker::ExportFile, idx as usize);\n        assert!((idx as usize) < self.dag.exprs.len());\n        out\n    }""",f"""    fn get_expr_ptr(&self, idx: u32) -> ExprPtr<'a> {{\n        match self.backrefs.get(&{key(2)}) {{ Some(ExternalPtr::Expr(p)) => *p, _ => panic!(\"unknown/wrong Expr back-reference {{}}\", idx) }}\n    }}""")
    rep("""    fn get_names(&self, idxs: &[u32]) -> Vec<NamePtr<'a>> {\n        let mut names = Vec::new();\n        for idx in idxs.iter().copied() {\n            assert!(self.dag.names.get_index(idx as usize).is_some());\n            names.push(NamePtr::from(DagMarker::ExportFile, idx as usize));\n        }\n        names\n    }""","""    fn get_names(&self, idxs: &[u32]) -> Vec<NamePtr<'a>> { idxs.iter().copied().map(|i| self.get_name_ptr(i)).collect() }""")
    rep("""    fn get_levels_ptr(&mut self, idxs: &[u32]) -> LevelsPtr<'a> {\n        let mut levels = Vec::new();\n        for idx in idxs.iter().copied() {\n            levels.push(LevelPtr::from(DagMarker::ExportFile, idx as usize));\n        }\n        LevelsPtr::from(DagMarker::ExportFile, self.dag.uparams.insert_full(Arc::from(levels)).0)\n    }""","""    fn get_levels_ptr(&mut self, idxs: &[u32]) -> LevelsPtr<'a> { let levels=idxs.iter().copied().map(|i| self.get_level_ptr(i)).collect::<Vec<_>>(); LevelsPtr::from(DagMarker::ExportFile,self.dag.uparams.insert_full(Arc::from(levels)).0) }""")
    ins="""
    fn bind_external(&mut self, assigned: Option<BackRef>, idx: usize) {
        let (tag, ext, val) = match assigned.expect("missing back-reference") {
            BackRef::In(i) => (0u8, i, ExternalPtr::Name(NamePtr::from(DagMarker::ExportFile,idx))),
            BackRef::Il(i) => (1u8, i, ExternalPtr::Level(LevelPtr::from(DagMarker::ExportFile,idx))),
            BackRef::Ie(i) => (2u8, i, ExternalPtr::Expr(ExprPtr::from(DagMarker::ExportFile,idx))),
        };
        let key = KEY_EXPR;
        GUARD_EXPR
    }
""".replace('KEY_EXPR','(tag, ext)' if typed else 'ext').replace('GUARD_EXPR','if self.backrefs.insert(key,val).is_some() { panic!("duplicate external back-reference"); }' if guard else 'self.backrefs.insert(key,val);')
    anchor="    fn has_fvars(&self, e: ExprPtr<'a>) -> bool { self.dag.exprs.get_index(e.idx()).unwrap().has_fvars() }\n"
    rep(anchor,anchor+ins)
    s=s.replace('assigned_idx.unwrap().assert_in(insert_result);','self.bind_external(assigned_idx, insert_result.0);')
    s=s.replace('assigned_idx.unwrap().assert_il(insert_result);','self.bind_external(assigned_idx, insert_result.0);')
    s=s.replace('assigned_idx.unwrap().assert_ie(insert_result);','self.bind_external(assigned_idx, insert_result.0);')
    (NANODA/'src/parser.rs').write_text(s)

def build():
    return subprocess.run(['cargo','build','--release','-q'],cwd=NANODA).returncode

def eval_mode(label):
    exe=NANODA/'target/release/nanoda_bin'; cfg=NANODA/'config.json'
    def run(p):
        with p.open('rb') as f: return subprocess.run([str(exe),str(cfg)],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
    pos=[run(p) for p in sorted((CORP/'positive').glob('*.ndjson'))]
    neg=[run(p) for p in sorted((CORP/'negative').glob('*.ndjson'))]
    row={'label':label,'positive_accepted':sum(x==0 for x in pos),'positive_total':len(pos),'duplicate_rejected':sum(x!=0 for x in neg),'duplicate_total':len(neg)}
    (OUT/f'{label}.json').write_text(json.dumps(row,indent=2,sort_keys=True)); print(row); return row

rows={}
# Baseline first.
if build()!=0: raise SystemExit('baseline build fail')
rows['BASELINE']=eval_mode('BASELINE')
for mode in ['TYPED','UNTYPED','NO_GUARD']:
    (NANODA/'src/parser.rs').write_text(orig); patch(mode)
    if build()!=0: raise SystemExit(f'{mode} build fail')
    rows[mode]=eval_mode(mode)
result={'rows':rows,'gates':{
    'baseline_obstruction':rows['BASELINE']['positive_accepted']==0,
    'typed_polymorphic_full_positive':rows['TYPED']['positive_accepted']==128,
    'typed_polymorphic_boundary':rows['TYPED']['duplicate_rejected']==128,
    'type_namespace_necessary':rows['UNTYPED']['positive_accepted']<128,
    'injectivity_necessary':rows['NO_GUARD']['positive_accepted']==128 and rows['NO_GUARD']['duplicate_rejected']==0,
}}
result['verdict']='PASS_POLYMORPHIC_BACKREF_V92C' if all(result['gates'].values()) else 'MIXED_POLYMORPHIC_BACKREF_V92C'
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)); print(json.dumps(result,indent=2,sort_keys=True))
