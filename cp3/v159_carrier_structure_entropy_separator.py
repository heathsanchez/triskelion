#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import v157_opaque_envelope_label_semantics_separator as v157

v156 = v157.v156
v155 = v157.v155
exp = v157.exp
SEEDS = exp.SEEDS
MODEL = exp.MODEL
MAX_TOKENS = exp.MAX_TOKENS
STRUCTURAL = set('{}[],:"')


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def flatten_structure(s: str) -> str:
    return ''.join(' ' if ch in STRUCTURAL else ch for ch in s)


def collapse_letters(s: str) -> str:
    out = []
    for ch in s:
        if ch.isascii() and ch.isalpha():
            out.append('X' if ch.isupper() else 'x')
        else:
            out.append(ch)
    return ''.join(out)


def build_carriers(t1: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    _raw, _labelled, opaque, v157_construction = v157.make_memories(t1)
    carriers = {
        'STRUCTURED_HIGH': opaque,
        'FLAT_HIGH': flatten_structure(opaque),
        'STRUCTURED_LOW': collapse_letters(opaque),
        'FLAT_LOW': flatten_structure(collapse_letters(opaque)),
        'COLD': '',
    }
    noncold = [carriers[k] for k in ['STRUCTURED_HIGH','FLAT_HIGH','STRUCTURED_LOW','FLAT_LOW']]
    n = len(opaque)

    first_newline = opaque.find('\n')
    structured_high_json_parses = False
    if first_newline >= 0:
        try:
            json.loads(opaque[first_newline + 1:])
            structured_high_json_parses = True
        except Exception:
            pass

    def same_positions(src: str, dst: str, pred) -> bool:
        if len(src) != len(dst):
            return False
        return all((not pred(a)) or a == b for a, b in zip(src, dst))

    construction = {
        'v157_construction': v157_construction,
        'length': n,
        'lengths': {k: len(v) for k, v in carriers.items()},
        'sha256': {k: sha_text(v) for k, v in carriers.items()},
        'all_noncold_same_length': all(len(x) == n for x in noncold),
        'structured_high_json_parses': structured_high_json_parses,
        'flat_high_no_structural_chars': not any(ch in STRUCTURAL for ch in carriers['FLAT_HIGH']),
        'flat_low_no_structural_chars': not any(ch in STRUCTURAL for ch in carriers['FLAT_LOW']),
        'structured_low_alphabet_collapsed': all((not (ch.isascii() and ch.isalpha())) or ch in 'xX' for ch in carriers['STRUCTURED_LOW']),
        'flat_low_alphabet_collapsed': all((not (ch.isascii() and ch.isalpha())) or ch in 'xX' for ch in carriers['FLAT_LOW']),
        'structured_low_preserves_nonletters': same_positions(opaque, carriers['STRUCTURED_LOW'], lambda ch: not (ch.isascii() and ch.isalpha())),
        'flat_high_preserves_nonstructural': same_positions(opaque, carriers['FLAT_HIGH'], lambda ch: ch not in STRUCTURAL),
    }
    construction['ok'] = all([
        construction['all_noncold_same_length'],
        construction['structured_high_json_parses'],
        construction['flat_high_no_structural_chars'],
        construction['flat_low_no_structural_chars'],
        construction['structured_low_alphabet_collapsed'],
        construction['flat_low_alphabet_collapsed'],
        construction['structured_low_preserves_nonletters'],
        construction['flat_high_preserves_nonstructural'],
    ])
    return carriers, construction


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--bugsinpy', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit('output directory exists; refusing to overwrite evidence')
    args.out.mkdir(parents=True)

    result: dict[str, Any] = {
        'canonical_id': 'V159_CARRIER_STRUCTURE_ENTROPY_SEPARATOR',
        'protocol': 'protocols/V159_CARRIER_STRUCTURE_ENTROPY_SEPARATOR_PRECOMMIT.md',
        'model': MODEL,
        'max_tokens': MAX_TOKENS,
        'max_calls': exp.MAX_CALLS,
        'seeds': SEEDS,
        'T1': 'httpie/5',
        'T2': 'youtube-dl/32',
    }

    try:
        exp.verify_o1_identity()
        t1 = exp.v145.verify_acquisition_intervention(args.bugsinpy, *exp.T1)
        if t1.get('status') != 'VERIFIED' or t1.get('diff_sha256') != exp.EXPECTED_T1_DIFF_SHA256:
            raise RuntimeError('T1 intervention identity/replay mismatch')
        task = exp.prepare_t2(args.bugsinpy)
        if task.get('status') != 'READY':
            raise RuntimeError(f"T2 not READY: {task.get('status')}")
        carriers, construction = build_carriers(t1)
        result['control_construction'] = construction
        if not construction.get('ok'):
            result['verdict'] = 'R10_INCONCLUSIVE_V159_CONTROL_CONSTRUCTION'
            args.out.joinpath('V159_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
            print(json.dumps(result, indent=2, sort_keys=True))
            return
    except Exception as exc:
        result.update(verdict='R10_INCONCLUSIVE_V159_CONTROL_CONSTRUCTION', reason=f'{exc.__class__.__name__}: {exc}')
        args.out.joinpath('V159_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    provider = exp.Qwen35ChatRiverProvider(MODEL)
    order = ['COLD','STRUCTURED_HIGH','FLAT_HIGH','STRUCTURED_LOW','FLAT_LOW']
    rows: dict[str, list[dict[str, Any]]] = {k: [] for k in order}
    for seed in SEEDS:
        for arm in order:
            rows[arm].append(v155.run_seed_arm_synced(provider, args.bugsinpy, task, arm, seed, carriers[arm]))

    result['rows'] = rows
    result['summary'] = {k: exp.arm_summary(v) for k, v in rows.items()}
    per_arm: dict[str, Any] = {}
    for arm, arm_rows in rows.items():
        details = []
        success_n = 0
        for rr in arm_rows:
            ok, detail = v156.rival_execution_success(rr)
            success_n += int(ok)
            details.append({'seed': rr.get('seed'), 'success': ok, **detail})
        per_arm[arm] = {'success_n': success_n, 'n': len(arm_rows), 'details': details}
    result['rival_execution_capability'] = per_arm

    comparable = all(s.get('n_comparable') == len(SEEDS) for s in result['summary'].values())
    SH = per_arm['STRUCTURED_HIGH']['success_n']
    FH = per_arm['FLAT_HIGH']['success_n']
    SL = per_arm['STRUCTURED_LOW']['success_n']
    FL = per_arm['FLAT_LOW']['success_n']
    C = per_arm['COLD']['success_n']

    if not comparable:
        verdict = 'R10_INCONCLUSIVE_V159'
    elif SH < 2:
        verdict = 'OBSTRUCTED_V159_V157_EFFECT_NOT_REPLICATED'
    elif FH >= 2 and FL >= 2 and abs(SH - FH) <= 1:
        verdict = 'NEGATIVE_V159_JSON_STRUCTURE_NOT_REQUIRED'
    elif SL >= 2 and FL < 2 and FH >= 2:
        verdict = 'PASS_V159_STRUCTURE_ENTROPY_INTERACTION'
    elif SL >= 2 and FH < 2:
        verdict = 'PASS_V159_STRUCTURE_DOMINANT'
    elif FH >= 2 and SL < 2:
        verdict = 'PASS_V159_ENTROPY_DOMINANT'
    elif SL < 2 and FH < 2 and FL < 2 and SH >= 2:
        verdict = 'PASS_V159_STRUCTURE_AND_ENTROPY_JOINTLY_REQUIRED'
    else:
        verdict = 'OBSTRUCTED_V159_INTERMEDIATE_CARRIER_SEPARATION'

    result['primary'] = {
        'STRUCTURED_HIGH': SH,
        'FLAT_HIGH': FH,
        'STRUCTURED_LOW': SL,
        'FLAT_LOW': FL,
        'COLD': C,
        'task_solved_n': {a: s.get('solved_n') for a, s in result['summary'].items()},
    }
    result['verdict'] = verdict
    args.out.joinpath('V159_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'verdict': verdict, 'control_construction': construction, 'primary': result['primary']}, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
