#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from itertools import permutations, combinations
import csv
import hashlib
import json
import sys

Q=3
OP_COUNT=19683
P3=[1,3,9,27,81,243,729,2187,6561]
PERMS=list(permutations(range(Q)))
SOURCE_RUN=35549071552
SOURCE_HASH='ceccb45b0486c2a163e4c19ab599387cd2f2f5aeb34615ce119e8bb37d76d484'


def decode_op(code:int):
    out=[]
    for _ in range(9):
        out.append(code%3); code//=3
    return out


def encode_op(t):
    return sum(int(v)*P3[i] for i,v in enumerate(t))


def permute_code(code:int,p):
    old=decode_op(code)
    nt=[0]*9
    for a in range(3):
        for b in range(3):
            nt[3*p[a]+p[b]]=p[old[3*a+b]]
    return encode_op(nt)


def sig_to_bits(sig:str)->int:
    # Source encoding stores function bits low-to-high in successive hex nibbles.
    z=0
    for j,ch in enumerate(sig.strip()):
        z |= int(ch,16) << (4*j)
    return z


def iter_set_bits(z:int):
    while z:
        lsb=z & -z
        i=lsb.bit_length()-1
        yield i
        z ^= lsb


def load_rows(root:Path):
    by_shard={}
    for p in root.rglob('shard_*.tsv'):
        try:
            shard=int(p.stem.split('_')[-1])
        except Exception:
            continue
        lines=p.read_text().splitlines()
        if not lines or not lines[0].startswith('#META\t'):
            continue
        if shard in by_shard:
            if p.read_bytes()!=by_shard[shard].read_bytes():
                raise RuntimeError(f'nonidentical duplicate for shard {shard}: {p} vs {by_shard[shard]}')
            continue
        by_shard[shard]=p
    if set(by_shard)!=set(range(24)):
        raise RuntimeError(f'expected shards 0..23 exactly, got {sorted(by_shard)}')
    rows=[]
    metas=[]
    for shard in range(24):
        p=by_shard[shard]
        lines=p.read_text().splitlines()
        meta=lines[0].split('\t')
        metas.append({'shard':int(meta[1]),'shards':int(meta[2]),'reps':int(meta[3]),'weight':int(meta[4])})
        rd=csv.DictReader(lines[1:],delimiter='\t')
        for r in rd:
            for k in ('key','weight','ground','opcode','unary','binary','no_ground','no_ground_all_constants',
                      'd0','d1','d2','d3','recombinant3','recur_distinct_sum','recur_distinct_max',
                      'recur_cycle_sum','recur_cycle_max'):
                r[k]=int(r[k])
            r['fixed_bits']=sig_to_bits(r['fixed_sig'])
            r['no_ground_bits']=sig_to_bits(r['no_ground_sig'])
            rows.append(r)
    return sorted(rows,key=lambda r:r['key']),metas


def build_perm_maps():
    maps=[]
    for p in PERMS:
        maps.append([permute_code(code,p) for code in range(OP_COUNT)])
    return maps


def make_transformer(perm_maps):
    cache={}
    def transform(bits:int,pi:int)->int:
        key=(bits,pi)
        if key in cache:return cache[key]
        mp=perm_maps[pi]
        out=0
        for i in iter_set_bits(bits):
            out |= 1 << mp[i]
        cache[key]=out
        return out
    return transform,cache


def canonical_bits(bits:int,transform)->int:
    return min(transform(bits,pi) for pi in range(len(PERMS)))


def canonical_pair(a:int,b:int,transform):
    return min((transform(a,pi),transform(b,pi)) for pi in range(len(PERMS)))


def named_query_witness_audit(unique_bits):
    # For Q_f(K) := [f in K], every two unequal capability sets
    # differ on at least one named membership query. Audit all pairs.
    n=len(unique_bits)
    checked=0
    sample=[]
    for i,j in combinations(range(n),2):
        x=unique_bits[i]^unique_bits[j]
        if x==0:
            raise AssertionError('distinct signatures had no membership-query witness')
        q=(x & -x).bit_length()-1
        if ((unique_bits[i]>>q)&1)==((unique_bits[j]>>q)&1):
            raise AssertionError('bad witness')
        checked+=1
        if len(sample)<5:
            sample.append({'left_index':i,'right_index':j,'query_function_code':q})
    return {'unique_signatures':n,'unordered_pairs_checked':checked,'sample_witnesses':sample}


def fixture_ab():
    PHASE0='phase0'; PHASEPI='phasePi'; BRIGHT='bright'; DARK='dark'
    def present(s): return False
    def recombine(s):
        return BRIGHT if s==PHASE0 else DARK if s==PHASEPI else s
    def protected(s): return s==BRIGHT
    present_equal=(present(PHASE0)==present(PHASEPI))
    future_separates=(protected(recombine(PHASE0))!=protected(recombine(PHASEPI)))
    return {
        'pass':present_equal and future_separates,
        'present_equal':present_equal,
        'recombination_separates':future_separates,
        'reading':'present agreement is not continuation-safe agreement',
    }


def fixture_which_path():
    LL='latentL'; LR='latentR'; SL='seenL'; SR='seenR'
    def probe(s): return {LL:SL,LR:SR,SL:SL,SR:SR}[s]
    def path_dist(x,y): return {x,y}=={SL,SR}
    pre=path_dist(LL,LR)
    post=path_dist(probe(LL),probe(LR))
    nonfabricating=(not post) or pre
    backward_admissible=post and nonfabricating
    return {
        'pass':(not pre) and post and (not nonfabricating) and (not backward_admissible),
        'pre_distinction':pre,
        'post_probe_distinction':post,
        'probe_nonfabricating_for_path_predicate':nonfabricating,
        'backward_attribution_admissible':backward_admissible,
        'reading':'the intervention creates the protected distinction, so it cannot certify a pre-intervention path distinction',
    }


def fixture_observer_boundary():
    A='wrappedA'; B='wrappedB'
    contexts=('id','wrapObserver','wrapObserverAgain')
    def obs(_ctx,_s): return 'same-consequence'
    equivalent=all(obs(c,A)==obs(c,B) for c in contexts)
    def external_selector(s): return 'rule1' if s==A else 'rule2'
    selector_descends=(not equivalent) or external_selector(A)==external_selector(B)
    return {
        'pass':equivalent and not selector_descends,
        'contextually_equivalent':equivalent,
        'selector_descends_through_equivalence':selector_descends,
        'selector_values':[external_selector(A),external_selector(B)],
        'reading':'a regime selector that distinguishes consequentially equivalent states is external to the represented semantics',
    }


def fixture_bell_like():
    corr=frozenset({(0,0),(1,1)})
    anti=frozenset({(0,1),(1,0)})
    def factor(rel):
        return (frozenset(a for a,_ in rel),frozenset(b for _,b in rel))
    def joint_consequence(rel):
        return all(a==b for a,b in rel)
    same_components=(factor(corr)==factor(anti))
    different_joint=(joint_consequence(corr)!=joint_consequence(anti))
    factorisation_possible=not (same_components and different_joint)
    return {
        'pass':same_components and different_joint and not factorisation_possible,
        'same_componentwise_local_supports':same_components,
        'different_protected_joint_consequence':different_joint,
        'factorisation_through_local_supports_possible':factorisation_possible,
        'reading':'the proposed local-support factor map loses a protected joint relation',
    }


def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def main():
    if len(sys.argv)!=4:
        raise SystemExit('usage: nucleus_contextual_quotient_v0.py SOURCE_ARTIFACT_ROOT SOURCE_RESULT_JSON OUT_DIR')
    root=Path(sys.argv[1]); source_path=Path(sys.argv[2]); out=Path(sys.argv[3]); out.mkdir(parents=True,exist_ok=True)
    source=json.loads(source_path.read_text())
    rows,metas=load_rows(root)

    source_bound=(
        source.get('protocol')=='DERIVED_CONSEQUENTIAL_QUOTIENT_V1' and
        source.get('verdict')=='PASS_DERIVED_CONSEQUENTIAL_QUOTIENT_V1' and
        source.get('aggregation_hash')==SOURCE_HASH and
        all(source.get('headline_gates',{}).values()) and
        source.get('audit',{}).get('mismatch_counts',{})=={}
    )

    if len(rows)!=5130 or len({r['key'] for r in rows})!=5130:
        raise RuntimeError(f'expected 5130 unique canonical rows, got {len(rows)}')
    total_weight=sum(r['weight'] for r in rows)

    bitcount_ok=all(
        r['fixed_bits'].bit_count()==r['binary'] and
        r['no_ground_bits'].bit_count()==r['no_ground']
        for r in rows
    )

    fixed_unique=sorted({r['fixed_bits'] for r in rows})
    pair_unique=sorted({(r['fixed_bits'],r['no_ground_bits']) for r in rows})

    perm_maps=build_perm_maps()
    transform,transform_cache=make_transformer(perm_maps)

    fixed_canon={b:canonical_bits(b,transform) for b in fixed_unique}
    pair_canon={pair:canonical_pair(pair[0],pair[1],transform) for pair in pair_unique}

    sym_fixed_classes=set(fixed_canon.values())
    sym_pair_classes=set(pair_canon.values())

    fixed_orbit_groups=defaultdict(list)
    pair_orbit_groups=defaultdict(list)
    for r in rows:
        fixed_orbit_groups[fixed_canon[r['fixed_bits']]].append(r)
        pair_orbit_groups[pair_canon[(r['fixed_bits'],r['no_ground_bits'])]].append(r)

    orbit_stable=True
    for b in fixed_unique:
        cb=fixed_canon[b]
        for pi in range(6):
            if canonical_bits(transform(b,pi),transform)!=cb:
                orbit_stable=False; break
        if not orbit_stable: break

    pair_orbit_stable=True
    for a,b in pair_unique:
        cp=pair_canon[(a,b)]
        for pi in range(6):
            if canonical_pair(transform(a,pi),transform(b,pi),transform)!=cp:
                pair_orbit_stable=False; break
        if not pair_orbit_stable: break

    named_query_audit=named_query_witness_audit(fixed_unique)

    fixtures={
        'AB_recombination':fixture_ab(),
        'which_path_nonfabrication':fixture_which_path(),
        'observer_boundary_endogenous_selector':fixture_observer_boundary(),
        'Bell_like_factorisation':fixture_bell_like(),
    }

    source_parts=source['partitions']
    gates={
        'NQ1_source_run_bound':source_bound,
        'NQ2_5130_canonical_orbits':len(rows)==5130 and len({r['key'] for r in rows})==5130,
        'NQ3_raw_weight_59049':total_weight==59049,
        'NQ4_exact_bitset_counts_match_source_counts':bitcount_ok,
        'NQ5_fixed_coordinate_capability_827':len(fixed_unique)==827,
        'NQ6_carrier_isomorphism_capability_747':len(sym_fixed_classes)==747,
        'NQ7_fixed_coordinate_reference_1158':len(pair_unique)==1158,
        'NQ8_carrier_isomorphism_reference_1091':len(sym_pair_classes)==1091,
        'NQ9_all_named_capability_signatures_pairwise_separated':named_query_audit['unordered_pairs_checked']==827*826//2,
        'NQ10_carrier_orbit_canonicalization_stable':orbit_stable,
        'NQ11_reference_orbit_canonicalization_stable':pair_orbit_stable,
        'NQ12_AB_fixture':fixtures['AB_recombination']['pass'],
        'NQ13_which_path_fixture':fixtures['which_path_nonfabrication']['pass'],
        'NQ14_observer_boundary_fixture':fixtures['observer_boundary_endogenous_selector']['pass'],
        'NQ15_Bell_like_factorisation_fixture':fixtures['Bell_like_factorisation']['pass'],
        'NQ16_source_contrasts_preserved':(
            source.get('v4',{}).get('distinct_signatures')==5130 and
            source_parts['Q_history_d3']['classes']==5129 and
            source_parts['Q_capability_fixed']['classes']==827 and
            source_parts['Q_capability_plus_reference']['classes']==1158
        ),
    }

    result={
        'protocol':'NUCLEUS_CONTEXTUAL_QUOTIENT_V0',
        'source_run':SOURCE_RUN,
        'source_aggregation_hash':SOURCE_HASH,
        'source_binding_ok':source_bound,
        'population':{'canonical_orbits':len(rows),'raw_weight':total_weight},
        'declared_observation_language':{
            'query':'Q_f(S) = true iff binary function f belongs to the complete term-function capability closure K(S)',
            'fixed_coordinate_equivalence':'S ~ T iff every named Q_f has the same answer; by membership extensionality this is exactly K(S)=K(T)',
            'symmetry':'S3 simultaneous carrier relabeling acts on both capability states and function-query names',
        },
        'quotients':{
            'fixed_coordinate_capability':{
                'classes':len(fixed_unique),
                'expected':827,
                'exact_named_query_quotient':True,
                'pairwise_query_witness_audit':named_query_audit,
            },
            'carrier_isomorphism_capability':{
                'classes':len(sym_fixed_classes),
                'expected':747,
                'kind':'isomorphism quotient of the fixed-coordinate behavioral quotient',
                'largest_class_orbits':max(len(v) for v in fixed_orbit_groups.values()),
                'largest_class_raw_weight':max(sum(r['weight'] for r in v) for v in fixed_orbit_groups.values()),
            },
            'fixed_coordinate_capability_plus_reference':{
                'classes':len(pair_unique),
                'expected':1158,
            },
            'carrier_isomorphism_capability_plus_reference':{
                'classes':len(sym_pair_classes),
                'expected':1091,
                'largest_class_orbits':max(len(v) for v in pair_orbit_groups.values()),
                'largest_class_raw_weight':max(sum(r['weight'] for r in v) for v in pair_orbit_groups.values()),
            },
        },
        'contrasts':{
            'V4_generator_incidence':source.get('v4',{}).get('distinct_signatures'),
            'history_d3':source_parts['Q_history_d3']['classes'],
            'old_protected_measurements':source_parts['Q_old_protected_measurements']['classes'],
        },
        'fixtures':fixtures,
        'artifact_audit':{
            'shards':metas,
            'all_bit_counts_match':bitcount_ok,
            'carrier_orbit_stable':orbit_stable,
            'reference_orbit_stable':pair_orbit_stable,
            'transform_cache_entries':len(transform_cache),
        },
        'headline_gates':gates,
        'claim_boundary':(
            'Exact finite theorem for the declared capability-membership observation language on the authoritative three-element census. '
            '827 is the fixed-coordinate behavioral quotient. 747 is the further carrier-isomorphism quotient and must not be described as equality under fixed named-function queries. '
            'No claim of full abstraction for arbitrary syntax-indexed continuations or a language exposing the primitive operation as an observable is made.'
        ),
    }
    result['aggregation_hash']=stable_hash(result)
    result['verdict']='PASS_NUCLEUS_CONTEXTUAL_QUOTIENT_V0' if all(gates.values()) else 'PARTIAL_NUCLEUS_CONTEXTUAL_QUOTIENT_V0'

    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (out/'summary.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('NUCLEUS CONTEXTUAL QUOTIENT V0',result['verdict'])
    print('Q_NAMED=827 observed='+str(len(fixed_unique)))
    print('Q_ISO=747 observed='+str(len(sym_fixed_classes)))
    print('Q_REFERENCE_NAMED=1158 observed='+str(len(pair_unique)))
    print('Q_REFERENCE_ISO=1091 observed='+str(len(sym_pair_classes)))
    print('PAIRWISE_QUERY_WITNESSES='+str(named_query_audit['unordered_pairs_checked']))
    print('FIXTURES='+json.dumps({k:v['pass'] for k,v in fixtures.items()},sort_keys=True))
    print('GATES='+json.dumps(gates,sort_keys=True))
    print('HASH='+result['aggregation_hash'])


if __name__=='__main__':
    main()
