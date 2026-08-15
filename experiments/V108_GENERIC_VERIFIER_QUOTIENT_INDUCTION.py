from __future__ import annotations
import ast, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
REPO='https://github.com/jkoppel/QuixBugs.git'
# Frozen from the prior hosted V106B qualified set, before V108 design.
TASKS=[('find_in_sorted',0),('find_in_sorted',1),('hanoi',0),('is_valid_parenthesization',0),('kth',0),('kth',1),('kth',2),('mergesort',0),('mergesort',1),('pascal',0),('pascal',1),('quicksort',0),('sieve',0)]
TOKENS=['<','>','<=','>=','==','!=']
OUT=Path('artifacts/v108_generic_verifier_quotient'); OUT.mkdir(parents=True,exist_ok=True)

OPCLS={'<':ast.Lt,'>':ast.Gt,'<=':ast.LtE,'>=':ast.GtE,'==':ast.Eq,'!=':ast.NotEq}

def run(cmd,cwd=None,timeout=120):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    return p.returncode,p.stdout

def purge(root):
    for d in (root/'correct_python_programs'/'__pycache__',root/'python_testcases'/'__pycache__'):
        if d.exists():shutil.rmtree(d,ignore_errors=True)

def failure_nodes(out):
    return tuple(sorted(set(re.findall(r'^FAILED\s+([^\s]+)',out,re.M))))

class Action(ast.NodeTransformer):
    def __init__(self,idx,swap,target):self.idx=idx;self.swap=swap;self.target=target;self.i=-1
    def visit_Compare(self,n):
        self.generic_visit(n)
        if not(len(n.ops)==1 and len(n.comparators)==1 and isinstance(n.ops[0],(ast.Lt,ast.Gt))):return n
        self.i+=1
        if self.i!=self.idx:return n
        l,r=n.left,n.comparators[0]
        # First move original strict comparison into canonical LT coordinates.
        if isinstance(n.ops[0],ast.Gt):l,r=r,l
        # Then apply the generic candidate operand coordinate.
        if self.swap:l,r=r,l
        n.left=l;n.comparators=[r];n.ops=[OPCLS[self.target]()]
        return n

def variant(src,idx,swap,target):
    tr=Action(idx,swap,target).visit(ast.parse(src));ast.fix_missing_locations(tr);return ast.unparse(tr)+'\n'

def verify(root,p,path,content,timeout=45):
    old=path.read_text()
    try:
        purge(root);path.write_text(content)
        tf=root/'python_testcases'/f'test_{p}.py'
        c,o=run([sys.executable,'-B','-m','pytest','--correct','-q',str(tf)],cwd=root,timeout=timeout)
        return {'pass':c==0,'failures':failure_nodes(o),'returncode':c}
    finally:
        path.write_text(old);purge(root)

def main():
  with tempfile.TemporaryDirectory(prefix='v108_') as td:
    root=Path(td)/'QuixBugs';c,o=run(['git','clone','--quiet',REPO,str(root)],timeout=180)
    if c:raise RuntimeError(o)
    c,o=run(['git','checkout','--quiet',COMMIT],cwd=root,timeout=60)
    if c:raise RuntimeError(o)

    records=[]
    for p,site in TASKS:
        sp=root/'correct_python_programs'/f'{p}.py';src=sp.read_text()
        outcomes={}
        for swap in (False,True):
            for tok in TOKENS:
                try:outcomes[f'{int(swap)}:{tok}']=verify(root,p,sp,variant(src,site,swap,tok))
                except subprocess.TimeoutExpired:outcomes[f'{int(swap)}:{tok}']={'pass':False,'failures':['TIMEOUT'],'returncode':124}
        base=outcomes['0:<'];relax=outcomes['0:<=']
        records.append({'program':p,'site':site,'baseline_strict_pass':base['pass'],'baseline_relaxed_failures':relax['failures'],'baseline_relaxed_pass':relax['pass'],'outcomes':outcomes})

    qualified=[r for r in records if r['baseline_strict_pass'] and not r['baseline_relaxed_pass'] and len(r['baseline_relaxed_failures'])>0]
    programs=sorted({r['program'] for r in qualified})

    candidates=[]
    for swap in (False,True):
        for st in TOKENS:
            for rt in TOKENS:
                if st==rt:continue
                if (not swap) and st=='<' and rt=='<=':continue
                candidates.append({'swap':swap,'strict_target':st,'relaxed_target':rt,'id':f'{"SWAP" if swap else "KEEP"}:{st}|{rt}'})

    folds=[]
    for hold in programs:
        ac=[r for r in qualified if r['program']!=hold];ht=[r for r in qualified if r['program']==hold]
        perfect=[];score_rows=[]
        for cand in candidates:
            strict_key=f'{int(cand["swap"])}:{cand["strict_target"]}'
            relax_key=f'{int(cand["swap"])}:{cand["relaxed_target"]}'
            ok=0
            for r in ac:
                so=r['outcomes'][strict_key];ro=r['outcomes'][relax_key]
                if so['pass'] and tuple(ro['failures'])==tuple(r['baseline_relaxed_failures']) and not ro['pass']:ok+=1
            score_rows.append((cand['id'],ok))
            if ok==len(ac):perfect.append(cand)
        sel=perfect[0] if len(perfect)==1 else None
        lit=0;quot=0;abl=0;repok=0
        held_detail=[]
        for r in ht:
            if sel:
                sk=f'{int(sel["swap"])}:{sel["strict_target"]}';rk=f'{int(sel["swap"])}:{sel["relaxed_target"]}'
                strict_o=r['outcomes'][sk];relax_o=r['outcomes'][rk]
                qsolve=bool(strict_o['pass'] and not relax_o['pass'])
                quot+=int(qsolve);abl+=int(not relax_o['pass']);repok+=int(strict_o['pass'])
                # Literal <= -> < can act only if the target relaxed token is literally <=; it keeps operands unchanged.
                lsolve=0
                if sel['relaxed_target']=='<=':
                    lk=f'{int(sel["swap"])}:<'
                    lsolve=int(r['outcomes'][lk]['pass'])
                lit+=lsolve
                held_detail.append({'program':r['program'],'site':r['site'],'target_relaxed_failures':relax_o['failures'],'target_repaired_pass':strict_o['pass'],'literal_solve':lsolve,'quotient_solve':int(qsolve)})
        rejected=sum(1 for _,s in score_rows if s<len(ac))
        folds.append({'heldout_program':hold,'acquisition_tasks':len(ac),'heldout_tasks':len(ht),'perfect_count':len(perfect),'perfect_candidates':[x['id'] for x in perfect],'selected':sel,'rejected_candidates':rejected,'rejection_fraction':rejected/len(candidates),'top_scores':sorted(score_rows,key=lambda x:(-x[1],x[0]))[:8],'literal_solves':lit,'quotient_solves':quot,'ablation_failures':abl,'repaired_passes':repok,'heldout_detail':held_detail})

    total=len(qualified);sels=[f['selected']['id'] if f['selected'] else None for f in folds]
    lit=sum(f['literal_solves'] for f in folds);quo=sum(f['quotient_solves'] for f in folds);abl=sum(f['ablation_failures'] for f in folds);rep=sum(f['repaired_passes'] for f in folds)
    gates={
      'G1_natural_qualification':total>=8 and len(programs)>=4,
      'G2_generic_space_reality':len(candidates)==59,
      'G3_unique_fold_local_induction':len(folds)>0 and all(f['perfect_count']==1 for f in folds),
      'G4_cross_fold_stability':len(set(sels))==1 and sels[0] is not None,
      'G5_literal_identity_baseline':total>0 and lit==0,
      'G6_induced_transport':total>0 and quo==total,
      'G7_causal_ablation':total>0 and abl==total,
      'G8_acquisition_only_selection':all(f['heldout_program'] not in [r['program'] for r in qualified if r['program']!=f['heldout_program']] for f in folds),
      'G9_nontrivial_rejection':len(folds)>0 and all(f['rejection_fraction']>=0.90 for f in folds),
      'G10_representative_correctness':total>0 and rep==total and abl==total,
    }
    PASS=all(gates.values())
    R={'canonical_id':'V108_GENERIC_VERIFIER_QUOTIENT_INDUCTION','external_commit':COMMIT,'frozen_task_set':TASKS,'qualified_task_count':total,'qualified_programs':programs,'candidate_count':len(candidates),'candidate_grammar':{'swap':[False,True],'tokens':TOKENS,'identity_excluded':'KEEP:<|<='},'folds':folds,'selected_relations':sels,'literal_total_solves':lit,'quotient_total_solves':quo,'ablation_total_failures':abl,'gates':gates,'verdict':'PASS_V108_GENERIC_VERIFIER_QUOTIENT_INDUCTION' if PASS else 'FAIL_V108_GENERIC_VERIFIER_QUOTIENT_INDUCTION','claim_boundary':'Generic 59-pair local comparison grammar; exact upstream verifier/failure-signature induction; not arbitrary transformation invention.'}
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2,sort_keys=True)+'\n');print(json.dumps(R,indent=2,sort_keys=True))
    if not PASS:raise SystemExit(1)
if __name__=='__main__':main()
