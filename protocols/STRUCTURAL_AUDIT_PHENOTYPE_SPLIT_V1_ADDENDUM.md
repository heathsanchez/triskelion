# STRUCTURAL AUDIT + PHENOTYPE SPLIT V1 — pre-execution addendum

Status: **FROZEN AFTER UNIT-TEST DISCOVERY, BEFORE SCIENTIFIC OUTCOME EXECUTION**

## Why this addendum exists

The first implementation unit test used the left projection operation

\[
d(a,b)=a
\]

and expected its recurrence map

\[
(a,b)\mapsto(b,d(a,b))=(b,a)
\]

to have two-cycles on unequal pairs.

The test instead evaluated the *canonical pointed representative* under the previously frozen symmetry that includes global argument swap

\[
d(a,b)\leftrightarrow d(b,a).
\]

For the transposed right projection,

\[
d^\top(a,b)=b,
\]

the same recurrence rule becomes

\[
(a,b)\mapsto(b,b),
\]

which has different recurrence behaviour.

This was discovered before the scientific audit ran: the workflow stopped at unit tests and produced no experiment result.

Therefore the audit must explicitly test whether every protected developmental measurement is invariant under the symmetry quotient used to define the 5,130 canonical orbits.

## Added symmetry-compatibility audit

For all 59,049 raw pointed operations:

1. compute its canonical orbit under carrier relabeling + global argument swap;
2. recompute the direct developmental fields that do not require pointed-census lookup:
   - d0,d1,d2,d3;
   - recombinant3;
   - recur_distinct_sum;
   - recur_distinct_max;
   - recur_cycle_sum;
   - recur_cycle_max;
3. group values by canonical orbit;
4. report, for each field:
   - number of canonical orbits with more than one raw value;
   - raw weight contained in non-invariant orbits;
   - first explicit raw-pair counterexample.

Also separate:
- carrier-relabeling invariance;
- transpose invariance.

## Interpretation rule

If a field is not invariant under the quotient used to create the 5,130 representatives, then orbit-weighting one canonical representative is not a valid raw-59,049 distribution for that field.

The canonical-representative measurement itself may still be reproducible, but it must be labeled as representative-dependent rather than orbit-intrinsic.

No previous developmental conclusion is silently retained if it depends on a non-invariant field.

## Added report

The final result must contain:

- symmetry_compatibility.direct_fields;
- symmetry_compatibility.all_direct_fields_orbit_invariant;
- explicit counterexamples for non-invariant fields.

This diagnostic is required but does not alter the original SA1–SA16 gate count. SA7 still means exact reproduction of the recorded canonical-representative values.

## Claim boundary correction

A PASS of the original gates validates canonical-representative recomputation.

Only fields passing this addendum's orbit-invariance audit may be interpreted as intrinsic to the previously defined symmetry orbit.
