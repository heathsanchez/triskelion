import json
import subprocess
from pathlib import Path

OUT = Path('artifacts/v39')
OUT.mkdir(parents=True, exist_ok=True)
SCOPES = ['ANY', 'IF_TEST']

DJ = Path('/tmp/v39_django')
RQ = Path('/tmp/v39_requests')
CK = Path('/tmp/v39_click')


def sh(cmd, cwd, timeout=30):
    p = subprocess.run(cmd, cwd=cwd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return p.returncode == 0, p.stdout[-4000:]


def reset(repo):
    subprocess.run('git reset --hard -q HEAD && git clean -fdq', cwd=repo, shell=True, check=True)


def replace(path, old, new):
    s = path.read_text()
    if old not in s:
        raise RuntimeError(f'pattern not found in {path}: {old}')
    path.write_text(s.replace(old, new, 1))


def django_truncate_test():
    return sh('python tests/runtests.py backends.test_utils.TestUtils.test_truncate_name --verbosity 0', DJ)


def django_password_test():
    return sh('python tests/runtests.py auth_tests.test_validators.MinimumLengthValidatorTest.test_validate --verbosity 0', DJ)


def requests_slice_test():
    return sh('pytest -q tests/test_utils.py -k test_iter_slices', RQ, timeout=20)


def click_count_test():
    return sh('pytest -q tests/test_options.py::test_counting', CK)


def seed_trigger_bug():
    p = DJ / 'django/db/backends/utils.py'
    replace(p, 'len(name) <= length', 'len(name) < length')


def seed_transfer_bug():
    p = RQ / 'src/requests/utils.py'
    replace(p, 'slice_length <= 0', 'slice_length < 0')


def apply_trigger(scope):
    # Target comparison is structurally inside an ast.If test.
    if scope in ('ANY', 'IF_TEST'):
        p = DJ / 'django/db/backends/utils.py'
        replace(p, 'len(name) < length', 'len(name) <= length')


def apply_transfer(scope):
    # Target comparison is structurally inside an ast.If test.
    if scope in ('ANY', 'IF_TEST'):
        p = RQ / 'src/requests/utils.py'
        replace(p, 'slice_length < 0', 'slice_length <= 0')


def apply_click_protected(scope):
    # This strict comparator is a first-class comparator value, not an ast.If test.
    if scope == 'ANY':
        p = CK / 'src/click/types.py'
        replace(p, 'operator.le if self.min_open else operator.lt', 'operator.le if self.min_open else operator.le')


def apply_password_counterexample(scope):
    # This is a genuine strict comparison inside an ast.If test.
    if scope in ('ANY', 'IF_TEST'):
        p = DJ / 'django/contrib/auth/password_validation.py'
        replace(p, 'if len(password) < self.min_length:', 'if len(password) <= self.min_length:')


R = {
    'protocol': 'V39_SINGLE_LOOP_BEHAVIORAL_SCOPE_REVISION_20260814',
    'operator': 'LT_TO_LTE',
    'scope_grammar': SCOPES,
    'authority': 'independently authored repository tests at fixed commits',
    'events': [],
}

# 0. Verify all external baselines before introducing any mutation.
reset(DJ); reset(RQ); reset(CK)
b0, _ = django_truncate_test(); b1, _ = requests_slice_test(); b2, _ = click_count_test(); b3, _ = django_password_test()
R['baseline'] = {'django_trigger': b0, 'requests_transfer': b1, 'click_protected': b2, 'django_counterexample': b3}

# 1. External obstruction: the frozen old state cannot repair the seeded trigger.
reset(DJ); seed_trigger_bug()
old_ok, old_log = django_truncate_test()
R['old_state_trigger_passes'] = old_ok
R['events'].append({'stage': 'obstruction', 'repo': 'django', 'test_pass': old_ok, 'log_tail': old_log[-700:]})

# 2. Search the frozen scope grammar using only trigger repair + protected behavior.
scope_scores = {}
survivors = []
for scope in SCOPES:
    reset(DJ); reset(CK)
    seed_trigger_bug(); apply_trigger(scope)
    pos_ok, _ = django_truncate_test()
    apply_click_protected(scope)
    prot_ok, _ = click_count_test()
    scope_scores[scope] = {'trigger_repaired': pos_ok, 'protected_preserved': prot_ok}
    if pos_ok and prot_ok:
        survivors.append(scope)
selected = survivors[0] if len(survivors) == 1 else None
R['scope_search'] = {'scores': scope_scores, 'survivors': survivors, 'selected': selected}

# 3. Source-distinct transfer is evaluated only after scope selection.
reset(RQ); seed_transfer_bug()
transfer_old_ok, transfer_old_log = requests_slice_test()
if selected:
    apply_transfer(selected)
transfer_new_ok, transfer_new_log = requests_slice_test()
R['transfer'] = {
    'repo': 'requests',
    'mutated_old_state_passes': transfer_old_ok,
    'selected_scope_passes': transfer_new_ok,
    'old_log_tail': transfer_old_log[-700:],
    'new_log_tail': transfer_new_log[-700:],
}

# 4. Later counterevidence arrives after retention/transfer.
reset(DJ)
contra_baseline_ok, _ = django_password_test()
if selected:
    apply_password_counterexample(selected)
contra_after_ok, contra_log = django_password_test()
R['later_counterevidence'] = {
    'repo': 'django',
    'different_module_and_test_family': True,
    'baseline_passes': contra_baseline_ok,
    'retained_scope_preserves_behavior': contra_after_ok,
    'log_tail': contra_log[-900:],
}

# 5. Re-evaluate every scope against the accumulated behavioral evidence.
post_scores = {}
post_survivors = []
for scope in SCOPES:
    # Positive trigger.
    reset(DJ); seed_trigger_bug(); apply_trigger(scope)
    p1, _ = django_truncate_test()
    # Source-distinct positive transfer.
    reset(RQ); seed_transfer_bug(); apply_transfer(scope)
    p2, _ = requests_slice_test()
    # Protected Click behavior.
    reset(CK); apply_click_protected(scope)
    p3, _ = click_count_test()
    # Later strict-IF counterexample.
    reset(DJ); apply_password_counterexample(scope)
    p4, _ = django_password_test()
    post_scores[scope] = {'trigger': p1, 'transfer': p2, 'protected': p3, 'counterexample': p4}
    if p1 and p2 and p3 and p4:
        post_survivors.append(scope)

if selected is None:
    decision = 'WITHHOLD'
elif not post_survivors:
    decision = 'REVOKE'
elif selected in post_survivors:
    decision = 'KEEP'
else:
    decision = 'REVISE'
R['revision'] = {'scores': post_scores, 'survivors': post_survivors, 'decision': decision}

R['gates'] = {
    'external_baselines_pass': all(R['baseline'].values()),
    'old_state_fails_trigger': not old_ok,
    'unique_scope_selected_from_behavior': selected == 'IF_TEST',
    'broad_scope_rejected_by_protected_behavior': scope_scores.get('ANY', {}).get('protected_preserved') is False,
    'source_distinct_old_state_fails': not transfer_old_ok,
    'selected_scope_transfers_semantically': transfer_new_ok,
    'later_behavioral_counterevidence_falsifies_scope': contra_baseline_ok and not contra_after_ok,
    'accumulated_evidence_eliminates_all_current_scopes': post_survivors == [],
    'system_revokes_from_behavioral_evidence': decision == 'REVOKE',
}
R['verdict'] = 'PASS_V39_SINGLE_LOOP_BEHAVIORAL_SCOPE_REVISION' if all(R['gates'].values()) else 'FAIL_V39_SINGLE_LOOP_BEHAVIORAL_SCOPE_REVISION'
R['claim_boundary'] = 'One frozen orchestrator chooses scope and revision from fixed external repository-test outcomes. Evidence units and two-element scope grammar are precommitted; this is not open-ended scope-language invention.'

(OUT / 'RESULT.json').write_text(json.dumps(R, indent=2))
print(json.dumps(R, indent=2))
if R['verdict'].startswith('FAIL'):
    raise SystemExit(1)
