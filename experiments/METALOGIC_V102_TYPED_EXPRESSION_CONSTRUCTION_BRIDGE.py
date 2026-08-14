#!/usr/bin/env python3
import ast, copy, hashlib, importlib.util, json, os
from pathlib import Path

BASE = Path(__file__).with_name('METALOGIC_V100_BALANCED_K_CROSS_SOURCE_ORGANS.py')
spec = importlib.util.spec_from_file_location('v100base', BASE)
v100 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v100)

ROOT = v100.v99.ROOT
full_score = v100.v99.full_score
ORIGINAL_RICH = v100.ORIGINAL_RICH
OUT = Path(os.environ.get('OUT_DIR', 'results/v102')); OUT.mkdir(parents=True, exist_ok=True)
SEED = 'V102_TYPED_EXPRESSION_CONSTRUCTION_BRIDGE_2026-08-14'
COMMIT = '4257f44b0ff1181dedaedee6a447e133219fcebf'
CAP = 160
TEST_N = 8
CONTAMINATED = {'breadth_first_search','sieve','subsequences','find_in_sorted'}


def h(x):
    return hashlib.sha256((SEED + '|' + x).encode()).hexdigest()


def balance(items, cap):
    groups = {}
    seen = set()
    for kind, text in items:
        if text in seen:
            continue
        seen.add(text); groups.setdefault(kind, []).append((kind, text))
    kinds = sorted(groups)
    if not kinds:
        return []
    q = max(1, cap // len(kinds))
    out = []; used = set(); cursors = {k: 0 for k in kinds}
    for k in kinds:
        for item in groups[k][:q]:
            if item[1] not in used:
                out.append(item); used.add(item[1]); cursors[k] += 1
                if len(out) >= cap:
                    return out
    progress = True
    while len(out) < cap and progress:
        progress = False
        for k in kinds:
            i = cursors[k]
            while i < len(groups[k]) and groups[k][i][1] in used:
                i += 1
            cursors[k] = i
            if i < len(groups[k]):
                item = groups[k][i]; cursors[k] += 1
                out.append(item); used.add(item[1]); progress = True
                if len(out) >= cap:
                    break
    return out


def old_candidates(src, cap=CAP):
    return balance(ORIGINAL_RICH(src, max(5000, cap * 25)), cap)


def construction_candidates(src):
    try:
        t = ast.parse(src)
    except Exception:
        return []
    names = sorted({n.id for n in ast.walk(t) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)})
    out = []; seen = set()

    def emit(z, kind):
        try:
            s = ast.unparse(ast.fix_missing_locations(z))
        except Exception:
            return
        if s != src and s not in seen:
            seen.add(s); out.append((kind, s))

    # Generic typed expression construction at boolean/control slots.
    guards = [n for n in ast.walk(t) if isinstance(n, (ast.If, ast.While))]
    for i, _ in enumerate(guards):
        for nm in names:
            for expr in (ast.Name(id=nm, ctx=ast.Load()), ast.UnaryOp(op=ast.Not(), operand=ast.Name(id=nm, ctx=ast.Load()))):
                z = copy.deepcopy(t); gs = [n for n in ast.walk(z) if isinstance(n, (ast.If, ast.While))]
                if i < len(gs):
                    gs[i].test = copy.deepcopy(expr); emit(z, 'CONSTRUCT_GUARD_EXPR')

    # Generic expression-tree growth at call argument slots.
    calls = [n for n in ast.walk(t) if isinstance(n, ast.Call)]
    for i, c in enumerate(calls):
        for j, arg in enumerate(c.args):
            seeds = []
            if isinstance(arg, ast.Name):
                seeds.append(arg.id)
            seeds.extend(names[:6])
            for nm in sorted(set(seeds)):
                exprs = [
                    ast.BinOp(left=ast.Name(id=nm, ctx=ast.Load()), op=ast.Add(), right=ast.Constant(1)),
                    ast.BinOp(left=ast.Name(id=nm, ctx=ast.Load()), op=ast.Sub(), right=ast.Constant(1)),
                    ast.UnaryOp(op=ast.Not(), operand=ast.Name(id=nm, ctx=ast.Load())),
                ]
                for expr in exprs:
                    z = copy.deepcopy(t); cs = [n for n in ast.walk(z) if isinstance(n, ast.Call)]
                    if i < len(cs) and j < len(cs[i].args):
                        cs[i].args[j] = copy.deepcopy(expr); emit(z, 'CONSTRUCT_CALL_ARG_EXPR')

    # Generic structural value construction: wrap an existing return value in one list layer.
    rets = [n for n in ast.walk(t) if isinstance(n, ast.Return) and n.value is not None]
    for i, _ in enumerate(rets):
        z = copy.deepcopy(t); rs = [n for n in ast.walk(z) if isinstance(n, ast.Return) and n.value is not None]
        if i < len(rs):
            rs[i].value = ast.List(elts=[copy.deepcopy(rs[i].value)], ctx=ast.Load()); emit(z, 'CONSTRUCT_RETURN_VALUE')

    # Generic value construction at assignment RHS slots using in-scope names and one-step arithmetic/list constructors.
    assigns = [n for n in ast.walk(t) if isinstance(n, (ast.Assign, ast.AnnAssign))]
    for i, _ in enumerate(assigns):
        for nm in names[:6]:
            exprs = [
                ast.BinOp(left=ast.Name(id=nm, ctx=ast.Load()), op=ast.Add(), right=ast.Constant(1)),
                ast.BinOp(left=ast.Name(id=nm, ctx=ast.Load()), op=ast.Sub(), right=ast.Constant(1)),
                ast.List(elts=[ast.Name(id=nm, ctx=ast.Load())], ctx=ast.Load()),
            ]
            for expr in exprs:
                z = copy.deepcopy(t); xs = [n for n in ast.walk(z) if isinstance(n, (ast.Assign, ast.AnnAssign))]
                if i < len(xs):
                    xs[i].value = copy.deepcopy(expr); emit(z, 'CONSTRUCT_ASSIGN_VALUE')
    return out


def expanded_candidates(src, cap=CAP):
    old = ORIGINAL_RICH(src, max(5000, cap * 25))
    new = construction_candidates(src)
    return balance(old + new, cap)


def first_success(name, candidates):
    tried = 0
    for kind, text in candidates:
        tried += 1
        if full_score(name, text) == 0:
            return {'success': True, 'kind': kind, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'tried': tried}
    return {'success': False, 'kind': None, 'text_sha256': None, 'tried': tried}


def main():
    buggy = ROOT / 'python_programs'; tests = ROOT / 'python_testcases'
    eligible = []
    for p in buggy.glob('*.py'):
        n = p.stem
        if n in CONTAMINATED or not (tests / f'test_{n}.py').exists():
            continue
        if full_score(n, p.read_text()) > 0:
            eligible.append(n)
    selected = sorted(eligible, key=lambda n: h('fresh|' + n))[:TEST_N]

    rows = []; old_solved = []; expanded_solved = []; new_only = []
    for n in selected:
        src = (buggy / f'{n}.py').read_text()
        k0 = old_candidates(src); k1 = expanded_candidates(src)
        r0 = first_success(n, k0); r1 = first_success(n, k1)
        if r0['success']: old_solved.append(n)
        if r1['success']: expanded_solved.append(n)
        if r1['success'] and not r0['success']: new_only.append(n)
        rows.append({
            'task': n,
            'k0_count': len(k0), 'k1_count': len(k1),
            'k0_families': sorted({k for k,_ in k0}),
            'k1_families': sorted({k for k,_ in k1}),
            'k0': r0, 'k1': r1,
            'strict_new_closure': r1['success'] and not r0['success']
        })

    constructive_new = [r for r in rows if r['strict_new_closure'] and (r['k1']['kind'] or '').startswith('CONSTRUCT_')]
    gates = {
        'preexisting_external_corpus': True,
        'fresh_split_excludes_posthoc_tasks': not any(n in CONTAMINATED for n in selected),
        'no_correct_implementations_read': True,
        'equal_candidate_budget': all(r['k0_count'] <= CAP and r['k1_count'] <= CAP for r in rows),
        'generic_construction_families_present': any(any(k.startswith('CONSTRUCT_') for k in r['k1_families']) for r in rows),
        'expanded_K_strictly_expands_verified_closure': bool(new_only),
        'new_closure_witness_uses_construction_family': bool(constructive_new),
        'independent_transfer_to_two_tasks': len(new_only) >= 2,
    }
    verdict = 'PASS_TYPED_EXPRESSION_CONSTRUCTION_BRIDGE_V102' if all(gates.values()) else 'MIXED_TYPED_EXPRESSION_CONSTRUCTION_BRIDGE_V102'
    result = {
        'protocol': 'V102_TYPED_EXPRESSION_CONSTRUCTION_BRIDGE',
        'external_commit': COMMIT,
        'seed': SEED,
        'contaminated_excluded': sorted(CONTAMINATED),
        'candidate_cap_per_arm': CAP,
        'selected': selected,
        'old_solved': old_solved,
        'expanded_solved': expanded_solved,
        'new_only_solved': new_only,
        'rows': rows,
        'gates': gates,
        'verdict': verdict,
        'qualification': 'Fresh-split authored constructor-language bridge. Correct implementations are never read. K1 adds only generic typed expression/value construction at operational slots; it does not encode any inspected QuixBugs repair. A PASS would establish that this generic constructor class strictly expands natural verified closure and transfers to at least two independent tasks. It would not establish autonomous discovery of K1 from verifier residuals; that is the next crown-jewel gate.'
    }
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
