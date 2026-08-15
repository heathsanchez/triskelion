# V112 Conditional Recurrence Null for V110 — PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen before V112 randomization output is inspected.

## Purpose

V110 found 10 verifier-passing one-site comparator repairs across three historical QuixBugs programs, including two quotient classes recurring across distinct programs with literal diversity. V112 asks a narrower quantitative question: **given the observed number of passing candidates per repaired program, how often would recurrence at least this structured arise if the identities of the passing candidates were random within each program's frozen candidate search space?**

This is a post-V110 conditional randomization analysis. It is not a prospective validation of V110 and cannot upgrade V110's causal claim by itself.

## Frozen null

For each V110 repaired program:

1. reconstruct exactly the comparator candidate universe V110 tested from the pinned QuixBugs buggy source;
2. preserve the observed number of passing candidates in that program;
3. uniformly sample that many candidate identities without replacement from that program's tested candidate universe;
4. canonicalize sampled candidates with the same V110 quotient function;
5. compute recurrence across distinct programs.

The null therefore preserves:

- repaired program identities;
- number of passing candidates per repaired program;
- each program's comparison-site/source-operator composition;
- candidate grammar and quotient map.

It destroys only the association between verifier success and candidate identity.

## Frozen statistic

Primary event E is true when a randomized draw contains:

- at least **two** quotient classes recurring across at least two distinct repaired programs; AND
- at least **two** recurrent classes have at least two distinct literal signatures.

This matches or exceeds the structural recurrence count observed in V110 without using candidate success labels in the null generation.

Secondary statistics recorded:

- number of recurrent quotient classes;
- number of literally diverse recurrent classes;
- maximum number of distinct programs sharing one quotient class;
- maximum recurrent-class member count.

## Monte Carlo

- deterministic seed: `11220260815`;
- trials: **200,000**;
- p-value estimate: `(1 + count(E)) / (1 + trials)`;
- report a binomial standard error for the raw Monte Carlo frequency.

## Interpretation

- `p <= 0.05`: recurrence is uncommon under this conditional identity-randomization null;
- `p > 0.05`: V110 recurrence may be unsurprising given the repair counts/search geometry and should not be presented as statistically exceptional under this null.

No threshold changes after execution.

## Claim boundary

This null is conditional on the three V110 repaired programs and their observed pass counts, and it was designed after V110 was observed. It measures whether the *identity structure* of those successes is surprising under a specific random-assignment model; it is not a population-level p-value for code repair or operator invention.
