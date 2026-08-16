from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

OUT = Path('artifacts/v137_semantic_quotient_recovery')
OUT.mkdir(parents=True, exist_ok=True)

# Import frozen V135 machinery.
TARGET135 = Path(__file__).with_name('V135_DEVELOPMENTAL_QUOTIENT_CAPSTONE.py')
spec135 = importlib.util.spec_from_file_location('v135', TARGET135)
m = importlib.util.module_from_spec(spec135)
assert spec135.loader is not None
spec135.loader.exec_module(m)

# Apparatus-only timeout handling inherited from V135B/V136.
_orig_verify = m.verify

def safe_verify(root, program, path, content, timeout=10):
    try:
        return _orig_verify(root, program, path, content, timeout=10)
    except subprocess.TimeoutExpired:
        return {'pass': False, 'failures': ('TIMEOUT',), 'returncode': 124}

m.verify = safe_verify

TOKENS = list(m.TOKENS)
DUAL = {'<':'>','>':'<','<=':'>=','>=':'<=','==':'==','!=':'!='}
ORIGINAL_GRAMMAR = m.candidate_grammar


def cid(swap, st, rt):
    return f'{"SWAP" if swap else "KEEP"}:{st}|{rt}'


def g4_expanded60():
    rows=[]
    for swap in (False, True):
        for st in TOKENS:
            for rt in TOKENS:
                if st == rt:
                    continue
                rows.append({
                    'swap': swap,
                    'strict_target': st,
                    'relaxed_target': rt,
                    'id': cid(swap, st, rt),
                })
    return rows


def semantic_class(c):
    if c['swap']:
        return (DUAL[c['strict_target']], DUAL[c['relaxed_target']])
    return (c['strict_target'], c['relaxed_target'])


def apply_rel(tok, x, y):
    if tok == '<': return x < y
    if tok == '>': return x > y
    if tok == '<=': return x <= y
    if tok == '>=': return x >= y
    if tok == '==': return x == y
    if tok == '!=': return x != y
    raise KeyError(tok)


def eval_candidate(c, x, y):
    if c['swap']:
        x, y = y, x
    return (
        apply_rel(c['strict_target'], x, y),
        apply_rel(c['relaxed_target'], x, y),
    )


def class_groups(candidates):
    groups = {}
    for c in candidates:
        groups.setdefault(semantic_class(c), []).append(c)
    return groups


def quotient_grammar30():
    expanded = g4_expanded60()
    groups = class_groups(expanded)
    g0_semantics = {
        (bool(c['swap']), c['strict_target'], c['relaxed_target'])
        for c in ORIGINAL_GRAMMAR()
    }
    out = []
    for cls in sorted(groups):
        members = groups[cls]
        # Fixed before outcomes: prefer a representative already admitted to
        # the V135 G0 syntactic support, then lexical ID.
        members = sorted(
            members,
            key=lambda c: (
                0 if (bool(c['swap']), c['strict_target'], c['relaxed_target']) in g0_semantics else 1,
                c['id'],
            )
        )
        out.append(dict(members[0], id='Q:'+members[0]['id']))
    return out


def perfect_classes(fold, candidates):
    by_id = {c['id']: c for c in candidates}
    classes = set()
    for pid in fold.get('perfect_ids', []):
        c = by_id[pid]
        classes.add(semantic_class(c))
    return classes


def main():
    expanded = g4_expanded60()
    groups = class_groups(expanded)

    # Stage A: exact quotient theorem check.
    a1 = (
        len(expanded) == 60
        and len(groups) == 30
        and all(len(v) == 2 for v in groups.values())
    )

    domain = [-2, -1, 0, 1, 2]
    equivalence_rows = []
    a2 = True
    for cls, members in sorted(groups.items()):
        identical = True
        for x in domain:
            for y in domain:
                vals = [eval_candidate(c, x, y) for c in members]
                if len(set(vals)) != 1:
                    identical = False
                    a2 = False
        equivalence_rows.append({
            'class': cls,
            'members': [c['id'] for c in members],
            'identical_on_exhaustive_domain': identical,
        })

    # Stage B1: expanded grammar, but judge acquisition uniqueness after quotienting.
    m.candidate_grammar = g4_expanded60
    B60, C60 = m.stratum_b_c()
    evaluable60 = [
        f for f in B60['folds']
        if f['acquisition_n'] and f['heldout_n']
    ]
    class_rows = []
    b1 = True
    for f in evaluable60:
        classes = perfect_classes(f, expanded)
        row = {
            'holdout_program': f['holdout_program'],
            'syntactic_perfect_n': f['perfect_n'],
            'syntactic_perfect_ids': f.get('perfect_ids', []),
            'semantic_perfect_n': len(classes),
            'semantic_classes': sorted(classes),
        }
        class_rows.append(row)
        if len(classes) != 1:
            b1 = False

    # Stage B2/B3: run same frozen natural stratum with one deterministic
    # representative per exact semantic class.
    m.candidate_grammar = quotient_grammar30
    B30, C30 = m.stratum_b_c()
    evaluable30 = [
        f for f in B30['folds']
        if f['acquisition_n'] and f['heldout_n']
    ]
    b2 = bool(evaluable30) and all(f['perfect_n'] == 1 for f in evaluable30)

    agg = B30['aggregate']
    heldout_ok = agg['heldout_n'] > 0 and agg['quotient'] / agg['heldout_n'] >= .90
    ablation_ok = agg['heldout_n'] > 0 and agg['ablation'] / agg['heldout_n'] >= .90
    reverse_ok = agg['reverse_n'] > 0 and agg['reverse_q'] / agg['reverse_n'] >= .90 and agg['reverse_ablation'] / agg['reverse_n'] >= .90
    b3 = heldout_ok and ablation_ok and reverse_ok

    # Stage C: does semantic quotienting also resolve V136's orientation failure?
    orientation_rows = []
    genuine_ambiguities = []
    for f in B30['orientation_folds']:
        if not (f['acquisition_n'] and f['heldout_n']):
            continue
        if f['perfect_n'] == 1:
            cls = 'C_REDUNDANCY_RESOLVED_OR_IDENTIFIED'
        else:
            cls = 'C_GENUINE_INFORMATION_AMBIGUITY'
            genuine_ambiguities.append({
                'direction': f['direction'],
                'holdout_program': f['holdout_program'],
                'perfect_n': f['perfect_n'],
            })
        orientation_rows.append({
            'direction': f['direction'],
            'holdout_program': f['holdout_program'],
            'acquisition_n': f['acquisition_n'],
            'heldout_n': f['heldout_n'],
            'perfect_n': f['perfect_n'],
            'selected': f['selected'],
            'evaluation': f['evaluation'],
            'classification': cls,
        })

    info_boundary = bool(C60['gate_C1_information_boundary'] and C30['gate_C1_information_boundary'])

    gates = {
        'A1_60_syntax_to_30_semantic_classes': a1,
        'A2_exact_extensional_equivalence': a2,
        'B1_every_expanded_fold_unique_at_class_level': b1,
        'B2_quotient30_unique_induction': b2,
        'B3_quotient30_transfer_ablation_reverse_reuse': b3,
        'C0_information_boundary': info_boundary,
    }

    if not info_boundary:
        verdict = 'INVALID_V137'
    elif a1 and a2 and b1 and b2 and b3:
        verdict = 'PASS_SEMANTIC_QUOTIENT_RECOVERY'
    elif a1 and a2:
        verdict = 'PARTIAL_SEMANTIC_QUOTIENT_RECOVERY'
    else:
        verdict = 'REJECT_SEMANTIC_QUOTIENT_HYPOTHESIS'

    R = {
        'canonical_id': 'V137_SEMANTIC_QUOTIENT_RECOVERY',
        'protocol': 'protocols/V137_SEMANTIC_QUOTIENT_RECOVERY_PRECOMMIT.md',
        'expanded_candidate_count': len(expanded),
        'semantic_class_count': len(groups),
        'equivalence_rows': equivalence_rows,
        'expanded_fold_classification': class_rows,
        'quotient30_candidate_count': len(quotient_grammar30()),
        'quotient30_aggregate': agg,
        'quotient30_gates_from_v135': B30['gates'],
        'orientation_after_quotient': orientation_rows,
        'genuine_orientation_ambiguities': genuine_ambiguities,
        'gates': gates,
        'verdict': verdict,
        'claim_boundary': 'Tests semantic quotient recovery of V136 syntactic ambiguity. Does not establish natural multigeneration, constructor growth, cross-domain generality or open-endedness.',
    }

    (OUT/'RESULT.json').write_text(json.dumps(R, indent=2, sort_keys=True)+'\n')
    print(json.dumps({
        'verdict': verdict,
        'gates': gates,
        'expanded_candidate_count': len(expanded),
        'semantic_class_count': len(groups),
        'quotient30_aggregate': agg,
        'genuine_orientation_ambiguities': genuine_ambiguities,
    }, indent=2, sort_keys=True))

    if not info_boundary:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
