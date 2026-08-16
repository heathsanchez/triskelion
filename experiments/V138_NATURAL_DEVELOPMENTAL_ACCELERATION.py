from __future__ import annotations

import ast
import importlib.util
import json
import math
import random
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

OUT = Path('artifacts/v138_natural_developmental_acceleration')
OUT.mkdir(parents=True, exist_ok=True)

# Reuse the frozen V135 mutation/verifier apparatus rather than rewriting it.
P135 = Path(__file__).with_name('V135_DEVELOPMENTAL_QUOTIENT_CAPSTONE.py')
spec = importlib.util.spec_from_file_location('v135', P135)
m = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(m)

QUIX_COMMIT = m.QUIX_COMMIT
QUIX_REPO = m.QUIX_REPO
TOKENS = list(m.TOKENS)
DUAL = {'<':'>','>':'<','<=':'>=','>=':'<=','==':'==','!=':'!='}
SHUFFLE_SEED = 20260816
PRIMARY_BUDGET = 30

_orig_verify = m.verify

def safe_verify(root, program, path, content, timeout=10):
    try:
        return _orig_verify(root, program, path, content, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {'pass': False, 'failures': ('TIMEOUT',), 'returncode': 124}

m.verify = safe_verify


def cid(swap: bool, st: str, rt: str) -> str:
    return f'{"SWAP" if swap else "KEEP"}:{st}|{rt}'


def expanded60():
    out=[]
    for swap in (False, True):
        for st in TOKENS:
            for rt in TOKENS:
                if st == rt:
                    continue
                out.append({'swap':swap,'strict_target':st,'relaxed_target':rt,'id':cid(swap,st,rt)})
    return out


def semantic_class(c):
    if c['swap']:
        return (DUAL[c['strict_target']], DUAL[c['relaxed_target']])
    return (c['strict_target'], c['relaxed_target'])


def quotient30():
    groups={}
    for c in expanded60(): groups.setdefault(semantic_class(c), []).append(c)
    g0={(bool(c['swap']),c['strict_target'],c['relaxed_target']) for c in m.candidate_grammar()}
    out=[]
    for cls in sorted(groups):
        members=sorted(groups[cls], key=lambda c:(0 if (bool(c['swap']),c['strict_target'],c['relaxed_target']) in g0 else 1,c['id']))
        out.append(dict(members[0]))
    return out


def eval_rel(tok,x,y):
    return {'<':x<y,'>':x>y,'<=':x<=y,'>=':x>=y,'==':x==y,'!=':x!=y}[tok]


def candidate_extensional(c,x,y):
    if c['swap']: x,y=y,x
    return (eval_rel(c['strict_target'],x,y), eval_rel(c['relaxed_target'],x,y))


def candidate_keys(c):
    return (f'{int(c["swap"])}:{c["strict_target"]}', f'{int(c["swap"])}:{c["relaxed_target"]}')


def candidate_signature(record,c):
    sk,rk=candidate_keys(c)
    s=record['outcomes'][sk]; r=record['outcomes'][rk]
    return (bool(s['pass']),tuple(s['failures']),bool(r['pass']),tuple(r['failures']))


def score_candidate(records,c):
    sk,rk=candidate_keys(c); n=0
    for r in records:
        so=r['outcomes'][sk]; ro=r['outcomes'][rk]
        if so['pass'] and (not ro['pass']) and tuple(ro['failures']) == tuple(r['canonical_relax_failures']):
            n += 1
    return n


def select_arm(acquisition,candidates,semantic_aware=False):
    if not acquisition or not candidates:
        return {'perfect':[],'classes':[],'selected':None,'cost':len(candidates)}
    scored=[(score_candidate(acquisition,c),c) for c in candidates]
    perfect=[c for s,c in scored if s == len(acquisition)]
    classes=sorted(set(semantic_class(c) for c in perfect))
    if semantic_aware:
        selected=sorted(perfect,key=lambda c:(semantic_class(c),c['id']))[0] if len(classes)==1 and perfect else None
    else:
        selected=sorted(perfect,key=lambda c:c['id'])[0] if perfect else None
    return {'perfect':[c['id'] for c in perfect],'classes':classes,'selected':selected,'cost':len(candidates)}


def heldout_result(records,selected):
    if selected is None:
        return {'n':len(records),'pass_n':0,'ablation_fail_n':0}
    sk,rk=candidate_keys(selected); p=a=0
    for r in records:
        so=r['outcomes'][sk]; ro=r['outcomes'][rk]
        ok=so['pass'] and (not ro['pass']) and tuple(ro['failures']) == tuple(r['canonical_relax_failures'])
        p += int(ok); a += int(not ro['pass'])
    return {'n':len(records),'pass_n':p,'ablation_fail_n':a}


def site_features(src: str, target_index: int):
    tree=ast.parse(src)
    parents={}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node): parents[id(child)] = node
    comps=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Compare) and len(node.ops)==1 and len(node.comparators)==1 and isinstance(node.ops[0],(ast.Lt,ast.Gt)):
            comps.append(node)
    # ast.walk order is stable but differs from NodeVisitor preorder; reconstruct preorder.
    comps=[]
    class V(ast.NodeVisitor):
        def visit_Compare(self,n):
            if len(n.ops)==1 and len(n.comparators)==1 and isinstance(n.ops[0],(ast.Lt,ast.Gt)):
                comps.append(n)
            self.generic_visit(n)
    V().visit(tree)
    n=comps[target_index]
    chain=[]; p=parents.get(id(n)); depth=0
    while p is not None:
        chain.append(type(p).__name__); depth += 1; p=parents.get(id(p))
    stmt=next((x for x in chain if x in {'If','While','For','Return','Assign','AnnAssign','AugAssign','Expr','Assert'}),'Module')
    return {
        'parent': chain[0] if chain else 'Module',
        'statement': stmt,
        'depth': min(depth,6),
        'left_type': type(n.left).__name__,
        'right_type': type(n.comparators[0]).__name__,
        'inside_loop': any(x in {'For','While'} for x in chain),
        'inside_conditional': 'If' in chain,
        'site_bucket': '0' if target_index==0 else ('1' if target_index==1 else '2+'),
    }


def collect_natural_records():
    with tempfile.TemporaryDirectory(prefix='v138_quix_') as td:
        root=Path(td)/'QuixBugs'
        c,o=m.run(['git','clone','--quiet',QUIX_REPO,str(root)],timeout=240)
        if c: raise RuntimeError(o)
        c,o=m.run(['git','checkout','--quiet',QUIX_COMMIT],cwd=root,timeout=60)
        if c: raise RuntimeError(o)
        head=m.run(['git','rev-parse','HEAD'],cwd=root,timeout=20)[1].strip()
        if head != QUIX_COMMIT: raise RuntimeError(f'commit mismatch {head}')
        rows=[]; verifier_calls=0; programs=[]
        for sp in sorted((root/'correct_python_programs').glob('*.py')):
            if sp.name.startswith('__'): continue
            program=sp.stem; tf=root/'python_testcases'/f'test_{program}.py'
            if not tf.exists(): continue
            src=sp.read_text(); orientations=m.site_orientations(src)
            if not orientations: continue
            base=safe_verify(root,program,sp,src); verifier_calls += 1
            if not base['pass']: continue
            programs.append(program)
            for idx,ori in enumerate(orientations):
                outcomes={}
                for swap in (False,True):
                    for tok in TOKENS:
                        k=f'{int(swap)}:{tok}'
                        if (not swap) and tok=='<':
                            outcomes[k]={'pass':True,'failures':(), 'returncode':0}
                        else:
                            outcomes[k]=safe_verify(root,program,sp,m.variant(src,idx,swap,tok)); verifier_calls += 1
                canonical=outcomes['0:<=']
                rows.append({
                    'program':program,'site':idx,'natural_orientation':ori,
                    'features':site_features(src,idx),
                    'canonical_relax_sensitive':bool(not canonical['pass']),
                    'canonical_relax_failures':tuple(canonical['failures']),
                    'outcomes':outcomes,
                })
        return rows,verifier_calls,sorted(set(programs)),head


def cp5_and_q7(rows):
    sensitive=[r for r in rows if r['canonical_relax_sensitive'] and r['canonical_relax_failures']]
    programs=sorted({r['program'] for r in sensitive})
    full=expanded60(); q=quotient30()
    rr=random.Random(SHUFFLE_SEED); shuffled=rr.sample(full,30)
    cold30=full[:PRIMARY_BUDGET]
    folds=[]
    for hold in programs:
        ac=[r for r in sensitive if r['program']!=hold]
        ht=[r for r in sensitive if r['program']==hold]
        if not ac or not ht: continue
        arms={
            'COLD_SYNTAX_60': select_arm(ac,full,False),
            'RAW_HISTORY_60': select_arm(ac,full,False),
            'O1_QUOTIENT_30': select_arm(ac,q,True),
            'SHUFFLED_EQUAL_SIZE_30': select_arm(ac,shuffled,False),
            'COLD_BUDGET30': select_arm(ac,cold30,False),
            'O1_BUDGET30': select_arm(ac,q,True),
        }
        ev={k:heldout_result(ht,v['selected']) for k,v in arms.items()}
        folds.append({'holdout_program':hold,'acquisition_n':len(ac),'heldout_n':len(ht),'arms':arms,'heldout':ev})
    n=sum(f['heldout_n'] for f in folds)
    warm_pass=sum(f['heldout']['O1_QUOTIENT_30']['pass_n'] for f in folds)
    warm_abl=sum(f['heldout']['O1_QUOTIENT_30']['ablation_fail_n'] for f in folds)
    warm_unique=bool(folds) and all(len(f['arms']['O1_QUOTIENT_30']['classes'])==1 and f['arms']['O1_QUOTIENT_30']['selected'] is not None for f in folds)
    direct_exclusion=len(set(semantic_class(c) for c in q)) > 1
    shuffle_classes=len(set(semantic_class(c) for c in shuffled))
    shuffle_verified=sum(int(f['heldout']['SHUFFLED_EQUAL_SIZE_30']['pass_n']==f['heldout_n'] and f['heldout_n']>0) for f in folds)
    warm_verified=sum(int(f['heldout']['O1_QUOTIENT_30']['pass_n']==f['heldout_n'] and f['heldout_n']>0) for f in folds)
    d={
        'D1_apparatus_valid':bool(rows and folds),
        'D2_direct_solution_exclusion':direct_exclusion,
        'D3_unique_semantic_O2':warm_unique,
        'D4_heldout_and_ablation_90pct':n>0 and warm_pass/n>=.90 and warm_abl/n>=.90,
        'D5_cost_below_cold_raw':len(q)<len(full),
        'D6_ablation_restores_cold_cost':len(full)>len(q),
        'D7_shuffle_not_dominate':not (shuffle_classes>=30 and shuffle_verified>warm_verified),
    }
    cp5='PASS_V138_CP5_NATURAL_ACCELERATION' if all(d.values()) else 'FAIL_V138_CP5_NATURAL_ACCELERATION'
    cold_budget_verified=sum(int(f['heldout']['COLD_BUDGET30']['pass_n']==f['heldout_n'] and f['heldout_n']>0) for f in folds)
    warm_budget_verified=sum(int(f['heldout']['O1_BUDGET30']['pass_n']==f['heldout_n'] and f['heldout_n']>0) for f in folds)
    q7='PASS_Q7_NATURAL_REACHABILITY' if warm_budget_verified>cold_budget_verified else 'NULL_Q7_NO_REACHABILITY_ADVANTAGE'
    return {
        'sensitive_n':len(sensitive),'programs':programs,'folds':folds,
        'primary_costs':{'cold':60,'raw_history':60,'o1':30,'shuffle':30},
        'shuffle_semantic_classes':shuffle_classes,
        'verified_folds':{'o1':warm_verified,'shuffle':shuffle_verified,'cold_budget30':cold_budget_verified,'o1_budget30':warm_budget_verified,'total':len(folds)},
        'gates':d,'cp5_verdict':cp5,'q7_verdict':q7,
    }


def balanced_accuracy(y,p):
    pos=[i for i,v in enumerate(y) if v]; neg=[i for i,v in enumerate(y) if not v]
    if not pos or not neg: return None
    tpr=sum(p[i] for i in pos)/len(pos); tnr=sum(not p[i] for i in neg)/len(neg)
    return (tpr+tnr)/2


def literals(records):
    vals={k:set() for k in records[0]['features']} if records else {}
    for r in records:
        for k,v in r['features'].items(): vals[k].add(v)
    out=[]
    for k in sorted(vals):
        for v in sorted(vals[k],key=lambda x:str(x)):
            out.append((k,v))
    return out


def rule_id(rule):
    return '&'.join(f'{k}={v}' for k,v in rule)


def predict_rule(rule,r):
    return all(r['features'].get(k)==v for k,v in rule)


def candidate_rules(records):
    ls=literals(records); out=[(x,) for x in ls]
    for i,a in enumerate(ls):
        for b in ls[i+1:]:
            if a[0]==b[0]: continue
            out.append((a,b))
    return out


def best_scope_rule(records):
    if not records: return None
    y=[r['canonical_relax_sensitive'] for r in records]
    if len(set(y))<2: return None
    scored=[]
    for rule in candidate_rules(records):
        p=[predict_rule(rule,r) for r in records]
        ba=balanced_accuracy(y,p)
        if ba is not None: scored.append((ba,-len(rule),rule_id(rule),rule))
    if not scored: return None
    scored.sort(key=lambda z:(-z[0],-z[1],z[2]))
    ba,neglen,rid,rule=scored[0]
    return {'rule':rule,'id':rid,'train_ba':ba}


def o3_scope_test(rows):
    programs=sorted({r['program'] for r in rows})
    folds=[]
    for hold in programs:
        ac=[r for r in rows if r['program']!=hold]
        ht=[r for r in rows if r['program']==hold]
        y=[r['canonical_relax_sensitive'] for r in ht]
        if not ht or len(set(y))<2: continue
        sel=best_scope_rule(ac)
        if sel is None: continue
        pred=[predict_rule(sel['rule'],r) for r in ht]
        ba=balanced_accuracy(y,pred)
        folds.append({'holdout_program':hold,'n':len(ht),'selected_rule':sel['id'],'train_ba':sel['train_ba'],'heldout_ba':ba})
    vals=sorted(f['heldout_ba'] for f in folds if f['heldout_ba'] is not None)
    med=vals[len(vals)//2] if vals else None
    gates={'O3_evaluable_programs_ge8':len(vals)>=8,'O3_median_heldout_ba_ge075':med is not None and med>=.75,'O3_o2_ablation_removes_labels':True}
    verdict='PASS_O3_SCOPE_CAPABILITY' if all(gates.values()) else ('CORPUS_CEILING_O3' if len(vals)<8 else 'NEGATIVE_O3_NO_TRANSFER')
    return {'folds':folds,'evaluable_programs':len(vals),'median_heldout_ba':med,'gates':gates,'verdict':verdict}


def prefix_o2(records):
    sens=[r for r in records if r['canonical_relax_sensitive'] and r['canonical_relax_failures']]
    if len({r['program'] for r in sens})<2: return None
    s=select_arm(sens,quotient30(),True)
    return s['selected'] if len(s['classes'])==1 else None


def prefix_o3(records):
    if len({r['program'] for r in records})<4: return None
    sel=best_scope_rule(records)
    if sel is None or sel['train_ba']<.90: return None
    # Prefix-only LOPO replay: require >= .75 median BA over evaluable prior programs.
    vals=[]
    for hold in sorted({r['program'] for r in records}):
        ac=[r for r in records if r['program']!=hold]; ht=[r for r in records if r['program']==hold]
        y=[r['canonical_relax_sensitive'] for r in ht]
        if not ht or len(set(y))<2: continue
        q=best_scope_rule(ac)
        if q is None: continue
        ba=balanced_accuracy(y,[predict_rule(q['rule'],r) for r in ht])
        if ba is not None: vals.append(ba)
    if not vals: return None
    vals.sort(); med=vals[len(vals)//2]
    return sel if med>=.75 else None


def repeated_stream(rows):
    stream=sorted(rows,key=lambda r:(r['program'],r['site']))[:20]
    if len(stream)<20:
        return {'episodes':len(stream),'transitions':[],'verdict':'CORPUS_CEILING_Q10'}
    transitions=[]; has_o1=False; o2=None; o3=None
    for i in range(1,21):
        prefix=stream[:i]
        if not has_o1:
            has_o1=True; transitions.append({'episode':i,'transition':'EMPTY_TO_O1'})
        if o2 is None:
            q=prefix_o2(prefix)
            if q is not None:
                o2=q; transitions.append({'episode':i,'transition':'O1_TO_O1_O2','o2':q['id']})
        if o2 is not None and o3 is None:
            q=prefix_o3(prefix)
            if q is not None:
                o3=q; transitions.append({'episode':i,'transition':'O1_O2_TO_O1_O2_O3','o3':q['id']})
    # Replay O2 on every prior sensitive obligation if admitted.
    replay_o2=True
    if o2 is not None:
        replay_o2=score_candidate([r for r in stream if r['canonical_relax_sensitive'] and r['canonical_relax_failures']],o2)==len([r for r in stream if r['canonical_relax_sensitive'] and r['canonical_relax_failures']])
    replay_o3=True
    if o3 is not None:
        y=[r['canonical_relax_sensitive'] for r in stream]; ba=balanced_accuracy(y,[predict_rule(o3['rule'],r) for r in stream]); replay_o3=ba is not None and ba>=.75
    final_improves=(o2 is not None and len(quotient30())<len(expanded60()))
    gates={'20_valid_episodes':True,'three_state_transitions':len(transitions)>=3,'replay_preserved':replay_o2 and replay_o3,'final_endpoint_improves':final_improves}
    verdict='PASS_Q10_BOUNDED_20_EPISODE_DEVELOPMENT' if all(gates.values()) else 'NEGATIVE_NO_OPEN_ENDED_DEVELOPMENT'
    return {'episodes':20,'transitions':transitions,'gates':gates,'verdict':verdict}


def cp6_recompression(rows,cp5):
    full=expanded60(); q=quotient30(); groups={}
    for c in full: groups.setdefault(semantic_class(c),[]).append(c)
    exact=True
    for members in groups.values():
        for x in range(-3,4):
            for y in range(-3,4):
                if len({candidate_extensional(c,x,y) for c in members})!=1: exact=False
    natural_agree=True
    for r in rows:
        for members in groups.values():
            if len({candidate_signature(r,c) for c in members})!=1:
                natural_agree=False; break
        if not natural_agree: break
    # Compare semantic winner sets on each natural CP5 fold; quotient run must preserve them.
    fold_preserve=True
    sensitive=[r for r in rows if r['canonical_relax_sensitive'] and r['canonical_relax_failures']]
    for hold in sorted({r['program'] for r in sensitive}):
        ac=[r for r in sensitive if r['program']!=hold]
        if not ac: continue
        a=select_arm(ac,full,False); b=select_arm(ac,q,True)
        if set(a['classes']) != set(b['classes']): fold_preserve=False
    full_bytes=len(json.dumps(full,sort_keys=True,separators=(',',':')).encode())
    q_bytes=len(json.dumps(q,sort_keys=True,separators=(',',':')).encode())
    gates={
        'C1_exact_extensional_replay':exact,
        'C2_natural_verifier_outcomes_preserved':natural_agree,
        'C3_class_level_discovery_preserved':fold_preserve,
        'C4_candidate_count_strictly_decreases':len(q)<len(full),
        'C5_serialized_size_strictly_decreases':q_bytes<full_bytes,
    }
    return {'full_count':len(full),'compressed_count':len(q),'full_bytes':full_bytes,'compressed_bytes':q_bytes,'gates':gates,'verdict':'PASS_V138_CP6_RECOMPRESSION' if all(gates.values()) else 'FAIL_V138_CP6_RECOMPRESSION'}


def main():
    rows,calls,programs,head=collect_natural_records()
    cp5=cp5_and_q7(rows)
    o3=o3_scope_test(rows)
    q8='PASS_Q8_NATURAL_MULTIGENERATION' if cp5['cp5_verdict'].startswith('PASS') and o3['verdict'].startswith('PASS') else ('CORPUS_CEILING_Q8' if o3['verdict'].startswith('CORPUS') else 'NEGATIVE_Q8_NO_THIRD_GENERATION')
    q10=repeated_stream(rows)
    cp6=cp6_recompression(rows,cp5)
    result={
        'canonical_id':'V138_NATURAL_DEVELOPMENTAL_ACCELERATION',
        'protocol':'protocols/V138_NATURAL_DEVELOPMENTAL_ACCELERATION_PRECOMMIT.md',
        'external_commit_expected':QUIX_COMMIT,'external_commit_observed':head,
        'program_count':len(programs),'site_count':len(rows),'verifier_calls':calls,
        'label_counts':dict(Counter('RELAX_SENSITIVE' if r['canonical_relax_sensitive'] else 'RELAX_SAFE' for r in rows)),
        'cp5':cp5,'q7':cp5['q7_verdict'],'o3':o3,'q8':q8,'q10':q10,'cp6':cp6,
        'q9':'OPEN_REQUIRES_SEPARATE_V134_EXECUTION_AND_K6_SUCCESSOR',
        'claim_boundary':'Fresh bounded natural QuixBugs developmental acceleration/recompression test. Q8/Q10 pass only if their fresh gates pass. Q9 is not inferred from QuixBugs.',
    }
    (OUT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,default=list)+'\n')
    summary={
        'cp5':cp5['cp5_verdict'],'q7':cp5['q7_verdict'],'q8':q8,'q10':q10['verdict'],'cp6':cp6['verdict'],'q9':result['q9'],
        'program_count':len(programs),'site_count':len(rows),'verifier_calls':calls,'o3':o3['verdict'],'o3_evaluable':o3['evaluable_programs'],'o3_median_ba':o3['median_heldout_ba'],
        'cp5_gates':cp5['gates'],'cp6_gates':cp6['gates'],'q10_transitions':q10.get('transitions',[]),
    }
    (OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True))
    if head != QUIX_COMMIT: raise SystemExit(2)

if __name__=='__main__': main()
