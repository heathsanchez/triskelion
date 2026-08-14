from __future__ import annotations
import json, random, shutil, subprocess
from pathlib import Path
import v94_tagged_backref_store as v94

ROOT=Path.cwd(); NANODA=ROOT/'nanoda_lib'; CORPUS=ROOT/'v95-corpus'; OUT=ROOT/'results'/'v95'

def run(cmd,cwd=None): subprocess.run(cmd,cwd=cwd,check=True)

def make_corpus():
    if CORPUS.exists(): shutil.rmtree(CORPUS)
    (CORPUS/'alias-positive').mkdir(parents=True); (CORPUS/'duplicate-negative').mkdir(parents=True); OUT.mkdir(parents=True,exist_ok=True)
    meta={'meta':{'exporter':{'name':'v95-law','version':'0.1.0'},'format':{'version':'3.1.0'},'lean':{'githash':'2fcce7258eeb6e324366bc25f9058293b04b7547','version':'4.29.1'}}}
    for seed in range(256):
        r=random.Random(seed); name_id=r.randrange(1,1_000_000); level_id=r.randrange(1,1_000_000); e1=r.randrange(1,1_000_000); e2=r.randrange(1,1_000_000)
        while len({name_id,level_id,e1,e2})<4:
            e2=r.randrange(1,1_000_000)
        # Two distinct external Expr IDs intentionally denote the same canonical Expr object Sort(level_id).
        rows=[meta,{'in':name_id,'str':{'pre':0,'str':'foo'}},{'il':level_id,'succ':0},{'ie':e1,'sort':level_id},{'ie':e2,'sort':level_id},{'axiom':{'isUnsafe':False,'levelParams':[],'name':name_id,'type':e2}}]
        p=CORPUS/'alias-positive'/f'{seed:03d}.ndjson'; p.write_text('\n'.join(json.dumps(x,separators=(',',':')) for x in rows)+'\n')
        # Same external Expr ID introduced twice for two different valid Expr objects.
        dup=[meta,{'in':name_id,'str':{'pre':0,'str':'foo'}},{'il':level_id,'succ':0},{'il':level_id+1,'succ':level_id},{'ie':e1,'sort':level_id},{'ie':e1,'sort':level_id+1},{'axiom':{'isUnsafe':False,'levelParams':[],'name':name_id,'type':e1}}]
        q=CORPUS/'duplicate-negative'/f'{seed:03d}.ndjson'; q.write_text('\n'.join(json.dumps(x,separators=(',',':')) for x in dup)+'\n')

def evaluate(label):
    exe=NANODA/'target/release/nanoda_bin'; cfg=NANODA/'config.json'
    def one(p):
        with p.open('rb') as f: return subprocess.run([str(exe),str(cfg)],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
    alias=[one(p) for p in sorted((CORPUS/'alias-positive').glob('*.ndjson'))]; dup=[one(p) for p in sorted((CORPUS/'duplicate-negative').glob('*.ndjson'))]
    row={'label':label,'alias_total':len(alias),'alias_accepted':sum(x==0 for x in alias),'duplicate_total':len(dup),'duplicate_rejected':sum(x!=0 for x in dup),'all_alias_accept':all(x==0 for x in alias),'all_duplicate_reject':all(x!=0 for x in dup)}
    (OUT/f'{label}.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n'); print(json.dumps(row,sort_keys=True),flush=True); return row

def normal_variant():
    v94.patch('TAGGED_SINGLE_STORE'); run(['cargo','build','--release','-q'],cwd=NANODA); return evaluate('SINGLE_ASSIGNMENT')

def no_single_assignment():
    v94.patch('NO_INJECTIVITY'); run(['cargo','build','--release','-q'],cwd=NANODA); return evaluate('NO_SINGLE_ASSIGNMENT')

def true_value_injectivity():
    v94.patch('TAGGED_SINGLE_STORE')
    p=NANODA/'src/parser.rs'; s=p.read_text()
    old='#[derive(Clone, Copy)]\nenum BackRefValue'
    if s.count(old)!=1: raise RuntimeError('BackRefValue derive anchor missing')
    s=s.replace(old,'#[derive(Clone, Copy, PartialEq, Eq)]\nenum BackRefValue',1)
    old2='''        if tagged {\n            if injective && self.tagged.insert((k,ext),v).is_some() { panic!("duplicate tagged back-reference {}",ext); }'''
    new2='''        if tagged {\n            if self.tagged.values().any(|old| *old == v) { panic!("true value-injectivity violation"); }\n            if injective && self.tagged.insert((k,ext),v).is_some() { panic!("duplicate tagged back-reference {}",ext); }'''
    if s.count(old2)!=1: raise RuntimeError('tagged bind anchor missing')
    s=s.replace(old2,new2,1); p.write_text(s)
    run(['cargo','build','--release','-q'],cwd=NANODA); return evaluate('TRUE_VALUE_INJECTIVITY')

def main():
    v94.setup(); make_corpus()
    normal=normal_variant(); noassign=no_single_assignment(); trueinj=true_value_injectivity()
    gates={'single_assignment_accepts_valid_aliasing':normal['all_alias_accept'],'single_assignment_rejects_duplicate_key':normal['all_duplicate_reject'],'removing_single_assignment_leaks_duplicate_key':not noassign['all_duplicate_reject'],'true_injectivity_is_too_strong':not trueinj['all_alias_accept']}
    result={'variants':{'SINGLE_ASSIGNMENT':normal,'NO_SINGLE_ASSIGNMENT':noassign,'TRUE_VALUE_INJECTIVITY':trueinj},'gates':gates,'law':'fresh typed external key per binding event; distinct external keys may alias one canonical internal object'}
    result['verdict']='PASS_SINGLE_ASSIGNMENT_NOT_INJECTIVITY_V95' if all(gates.values()) else 'MIXED_SINGLE_ASSIGNMENT_NOT_INJECTIVITY_V95'
    (OUT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True),flush=True)
    if result['verdict'].startswith('MIXED'): raise SystemExit(1)
if __name__=='__main__': main()
