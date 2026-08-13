import ast, hashlib, json, random
from dataclasses import dataclass
from pathlib import Path

OUT = Path('artifacts/scope_revision_ratchet_v35')
OUT.mkdir(parents=True, exist_ok=True)
SEED = 'V35_SCOPE_REVISION_20260814'
RNG = random.Random(SEED)

# Bounded executable micro-world.  The repair operator is intentionally useful in one
# structural context and harmful in another.  The learner sees only source + verifier
# outcomes and must revise an initially over-broad retained rule to a scoped hypothesis.
# This tests Bill Bao's scope/reversibility criterion; it is NOT claimed as an external
# source-distinct operator-invention result.

@dataclass(frozen=True)
class Case:
    family: str
    mode: str       # inclusive or exclusive semantics (used only by verifier)
    n: int
    source: str
    expected: tuple
    rank: str


def mk_source(family, mode, n, broken=False):
    # Structural contexts differ without an explicit mode marker in the executable body.
    # threshold-family uses a direct comparison; scan-family embeds the comparison in a loop.
    if family == 'threshold':
        op = '<' if (mode == 'inclusive' and broken) else '<=' if mode == 'inclusive' else '<'
        return f'def f(x, limit):\n    return x {op} limit\n'
    if family == 'scan':
        # Exclusive scan is valid with <. Inclusive scan is deliberately mutated to <.
        op = '<' if (mode == 'exclusive' or broken) else '<='
        return ('def f(xs, limit):\n'
                '    out = []\n'
                '    for x in xs:\n'
                f'        if x {op} limit:\n'
                '            out.append(x)\n'
                '    return out\n')
    raise ValueError(family)


def verifier(case, source):
    ns = {}
    try:
        exec(compile(source, '<candidate>', 'exec'), ns, ns)
        fn = ns['f']
    except Exception:
        return False
    lim = case.n
    if case.family == 'threshold':
        probes = [lim-1, lim, lim+1]
        got = tuple(fn(x, lim) for x in probes)
        exp = tuple(x <= lim if case.mode == 'inclusive' else x < lim for x in probes)
    else:
        xs = [lim-1, lim, lim+1]
        got = tuple(fn(xs, lim))
        exp = tuple(x for x in xs if (x <= lim if case.mode == 'inclusive' else x < lim))
    return got == exp


def context_of_compare(tree):
    parents = {}
    for p in ast.walk(tree):
        for c in ast.iter_child_nodes(p):
            parents[id(c)] = p
    comps = [n for n in ast.walk(tree) if isinstance(n, ast.Compare) and len(n.ops) == 1]
    if not comps:
        return None
    n = comps[0]
    cur = n
    while id(cur) in parents:
        p = parents[id(cur)]
        if isinstance(p, ast.If):
            return 'IF_TEST'
        if isinstance(p, ast.Return):
            return 'RETURN'
        cur = p
    return 'OTHER'


def apply_flip_lt_le(source, scope='ANY'):
    tree = ast.parse(source)
    ctx = context_of_compare(tree)
    if scope != 'ANY' and ctx != scope:
        return source
    done = False
    class T(ast.NodeTransformer):
        def visit_Compare(self, n):
            nonlocal done
            self.generic_visit(n)
            if not done and len(n.ops) == 1 and isinstance(n.ops[0], ast.Lt):
                n.ops[0] = ast.LtE(); done = True
            return n
    T().visit(tree); ast.fix_missing_locations(tree)
    return ast.unparse(tree) + '\n'


def make_case(family, mode, n, broken):
    src = mk_source(family, mode, n, broken=broken)
    ident = f'{family}|{mode}|{n}|{broken}'
    return Case(family, mode, n, src, (), hashlib.sha256((SEED+'|'+ident).encode()).hexdigest())

# Positive repair episodes: inclusive semantics with a strict-inequality mutation.
positives = [make_case(f, 'inclusive', n, True) for f in ('threshold','scan') for n in range(2, 22)]
# Protected valid behaviours: exclusive semantics already correct with strict inequality.
negatives = [make_case(f, 'exclusive', n, False) for f in ('threshold','scan') for n in range(2, 22)]
positives.sort(key=lambda c:c.rank); negatives.sort(key=lambda c:c.rank)

# Precommitted developmental stream deliberately starts with one structural family, so an
# unscoped repair appears locally successful; later protected cases expose over-generalization.
train_pos = [c for c in positives if c.family == 'scan'][:8]
revision_neg = [c for c in negatives if c.family == 'threshold'][:8]
held_pos = [c for c in positives if c.family == 'scan'][8:]
held_neg = [c for c in negatives if c.family == 'threshold'][8:]
# Cross-family challenge ensures scope is structural, not instance memorisation.
cross_pos = [c for c in positives if c.family == 'threshold'][:6]
cross_neg = [c for c in negatives if c.family == 'scan'][:6]

# Gate 1: old/no-operator state cannot repair positive cases.
old_fail = all(not verifier(c, c.source) for c in train_pos)
# Local success causes provisional ANY retention.
local_any = all(verifier(c, apply_flip_lt_le(c.source, 'ANY')) for c in train_pos)
# Counterevidence: ANY damages valid protected behaviour.
any_breaks = [c for c in revision_neg if verifier(c, c.source) and not verifier(c, apply_flip_lt_le(c.source, 'ANY'))]

# Fixed scope grammar; select the broadest verified hypothesis that repairs positives while
# preserving all counterexamples.  Context predicates are computed from AST only.
SCOPES = ['ANY','IF_TEST','RETURN']
def score(scope, pos, neg):
    p = sum(verifier(c, apply_flip_lt_le(c.source, scope)) for c in pos)
    n = sum(verifier(c, apply_flip_lt_le(c.source, scope)) for c in neg)
    return p, n
survivors=[]
for s in SCOPES:
    p,n=score(s,train_pos,revision_neg)
    if p==len(train_pos) and n==len(revision_neg): survivors.append(s)
# Unique minimal revision expected to IF_TEST because scan comparison is inside an If,
# while threshold comparison is directly inside Return.
revised = survivors[0] if len(survivors)==1 else None

# Held-out evaluation and causal ablation of revision machinery.
held_scoped = score(revised, held_pos, held_neg) if revised else (0,0)
held_fossil = score('ANY', held_pos, held_neg)
# Nearby opposite-family challenges test and expose the learned scope boundary.
cross_scoped = score(revised, cross_pos, cross_neg) if revised else (0,0)

# Explicit revocation/narrowing rule: any protected regression forbids promotion at that scope;
# if no narrower grammar member survives, revoke the operator.
def revision_decision(scope, pos, neg):
    p,n=score(scope,pos,neg)
    if p==len(pos) and n==len(neg): return {'action':'KEEP','scope':scope}
    narrower=[]
    for s in SCOPES:
        if s==scope: continue
        pp,nn=score(s,pos,neg)
        if pp==len(pos) and nn==len(neg): narrower.append(s)
    if len(narrower)==1:return {'action':'NARROW','from':scope,'to':narrower[0]}
    return {'action':'REVOKE','from':scope,'reason':'no unique scope preserves positives and protected behaviours'}

revision = revision_decision('ANY', train_pos, revision_neg)
# Contradict the scoped hypothesis with threshold positives as well: no single context-specific
# scope in the current grammar can cover both structural positive families while preserving both
# negative families, so the correct action is revocation rather than fossilisation.
revocation = revision_decision(revised or 'IF_TEST', train_pos+cross_pos, revision_neg+cross_neg)

R={
 'protocol':'V35 bounded executable scope/revision ratchet; fixed operator and fixed scope grammar',
 'seed':SEED,
 'operator':'FLIP_LT_TO_LE',
 'scope_grammar':SCOPES,
 'counts':{'train_pos':len(train_pos),'revision_neg':len(revision_neg),'held_pos':len(held_pos),'held_neg':len(held_neg),'cross_pos':len(cross_pos),'cross_neg':len(cross_neg)},
 'local':{'old_positive_fail':old_fail,'provisional_any_repairs_all':local_any,'protected_regressions_under_any':len(any_breaks)},
 'scope_search':{'survivors':survivors,'selected':revised,'scores':{s:{'positive':score(s,train_pos,revision_neg)[0],'protected':score(s,train_pos,revision_neg)[1]} for s in SCOPES}},
 'heldout':{'scoped_positive':held_scoped[0],'scoped_protected':held_scoped[1],'fossil_positive':held_fossil[0],'fossil_protected':held_fossil[1]},
 'cross_family':{'scoped_positive':cross_scoped[0],'scoped_protected':cross_scoped[1]},
 'revision_decision':revision,
 'contradictory_evidence_decision':revocation,
}
R['gates']={
 'old_language_fails_trigger_family':old_fail,
 'locally_successful_operator_is_provisionally_useful':local_any,
 'unscoped_operator_excludes_valid_behaviour':len(any_breaks)==len(revision_neg) and len(any_breaks)>0,
 'unique_scope_is_discovered':revised=='IF_TEST',
 'scoped_operator_transfers_on_heldout':held_scoped==(len(held_pos),len(held_neg)),
 'revision_ablation_fossilizes_bad_rule':held_fossil[0]==len(held_pos) and held_fossil[1]<len(held_neg),
 'system_narrows_on_counterevidence':revision.get('action')=='NARROW' and revision.get('to')=='IF_TEST',
 'system_revokes_when_scope_grammar_cannot_reconcile_evidence':revocation.get('action')=='REVOKE',
}
R['verdict']='PASS_SCOPE_REVISION_RATCHET_V35' if all(R['gates'].values()) else 'MIXED_SCOPE_REVISION_RATCHET_V35'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
print(json.dumps(R,indent=2))