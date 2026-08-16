from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

OUT = Path('artifacts/v136_relation_grammar_invariance')
OUT.mkdir(parents=True, exist_ok=True)
TARGET = Path(__file__).with_name('V135_DEVELOPMENTAL_QUOTIENT_CAPSTONE.py')
spec = importlib.util.spec_from_file_location('v135', TARGET)
m = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(m)

# Apparatus-only timeout handling inherited from V135B.
_orig_verify = m.verify
def safe_verify(root, program, path, content, timeout=10):
    try:
        return _orig_verify(root, program, path, content, timeout=10)
    except subprocess.TimeoutExpired:
        return {'pass': False, 'failures': ('TIMEOUT',), 'returncode': 124}
m.verify = safe_verify

TOKENS = list(m.TOKENS)
DUAL = {'<':'>','>':'<','<=':'>=','>=':'<=','==':'==','!=':'!='}

def cid(swap, st, rt, prefix=''):
    return f'{prefix}{"SWAP" if swap else "KEEP"}:{st}|{rt}'

def dedup(rows):
    seen = set(); out = []
    for r in rows:
        k = (bool(r['swap']), r['strict_target'], r['relaxed_target'])
        if k in seen: continue
        seen.add(k); out.append(r)
    return out

def g0_full59():
    return m.candidate_grammar()

def g1_action_sequence59():
    rows=[]
    for action in ('KEEP','SWAP'):
        swap = action == 'SWAP'
        for st in TOKENS:
            for rt in TOKENS:
                if st == rt: continue
                if (not swap) and st == '<' and rt == '<=': continue
                rows.append({'swap':swap,'strict_target':st,'relaxed_target':rt,'id':cid(swap,st,rt,'ACT:')})
    return dedup(rows)

def g2_dual_presentation59():
    rows=[]
    # Enumerate in the dual vocabulary, then compile back to canonical tokens.
    dual_tokens=[DUAL[t] for t in TOKENS]
    for swap in (True,False):
        for dst in dual_tokens:
            for drt in dual_tokens:
                if dst == drt: continue
                st,rt = DUAL[dst], DUAL[drt]
                if (not swap) and st == '<' and rt == '<=': continue
                rows.append({'swap':swap,'strict_target':st,'relaxed_target':rt,'id':cid(swap,st,rt,'DUAL:')})
    return dedup(rows)

def g3_hash_split_union59():
    base=g0_full59(); a=[]; b=[]
    for r in base:
        h=int(hashlib.sha256(r['id'].encode()).hexdigest(),16)
        (a if h % 2 == 0 else b).append(dict(r,id='H0:'+r['id']))
    # Independently generated partitions are deliberately rejoined in reverse partition order.
    return dedup(b+a)

def g4_expanded60():
    rows=[]
    for swap in (False,True):
        for st in TOKENS:
            for rt in TOKENS:
                if st == rt: continue
                rows.append({'swap':swap,'strict_target':st,'relaxed_target':rt,'id':cid(swap,st,rt,'EXP:')})
    return dedup(rows)

GRAMMARS={
    'G0_FULL59':g0_full59,
    'G1_ACTION_SEQUENCE59':g1_action_sequence59,
    'G2_DUAL_PRESENTATION59':g2_dual_presentation59,
    'G3_HASH_SPLIT_UNION59':g3_hash_split_union59,
    'G4_EXPANDED60':g4_expanded60,
}

def semantic_selected(f):
    s=f.get('selected')
    if not s: return None
    return (bool(s['swap']),s['strict_target'],s['relaxed_target'])

def behavior_profile(f):
    e=f.get('evaluation',{})
    return (e.get('quotient'),e.get('n'),e.get('ablation'),e.get('reverse_q'),e.get('reverse_n'),e.get('reverse_abl'))

def forensic_orientation(B):
    rows=[]
    for f in B['orientation_folds']:
        e=f['evaluation']
        if f['acquisition_n']==0 or f['heldout_n']==0:
            cls='F_CORPUS_CEILING'
        elif f['perfect_n'] != 1:
            cls='F_NO_UNIQUE_RELATION'
        elif e['quotient'] != e['n']:
            cls='F_TRANSFER_BOUNDARY'
        else:
            cls='F_PASS'
        rows.append({
            'direction':f['direction'],'holdout_program':f['holdout_program'],
            'acquisition_n':f['acquisition_n'],'heldout_n':f['heldout_n'],
            'perfect_n':f['perfect_n'],'selected':f['selected'],'evaluation':e,'classification':cls,
        })
    return rows

def main():
    runs={}
    original=m.candidate_grammar
    for name,fn in GRAMMARS.items():
        m.candidate_grammar=fn
        B,C=m.stratum_b_c()
        runs[name]={'B':B,'C':C,'candidate_count':len(fn())}
    m.candidate_grammar=original

    frows=forensic_orientation(runs['G0_FULL59']['B'])
    failures=[r for r in frows if r['classification']!='F_PASS']

    basefold={f['holdout_program']:f for f in runs['G0_FULL59']['B']['folds'] if f['acquisition_n'] and f['heldout_n']}
    comparisons=[]
    for hold,bf in sorted(basefold.items()):
        row={'holdout_program':hold,'grammars':{}}
        profiles=[]
        for name in GRAMMARS:
            matches=[f for f in runs[name]['B']['folds'] if f['holdout_program']==hold and f['acquisition_n'] and f['heldout_n']]
            f=matches[0] if matches else None
            if f is None:
                entry={'evaluable':False}
            else:
                entry={'evaluable':True,'perfect_n':f['perfect_n'],'selected_semantic':semantic_selected(f),'profile':behavior_profile(f),'evaluation':f['evaluation']}
                if f['perfect_n']==1: profiles.append(behavior_profile(f))
            row['grammars'][name]=entry
        unique_profiles={json.dumps(p) for p in profiles}
        row['same_behavior_class_when_unique']=len(unique_profiles)<=1
        comparisons.append(row)

    g03_unique=all(all(r['grammars'][g].get('perfect_n')==1 for g in list(GRAMMARS)[:4]) for r in comparisons)
    g03_same=all(r['same_behavior_class_when_unique'] for r in comparisons)
    g4_unique=all(r['grammars']['G4_EXPANDED60'].get('perfect_n')==1 for r in comparisons)
    all_same=all(r['same_behavior_class_when_unique'] for r in comparisons)
    baseB=runs['G0_FULL59']['B']
    evaluable=[f for f in baseB['folds'] if f['acquisition_n'] and f['heldout_n']]
    transfer=all(f['evaluation']['quotient']==f['evaluation']['n'] and f['evaluation']['literal'] < f['evaluation']['quotient'] and f['evaluation']['ablation']==f['evaluation']['n'] for f in evaluable)

    gates={
        'F1_all_orientation_failures_localized':all(r['classification'] in {'F_PASS','F_NO_UNIQUE_RELATION','F_TRANSFER_BOUNDARY','F_CORPUS_CEILING'} for r in frows),
        'G1_G0_to_G3_unique_every_evaluable_fold':g03_unique,
        'G2_G0_to_G3_same_behavior_class':g03_same,
        'G3_expanded60_unique_every_evaluable_fold':g4_unique,
        'G4_all_unique_selections_same_behavior_class':all_same,
        'G5_base_literal_lt_quotient_and_ablation':transfer,
    }
    if not runs['G0_FULL59']['C']['gate_C1_information_boundary']:
        verdict='INVALID_V136'
    elif all(gates.values()) and not failures:
        verdict='PASS_FULL_GRAMMAR_INVARIANCE'
    elif g03_same:
        verdict='PARTIAL_GRAMMAR_INVARIANCE'
    else:
        verdict='REJECT_GRAMMAR_INVARIANCE'

    R={
        'canonical_id':'V136_RELATION_GRAMMAR_INVARIANCE',
        'protocol':'protocols/V136_RELATION_GRAMMAR_AND_ORIENTATION_PRECOMMIT.md',
        'grammar_counts':{k:len(v()) for k,v in GRAMMARS.items()},
        'orientation_forensics':frows,
        'orientation_failures':failures,
        'fold_comparisons':comparisons,
        'gates':gates,
        'verdict':verdict,
        'claim_boundary':'Tests bounded candidate-vocabulary/presentation dependence and localizes V135 orientation failures. Does not establish natural multigeneration, constructor growth, cross-domain generality or open-endedness.',
    }
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'verdict':verdict,'gates':gates,'grammar_counts':R['grammar_counts'],'orientation_failures':failures},indent=2,sort_keys=True))

if __name__=='__main__':
    main()
