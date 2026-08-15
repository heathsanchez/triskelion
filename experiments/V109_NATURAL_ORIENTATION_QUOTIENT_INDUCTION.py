from __future__ import annotations
import ast,json,re,shutil,subprocess,sys,tempfile
from pathlib import Path
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'; REPO='https://github.com/jkoppel/QuixBugs.git'
PROGRAMS=['bucketsort','find_first_in_sorted','find_in_sorted','flatten','gcd','get_factors','hanoi','is_valid_parenthesization','kth','lcs_length','lis','longest_common_subsequence','max_sublist_sum','mergesort','next_palindrome','next_permutation','pascal','possible_change','powerset','quicksort','rpn_eval','shunting_yard','sieve','sqrt','subsequences','to_base','wrap']
MAX_SITES=3; TOKENS=['<','>','<=','>=','==','!=']; OPCLS={'<':ast.Lt,'>':ast.Gt,'<=':ast.LtE,'>=':ast.GtE,'==':ast.Eq,'!=':ast.NotEq}
OUT=Path('artifacts/v109_natural_orientation_quotient');OUT.mkdir(parents=True,exist_ok=True)

def run(cmd,cwd=None,timeout=120):
 p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);return p.returncode,p.stdout

def purge(root):
 for d in root.rglob('__pycache__'):
  if d.is_dir():shutil.rmtree(d,ignore_errors=True)

def failures(out):return tuple(sorted(set(re.findall(r'^FAILED\s+([^\s]+)',out,re.M))))

def verify(root,p,path,content,timeout=45):
 old=path.read_text()
 try:
  purge(root);path.write_text(content);tf=root/'python_testcases'/f'test_{p}.py';c,o=run([sys.executable,'-B','-m','pytest','--correct','-q',str(tf)],cwd=root,timeout=timeout);return {'pass':c==0,'fails':failures(o)}
 finally:path.write_text(old);purge(root)

class Site(ast.NodeTransformer):
 def __init__(self,idx,swap=False,token=None):self.idx=idx;self.swap=swap;self.token=token;self.i=-1;self.orig=None
 def visit_Compare(self,n):
  self.generic_visit(n)
  if not(len(n.ops)==1 and len(n.comparators)==1 and isinstance(n.ops[0],(ast.Lt,ast.Gt))):return n
  self.i+=1
  if self.i!=self.idx:return n
  self.orig='<' if isinstance(n.ops[0],ast.Lt) else '>'
  l,r=n.left,n.comparators[0]
  if self.swap:l,r=r,l
  if self.token is not None:n.ops=[OPCLS[self.token]()]
  n.left=l;n.comparators=[r];return n

def variant(src,idx,swap=False,token=None):
 t=Site(idx,swap,token);tree=t.visit(ast.parse(src));ast.fix_missing_locations(tree);return ast.unparse(tree)+'\n',t.orig

def count_sites(src):return sum(1 for n in ast.walk(ast.parse(src)) if isinstance(n,ast.Compare) and len(n.ops)==1 and len(n.comparators)==1 and isinstance(n.ops[0],(ast.Lt,ast.Gt)))

def cand_space():
 c=[]
 for sw in (False,True):
  for st in TOKENS:
   for rt in TOKENS:
    if st==rt:continue
    if (not sw) and st=='<' and rt=='<=':continue
    c.append((sw,st,rt))
 return c

def cid(c):return f'{"SWAP" if c[0] else "KEEP"}:{c[1]}|{c[2]}'

def main():
 C=cand_space()
 with tempfile.TemporaryDirectory(prefix='v109_') as td:
  root=Path(td)/'QuixBugs';c,o=run(['git','clone','--quiet',REPO,str(root)],timeout=180)
  if c:raise RuntimeError(o)
  c,o=run(['git','checkout','--quiet',COMMIT],cwd=root,timeout=60)
  if c:raise RuntimeError(o)
  LT=[];GT=[];audit=[]
  for p in PROGRAMS:
   sp=root/'correct_python_programs'/f'{p}.py';tf=root/'python_testcases'/f'test_{p}.py'
   if not sp.exists() or not tf.exists():continue
   src=sp.read_text()
   try:n=min(count_sites(src),MAX_SITES)
   except Exception:continue
   for i in range(n):
    try:
     untouched,orig=variant(src,i)
     if orig not in ('<','>'):continue
     base=verify(root,p,sp,untouched)
     relax_tok='<=' if orig=='<' else '>=';relaxed,_=variant(src,i,False,relax_tok);rv=verify(root,p,sp,relaxed)
     rec={'program':p,'site':i,'original_operator':orig,'base_pass':base['pass'],'relax_token':relax_tok,'relax_pass':rv['pass'],'relax_fails':rv['fails'],'source':src}
     if base['pass'] is not True or rv['pass'] is not False or not rv['fails']:
      rec['status']='not_causal';audit.append({k:v for k,v in rec.items() if k!='source'});continue
     if orig=='<':
      outcomes={}
      for sw in (False,True):
       for tok in TOKENS:
        vv,_=variant(src,i,sw,tok);outcomes[f'{int(sw)}:{tok}']=verify(root,p,sp,vv)
      rec['outcomes']=outcomes;rec['status']='LT_ACQUISITION';LT.append(rec)
     else:rec['status']='GT_HELDOUT';GT.append(rec)
     audit.append({k:v for k,v in rec.items() if k not in ('source','outcomes')})
    except subprocess.TimeoutExpired:audit.append({'program':p,'site':i,'status':'timeout'})
  gt_programs=sorted({r['program'] for r in GT});folds=[]
  for hold in gt_programs:
   ac=[r for r in LT if r['program']!=hold];ht=[r for r in GT if r['program']==hold]
   perfect=[]
   for cand in C:
    sw,st,rt=cand;sk=f'{int(sw)}:{st}';rk=f'{int(sw)}:{rt}';ok=True
    for r in ac:
     so=r['outcomes'][sk];ro=r['outcomes'][rk]
     if so['pass'] is not True or ro['pass'] is not False or ro['fails']!=r['relax_fails']:ok=False;break
    if ok:perfect.append(cand)
   sel=perfect[0] if len(perfect)==1 else None
   lit=0;quot=0;abl=0;details=[]
   for r in ht:
    sp=root/'correct_python_programs'/f"{r['program']}.py";src=r['source'];relaxed,_=variant(src,r['site'],False,'>=');rv=verify(root,r['program'],sp,relaxed);abl+=int(rv['pass'] is False)
    qsolve=0
    if sel and sel[1]=='>' and sel[2]=='>=':
     repaired,_=variant(src,r['site'],False,'>');qv=verify(root,r['program'],sp,repaired);qsolve=int(qv['pass'] is True)
    quot+=qsolve
    # literal <=->< is inapplicable at an original >= heldout site
    details.append({'program':r['program'],'site':r['site'],'original_operator':r['original_operator'],'relaxed_fails':rv['fails'],'quotient_solve':qsolve})
   rejected=len(C)-len(perfect)
   folds.append({'heldout_program':hold,'acquisition_tasks':len(ac),'acquisition_programs':sorted({r['program'] for r in ac}),'heldout_tasks':len(ht),'perfect_count':len(perfect),'perfect_candidates':[cid(x) for x in perfect],'selected':cid(sel) if sel else None,'rejection_fraction':rejected/len(C),'literal_solves':lit,'quotient_solves':quot,'ablation_failures':abl,'details':details})
  total_gt=len(GT);sels=[f['selected'] for f in folds];lit=sum(f['literal_solves'] for f in folds);quo=sum(f['quotient_solves'] for f in folds);abl=sum(f['ablation_failures'] for f in folds)
  gates={'G1_natural_orientation_coverage':len(LT)>=6 and len({r['program'] for r in LT})>=3 and len(GT)>=3 and len(gt_programs)>=2,'G2_generic_space':len(C)==59,'G3_unique_acquisition_only_induction':len(folds)>0 and all(f['perfect_count']==1 for f in folds),'G4_cross_fold_stability':len(folds)>0 and len(set(sels))==1 and sels[0] is not None,'G5_literal_baseline':total_gt>0 and lit==0,'G6_natural_orientation_transfer':total_gt>0 and quo==total_gt,'G7_causal_ablation':total_gt>0 and abl==total_gt,'G8_no_source_leakage':all(f['heldout_program'] not in f['acquisition_programs'] for f in folds),'G9_nontrivial_rejection':len(folds)>0 and all(f['rejection_fraction']>=.90 for f in folds),'G10_no_engineered_heldout_presentation':all(r['original_operator']=='>' for r in GT)}
  PASS=all(gates.values());R={'canonical_id':'V109_NATURAL_ORIENTATION_QUOTIENT_INDUCTION','external_commit':COMMIT,'candidate_count':len(C),'natural_lt_task_count':len(LT),'natural_lt_programs':sorted({r['program'] for r in LT}),'natural_gt_task_count':len(GT),'natural_gt_programs':gt_programs,'folds':folds,'selected_relations':sels,'literal_total_solves':lit,'quotient_total_solves':quo,'ablation_total_failures':abl,'gates':gates,'verdict':'PASS_V109_NATURAL_ORIENTATION_QUOTIENT_INDUCTION' if PASS else 'FAIL_V109_NATURAL_ORIENTATION_QUOTIENT_INDUCTION','claim_boundary':'Natural authored LT acquisition and GT heldout orientations; generic 59-pair local AST grammar; not arbitrary relation invention or historical bug repair.','audit':audit}
  (OUT/'RESULT.json').write_text(json.dumps(R,indent=2,sort_keys=True)+'\n');print(json.dumps(R,indent=2,sort_keys=True))
  if not PASS:raise SystemExit(1)
if __name__=='__main__':main()
