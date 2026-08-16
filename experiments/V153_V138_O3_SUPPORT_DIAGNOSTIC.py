from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

OUT = Path('artifacts/v153_v138_o3_support_diagnostic')
OUT.mkdir(parents=True, exist_ok=True)

P138 = Path(__file__).with_name('V138_NATURAL_DEVELOPMENTAL_ACCELERATION.py')
spec = importlib.util.spec_from_file_location('v138', P138)
v138 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(v138)

EXPECTED_COMMIT = '4257f44b0ff1181dedaedee6a447e133219fcebf'
EXPECTED_PROGRAMS = 17
EXPECTED_SITES = 24
EXPECTED_VERIFIER_CALLS = 281
EXPECTED_LABEL_COUNTS = {'RELAX_SAFE': 8, 'RELAX_SENSITIVE': 16}


def label(r):
    return 'RELAX_SENSITIVE' if r['canonical_relax_sensitive'] else 'RELAX_SAFE'


def program_support(rows):
    out = []
    for program in sorted({r['program'] for r in rows}):
        rr = [r for r in rows if r['program'] == program]
        counts = Counter(label(r) for r in rr)
        out.append({
            'program': program,
            'sha256': hashlib.sha256(program.encode()).hexdigest(),
            'sites': len(rr),
            'label_counts': dict(sorted(counts.items())),
            'single_program_o3_evaluable': len(counts) >= 2,
        })
    return out


def paired_groups(programs):
    ordered = sorted(programs, key=lambda p: (hashlib.sha256(p.encode()).hexdigest(), p))
    return [ordered[i:i+2] for i in range(0, len(ordered), 2)]


def paired_scope_test(rows):
    programs = sorted({r['program'] for r in rows})
    groups = paired_groups(programs)
    folds = []
    for idx, hold in enumerate(groups):
        holdset = set(hold)
        ac = [r for r in rows if r['program'] not in holdset]
        ht = [r for r in rows if r['program'] in holdset]
        counts = Counter(label(r) for r in ht)
        fold = {
            'fold': idx,
            'holdout_programs': hold,
            'heldout_n': len(ht),
            'heldout_label_counts': dict(sorted(counts.items())),
            'evaluable': len(counts) >= 2,
        }
        if not fold['evaluable']:
            folds.append(fold)
            continue
        sel = v138.best_scope_rule(ac)
        if sel is None:
            fold['evaluable'] = False
            fold['reason'] = 'no_train_rule'
            folds.append(fold)
            continue
        pred = [v138.predict_rule(sel['rule'], r) for r in ht]
        y = [r['canonical_relax_sensitive'] for r in ht]
        ba = v138.balanced_accuracy(y, pred)
        fold.update({
            'selected_rule': sel['id'],
            'train_ba': sel['train_ba'],
            'heldout_ba': ba,
        })
        folds.append(fold)
    vals = sorted(f['heldout_ba'] for f in folds if f.get('evaluable') and f.get('heldout_ba') is not None)
    median = vals[len(vals)//2] if vals else None
    return groups, folds, vals, median


def main():
    rows, calls, programs, head = v138.collect_natural_records()
    counts = dict(sorted(Counter(label(r) for r in rows).items()))
    replay_identity = {
        'commit': head == EXPECTED_COMMIT,
        'program_count': len(programs) == EXPECTED_PROGRAMS,
        'site_count': len(rows) == EXPECTED_SITES,
        'verifier_calls': calls == EXPECTED_VERIFIER_CALLS,
        'label_counts': counts == EXPECTED_LABEL_COUNTS,
    }

    support = program_support(rows)
    single_evaluable = sum(int(x['single_program_o3_evaluable']) for x in support)
    groups, folds, vals, median = paired_scope_test(rows) if all(replay_identity.values()) else ([], [], [], None)

    if not all(replay_identity.values()):
        verdict = 'R10_V138_REPLAY_IDENTITY_MISMATCH'
    elif len(vals) < 8:
        verdict = 'CORPUS_CEILING_V153_PAIRED_SUPPORT'
    elif single_evaluable == 0 and median is not None and median >= 0.75:
        verdict = 'PASS_V153_SINGLE_PROGRAM_SUPPORT_OBSTRUCTION'
    elif median is not None and median < 0.75:
        verdict = 'NEGATIVE_V153_O3_RULE_LANGUAGE_UNDER_PAIRED_SUPPORT'
    else:
        verdict = 'DIAGNOSTIC_V153_NONCANONICAL_SUPPORT_PATTERN'

    result = {
        'canonical_id': 'V153_V138_O3_SUPPORT_DIAGNOSTIC',
        'protocol': 'protocols/V153_V138_O3_SUPPORT_DIAGNOSTIC_PRECOMMIT.md',
        'apparatus_addendum': 'protocols/V153A_V138_RUNTIME_APPARATUS_ADDENDUM.md',
        'external_commit_expected': EXPECTED_COMMIT,
        'external_commit_observed': head,
        'v138_replay_identity': replay_identity,
        'verifier_calls': calls,
        'program_count': len(programs),
        'site_count': len(rows),
        'global_label_counts': counts,
        'program_support': support,
        'single_program_evaluable': single_evaluable,
        'pair_order_method': 'SHA256(program_name) ascending; consecutive pairs',
        'paired_groups': groups,
        'paired_folds': folds,
        'paired_evaluable': len(vals),
        'paired_median_heldout_ba': median,
        'verdict': verdict,
        'claim_boundary': 'Diagnostic only. A PASS identifies V138 single-program holdout support as the obstruction and licenses external-corpus expansion; it does not admit O3 or upgrade Q8/Q10.',
    }
    (OUT/'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({
        'verdict': verdict,
        'v138_replay_identity': replay_identity,
        'program_count': len(programs),
        'site_count': len(rows),
        'global_label_counts': counts,
        'single_program_evaluable': single_evaluable,
        'paired_evaluable': len(vals),
        'paired_median_heldout_ba': median,
        'paired_groups': groups,
    }, indent=2, sort_keys=True))
    if verdict.startswith('R10_'):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
