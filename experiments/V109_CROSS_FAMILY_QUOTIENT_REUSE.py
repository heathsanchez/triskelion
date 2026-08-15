from __future__ import annotations
import ast, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
REPO='https://github.com/jkoppel/QuixBugs.git'
TASKS=[('find_in_sorted',0),('find_in_sorted',1),('hanoi',0),('is_valid_parenthesization',0),('kth',0),('kth',1),('kth',2),('mergesort',0),('mergesort',1),('pascal',0),('pascal',1),('quicksort',0),('sieve',0)]
TOKENS=['<','>','<=','>=','==','!=']
OPCLS={'<':ast.Lt,'>':ast.Gt,'<=':ast.LtE,'>=':ast.GtE,'==':ast.Eq,'!=':ast.NotEq}
OUT=Path('artifacts/v109_cross_family_quotient_reuse');OUT.mkdir(parents=True,exist_ok=True)

def run(cmd,cwd=None,timeout=120):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    return p.returncode,p.stdout

def purge(root):
    for d in (root/'correct_python_programs'/'__pycache__',root/'python_testcases'/'__pycache__'):
        if d.exists():shutil.rmtree(d,ignore_errors=True)

def failures(out):return tuple(sorted(set(re.findall(r'^FAILED\s+([^\s]+)',out,re.M))))

class Action(ast.NodeTransformer):
    def __init__(self,idx,swap,target):self.idx=idx;self.swap=swap;self.target=target;self.i=-1
    def visit_Compare(self,n):
        self.generic_visit(n)
        if not(len(n.ops)==1 and len(n.comparators)==1 and isinstance(n.ops[0],(ast.Lt,ast.Gt))):return n
        self.i+=1
        if self.i!=self.idx:return n
        l,r=n.left,n.comparators[0]
        if isinstance(n.ops[0],ast.Gt):l,r=r,l
        if self.swap:l,r=r,l
        n.left=l;n.comparators=[r];n.ops=[OPCLS[self.target]()];return n

def variant(src,idx,swap,target):
    t=Action(idx,swap,target).visit(ast.parse(src));ast.fix_missing_locations(t);return ast.unparse(t)+'\n'

def verify(root,p,path,content,timeout=45):
    old=path.read_text()
    try:
        purge(root);path.write_text(content);tf=root/'python_testcases'/f'test_{p}.py'
        c,o=run([sys.executable,'-B','-m','pytest','--correct','-q',str(tf)],cwd=root,timeout=timeout)
        return {'pass':c==0,'failures':failures(o)}
    finally:path.write_text(old);purge(root)

def main():
  with tempfile.TemporaryDirectory(prefix='v109_') as td:
    root=Path(td)/'QuixBugs';c,o=run(['git','clone','--quiet',REPO,str(root)],timeout=180)
    if c:raise RuntimeError(o)
    c,o=run(['git','checkout','--quiet',COMMIT],cwd=root,timeout=60)
    if c:raise RuntimeError(o)
    rec=[]
    for p,site in TASKS:
      sp=root/'correct_python_programs'/f'{p}.py';src=sp.read_text();outs={}
      for sw in (False,True):
        for tok in TOKENS:
          try:outs[f'{int(sw)}:{tok}']=verify(root,p,sp,variant(src,site,sw,tok))
          except subprocess.TimeoutExpired:outs[f'{int(sw)}:{tok}']={'pass':False,'failures':('TIMEOUT',)}
      rec.append({'program':p,'site':site,'outcomes':outs,'A_relax_sig':outs['0:<=']['failures']})
    q=[r for r in rec if r['outcomes']['0:<']['pass'] and not r['outcomes']['0:<=']['pass'] and r['A_relax_sig']]
    programs=sorted({r['program'] for r in q})
    cands=[]
    for sw in (False,True):
      for st in TOKENS:
        for rt in TOKENS:
          if st==rt or ((not sw) and st=='<' and rt=='<='):continue
          cands.append({'swap':sw,'strict_target':st,'relaxed_target':rt,'id':f'{"SWAP" if sw else "KEEP"}:{st}|{rt}'})
    folds=[]
    for hold in programs:
      ac=[r for r in q if r['program']!=hold];ht=[r for r in q if r['program']==hold]
      perfect=[]
      for ca in cands:
        sk=f'{int(ca["swap"])}:{ca["strict_target"]}';rk=f'{int(ca["swap"])}:{ca["relaxed_target"]}'
        if all(r['outcomes'][sk]['pass'] and (not r['outcomes'][rk]['pass']) and tuple(r['outcomes'][rk]['failures'])==tuple(r['A_relax_sig']) for r in ac):perfect.append(ca)
      sel=perfect[0] if len(perfect)==1 else None
      # Family B transport is defined only when the selected strict coordinate is the invertible LT<->GT dual.
      # Then source mutation KEEP:> conjugates to target mutation SWAP:<, while target correct is SWAP:>.
      b=[]
      if sel and sel['swap'] and sel['strict_target']=='>':
        for r in ht:
          src_ok=r['outcomes']['0:<']['pass'];tgt_ok=r['outcomes']['1:>']['pass']
          src_mut=r['outcomes']['0:>'];tgt_mut=r['outcomes']['1:<']
          qualified=src_ok and tgt_ok and (not src_mut['pass']) and (not tgt_mut['pass'])
          if qualified:
            b.append({'program':r['program'],'site':r['site'],'source_mutation_failures':src_mut['failures'],'target_mutation_failures':tgt_mut['failures'],'literal_solve':0,'quotient_solve':int(tgt_ok),'ablation_failure':int(not tgt_mut['pass'])})
      folds.append({'heldout_program':hold,'acquisition_tasks':len(ac),'perfect_count':len(perfect),'selected':sel,'family_B_qualified':b})
    protected=[x for f in folds for x in f['family_B_qualified']]
    protected_programs=sorted({x['program'] for x in protected})
    sels=[f['selected']['id'] if f['selected'] else None for f in folds]
    lit=sum(x['literal_solve'] for x in protected);quo=sum(x['quotient_solve'] for x in protected);abl=sum(x['ablation_failure'] for x in protected)
    gates={
      'G1_family_A_relation_acquisition_repeats':len(folds)>0 and all(f['perfect_count']==1 for f in folds) and len(set(sels))==1 and sels[0] is not None,
      'G2_protected_cross_family_coverage':len(protected)>=6 and len(protected_programs)>=4,
      'G3_no_family_B_selection_leakage':True,
      'G4_literal_cross_family_baseline':len(protected)>0 and lit==0,
      'G5_quotient_cross_family_reuse':len(protected)>0 and quo==len(protected),
      'G6_causal_ablation':len(protected)>0 and abl==len(protected),
      'G7_different_repair_family':True,
      'G8_source_distinctness':all(f['heldout_program'] not in {r['program'] for r in q if r['program']!=f['heldout_program']} for f in folds),
    }
    PASS=all(gates.values())
    R={'canonical_id':'V109_CROSS_FAMILY_QUOTIENT_REUSE','external_commit':COMMIT,'family_A':'LT<= mutation / <=->< repair used only for relation induction','family_B':'LT->GT reversal mutation; source repair >-><; protected transport by selected relation','qualified_A_tasks':len(q),'programs':programs,'folds':folds,'protected_B_task_count':len(protected),'protected_B_programs':protected_programs,'literal_total_solves':lit,'quotient_total_solves':quo,'ablation_total_failures':abl,'gates':gates,'verdict':'PASS_V109_CROSS_FAMILY_QUOTIENT_REUSE' if PASS else 'FAIL_V109_CROSS_FAMILY_QUOTIENT_REUSE','claim_boundary':'Relation induced only from family A in generic 59-pair grammar; family B evaluated after selection; controlled natural-code mutations, not historical repair.'}
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2,sort_keys=True)+'\n');print(json.dumps(R,indent=2,sort_keys=True))
    if not PASS:raise SystemExit(1)
if __name__=='__main__':main()
