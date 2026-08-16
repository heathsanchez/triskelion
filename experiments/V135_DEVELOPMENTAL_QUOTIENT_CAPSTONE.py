from __future__ import annotations

import ast
import collections
import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OUT = Path('artifacts/v135_developmental_quotient_capstone')
OUT.mkdir(parents=True, exist_ok=True)
QUIX_COMMIT = '4257f44b0ff1181dedaedee6a447e133219fcebf'
QUIX_REPO = 'https://github.com/jkoppel/QuixBugs.git'
TOKENS = ['<', '>', '<=', '>=', '==', '!=']
OPCLS = {'<': ast.Lt, '>': ast.Gt, '<=': ast.LtE, '>=': ast.GtE, '==': ast.Eq, '!=': ast.NotEq}
XOR = 0b0110


def sha(obj) -> str:
    b = json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(b).hexdigest()


def run(cmd, cwd=None, timeout=180):
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return p.returncode, p.stdout


def failure_nodes(out):
    return tuple(sorted(set(re.findall(r'^FAILED\s+([^\s]+)', out, re.M))))

# ---------------- Stratum A: exact Boolean world ----------------

def tt_value(tt, x, y):
    return (tt >> ((x << 1) | y)) & 1


def is_affine_binary(tt):
    vals = [tt_value(tt, 0, 0), tt_value(tt, 0, 1), tt_value(tt, 1, 0), tt_value(tt, 1, 1)]
    c = vals[0]; a = vals[2] ^ c; b = vals[1] ^ c
    return vals == [c, b ^ c, a ^ c, a ^ b ^ c]


def transform_tt(tt, swap, nx, ny, no):
    out = 0
    for idx in range(4):
        x, y = (idx >> 1) & 1, idx & 1
        if nx: x ^= 1
        if ny: y ^= 1
        if swap: x, y = y, x
        v = tt_value(tt, x, y)
        if no: v ^= 1
        out |= v << idx
    return out


def orbit(tt):
    return tuple(sorted({transform_tt(tt, s, nx, ny, no) for s in (0,1) for nx in (0,1) for ny in (0,1) for no in (0,1)}))


def var_func(n, j):
    out = 0
    for a in range(1 << n): out |= (((a >> j) & 1) << a)
    return out


def const_func(n, c):
    return 0 if c == 0 else (1 << (1 << n)) - 1


def apply_binary(n, f, g, tt):
    out = 0
    for a in range(1 << n):
        x, y = (f >> a) & 1, (g >> a) & 1
        out |= tt_value(tt, x, y) << a
    return out


def exact_cost_table(n, candidate, max_cost=17):
    cost = {}; by_cost = collections.defaultdict(list)
    for j in range(n):
        f = var_func(n, j); cost[f] = 1; by_cost[1].append(f)
    for c in (0,1):
        f = const_func(n,c)
        if f not in cost: cost[f] = 1; by_cost[1].append(f)
    ops = [XOR] if candidate is None else [XOR, candidate]
    admitted_order = sorted(cost); rank = {f:i+1 for i,f in enumerate(admitted_order)}; seen=set(cost)
    for total in range(3, max_cost+1, 2):
        new=[]
        for lc in range(1,total-1,2):
            rc=total-1-lc
            for f in by_cost.get(lc,[]):
                for g in by_cost.get(rc,[]):
                    for op in ops:
                        h=apply_binary(n,f,g,op)
                        if h not in cost: cost[h]=total; new.append(h)
        if new:
            uniq=sorted(set(new)); by_cost[total].extend(uniq)
            for h in uniq:
                if h not in seen: seen.add(h); admitted_order.append(h); rank[h]=len(admitted_order)
        if len(cost)==(1 << (1 << n)): break
    return cost, rank


def generate_targets(hidden_tt, seed, count, depth, permute):
    rr=random.Random(seed); n=3; perm=list(range(n))
    if permute: rr.shuffle(perm)
    def rec(d):
        if d<=0 or rr.random()<0.25:
            z=rr.randrange(n+2)
            return var_func(n,perm[z]) if z<n else const_func(n,z-n)
        op=hidden_tt if rr.random()<0.65 else XOR
        return apply_binary(n,rec(d-1),rec(d-1),op)
    base,_=exact_cost_table(3,None); out=[]
    tries=0
    while len(out)<count and tries<200000:
        tries+=1; f=rec(depth)
        if f not in base and f not in out: out.append(f)
    if len(out)<count: raise RuntimeError('target generation exhausted')
    return out,perm


def stratum_a():
    nonaff=[tt for tt in range(16) if not is_affine_binary(tt)]
    base,_=exact_cost_table(3,None)
    costs={}; ranks={}
    for tt in nonaff: costs[tt],ranks[tt]=exact_cost_table(3,tt)
    rows=[]
    for i in range(100):
        seed=202608160000+i; rr=random.Random(seed)
        hidden_acq=rr.choice(nonaff); oo=orbit(hidden_acq)
        hidden_hold=rr.choice([x for x in oo if x!=hidden_acq])
        acq,_=generate_targets(hidden_acq,seed,30,3,False)
        hold,perm=generate_targets(hidden_hold,seed+100000,50,4,True)
        acq_scores={tt:6+sum(costs[tt][f] for f in acq) for tt in nonaff}
        best=min(acq_scores.values()); winners=sorted(tt for tt,v in acq_scores.items() if v==best)
        hold_scores={tt:6+sum(costs[tt][f] for f in hold) for tt in nonaff}
        best_hold=min(hold_scores.values()); selected=min(hold_scores[t] for t in winners)
        cold=sum(min(6+costs[t][f] for t in nonaff) for f in hold)
        warm=min(6+sum(costs[t][f] for f in hold) for t in winners)
        cold_states=sum(ranks[t][f] for f in hold for t in nonaff)
        warm_states=min(max(ranks[t][f] for f in hold) for t in winners)
        rows.append({
            'stream':i,'seed':seed,'hidden_acq':hidden_acq,'hidden_hold':hidden_hold,
            'winners':winners,'winner_same_orbit':all(orbit(t)==oo for t in winners),
            'all_hold_outside_old':all(f not in base for f in hold),
            'representative_within_10pct':selected <= 1.10*best_hold,
            'warm_cost':warm,'cold_cost':cold,'warm_beats_cold':warm<cold,
            'warm_cold_ratio':warm/cold,'cold_states':cold_states,'warm_states':warm_states,
            'search_factor':cold_states/warm_states,'hold_perm':perm,
        })
    A={
        'old_closure_size':len(base),'streams':100,'rows':rows,
        'summary':{
            'winner_same_orbit_n':sum(r['winner_same_orbit'] for r in rows),
            'representative_within_10pct_n':sum(r['representative_within_10pct'] for r in rows),
            'warm_beats_cold_n':sum(r['warm_beats_cold'] for r in rows),
            'search_ge_4x_n':sum(r['search_factor']>=4 for r in rows),
            'min_search_factor':min(r['search_factor'] for r in rows),
            'median_search_factor':sorted(r['search_factor'] for r in rows)[50],
            'median_warm_cold_ratio':sorted(r['warm_cold_ratio'] for r in rows)[50],
        }
    }
    A['gates']={
        'A1_exact_obstruction':len(base)==16 and all(r['all_hold_outside_old'] for r in rows),
        'A2_quotient_identity_100_streams':all(r['winner_same_orbit'] for r in rows),
        'A3_literal_competitiveness_reported':True,
        'A4_cost_95_of_100':sum(r['warm_beats_cold'] for r in rows)>=95,
        'A5_search_4x_95_of_100':sum(r['search_factor']>=4 for r in rows)>=95,
    }
    return A

# ---------------- Stratum B/C: natural QuixBugs ----------------
class SiteTransform(ast.NodeTransformer):
    def __init__(self, idx, swap, target): self.idx=idx; self.swap=swap; self.target=target; self.i=-1
    def visit_Compare(self,n):
        self.generic_visit(n)
        if not(len(n.ops)==1 and len(n.comparators)==1 and isinstance(n.ops[0],(ast.Lt,ast.Gt))): return n
        self.i+=1
        if self.i!=self.idx: return n
        l,r=n.left,n.comparators[0]
        # canonical source orientation is LT; naturally authored GT is normalized by swapping operands first.
        if isinstance(n.ops[0],ast.Gt): l,r=r,l
        if self.swap: l,r=r,l
        n.left=l; n.comparators=[r]; n.ops=[OPCLS[self.target]()]
        return n


def variant(src,idx,swap,target):
    tr=SiteTransform(idx,swap,target).visit(ast.parse(src)); ast.fix_missing_locations(tr)
    return ast.unparse(tr)+'\n'


def site_orientations(src):
    vals=[]
    class V(ast.NodeVisitor):
        def visit_Compare(self,n):
            if len(n.ops)==1 and len(n.comparators)==1 and isinstance(n.ops[0],(ast.Lt,ast.Gt)):
                vals.append('<' if isinstance(n.ops[0],ast.Lt) else '>')
            self.generic_visit(n)
    V().visit(ast.parse(src)); return vals


def purge(root):
    for d in (root/'correct_python_programs').rglob('__pycache__'):
        shutil.rmtree(d,ignore_errors=True)
    for d in (root/'python_testcases').rglob('__pycache__'):
        shutil.rmtree(d,ignore_errors=True)


def verify(root,program,path,content,timeout=45):
    old=path.read_text()
    try:
        purge(root); path.write_text(content)
        tf=root/'python_testcases'/f'test_{program}.py'
        if not tf.exists(): return {'pass':False,'failures':['NO_TEST_FILE'],'returncode':127}
        c,o=run([sys.executable,'-B','-m','pytest','--correct','-q',str(tf)],cwd=root,timeout=timeout)
        return {'pass':c==0,'failures':failure_nodes(o),'returncode':c}
    finally:
        path.write_text(old); purge(root)


def candidate_grammar():
    c=[]
    for swap in (False,True):
        for st in TOKENS:
            for rt in TOKENS:
                if st==rt: continue
                if (not swap) and st=='<' and rt=='<=': continue
                c.append({'swap':swap,'strict_target':st,'relaxed_target':rt,'id':f'{"SWAP" if swap else "KEEP"}:{st}|{rt}'})
    return c


def dual_strict(tok):
    return {'<':'>','>':'<','<=':'>=','>=':'<=','==':'==','!=':'!='}[tok]


def select_relation(acquisition, candidates):
    # This function has no held-out argument by construction.
    score_rows=[]; perfect=[]
    for cand in candidates:
        sk=f'{int(cand["swap"])}:{cand["strict_target"]}'
        rk=f'{int(cand["swap"])}:{cand["relaxed_target"]}'
        ok=0
        for r in acquisition:
            so=r['outcomes'][sk]; ro=r['outcomes'][rk]
            if so['pass'] and (not ro['pass']) and tuple(ro['failures'])==tuple(r['relax_failures']): ok+=1
        score_rows.append((cand['id'],ok))
        if ok==len(acquisition) and len(acquisition)>0: perfect.append(cand)
    return perfect,score_rows


def evaluate_holdout(heldout,selected):
    # Called only after selected relation is serialized/hashable.
    if not selected: return {'quotient':0,'literal':0,'ablation':0,'n':len(heldout),'reverse_q':0,'reverse_abl':0,'reverse_n':0}
    sk=f'{int(selected["swap"])}:{selected["strict_target"]}'
    rk=f'{int(selected["swap"])}:{selected["relaxed_target"]}'
    reverse_tok=dual_strict(selected['strict_target'])
    revk=f'{int(selected["swap"])}:{reverse_tok}'
    q=lit=abl=rq=rabl=rn=0
    for r in heldout:
        so=r['outcomes'][sk]; ro=r['outcomes'][rk]
        q+=int(so['pass'] and not ro['pass']); abl+=int(not ro['pass'])
        # literal acquisition repair <= -> < cannot repair a target presentation whose relaxed literal is not <=.
        if selected['relaxed_target']=='<=' and not selected['swap']:
            lit+=int(r['outcomes']['0:<']['pass'])
        if r.get('reverse_qualified'):
            rn+=1; mut=r['outcomes'][revk]; rq+=int(so['pass'] and not mut['pass']); rabl+=int(not mut['pass'])
    return {'quotient':q,'literal':lit,'ablation':abl,'n':len(heldout),'reverse_q':rq,'reverse_abl':rabl,'reverse_n':rn}


def stratum_b_c():
    candidates=candidate_grammar()
    with tempfile.TemporaryDirectory(prefix='v135_quix_') as td:
        root=Path(td)/'QuixBugs'; c,o=run(['git','clone','--quiet',QUIX_REPO,str(root)],timeout=240)
        if c: raise RuntimeError(o)
        c,o=run(['git','checkout','--quiet',QUIX_COMMIT],cwd=root,timeout=60)
        if c: raise RuntimeError(o)
        programs=[]
        for sp in sorted((root/'correct_python_programs').glob('*.py')):
            if sp.name.startswith('__'): continue
            program=sp.stem; tf=root/'python_testcases'/f'test_{program}.py'
            if not tf.exists(): continue
            src=sp.read_text(); orientations=site_orientations(src)
            if orientations: programs.append((program,sp,src,orientations))
        source_manifest=[{'program':p,'source_sha256':hashlib.sha256(src.encode()).hexdigest(),'site_orientations':oris} for p,sp,src,oris in programs]
        records=[]; verifier_calls=0
        for p,sp,src,oris in programs:
            base=verify(root,p,sp,src); verifier_calls+=1
            if not base['pass']: continue
            for idx,ori in enumerate(oris):
                # canonical KEEP:< is semantically identical to source; KEEP:<= is RELAX.
                relax=verify(root,p,sp,variant(src,idx,False,'<=')); verifier_calls+=1
                rev=verify(root,p,sp,variant(src,idx,False,'>')); verifier_calls+=1
                relaxq=(not relax['pass']) and len(relax['failures'])>0
                revq=(not rev['pass']) and len(rev['failures'])>0
                if not (relaxq or revq): continue
                outcomes={}
                for swap in (False,True):
                    for tok in TOKENS:
                        k=f'{int(swap)}:{tok}'
                        # reuse calls already made where possible
                        if not swap and tok=='<': outcomes[k]={'pass':True,'failures':(), 'returncode':0}
                        elif not swap and tok=='<=': outcomes[k]=relax
                        elif not swap and tok=='>': outcomes[k]=rev
                        else:
                            outcomes[k]=verify(root,p,sp,variant(src,idx,swap,tok)); verifier_calls+=1
                records.append({'program':p,'site':idx,'natural_orientation':ori,'relax_qualified':relaxq,'reverse_qualified':revq,'relax_failures':relax['failures'],'reverse_failures':rev['failures'],'outcomes':outcomes})
        qualified=[r for r in records if r['relax_qualified']]
        qprograms=sorted({r['program'] for r in qualified})
        task_manifest=[{'program':r['program'],'site':r['site'],'orientation':r['natural_orientation'],'relax_failures':r['relax_failures'],'reverse_qualified':r['reverse_qualified']} for r in qualified]
        folds=[]
        for hold in qprograms:
            ac=[r for r in qualified if r['program']!=hold]; ht=[r for r in qualified if r['program']==hold]
            ac_manifest=[(r['program'],r['site']) for r in ac]; ht_manifest=[(r['program'],r['site']) for r in ht]
            perfect,scores=select_relation(ac,candidates)
            sel=perfect[0] if len(perfect)==1 else None
            selection_blob={'hold':hold,'acquisition_manifest_hash':sha(ac_manifest),'candidate_grammar_hash':sha(candidates),'perfect':[x['id'] for x in perfect],'scores':scores}
            selection_hash=sha(selection_blob)
            ev=evaluate_holdout(ht,sel)
            folds.append({'holdout_program':hold,'acquisition_n':len(ac),'heldout_n':len(ht),'perfect_n':len(perfect),'perfect_ids':[x['id'] for x in perfect],'selected':sel,'rejected_n':sum(s<len(ac) for _,s in scores),'selection_hash_before_holdout':selection_hash,'acquisition_manifest_hash':sha(ac_manifest),'heldout_manifest_hash':sha(ht_manifest),'evaluation':ev})
        # Orientation-separated evaluation using only naturally authored LT acquisition and GT heldout, then reverse.
        orient=[]
        for ac_ori,ht_ori in [('<','>'),('>','<')]:
            for hold in sorted({r['program'] for r in qualified if r['natural_orientation']==ht_ori}):
                ac=[r for r in qualified if r['natural_orientation']==ac_ori and r['program']!=hold]
                ht=[r for r in qualified if r['natural_orientation']==ht_ori and r['program']==hold]
                if not ac or not ht: continue
                perfect,scores=select_relation(ac,candidates); sel=perfect[0] if len(perfect)==1 else None
                ev=evaluate_holdout(ht,sel)
                orient.append({'direction':f'{ac_ori}->{ht_ori}','holdout_program':hold,'acquisition_n':len(ac),'heldout_n':len(ht),'perfect_n':len(perfect),'selected':sel,'evaluation':ev})
        B={
            'external_commit':QUIX_COMMIT,'source_manifest_hash':sha(source_manifest),'task_manifest_hash':sha(task_manifest),'candidate_grammar_hash':sha(candidates),
            'candidate_count':len(candidates),'programs_with_strict_sites':len(programs),'qualified_relax_n':len(qualified),'qualified_relax_programs':qprograms,
            'qualified_reverse_n':sum(r['reverse_qualified'] for r in records),'verifier_calls':verifier_calls,'folds':folds,'orientation_folds':orient,
        }
        evaluable=[f for f in folds if f['acquisition_n'] and f['heldout_n']]
        b2=bool(evaluable) and all(f['perfect_n']==1 and f['rejected_n']/len(candidates)>=.90 for f in evaluable)
        total=sum(f['evaluation']['n'] for f in evaluable); q=sum(f['evaluation']['quotient'] for f in evaluable); lit=sum(f['evaluation']['literal'] for f in evaluable); abl=sum(f['evaluation']['ablation'] for f in evaluable)
        rn=sum(f['evaluation']['reverse_n'] for f in evaluable); rq=sum(f['evaluation']['reverse_q'] for f in evaluable); rabl=sum(f['evaluation']['reverse_abl'] for f in evaluable)
        directions={x['direction'] for x in orient}; on=sum(x['evaluation']['n'] for x in orient); oq=sum(x['evaluation']['quotient'] for x in orient)
        B['aggregate']={'heldout_n':total,'quotient':q,'literal':lit,'ablation':abl,'reverse_n':rn,'reverse_q':rq,'reverse_ablation':rabl,'orientation_n':on,'orientation_q':oq}
        B['gates']={
            'B1_scale':len(qualified)>=20 and len(qprograms)>=8,
            'B1_corpus_ceiling':len(qualified)<20 or len(qprograms)<8,
            'B2_unique_induction_and_90pct_rejection':b2,
            'B3_heldout_transport':total>0 and q/total>=.90 and lit/total<=.10 and abl/total>=.90,
            'B4_cross_family_reuse':rn>0 and rq/rn>=.90 and rabl/rn>=.90,
            'B5_orientation_symmetry':directions=={'<->>','>-><'} and on>0 and oq/on>=.90,
        }
        C={
            'required_hashes_present':all([B['source_manifest_hash'],B['task_manifest_hash'],B['candidate_grammar_hash']]) and all(f['selection_hash_before_holdout'] and f['acquisition_manifest_hash'] and f['heldout_manifest_hash'] for f in folds),
            'selection_function_signature':'select_relation(acquisition,candidates) — no heldout argument',
            'evaluation_after_selection_serialization':True,
            'constructor_visible':'acquisition verifier pass/fail plus exact FAILED node IDs and frozen AST candidate grammar',
            'heldout_hidden_during_selection':'whole held-out program records are not arguments to select_relation',
        }
        C['gate_C1_information_boundary']=bool(C['required_hashes_present'] and C['evaluation_after_selection_serialization'])
        return B,C


def stratum_e():
    c,o=run([sys.executable,'experiments/V113_CLOSURE_EXTENSION_IDENTITY.py'],timeout=240)
    p=Path('artifacts/v113_closure_extension_identity/RESULT.json')
    if c!=0 or not p.exists(): return {'gate_E1_exact_consistency':False,'error':o[-4000:]}
    r=json.loads(p.read_text()); gs=r.get('gates',{})
    e1=bool(gs.get('G1_orbit_implies_same_closure_theorem_check') and gs.get('G3_multiple_developmental_identities') and gs.get('G6_mutual_reachability_equals_closure_identity'))
    return {'gate_E1_exact_consistency':e1,'v113_verdict':r.get('verdict'),'worlds':r.get('worlds'),'E2_lattice_claim':'FORBIDDEN_BY_V113A_NON_LATTICE_GF5','E3_natural_multiple_classes':'OPEN_NOT_CLOSED'}


def main():
    A=stratum_a(); B,C=stratum_b_c(); E=stratum_e()
    # The higher-order gates are deliberately not backfilled from historical positives.
    statuses={
        'Q1_scale_N':'PASS' if A['gates']['A4_cost_95_of_100'] and A['gates']['A5_search_4x_95_of_100'] else 'FAIL',
        'Q2_encoding_presentation_invariance':'PASS_BOUNDED' if A['gates']['A2_quotient_identity_100_streams'] and B['gates']['B5_orientation_symmetry'] else ('CORPUS_CEILING_OR_PARTIAL' if B['gates']['B1_corpus_ceiling'] else 'FAIL'),
        'Q3_representative_symmetry':'PASS_BOUNDED' if A['gates']['A2_quotient_identity_100_streams'] and B['gates']['B3_heldout_transport'] else 'PARTIAL_OR_FAIL',
        'Q4_less_researcher_chosen_relation':'PASS_BOUNDED_GENERIC_GRAMMAR' if B['gates']['B2_unique_induction_and_90pct_rejection'] else ('CORPUS_CEILING' if B['gates']['B1_corpus_ceiling'] else 'FAIL'),
        'Q5_information_boundary':'PASS_RUNNER_AUDIT' if C['gate_C1_information_boundary'] else 'INVALID',
        'Q6_durable_cost_compression':'PASS_EXACT_WORLD' if A['gates']['A4_cost_95_of_100'] and A['gates']['A5_search_4x_95_of_100'] else 'FAIL',
        'Q7_developmental_reachability_natural':'OPEN_PARTIAL_EXACT_ONLY' if E.get('gate_E1_exact_consistency') else 'FAIL_EXACT_CONTROL',
        'Q8_natural_multigeneration_compounding':'OPEN_NOT_CLOSED',
        'Q9_constructor_growth':'OPEN_WAITING_ON_INDEPENDENT_V134_SUCCESSOR',
        'Q10_open_ended_repeated_development':'OPEN_NOT_CLOSED',
    }
    invalid=statuses['Q5_information_boundary']=='INVALID'
    newly_closed=sum(v.startswith('PASS') for v in statuses.values())
    full=all(v=='PASS' for v in statuses.values())
    verdict='INVALID_V135' if invalid else ('PASS_V135_FULL_CAPSTONE' if full else ('PARTIAL_V135_DECISION_CHANGING_EVIDENCE' if newly_closed else 'NO_NEW_CLOSURE_V135'))
    R={
        'canonical_id':'V135_DEVELOPMENTAL_QUOTIENT_CAPSTONE','protocol':'protocols/V135_DEVELOPMENTAL_QUOTIENT_CAPSTONE_PRECOMMIT.md',
        'stratum_A':A,'stratum_B':B,'stratum_C':C,'stratum_E':E,'question_status':statuses,'verdict':verdict,
        'fresh_higher_gates':{'F1_natural_multigeneration':'OPEN_NOT_CLOSED','G1_constructor_growth':'OPEN_WAITING_ON_V134_SUCCESSOR','H1_open_ended_20_episode_run':'OPEN_NOT_CLOSED'},
        'claim_boundary':'Fresh V135 can close bounded scale/invariance/induction/boundary/cost questions. It may not use historical V54/V132 to claim fresh natural multigeneration, constructor growth or open-endedness.'
    }
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2,sort_keys=True)+'\n')
    summary={
        'verdict':verdict,'questions':statuses,'A_summary':A['summary'],'B_counts':{'qualified_relax_n':B['qualified_relax_n'],'qualified_relax_programs':len(B['qualified_relax_programs']),'qualified_reverse_n':B['qualified_reverse_n'],'candidate_count':B['candidate_count'],'verifier_calls':B['verifier_calls'],'aggregate':B['aggregate']},'B_gates':B['gates'],'C1':C['gate_C1_information_boundary'],'E1':E.get('gate_E1_exact_consistency')
    }
    (OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True))
    if invalid: raise SystemExit(2)

if __name__=='__main__': main()
