# Checkpoint-free reproduction of two fixed-prefix pair relaxations

The published computation reported native UNSAT on the degree-plus-pair relaxations for two fixed near-quarter-turn prefixes at n79. This is a conditional solver result for those prefixes, not a checked UNSAT proof or global n79 exclusion. The audited source report's SHA-256 is `1e3cc59e60b3e989a41cf46f84a372d1f993891f27048a2cb79db4c959447014`.

`research/reproduce_main_ancestor_pairs.py` embeds the saved ordered orbit IDs and the audited mask, variable-order, pair-cut and degree-formula digests/counts. It reconstructs the n79 orbit map and each prefix from the repository's source, recomputes a complete admissibility mask and every unordered pair, checks those identities, then solves each degree-plus-pair formula afresh with Glucose3. It does not read any checkpoint, receipt, private state file, previously generated mask, pair clause or solver state. It does not run a general DFS or assert that SAT would be a valid geometric configuration.

After installing the optional pinned dependencies from `requirements-research.txt`, a reader can run from the repository root:

```sh
.venv/bin/python research/reproduce_main_ancestor_pairs.py --seconds 25
```

A complete successful replay reports two `unsat` solver statuses. The shared time budget is cooperative; a reader should apply an appropriate independent process and memory limit. Timeout or a differing digest/solver result is not a negative result. Reusing Glucose3 is a reproduction of the native solver observation, not an independent proof; independently reconstructing the clauses with another implementation and verifying a checkable UNSAT proof would provide stronger evidence.

The source and its public dependencies must be committed together before a fresh clone can use this recipe. Tiny-grid tests exercise checkpoint-free reconstruction and the existing pair/degree oracles; this preparation did not run the n79 replay.
