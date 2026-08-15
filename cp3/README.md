# Triskelion Checkpoint 3 recovery

This branch restores only the frozen Checkpoint 3 qualification/evaluation lineage. It does not alter the scientific corpus, selection criteria, acquisition/protected partition, or four-arm protocol.

Current execution order:

1. Re-qualify only the three unresolved frozen projects: pandas, Scrapy, Luigi.
2. Merge those results with the seven already-qualified cases.
3. Freeze the acquisition capability from acquisition evidence only.
4. Sanitize protected inputs.
5. Run exactly one COLD / RAW MEMORY / ALWAYS-ON / VERIFIED evaluation per protected case-arm.

The qualification workflow records infrastructure failures without promoting them to semantic outcomes and never selects a later candidate based on source semantics.
