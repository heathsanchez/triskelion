"""IKKF V2B: execute the frozen V2 routing harness with only the heldout
programs that V2's pre-neural semantic census showed valid for BOTH C and J.
No neural V2 outcome existed.  Keep every other V2 mechanism/budget unchanged.
"""
from pathlib import Path
import hashlib

parent = Path('experiments/IKKF_V2_CAPABILITY_ROUTING.py')
src = parent.read_text()
parent_sha = hashlib.sha256(src.encode()).hexdigest()
print('V2_PARENT_SHA256', parent_sha, flush=True)

old = "HELD_PROGS=['possible_change','quicksort','sieve','subsequences']"
new = "HELD_PROGS=['possible_change','sieve','subsequences']"
assert old in src and src.count(old) == 1
src = src.replace(old, new)

src = src.replace("OUT=Path('artifacts/ikkf_v2_capability_routing')", "OUT=Path('artifacts/ikkf_v2b_capability_routing')")
src = src.replace("protocols/IKKF_V2_CAPABILITY_ROUTING_PRECOMMIT.txt", "protocols/IKKF_V2B_CAPABILITY_ROUTING_PRECOMMIT.txt")
src = src.replace("ikkf-v2-B0", "ikkf-v2b-B0")
src = src.replace("ikkf-v2-CJ", "ikkf-v2b-CJ")
src = src.replace("ikkf-v2-SHUFFLE", "ikkf-v2b-SHUFFLE")
src = src.replace("ikkf-v2-reload", "ikkf-v2b-reload")
src = src.replace("PASS_IKKF_V2_CAPABILITY_ROUTING", "PASS_IKKF_V2B_CAPABILITY_ROUTING")
src = src.replace("FAIL_IKKF_V2_CAPABILITY_ROUTING", "FAIL_IKKF_V2B_CAPABILITY_ROUTING")

compile(src, 'IKKF_V2B_DERIVED_FROM_FROZEN_V2', 'exec')
exec(compile(src, 'IKKF_V2B_DERIVED_FROM_FROZEN_V2', 'exec'), {'__name__': '__main__'})
