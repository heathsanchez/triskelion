#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
import copy
import hashlib
import json

PROTOCOL = "ASSUMPTION_TOURNAMENT_V1"
PRECOMMIT_COMMIT = "b7b630d957454fbbd8bb0b78db051376e9be623f"
CARRIERS = (3, 4, 5)
OP_FAMILIES = ("ALL16", "SYMMETRIC", "ASYMMETRIC")
VERIFIERS = ("EXACT", "HALF", "POSITIVE")
BUDGETS = (8, 24, 48)
SEEDS = tuple(range(12))
ARMS = ("NONE", "D", "M", "I", "DM", "DI", "MI", "DMI")
SUCCESS_CONTRACTS = ("CURRENT", "DEPTH3", "DEPTH6", "RECOVERY")
PROTECTED_PROFILES = ("VALUE", "LINEAGE", "COUNTERFACTUAL", "ADAPTIVE")

def digest(*parts: object) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()

def bit(sem: int, row: int) -> int:
    return (sem >> row) & 1

def apply_table(table: int, left: int, right: int, rows: int) -> int:
    out = 0
    for r in range(rows):
        a = bit(left, r)
        b = bit(right, r)
        idx = a + 2 * b
        out |= ((table >> idx) & 1) << r
    return out

def table_symmetric(table: int) -> bool:
    return ((table >> 1) & 1) == ((table >> 2) & 1)

def table_essential(table: int) -> bool:
    left = any(((table >> (0 + 2*b)) & 1) != ((table >> (1 + 2*b)) & 1) for b in (0,1))
    right = any(((table >> (a + 0)) & 1) != ((table >> (a + 2)) & 1) for a in (0,1))
    return left and right

ESSENTIAL_TABLES = tuple(t for t in range(16) if table_essential(t))

def allowed_tables(family: str) -> tuple[int, ...]:
    if family == "ALL16":
        return tuple(range(16))
    if family == "SYMMETRIC":
        return tuple(t for t in range(16) if table_symmetric(t))
    if family == "ASYMMETRIC":
        return tuple(t for t in range(16) if not table_symmetric(t))
    raise ValueError(family)

def raw_sem(n: int, index: int) -> int:
    rows = 1 << n
    out = 0
    for r in range(rows):
        if (r >> index) & 1:
            out |= 1 << r
    return out

def raw_features(n: int) -> dict[str, int]:
    return {f"q{i}": raw_sem(n, i) for i in range(n)}

def full_rows(n: int) -> tuple[int, ...]:
    return tuple(range(1 << n))

def verifier_rows(mode: str, target: int, n: int, salt: str) -> tuple[int, ...]:
    rows = list(full_rows(n))
    if mode == "EXACT":
        return tuple(rows)
    if mode == "HALF":
        rows.sort(key=lambda r: digest(salt, "HALF", r))
        return tuple(sorted(rows[: max(1, len(rows)//2)]))
    if mode == "POSITIVE":
        return tuple(r for r in rows if bit(target, r) == 1)
    raise ValueError(mode)

def agrees_on_rows(proposal: int, target: int, rows: tuple[int, ...]) -> bool:
    return all(bit(proposal, r) == bit(target, r) for r in rows)

def observed_essential(target: int, left: int, right: int, rows: tuple[int, ...]) -> bool:
    left_matters = False
    right_matters = False
    data = [(bit(left,r), bit(right,r), bit(target,r)) for r in rows]
    for b in (0,1):
        y0 = {y for a,bb,y in data if bb == b and a == 0}
        y1 = {y for a,bb,y in data if bb == b and a == 1}
        if y0 and y1 and any(x != y for x in y0 for y in y1):
            left_matters = True
    for a in (0,1):
        y0 = {y for aa,b,y in data if aa == a and b == 0}
        y1 = {y for aa,b,y in data if aa == a and b == 1}
        if y0 and y1 and any(x != y for x in y0 for y in y1):
            right_matters = True
    return left_matters and right_matters

def fitting_tables(target: int, left: int, right: int, auth_rows: tuple[int,...], family: str, n: int) -> list[int]:
    rows = 1 << n
    out = []
    for t in allowed_tables(family):
        p = apply_table(t, left, right, rows)
        if agrees_on_rows(p, target, auth_rows):
            out.append(t)
    return out

def exact_sufficient_pairs(target: int, features: dict[str,int], n: int) -> list[tuple[str,str,int]]:
    rows = 1 << n
    auth = full_rows(n)
    out = []
    for a,b in combinations(sorted(features),2):
        for t in range(16):
            p = apply_table(t, features[a], features[b], rows)
            if p == target and observed_essential(target, features[a], features[b], auth):
                out.append((a,b,t))
                break
    return out

@dataclass(frozen=True)
class Episode:
    generation: int
    episode_id: str
    hidden_table: int
    target: int
    prev_id: str
    raw_id: str

@dataclass(frozen=True)
class Feature:
    feature_id: str
    semantics: int
    dependencies: tuple[str,...] = ()
    provenance: str = "primitive"

def relation_order(seed: str, generation: int, replacement: bool=False) -> list[int]:
    phase = "R" if replacement else "N"
    return sorted(ESSENTIAL_TABLES, key=lambda t: digest(seed, phase, generation, t))

def build_world(n: int, seed: str) -> list[Episode]:
    features = raw_features(n)
    prev_id = "q0"
    prev = features[prev_id]
    schedule = [f"q{(i % n)}" for i in range(1,7)]
    episodes = []
    for gen, raw_id in enumerate(schedule,1):
        chosen = None
        for t in relation_order(seed, gen):
            target = apply_table(t, prev, features[raw_id], 1 << n)
            if target in features.values():
                continue
            pairs = exact_sufficient_pairs(target, features, n)
            if not pairs:
                continue
            if gen > 1:
                if any(a.startswith("q") and b.startswith("q") for a,b,_ in pairs):
                    continue
                if not any(prev_id in (a,b) for a,b,_ in pairs):
                    continue
            chosen = Episode(gen, f"G{gen}", t, target, prev_id, raw_id)
            break
        if chosen is None:
            raise RuntimeError(f"world construction failed n={n} seed={seed} gen={gen}")
        episodes.append(chosen)
        features[chosen.episode_id] = chosen.target
        prev_id = chosen.episode_id
        prev = chosen.target
    return episodes

def build_replacement_world(n: int, seed: str, original: list[Episode]) -> list[Episode]:
    features = raw_features(n)
    features["G1"] = original[0].target
    features["G2"] = original[1].target
    prev_id = "G2"
    prev = features[prev_id]
    out = []
    schedule = [original[i].raw_id for i in range(2,6)]
    for offset, raw_id in enumerate(schedule, start=3):
        exclude = original[2].hidden_table if offset == 3 else None
        chosen = None
        for t in relation_order(seed + ":REPLACEMENT", offset, True):
            if exclude is not None and t == exclude:
                continue
            target = apply_table(t, prev, features[raw_id], 1 << n)
            if target in features.values():
                continue
            pairs = exact_sufficient_pairs(target, features, n)
            if not pairs or not any(prev_id in (a,b) for a,b,_ in pairs):
                continue
            chosen = Episode(offset, f"G{offset}R", t, target, prev_id, raw_id)
            break
        if chosen is None:
            raise RuntimeError(f"replacement construction failed n={n} seed={seed} gen={offset}")
        out.append(chosen)
        features[chosen.episode_id] = chosen.target
        prev_id = chosen.episode_id
        prev = chosen.target
    return out

def initial_state(n: int) -> dict[str,Feature]:
    return {k: Feature(k,v) for k,v in raw_features(n).items()}

def proposal_order(seed: str, episode_id: str, pairs: list[tuple[str,str]], tables: tuple[int,...]) -> list[tuple[str,str,int]]:
    rows = [(a,b,t) for a,b in pairs for t in tables]
    return sorted(rows, key=lambda x: digest(seed, episode_id, *x))

def solve_episode(*, n:int, seed:str, episode:Episode, arm:str, family:str, verifier:str, budget:int, state:dict[str,Feature]):
    has_d = "D" in arm
    has_m = "M" in arm
    has_i = "I" in arm
    if not has_m:
        return {"online_ok":False,"exact_ok":False,"route":"NO_MEDIATOR","work":0}, state

    ids = sorted(state)
    pairs = list(combinations(ids,2))
    auth = verifier_rows(verifier, episode.target, n, f"{seed}:{episode.episode_id}")
    selected = None
    work = 0

    if has_d:
        for a,b in pairs:
            if work >= budget:
                break
            work += 1
            fits = fitting_tables(episode.target, state[a].semantics, state[b].semantics, auth, family, n)
            if fits:
                selected = (a,b,min(fits))
                break
    else:
        for a,b,t in proposal_order(seed, episode.episode_id, pairs, allowed_tables(family)):
            if work >= budget:
                break
            work += 1
            proposal = apply_table(t, state[a].semantics, state[b].semantics, 1 << n)
            if agrees_on_rows(proposal, episode.target, auth):
                selected = (a,b,t)
                break

    if selected is None:
        return {"online_ok":False,"exact_ok":False,"route":"RESOURCE_LIMIT_OR_NO_FIT","work":work}, state

    a,b,t = selected
    proposal = apply_table(t, state[a].semantics, state[b].semantics, 1 << n)
    online_ok = agrees_on_rows(proposal, episode.target, auth)
    exact_ok = proposal == episode.target
    next_state = state
    installed = False
    if online_ok and has_i:
        next_state = copy.deepcopy(state)
        next_state[episode.episode_id] = Feature(
            episode.episode_id, proposal, (a,b),
            f"{PRECOMMIT_COMMIT}:{seed}:{family}:{verifier}:{budget}:{episode.episode_id}:{a}:{b}:{t}"
        )
        installed = True
    return {
        "online_ok":online_ok,
        "exact_ok":exact_ok,
        "route":"ACCEPTED" if online_ok else "REJECTED",
        "work":work,
        "selected":[a,b,t],
        "installed":installed,
        "uses_previous": episode.generation == 1 or episode.prev_id in (a,b),
        "auth_rows":len(auth),
        "full_rows":1<<n,
    }, next_state

def remove_dependency_cone(state:dict[str,Feature], root:str):
    nxt = copy.deepcopy(state)
    removed=set()
    frontier={root}
    while frontier:
        cur=frontier.pop()
        if cur in removed:
            continue
        removed.add(cur)
        for k,v in list(nxt.items()):
            if cur in v.dependencies:
                frontier.add(k)
    for k in removed:
        nxt.pop(k,None)
    return nxt,removed

def run_arm(*, n:int, seed:str, world:list[Episode], arm:str, family:str, verifier:str, budget:int):
    state=initial_state(n)
    records=[]
    snapshots={}
    for ep in world:
        result,state = solve_episode(n=n,seed=seed,episode=ep,arm=arm,family=family,verifier=verifier,budget=budget,state=state)
        records.append(result)
        snapshots[ep.generation]=copy.deepcopy(state)
        if not result["online_ok"]:
            break
    exact_depth=0
    for r in records:
        if r["online_ok"] and r["exact_ok"]:
            exact_depth += 1
        else:
            break
    online_depth=sum(1 for r in records if r["online_ok"])
    false_promotions=sum(1 for r in records if r["online_ok"] and r.get("installed") and not r["exact_ok"])
    parentage = exact_depth >= 1 and all(r.get("uses_previous",False) for r in records[1:exact_depth])

    ablation_pass=False
    restore_pass=False
    if exact_depth >= 4 and "I" in arm and 4 in snapshots and "G3" in snapshots.get(3,{}):
        after4=copy.deepcopy(snapshots[4])
        ablated,removed=remove_dependency_cone(after4,"G3")
        fail,_=solve_episode(n=n,seed=seed+":ABL",episode=world[3],arm=arm,family=family,verifier=verifier,budget=budget,state=ablated)
        restored=copy.deepcopy(ablated)
        restored["G3"]=copy.deepcopy(snapshots[3]["G3"])
        good,_=solve_episode(n=n,seed=seed+":RESTORE",episode=world[3],arm=arm,family=family,verifier=verifier,budget=budget,state=restored)
        ablation_pass = not fail["exact_ok"]
        restore_pass = good["exact_ok"]

    metamorphosis_pass=False
    if exact_depth == 6 and "I" in arm and 6 in snapshots:
        repl=build_replacement_world(n,seed,world)
        state2,removed=remove_dependency_cone(copy.deepcopy(snapshots[6]),"G3")
        preserved=("G1" in state2 and "G2" in state2)
        descendants=all(x not in state2 for x in ("G3","G4","G5","G6"))
        ok=True
        for ep in repl:
            rr,state2=solve_episode(n=n,seed=seed+":META",episode=ep,arm=arm,family=family,verifier=verifier,budget=budget,state=state2)
            if not rr["exact_ok"] or not rr.get("uses_previous",False):
                ok=False
                break
        metamorphosis_pass = preserved and descendants and ok

    protected={
        "VALUE": exact_depth == 6,
        "LINEAGE": exact_depth == 6 and parentage,
        "COUNTERFACTUAL": exact_depth == 6 and parentage and ablation_pass and restore_pass,
        "ADAPTIVE": exact_depth == 6 and parentage and ablation_pass and restore_pass and metamorphosis_pass,
    }
    success={
        "CURRENT": exact_depth >= 1,
        "DEPTH3": exact_depth >= 3,
        "DEPTH6": exact_depth == 6,
        "RECOVERY": protected["ADAPTIVE"],
    }
    return {
        "online_depth":online_depth,
        "exact_depth":exact_depth,
        "false_promotions":false_promotions,
        "work":sum(r.get("work",0) for r in records),
        "parentage":parentage,
        "ablation_pass":ablation_pass,
        "restore_pass":restore_pass,
        "metamorphosis_pass":metamorphosis_pass,
        "success":success,
        "protected":protected,
    }

def compact_world(world:list[Episode]) -> list[dict]:
    return [{"generation":e.generation,"hidden_table":e.hidden_table,"target_hash":hashlib.sha256(e.target.to_bytes(8,"little")).hexdigest(),"prev_id":e.prev_id,"raw_id":e.raw_id} for e in world]

def main() -> int:
    worlds={}
    records=[]
    world_failures=[]
    for n in CARRIERS:
        for si in SEEDS:
            seed=f"TRISKELION_ASSUMPTION_TOURNAMENT_V1:B{n}:{si:03d}"
            try:
                world=build_world(n,seed)
            except Exception as exc:
                world_failures.append({"carrier":n,"seed":seed,"error":str(exc)})
                continue
            worlds[f"B{n}:{si:03d}"]=compact_world(world)
            for family in OP_FAMILIES:
                for verifier in VERIFIERS:
                    for budget in BUDGETS:
                        for arm in ARMS:
                            row=run_arm(n=n,seed=seed,world=world,arm=arm,family=family,verifier=verifier,budget=budget)
                            records.append({"carrier":n,"seed_index":si,"family":family,"verifier":verifier,"budget":budget,"arm":arm,**row})

    def cell_counts(field:str, key:str):
        cells={}
        for r in records:
            cell=(r["carrier"],r["family"],r["verifier"],r["budget"],r["arm"])
            cells.setdefault(cell,0)
            if r[field][key]:
                cells[cell]+=1
        return [{"carrier":c[0],"family":c[1],"verifier":c[2],"budget":c[3],"arm":c[4],"passed":v,"total":len(SEEDS)} for c,v in sorted(cells.items())]

    success_tables={k:cell_counts("success",k) for k in SUCCESS_CONTRACTS}
    protected_tables={k:cell_counts("protected",k) for k in PROTECTED_PROFILES}

    strongest=protected_tables["ADAPTIVE"]
    strongest_survivors=[r for r in strongest if r["passed"]>0]
    exact_all16_stable=[]
    for arm in ARMS:
        subset=[r for r in strongest if r["arm"]==arm and r["family"]=="ALL16" and r["verifier"]=="EXACT"]
        if subset and all(r["passed"]==len(SEEDS) for r in subset):
            exact_all16_stable.append(arm)

    all_family_exact_stable=[]
    for arm in ARMS:
        subset=[r for r in strongest if r["arm"]==arm and r["verifier"]=="EXACT"]
        if subset and all(r["passed"]==len(SEEDS) for r in subset):
            all_family_exact_stable.append(arm)

    verifier_false={}
    for verifier in VERIFIERS:
        rows=[r for r in records if r["verifier"]==verifier]
        verifier_false[verifier]={
            "runs":len(rows),
            "false_promotions":sum(r["false_promotions"] for r in rows),
            "runs_with_false_promotion":sum(r["false_promotions"]>0 for r in rows),
        }

    family_rates={}
    for family in OP_FAMILIES:
        rows=[r for r in records if r["family"]==family and r["verifier"]=="EXACT" and r["arm"]=="DMI"]
        family_rates[family]={
            "adaptive_passes":sum(r["protected"]["ADAPTIVE"] for r in rows),
            "runs":len(rows),
        }

    if all_family_exact_stable:
        verdict="STABLE_EMERGENT_CORE_V1"
    elif exact_all16_stable or strongest_survivors:
        verdict="CONDITIONAL_EMERGENT_CORE_V1"
    elif records:
        verdict="VALID_ASSUMPTION_SENSITIVITY_V1"
    else:
        verdict="NO_STABLE_CORE_V1"

    summary={
        "protocol":PROTOCOL,
        "precommit_commit":PRECOMMIT_COMMIT,
        "verdict":verdict,
        "axes":{
            "carriers":list(CARRIERS),
            "operation_families":list(OP_FAMILIES),
            "verifiers":list(VERIFIERS),
            "budgets":list(BUDGETS),
            "arms":list(ARMS),
            "success_contracts":list(SUCCESS_CONTRACTS),
            "protected_profiles":list(PROTECTED_PROFILES),
            "seeds_per_carrier":len(SEEDS),
        },
        "world_failures":world_failures,
        "records":len(records),
        "strongest_nonzero_cells":len(strongest_survivors),
        "exact_all16_all_carrier_budget_stable_arms":exact_all16_stable,
        "all_operation_family_exact_stable_arms":all_family_exact_stable,
        "verifier_false_promotion":verifier_false,
        "dmi_exact_family_rates":family_rates,
        "claim_boundary":"Finite synthetic tournament over declared binary carriers, operation-family restrictions, developmental-role subsets, verifier regimes and resource budgets only.",
    }
    summary["world_hash"]=hashlib.sha256(json.dumps(worlds,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    summary["summary_hash"]=hashlib.sha256(json.dumps({k:v for k,v in summary.items() if k!="summary_hash"},sort_keys=True,separators=(",",":")).encode()).hexdigest()

    out=Path("results/assumption_tournament_v1")
    out.mkdir(parents=True,exist_ok=True)
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    (out/"success_cells.json").write_text(json.dumps(success_tables,indent=2,sort_keys=True)+"\n")
    (out/"protected_cells.json").write_text(json.dumps(protected_tables,indent=2,sort_keys=True)+"\n")
    (out/"records.json").write_text(json.dumps(records,indent=2,sort_keys=True)+"\n")

    print("ASSUMPTION TOURNAMENT V1")
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
