from __future__ import annotations
import hashlib, json, random, shutil, subprocess
from pathlib import Path

ROOT=Path.cwd(); NANODA=ROOT/'nanoda_lib'; CORPUS=ROOT/'v94-corpus'; OUT=ROOT/'results'/'v94'
REV='418320295890faed83a96fd97907b12a3b6728c2'

def run(cmd,cwd=None): subprocess.run(cmd,cwd=cwd,check=True)

def setup():
    if NANODA.exists(): shutil.rmtree(NANODA)
    run(['git','clone','-q','https://github.com/ammkrn/nanoda_lib.git',str(NANODA)])
    run(['git','checkout','-q',REV],cwd=NANODA)
    (NANODA/'config.json').write_text(json.dumps({'use_stdin':True,'nat_extension':True,'string_extension':True,'unpermitted_axiom_hard_error':False,'unsafe_permit_all_axioms':True,'num_threads':4},indent=2)+'\n')
    run(['cargo','build','--release','-q'],cwd=NANODA)

def corpus():
    if CORPUS.exists(): shutil.rmtree(CORPUS)
    (CORPUS/'positive').mkdir(parents=True); (CORPUS/'negative').mkdir(parents=True); OUT.mkdir(parents=True,exist_ok=True)
    meta={'meta':{'exporter':{'name':'v94-tagged-backref','version':'0.1.0'},'format':{'version':'3.1.0'},'lean':{'githash':'2fcce7258eeb6e324366bc25f9058293b04b7547','version':'4.29.1'}}}
    man=[]
    for seed in range(256):
        r=random.Random(seed); shared=r.randrange(1,1_000_000); la=r.randrange(1,1_000_000)
        while la==shared: la=r.randrange(1,1_000_000)
        rows=[meta,{'in':shared,'str':{'pre':0,'str':'foo'}},{'il':shared,'succ':0},{'il':la,'succ':shared},{'ie':shared,'sort':la},{'axiom':{'isUnsafe':False,'levelParams':[],'name':shared,'type':shared}}]
        p=CORPUS/'positive'/f'{seed:03d}.ndjson'; p.write_text('\n'.join(json.dumps(x,separators=(',',':')) for x in rows)+'\n')
        man.append({'kind':'positive-cross-type-overlap','seed':seed,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        d=[dict(x) for x in rows]; d[4]={'ie':shared,'sort':2_000_001+seed}
        q=CORPUS/'negative'/f'{seed:03d}-dangling.ndjson'; q.write_text('\n'.join(json.dumps(x,separators=(',',':')) for x in d)+'\n'); man.append({'kind':'dangling','seed':seed,'path':str(q)})
        dup=rows[:-1]+[{'ie':shared,'sort':shared},rows[-1]]
        q=CORPUS/'negative'/f'{seed:03d}-duplicate.ndjson'; q.write_text('\n'.join(json.dumps(x,separators=(',',':')) for x in dup)+'\n'); man.append({'kind':'duplicate','seed':seed,'path':str(q)})
    (OUT/'manifest.json').write_text(json.dumps(man,indent=2)+'\n')

def patch(mode):
    run(['git','checkout','-q','--','src/parser.rs'],cwd=NANODA)
    p=NANODA/'src/parser.rs'; s=p.read_text(); tagged=mode!='TYPE_ERASED'; injective=mode!='NO_INJECTIVITY'
    def rep(a,b,n=1):
        nonlocal s
        if s.count(a)!=n: raise RuntimeError(f'anchor {s.count(a)} != {n}: {a[:80]}')
        s=s.replace(a,b,n)
    store=r'''
#[derive(Clone, Copy, PartialEq, Eq, Hash)]
enum BackRefKind { Name, Level, Expr }
#[derive(Clone, Copy)]
enum BackRefValue<'a> { Name(NamePtr<'a>), Level(LevelPtr<'a>), Expr(ExprPtr<'a>) }
struct BackRefStore<'a> {
    tagged: FxHashMap<(BackRefKind, u32), BackRefValue<'a>>,
    erased: FxHashMap<u32, BackRefValue<'a>>,
}
impl<'a> BackRefStore<'a> {
    fn new() -> Self { Self { tagged: new_fx_hash_map(), erased: new_fx_hash_map() } }
    fn seed(&mut self, k: BackRefKind, ext: u32, v: BackRefValue<'a>, tagged: bool) {
        if tagged { self.tagged.insert((k,ext),v); } else { self.erased.insert(ext,v); }
    }
    fn bind(&mut self, k: BackRefKind, ext: u32, v: BackRefValue<'a>, tagged: bool, injective: bool) {
        if tagged {
            if injective && self.tagged.insert((k,ext),v).is_some() { panic!("duplicate tagged back-reference {}",ext); }
            if !injective { self.tagged.insert((k,ext),v); }
        } else {
            if injective && self.erased.insert(ext,v).is_some() { panic!("type-erased key collision {}",ext); }
            if !injective { self.erased.insert(ext,v); }
        }
    }
    fn get(&self, k: BackRefKind, ext: u32, tagged: bool) -> BackRefValue<'a> {
        if tagged { *self.tagged.get(&(k,ext)).unwrap_or_else(|| panic!("unknown tagged back-reference {}",ext)) }
        else { *self.erased.get(&ext).unwrap_or_else(|| panic!("unknown erased back-reference {}",ext)) }
    }
}

'''
    rep("pub struct Parser<'a, R: BufRead> {",store+"pub struct Parser<'a, R: BufRead> {")
    rep("    mutual_block_sizes: FxHashMap<NamePtr<'a>, (usize, usize)>\n}","    mutual_block_sizes: FxHashMap<NamePtr<'a>, (usize, usize)>,\n    backrefs: BackRefStore<'a>\n}")
    old="""    pub fn new(buf_reader: R, config: Config) -> Self {
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
    tg='true' if tagged else 'false'; inj='true' if injective else 'false'
    new=f"""    pub fn new(buf_reader: R, config: Config) -> Self {{
        let dag=LeanDag::new(&config);
        let mut backrefs=BackRefStore::new();
        backrefs.seed(BackRefKind::Name,0,BackRefValue::Name(NamePtr::from(DagMarker::ExportFile,0)),{tg});
        backrefs.seed(BackRefKind::Level,0,BackRefValue::Level(LevelPtr::from(DagMarker::ExportFile,0)),{tg});
        Self {{ buf_reader, line_num:0usize, dag, declars:new_fx_index_map(), notations:new_fx_hash_map(), config, skipped:Vec::new(), mutual_block_sizes:new_fx_hash_map(), backrefs }}
    }}"""
    rep(old,new)
    rep("""    fn get_name_ptr(&self, idx: u32) -> NamePtr<'a> {
        let out = crate::util::Ptr::from(DagMarker::ExportFile, idx as usize);
        assert!((idx as usize) < self.dag.names.len());
        out
    }""",f"""    fn get_name_ptr(&self, idx: u32) -> NamePtr<'a> {{ match self.backrefs.get(BackRefKind::Name,idx,{tg}) {{ BackRefValue::Name(x)=>x, _=>panic!(\"back-reference type mismatch\") }} }}""")
    rep("""    fn get_level_ptr(&self, idx: u32) -> LevelPtr<'a> {
        let out = crate::util::Ptr::from(DagMarker::ExportFile, idx as usize);
        assert!((idx as usize) < self.dag.levels.len());
        out
    }""",f"""    fn get_level_ptr(&self, idx: u32) -> LevelPtr<'a> {{ match self.backrefs.get(BackRefKind::Level,idx,{tg}) {{ BackRefValue::Level(x)=>x, _=>panic!(\"back-reference type mismatch\") }} }}""")
    rep("""    fn get_names(&self, idxs: &[u32]) -> Vec<NamePtr<'a>> {
        let mut names = Vec::new();
        for idx in idxs.iter().copied() {
            assert!(self.dag.names.get_index(idx as usize).is_some());
            names.push(NamePtr::from(DagMarker::ExportFile, idx as usize));
        }
        names
    }""","""    fn get_names(&self, idxs: &[u32]) -> Vec<NamePtr<'a>> { idxs.iter().copied().map(|idx| self.get_name_ptr(idx)).collect() }""")
    rep("""    fn get_levels_ptr(&mut self, idxs: &[u32]) -> LevelsPtr<'a> {
        let mut levels = Vec::new();
        for idx in idxs.iter().copied() {
            levels.push(LevelPtr::from(DagMarker::ExportFile, idx as usize));
        }
        LevelsPtr::from(DagMarker::ExportFile, self.dag.uparams.insert_full(Arc::from(levels)).0)
    }""","""    fn get_levels_ptr(&mut self, idxs: &[u32]) -> LevelsPtr<'a> { let levels=idxs.iter().copied().map(|idx| self.get_level_ptr(idx)).collect::<Vec<_>>(); LevelsPtr::from(DagMarker::ExportFile,self.dag.uparams.insert_full(Arc::from(levels)).0) }""")
    rep("""    fn get_expr_ptr(&self, idx: u32) -> ExprPtr<'a> {
        let out = crate::util::Ptr::from(DagMarker::ExportFile, idx as usize);
        assert!((idx as usize) < self.dag.exprs.len());
        out
    }""",f"""    fn get_expr_ptr(&self, idx: u32) -> ExprPtr<'a> {{ match self.backrefs.get(BackRefKind::Expr,idx,{tg}) {{ BackRefValue::Expr(x)=>x, _=>panic!(\"back-reference type mismatch\") }} }}""")
    anchor="    fn has_fvars(&self, e: ExprPtr<'a>) -> bool { self.dag.exprs.get_index(e.idx()).unwrap().has_fvars() }\n"
    def binder(kind,br,val): return f'''\n    fn bind_{kind.lower()}(&mut self, assigned: Option<BackRef>, (idx,_inserted):(usize,bool)) {{
        let ext=match assigned.expect("missing {kind} back-reference") {{ BackRef::{br}(i)=>i, other=>panic!("wrong {kind} back-reference kind: {{:?}}",other) }};
        self.backrefs.bind(BackRefKind::{kind},ext,BackRefValue::{kind}({val}::from(DagMarker::ExportFile,idx)),{tg},{inj});
    }}\n'''
    rep(anchor,anchor+binder('Name','In','NamePtr')+binder('Level','Il','LevelPtr')+binder('Expr','Ie','ExprPtr'))
    for oldcall,newcall in [('assigned_idx.unwrap().assert_in(insert_result);','self.bind_name(assigned_idx, insert_result);'),('assigned_idx.unwrap().assert_il(insert_result);','self.bind_level(assigned_idx, insert_result);'),('assigned_idx.unwrap().assert_ie(insert_result);','self.bind_expr(assigned_idx, insert_result);')]:
        if s.count(oldcall)==0: raise RuntimeError('missing bind family')
        s=s.replace(oldcall,newcall)
    p.write_text(s)
    return {'mode':mode,'tagged':tagged,'injective':injective,'store_definitions':s.count("struct BackRefStore<'a>"),'parser_store_fields':s.count("backrefs: BackRefStore<'a>")}

def eval(label):
    exe=NANODA/'target/release/nanoda_bin'; cfg=NANODA/'config.json'
    def one(p):
        with p.open('rb') as f: return subprocess.run([str(exe),str(cfg)],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
    pos=[one(p) for p in sorted((CORPUS/'positive').glob('*.ndjson'))]; dang=[one(p) for p in sorted((CORPUS/'negative').glob('*-dangling.ndjson'))]; dup=[one(p) for p in sorted((CORPUS/'negative').glob('*-duplicate.ndjson'))]
    row={'label':label,'positive_accepted':sum(x==0 for x in pos),'positive_total':len(pos),'dangling_rejected':sum(x!=0 for x in dang),'dangling_total':len(dang),'duplicate_rejected':sum(x!=0 for x in dup),'duplicate_total':len(dup),'all_positive_accept':all(x==0 for x in pos),'all_dangling_reject':all(x!=0 for x in dang),'all_duplicate_reject':all(x!=0 for x in dup)}
    (OUT/f'{label}.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n'); print(json.dumps(row,sort_keys=True),flush=True); return row

def main():
    setup(); corpus(); baseline=eval('BASELINE'); rows={}; meta={}
    for mode in ['TAGGED_SINGLE_STORE','TYPE_ERASED','NO_INJECTIVITY']:
        meta[mode]=patch(mode); run(['cargo','build','--release','-q'],cwd=NANODA); rows[mode]=eval(mode)
    good=rows['TAGGED_SINGLE_STORE']; erased=rows['TYPE_ERASED']; nog=rows['NO_INJECTIVITY']
    gates={'one_store_schema':meta['TAGGED_SINGLE_STORE']['store_definitions']==1 and meta['TAGGED_SINGLE_STORE']['parser_store_fields']==1,'single_tagged_store_sufficient':good['all_positive_accept'] and good['all_dangling_reject'] and good['all_duplicate_reject'],'type_tag_necessary':good['all_positive_accept'] and not erased['all_positive_accept'],'injectivity_necessary':good['all_duplicate_reject'] and not nog['all_duplicate_reject'],'positive_closure_independent_of_injectivity':nog['all_positive_accept'],'dangling_boundary_independent_of_injectivity':nog['all_dangling_reject']}
    result={'nanoda_rev':REV,'baseline':baseline,'variants':rows,'representation_metadata':meta,'gates':gates}; result['verdict']='PASS_SINGLE_TAGGED_BACKREF_STORE_V94' if all(gates.values()) else 'MIXED_SINGLE_TAGGED_BACKREF_STORE_V94'
    (OUT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True),flush=True)
    if result['verdict'].startswith('MIXED'): raise SystemExit(1)
if __name__=='__main__': main()
