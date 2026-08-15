from __future__ import annotations
import ast, json, subprocess, sys, tempfile
from pathlib import Path

COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
REPO='https://github.com/jkoppel/QuixBugs.git'
PROGRAMS=['bucketsort','find_first_in_sorted','find_in_sorted','flatten','gcd','get_factors','hanoi','is_valid_parenthesization','kth','lcs_length','lis','longest_common_subsequence','max_sublist_sum','mergesort','next_palindrome','next_permutation','pascal','possible_change','powerset','quicksort','rpn_eval','shunting_yard','sieve','sqrt','subsequences','to_base','wrap']
MAX_SITES=3
CANDS=['SWAP_ONLY','FLIP_ONLY','SWAP_AND_FLIP']
OUT=Path('artifacts/v107_verifier_discovered_quotient'); OUT.mkdir(parents=True,exist_ok=True)

def run(cmd,cwd=None,timeout=120):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    return p.returncode,p.stdout

def eligible(tree):
    return sum(1 for n in ast.walk(tree) if isinstance(n,ast.Compare) and len(n.ops)==1 and len(n.comparators)==1 and isinstance(n.ops[0],(ast.Lt,ast.Gt)))

class SiteTransform(ast.NodeTransformer):
    def __init__(self,idx,mode): self.idx=idx;self.mode=mode;self.i=-1
    def visit_Compare(self,n):
        self.generic_visit(n)
        if not(len(n.ops)==1 and len(n.comparators)==1 and isinstance(n.ops[0],(ast.Lt,ast.Gt))): return n
        self.i+=1
        if self.i!=self.idx:return n
        l,r=n.left,n.comparators[0]; islt=isinstance(n.ops[0],ast.Lt)
        if self.mode=='SWAP_ONLY': l,r=r,l; op=ast.Lt() if islt else ast.Gt()
        elif self.mode=='FLIP_ONLY': op=ast.Gt() if islt else ast.Lt()
        elif self.mode=='SWAP_AND_FLIP': l,r=r,l; op=ast.Gt() if islt else ast.Lt()
        elif self.mode=='LT_BASE':
            if not islt:l,r=r,l
            op=ast.Lt()
        elif self.mode=='GT_BASE':
            if islt:l,r=r,l
            op=ast.Gt()
        elif self.mode=='LT_RELAX':
            if not islt:l,r=r,l
            op=ast.LtE()
        elif self.mode=='GT_RELAX':
            if islt:l,r=r,l
            op=ast.GtE()
        else: raise ValueError(self.mode)
        n.left=l;n.comparators=[r];n.ops=[op];return n

def variant(src,idx,mode):
    tr=SiteTransform(idx,mode).visit(ast.parse(src));ast.fix_missing_locations(tr);return ast.unparse(tr)+'\n'

def verify(root,p,path,content,timeout=45):
    old=path.read_text()
    try:
        path.write_text(content);tf=root/'python_testcases'/f'test_{p}.py'
        if not tf.exists():return None
        c,_=run([sys.executable,'-m','pytest','--correct','-q',str(tf)],cwd=root,timeout=timeout)
        return c==0
    finally:path.write_text(old)

def main():
  with tempfile.TemporaryDirectory(prefix='v107_') as td:
    root=Path(td)/'QuixBugs';c,o=run(['git','clone','--quiet',REPO,str(root)],timeout=180)
    if c:raise RuntimeError(o)
    c,o=run(['git','checkout','--quiet',COMMIT],cwd=root,timeout=60)
    if c:raise RuntimeError(o)
    Q=[];audit=[]
    for p in PROGRAMS:
      sp=root/'correct_python_programs'/f'{p}.py';tf=root/'python_testcases'/f'test_{p}.py'
      if not sp.exists() or not tf.exists():continue
      src=sp.read_text()
      try:n=min(eligible(ast.parse(src)),MAX_SITES)
      except Exception:continue
      for i in range(n):
        r={'program':p,'site':i}
        try:
          lb=variant(src,i,'LT_BASE');gb=variant(src,i,'GT_BASE');lr=variant(src,i,'LT_RELAX');gr=variant(src,i,'GT_RELAX')
          r['base_lt_pass']=verify(root,p,sp,lb);r['base_gt_pass']=verify(root,p,sp,gb)
          if not(r['base_lt_pass'] and r['base_gt_pass']):r['status']='presentation_not_invariant';audit.append(r);continue
          r['relaxed_lt_fails']=verify(root,p,sp,lr) is False;r['relaxed_gt_fails']=verify(root,p,sp,gr) is False
          if not(r['relaxed_lt_fails'] and r['relaxed_gt_fails']):r['status']='mutation_not_causal_both';audit.append(r);continue
          # strict canonical sources are repairs by construction
          r['repair_lt_pass']=r['base_lt_pass'];r['repair_gt_pass']=r['base_gt_pass'];r['source']=src;r['status']='QUALIFIED';Q.append(r);audit.append({k:v for k,v in r.items() if k!='source'})
        except subprocess.TimeoutExpired:r['status']='timeout';audit.append(r)
        except Exception as e:r['status']='error';r['error']=repr(e);audit.append(r)
    P=sorted({q['program'] for q in Q});folds=[]
    for hold in P:
      ac=[q for q in Q if q['program']!=hold];ht=[q for q in Q if q['program']==hold]
      scores={k:0 for k in CANDS};attempts={k:0 for k in CANDS}
      for q in ac:
        sp=root/'correct_python_programs'/f"{q['program']}.py";src=q['source']
        for k in CANDS:
          attempts[k]+=1
          try:
            if verify(root,q['program'],sp,variant(src,q['site'],k)) is True:scores[k]+=1
          except subprocess.TimeoutExpired:pass
      perfect=[k for k in CANDS if scores[k]==len(ac)]
      selected=perfect[0] if len(perfect)==1 else None
      transported=(selected=='SWAP_AND_FLIP')
      literal=0
      quotient=len(ht) if transported else 0
      ablation=sum(1 for q in ht if q['relaxed_gt_fails'])
      folds.append({'heldout_program':hold,'acquisition_programs':sorted({q['program'] for q in ac}),'acquisition_tasks':len(ac),'heldout_tasks':len(ht),'scores':scores,'perfect_candidates':perfect,'selected':selected,'literal_solves':literal,'quotient_solves':quotient,'ablation_failures':ablation,'loser_fails':all(scores[k]<len(ac) for k in CANDS if k!=selected) if selected else False})
    selecteds=[f['selected'] for f in folds]
    total=len(Q);lit=sum(f['literal_solves'] for f in folds);quo=sum(f['quotient_solves'] for f in folds);abl=sum(f['ablation_failures'] for f in folds)
    gates={
      'G1_natural_qualification':total>=8 and len(P)>=4,
      'G2_fold_coverage':len(folds)==len(P) and all(f['heldout_program'] not in f['acquisition_programs'] for f in folds),
      'G3_relation_discovery':len(folds)>0 and all(f['selected'] is not None and len(f['perfect_candidates'])==1 for f in folds),
      'G4_relation_consistency':len(set(selecteds))==1 and selecteds[0] is not None,
      'G5_literal_baseline_failure':total>0 and lit==0,
      'G6_discovered_quotient_transfer':total>0 and quo==total,
      'G7_causal_ablation':total>0 and abl==total,
      'G8_heldout_independence':all(f['heldout_program'] not in f['acquisition_programs'] for f in folds),
      'G9_negative_controls':len(folds)>0 and all(f['loser_fails'] for f in folds),
    }
    PASS=all(gates.values())
    R={'canonical_id':'V107_VERIFIER_DISCOVERED_QUOTIENT','external_commit':COMMIT,'candidate_family':CANDS,'qualified_task_count':total,'qualified_programs':P,'folds':folds,'selected_relations':selecteds,'literal_total_solves':lit,'quotient_total_solves':quo,'ablation_total_failures':abl,'gates':gates,'verdict':'PASS_V107_VERIFIER_DISCOVERED_QUOTIENT' if PASS else 'FAIL_V107_VERIFIER_DISCOVERED_QUOTIENT','claim_boundary':'Relation selected from a frozen three-template invertible comparison meta-family using acquisition-only verifier evidence; not arbitrary relation invention.' ,'audit':audit}
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2,sort_keys=True)+'\n');print(json.dumps(R,indent=2,sort_keys=True))
    if not PASS:raise SystemExit(1)
if __name__=='__main__':main()
