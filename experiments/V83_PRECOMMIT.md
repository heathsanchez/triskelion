# V83 Natural IVAG — frozen protocol

External corpus: `jkoppel/QuixBugs` at `4257f44b0ff1181dedaedee6a447e133219fcebf`.

Purpose: test whether a pre-existing independently authored repair stream induces reusable minimum-description repair schemas and strict held-out closure growth before attempting descendant discoverability.

Frozen rules:
- never read `correct_python_programs/` during discovery;
- derive task order only by SHA-256 from task names and fixed seeds;
- stream size 12, probe set size 10;
- fixed generic one-token schema space in `V83_QUIXBUGS_NATURAL_IVAG.py`;
- test current retained closure before searching a new schema;
- if multiple previously unseen schemas solve an obstruction, admit only a minimum-description schema (lexical tie-break);
- retain boring closures and unclosed obstructions;
- run two independent hash orderings over the same frozen stream pool;
- report probe-frontier growth after each admitted extension;
- do not inspect or reorder selected tasks after launch;
- `three_generation_developmental_causality` is frozen FALSE because all generic token-pair schemas are candidate-discoverable from the start. V83 cannot close the IVAG crown-jewel lineage gate by construction.

Allowed verdicts: `PASS_NATURAL_IVAG_V83`, `MIXED_NATURAL_IVAG_V83`, `NEGATIVE_NATURAL_IVAG_V83`, though under this frozen constructor a full PASS is intentionally unreachable because the descendant-causality gate is false.

Interpretation boundary: a MIXED result can support natural minimum-extension / closure-growth / convergence evidence. It cannot support autonomous constructor growth or ancestor-dependent descendant discoverability.
