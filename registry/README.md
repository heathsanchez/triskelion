# Research Registry

The canonical programme index lives here.

- `RESEARCH_REGISTRY.jsonl` — canonical machine-readable records. One JSON object per line.
- `RESEARCH_REGISTRY.csv` — provisional human table created during the initial consolidation. **Do not parse as canonical data**; some narrative fields contain commas. It will be regenerated from JSONL in a later tooling pass.
- `RESEARCH_REGISTRY_SCHEMA.md` — identity, status and evidence-precedence rules.
- `PROGRAMME_STATE_20260816.md` — human-readable consolidated state.

## Update rule

Every new experiment must receive a descriptive `canonical_id` and append/update one JSONL record. Bare V-numbers are aliases only.

A workflow success is not a scientific PASS. The registry status must be derived from the primary artifact, protocol gates and current counterevidence.

When a later result narrows an earlier claim, retain both records and link them through `supersedes` / `next_residual`; never rewrite history to make the programme look cleaner.
