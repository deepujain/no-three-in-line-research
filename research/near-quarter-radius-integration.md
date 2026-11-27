# Radius policy2 packed integration

Fresh derivation only, awaiting independent source/request review. Baseline
sources and accepted11-node frontier are preserved in commit26fec70; no old
checkpoint is migrated. Implementation model `gpt-6.1-sol`, reasoning `high`.

Frozen new core `research/near_quarter_rowbatch_core.py` SHA-256
2f758f6383ebefc9772e2bf34969e477c29f70efc396a3d96e8d13aed1822ed5;
codec `research/near_quarter_rowbatch_checkpoint.py` SHA-256
46e5a2db0848f41954645aed8b923e6d9c5bd7d18c9c1adde133c15ee269aeba.
Reviewed pure helper647ae137, worker7f8c8a16, state860711b8, cursor738a545a,
helperc119b58f and model/verifier sources are unchanged.

The production diff is18core/15codec changed lines. The adapter2 hook runs only
after the complete geometry mask and existing orbit/row bounds, immediately
before MRV row choice. It does no extra geometry probe. Passing nodes retain
identical row, domain IDs/weights and batch cursor order. A stop propagates before
a verdict/frame/prune-counter commit with coherent geometry.

Identity byte12 is2 for packed radius policy, remaining1 for tiny adapter1.
The new codec rejects a packed policy1 identity. New closed reason6,
RADIUS_SHORTFALL, has zero inactive metadata and requires nonzero orbit_prunes;
private replay reruns the complete scan and checks the same reason. Adapter1
cannot use reason6. Under policy2 orbit_prunes includes both global orbit
shortage and radius-graph obstructions; there is no separate exact historical
radius-event counter. Frame/header sizes, seven source slots and7868byte v1
maximum remain unchanged. Source/policy hashes separate this derivation.

The helper is transitively bound: core contains its literal reviewed SHA647ae137
and checks bounded helper bytes during import-time source capture and every
later packed source check. The core's own SHA occupies its existing source slot,
so changing that literal changes the manifest; no arbitrary module path or
unbound utility is introduced. No lifecycle worker/protocol framework changes.

53tests passed in4.498s under the unchanged10s command ceiling. Evidence
`data/near-quarter-radius-integration-tiny-evidence.json` SHA-256
157827c027e0a5aa6157af19030e1d44609441409619fa4123e85654e8254d38.
Focused tests `tests/test_near_quarter_radius_integration.py` SHA-256
03ffe5eb0360ef3ec7a12737ffa85115b9a22d09f078c631e47a05271f0517e0.
Existing packed core tests now2cb1de60 and worker tests9056f65e.

The hook was checked at all73coherent below-target n3/n5/n7 prefixes. It ran at
19prefixes passing the old bounds, added8sound rejections, and preserved every
passing MRV result and geometry snapshot. All19checks along an actually
rejecting post-mask hook were interrupted with unchanged COUNTED frontier,
geometry and logical counters. New reason6 privately roundtrips; policy1 is
rejected; helper hash mismatch fails closed. The full existing transaction,
checkpoint, lease, publication and uncertainty suites still pass.

Initially two baseline comparisons failed as expected because policy2 changes
the tiny tree. Tests now compare exact frozen complete leaf sets and new-policy
uninterrupted versus one-node resume frontiers, rather than claiming stepwise
unpruned equivalence. Forward/reverse full nodes are2/4/11, leaves1/0/0; old
baseline nodes were2/5/11. No runtime improvement follows from these counts.

Prepared fresh n79 root request/proposal are
`data/packed-radius-n79-r1-root.request.json` and
`data/packed-radius-n79-r1-root.proposal.json`, binding current source manifest,
transitive helper hash and policy2. They request30s/256MiB,2s worker reserve,
max_new_nodes0, historical ordered map78054420, and an absent fresh chain.
Only permutation arithmetic and saved-artifact reads occurred in preparation.
No new actual-host gate or n9/n71/n79 geometry ran for this integration package.
Root executes only after independent source/request approval, then separately
allocates a bounded same-declaration comparison stage if the root gate passes.
