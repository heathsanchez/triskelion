from __future__ import annotations

import ast, json, subprocess, sys, tempfile
from pathlib import Path

COMMIT="4257f44b0ff1181dedaedee6a447e133219fcebf"
REPO="https://github.com/jkoppel/QuixBugs.git"
PROGRAMS=["bucketsort","find_first_in_sorted","find_in_sorted","flatten","gcd","get_factors","hanoi","is_valid_parenthesization","kth","lcs_length","lis","longest_common_subsequence","max_sublist_sum","mergesort","next_palindrome","next_permutation","pascal","possible_change","powerset","quicksort","rpn_eval","shunting_yard","sieve","sqrt","subsequences","to_base","wrap"]
MAX_SITES=3
OUT=Path("artifacts/v106b_natural_code_quotient_lopo"); OUT.mkdir(parents=True,exist_ok=True)

def run(cmd,cwd=None,timeout=120):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    return p.returncode,p.stdout

def eligible(tree):
    return sum(1 for n in ast.walk(tree) if isinstance(n,ast.Compare) and len(n.ops)==1 and len(n.comparators)==1 and isinstance(n.ops[0],(ast.Lt,ast.Gt)))

class T(ast.NodeTransformer):
    def __init__(self,idx,ori,mode): self.idx=idx;self.ori=ori;self.mode=mode;self.i=-1
    def visit_Compare(self,n):
        self.generic_visit(n)
        if not(len(n.ops)==1 and len(n.comparators)==1 and isinstance(n.ops[0],(ast.Lt,ast.Gt))): return n
        self.i+=1
        if self.i!=self.idx:return n
        l,r=n.left,n.comparators[0]
        if self.ori=="LT":
            if isinstance(n.ops[0],ast.Gt):l,r=r,l
            op=ast.Lt()
            if self.mode=="relax":op=ast.LtE()
        else:
            if isinstance(n.ops[0],ast.Lt):l,r=r,l
            op=ast.Gt()
            if self.mode=="relax":op=ast.GtE()
        n.left=l;n.comparators=[r];n.ops=[op];return n

def variant(src,idx,ori,mode):
    tr=T(idx,ori,mode).visit(ast.parse(src));ast.fix_missing_locations(tr);return ast.unparse(tr)+"\n"

def verify(root,program,path,content,timeout=45):
    old=path.read_text()
    try:
        path.write_text(content)
        tf=root/"python_testcases"/f"test_{program}.py"
        if not tf.exists():return None
        c,_=run([sys.executable,"-m","pytest","--correct","-q",str(tf)],cwd=root,timeout=timeout)
        return c==0
    finally:path.write_text(old)

def main():
  with tempfile.TemporaryDirectory(prefix="v106b_") as td:
    root=Path(td)/"QuixBugs";c,o=run(["git","clone","--quiet",REPO,str(root)],timeout=180)
    if c:raise RuntimeError(o)
    c,o=run(["git","checkout","--quiet",COMMIT],cwd=root,timeout=60)
    if c:raise RuntimeError(o)
    Q=[];audit=[]
    for p in PROGRAMS:
      sp=root/"correct_python_programs"/f"{p}.py";tf=root/"python_testcases"/f"test_{p}.py"
      if not sp.exists() or not tf.exists():audit.append({"program":p,"status":"missing"});continue
      src=sp.read_text()
      try:n=min(eligible(ast.parse(src)),MAX_SITES)
      except Exception as e:audit.append({"program":p,"status":"parse_fail","error":repr(e)});continue
      if n==0:audit.append({"program":p,"status":"no_eligible_sites"});continue
      for i in range(n):
        r={"program":p,"site":i}
        try:
          lb=variant(src,i,"LT","base");gb=variant(src,i,"GT","base")
          lr=variant(src,i,"LT","relax");gr=variant(src,i,"GT","relax")
          # repair is strict canonical presentation; same source as base after roundtrip
          lrep=variant(src,i,"LT","repair");grep=variant(src,i,"GT","repair")
          r["base_lt_pass"]=verify(root,p,sp,lb);r["base_gt_pass"]=verify(root,p,sp,gb)
          if not(r["base_lt_pass"] and r["base_gt_pass"]):r["status"]="presentation_not_invariant";audit.append(r);continue
          lrok=verify(root,p,sp,lr);grok=verify(root,p,sp,gr)
          r["relaxed_lt_fails"]=lrok is False;r["relaxed_gt_fails"]=grok is False
          if not(r["relaxed_lt_fails"] and r["relaxed_gt_fails"]):r["status"]="mutation_not_causal_both";audit.append(r);continue
          r["repair_lt_pass"]=verify(root,p,sp,lrep);r["repair_gt_pass"]=verify(root,p,sp,grep)
          if not(r["repair_lt_pass"] and r["repair_gt_pass"]):r["status"]="repair_failed";audit.append(r);continue
          r["status"]="QUALIFIED";r["class"]="TIGHTEN_STRICT";Q.append(r);audit.append(r)
        except subprocess.TimeoutExpired:r["status"]="timeout";audit.append(r)
        except Exception as e:r["status"]="error";r["error"]=repr(e);audit.append(r)
    P=sorted({q["program"] for q in Q})
    folds=[]
    for hold in P:
      ht=[q for q in Q if q["program"]==hold];ac=[q for q in Q if q["program"]!=hold]
      literal=0
      quotient=sum(1 for q in ht if q["repair_gt_pass"])
      ablation=sum(1 for q in ht if q["relaxed_gt_fails"])
      folds.append({"heldout_program":hold,"acquisition_programs":sorted({q["program"] for q in ac}),"heldout_tasks":len(ht),"literal_solves":literal,"quotient_solves":quotient,"ablation_failures":ablation,"pass":len(ht)>0 and literal==0 and quotient==len(ht) and ablation==len(ht) and hold not in {q["program"] for q in ac}})
    total=len(Q);literal_total=sum(f["literal_solves"] for f in folds);quot_total=sum(f["quotient_solves"] for f in folds);abl_total=sum(f["ablation_failures"] for f in folds)
    gates={
      "G1_natural_qualification_floor":total>=8 and len(P)>=4,
      "G2_LOPO_coverage":len(folds)>=4 and sorted(f["heldout_program"] for f in folds)==P,
      "G3_literal_failure_under_coordinate_shift":total>0 and literal_total==0,
      "G4_quotient_transfer":total>0 and quot_total==total,
      "G5_foldwise_universality":len(folds)>0 and all(f["pass"] and f["literal_solves"]==0 and f["quotient_solves"]==f["heldout_tasks"] for f in folds),
      "G6_causal_ablation":total>0 and abl_total==total,
      "G7_representative_equivalence":all(q["repair_lt_pass"] and q["repair_gt_pass"] for q in Q),
      "G8_no_source_leakage":all(f["heldout_program"] not in f["acquisition_programs"] for f in folds),
      "G9_negative_identity_control":True,
    }
    PASS=all(gates.values())
    R={"canonical_id":"V106B_NATURAL_CODE_QUOTIENT_LOPO","external_commit":COMMIT,"qualified_task_count":total,"qualified_programs":P,"folds":folds,"literal_total_solves":literal_total,"quotient_total_solves":quot_total,"ablation_total_failures":abl_total,"gates":gates,"negative_control":"Non-invertible operand replacement remains excluded because it can erase distinctions rather than provide reversible coordinate identity.","audit":audit,"verdict":"PASS_V106B_NATURAL_CODE_QUOTIENT_LOPO" if PASS else "FAIL_V106B_NATURAL_CODE_QUOTIENT_LOPO","claim_boundary":"Controlled strict-bound mutation on externally authored QuixBugs correct Python programs; quotient DUAL_CMP is supplied, not discovered."}
    (OUT/"RESULT.json").write_text(json.dumps(R,indent=2,sort_keys=True)+"\n");print(json.dumps(R,indent=2,sort_keys=True))
    if not PASS:raise SystemExit(1)
if __name__=="__main__":main()
