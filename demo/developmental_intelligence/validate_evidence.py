#!/usr/bin/env python3
import json
from pathlib import Path

P = Path(__file__).with_name('evidence_pack.json')
data = json.loads(P.read_text())
assert data['schema'] == 'METALOGIC_DI_DEMO_EVIDENCE_V1'
records = {r['id']: r for r in data['records']}

v161 = records['V161_AST_ROLE_RESCUE']['result']
assert v161 == {
    'neural_only': '8/16',
    'raw_verified_memory': '8/16',
    'compiled_structural_map': '16/16',
    'shuffled_map': '0/16',
}

arena = records['LEAN_KERNEL_ARENA_REPRESENTATION_GROWTH']['result']
assert arena['full_suite_before'] == '152/161'
assert arena['full_suite_after'] == '161/161'
assert arena['arbitrary_id_valid_before'] == '0/256'
assert arena['arbitrary_id_valid_after'] == '256/256'
assert arena['malformed_rejected'] == '512/512'
assert arena['ablation_valid_fail_again'] == '32/32'
assert arena['false_accepts'] == 0
assert arena['regressions'] == 0

v54 = records['V54_TWO_GENERATION_COMPOUNDING']
assert v54['run'] == '31761530951'
assert v54['result']['before_O1'] == 'O2 not discoverable'
assert v54['result']['after_O1'] == 'O2 discoverable'
assert v54['result']['final_target_requires'] == ['O1', 'O2']

ikkf = records['IKKF_PORTABLE_CAPABILITY_V1']['result']
assert ikkf['baseline_AB_TEST'] == 0.0
assert ikkf['compiled_AB_TEST'] == 1.0
assert ikkf['uninstall_AB_TEST'] == 0.0
assert ikkf['recompiled_AB_TEST'] == 1.0

print('PASS_METALOGIC_DI_EVIDENCE_PACK_V1')
