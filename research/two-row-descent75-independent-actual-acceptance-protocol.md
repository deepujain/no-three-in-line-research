# Two-row pilot: independent artifact and trajectory acceptance protocol

Status: DESIGN ONLY. No actual input coordinates, n75 geometry, endpoint recount, optimization or trajectory replay were read or performed to prepare this protocol. Root owns allocation and must explicitly hand off each actual audit. This protocol supplements the frozen production SOURCE/TINY review protocol; it neither approves production source nor authorizes a pilot or audit run.

Design bindings:

- `research/row-block-continuation-no-go-and-two-row-design.md`: `9ae208d8cb88117f886a73dcf808a365cad6c5b3757707f7f6575317d8c4493c`.
- `research/two-row-descent75-lex-zero-clarification.md`: `29d12ad9d514ef9cb81507932989db58d9f983fd0bc292274b02586d8c335e88`.
- `research/two-row-descent75-independent-production-review-protocol.md`: `1b4262d15af1d3e536354631993ca8728195695096c806cab22591f58607b3e4`.

## Allocation and immutable evidence handoff

Before actual work, Root supplies the explicit audit scope and owned budget, frozen worker and audit-source hashes, exact receipt/report/output paths, and accepted original best97 provenance and normalized identity. Do not find or choose an alternate incumbent. Reading actual points, building geometry, recounting endpoints, reconstructing moves and replaying search are distinct charged activities. An endpoint allocation does not authorize optimization replay. Keep all historical artifacts immutable and put audit outputs in separate files.

Bind the original best97 file bytes and normalized point identity to its independently accepted original audit, original worker manifest, owned receipt, runtime and checkpoint/report chain. Do not infer identity from the basename, claimed score or cardinality. The new algorithm imports only that authenticated coordinate state; old weighted-search weights, RNG and counters remain provenance. Reject substitution of the old final203 state, a newly normalized alternative geometry, or a different artifact with the same score. Require the frozen serialization specification to make the normalized identity independently reproducible; file-byte hash and normalized geometry hash serve different purposes and both are recorded. If the specification is missing or ambiguous, report an identity gap rather than inventing a normalization convention.

The actual gate remains the proposed25-second soft/30-second owned/256MiB allocation only if Root explicitly grants it after source/tiny/lifecycle review. The audit has a separate allocation; its time must not be silently omitted or borrowed from search. No automatic retry, different seed, cap expansion, unchanged continuation or new actual geometry follows an inconclusive audit. No future scheduled reservation exceeds900 seconds without a new governing decision.

## Independently recounted saved states

For each authorized handoff, saved improvement and final artifact, parse coordinates independently of the production loader and check integer pairs, exactly149 distinct points in `[0,74]^2`, all75 rows occupied, exactly one singleton row and74 rows of load two. Reject duplicate points before set conversion. Check claimed axis counts against directly counted coordinates. Column occupancy is diagnostic and is not a hard permutation constraint.

Recompute exact raw U using integer determinant tests over all unordered triples, or another explicitly reviewed independent method. Do not use production U, production line masks, weighted score or telemetry as the oracle. Record file-byte hash, normalized identity, point count, row pattern, exact U, audit source hash, scope and resource receipt. The authenticated initial state must recount to97. Any saved positive-U state is an invalid research incumbent, even when improved. A claimed149-point witness requires U=0 and the applicable independent validator/receipt requirements; a positive state does not improve the verified construction record.

Do not require reading every saved improvement if only endpoint scope was granted. State precisely which artifacts were recounted. An independently recounted initial and final state proves those endpoint scores and net change; it does not independently establish every intervening accepted move, the production ordering policy or scan exhaustion.

## Reconstructable accepted-move chain

A full artifact-chain audit requires the authenticated initial state and every accepted improvement state, or an unambiguous lossless move record sufficient to reconstruct each state. Bind sequential records by before/after normalized identity, accepted ordinal, declared selected row or ordered pair, stage, raw scores and started/completed counters. A digest without reconstructable coordinates is an identity assertion, not a state recount. Missing intermediates reduce the result to the available endpoints and bounded partial-chain evidence; never fill gaps by searching.

Recount every reconstructed state independently. For each accepted transition require integer `U_after < U_before`; neutral or uphill changes fail this policy. Initial U97 implies at most97 accepted transitions and a strictly decreasing score sequence. Verify that the point-set symmetric difference is confined to the declared selected row(s). A row move preserves that row's load. A pair move preserves its combined load: four implies2/2; three permits1/2 or2/1, including deficiency migration. All unselected rows and their coordinates remain identical. The resulting state must match the declared after identity and invariant checks.

Current eligibility is a feasibility and implementation property: the unchanged selected row assignment, or unchanged pair assignment in one of the allowed load orientations, must be in the defined neighborhood. Inspect frozen source and exhaustive tiny comparisons for actual inclusion. Recounting a chosen improved move alone cannot prove the optimizer considered current, found the exact minimum, used the prescribed tie rule or selected the first improving row/pair. Those stronger claims need the source/tiny evidence and appropriately bound execution evidence, or a separately authorized independent certificate/replay. The audit must distinguish these bases.

If complete records exist, check counters are monotone shared totals across all accepted states, with row started at most512 and pair started at most32, completed no greater than started, and no reset on improvement. Charge an interrupted started optimization. Source/lifecycle evidence must establish where counters increment and what completion means; counter consistency alone does not prove that an optimization really ran or finished. A zero candidate may be an exact optimum by nonnegativity and merged lexical order even if its candidate enumeration ends early; distinguish optimum established from enumeration exhausted.

## Local-minimum and skipped-neighborhood claims

Use separate conclusions for (a) independently recounted state improvements, (b) source-supported policy execution, and (c) independently established neighborhood exclusion. A cap or deadline stop is partial. In particular,512 total row attempts and32 total pair attempts span every accepted state; they are not per-state exhaustive scan allowances. A completed sweep on a previous state says nothing about whether the final improved state is a local minimum. Accepting an improvement invalidates earlier nonimprovement results for the new state and restarts Stage1.

A single-row local-minimum label for a given positive state requires that every positive-I row was completely optimized on that exact state with no strict improvement, plus a valid zero-I omission argument. A two-row local-minimum label additionally requires every positive-M pair completely optimized on that same state with both permitted deficiency orientations and no strict improvement, plus the zero-M omission argument. Neither label implies global impossibility or excludes149-point configurations outside these neighborhoods. A terminal status string or totals matching a plausible number of rows/pairs is insufficient.

The mathematical omission proof is that removing a zero-I row or zero-M pair destroys no old triple, while every added triple contribution is nonnegative. The formulas `I_r`, `J_rs`, and `M_rs = I_r + I_s - J_rs` must represent direct triple incidence/intersection/union for the state in question. Source review and exhaustive tiny direct-triple comparisons can support the implementation claim. For stronger actual-state certification, independently enumerate the authorized state's triple incidences and bind the exact ordered eligible row/pair list to it. Require coverage records identifying each completed optimization on that state, with exact-minimum evidence at the chosen assurance level. Do not infer zero skips, correct ordering or absence of missing pairs from counts alone. Independently proving all minima would require separately allocated certificates or optimization replay; do not perform that work under an endpoint-audit label.

An interrupted positive candidate is not an accepted best-of-partial-scan move. Confirm the saved incumbent is the last fully accepted state, or clearly distinguish an uncommitted diagnostic candidate. If a zero candidate was preserved, audit its exact saved identity independently and distinguish raw candidate, validated witness and accepted final receipt. The zero witness exception does not permit a positive partial minimum to be accepted.

## Receipt, resource and failure acceptance

Bind pre/post source and input pins, frozen runtime/guard identity, worker exit status, owned process termination and declared outputs to the receipt. Independently hash the files actually audited. Source/pin/report failures cannot be concealed by a useful endpoint. Report independently valid geometry separately from overall run acceptance when those differ.

Report RSS according to what was measured: sampled RSS is sampled observation, not a proved process maximum. Apply the guard's declared units and256MiB condition without assuming tiny-grid measurements establish actual n75 memory. Source bounds on the5625-entry cross table and finite work are separate from an owned actual-resource result. Include audit computation in its own resource account.

A completed zero is preserved promptly before optional rebuilding/reporting work. If the first validator completes after the allowed deadline, the second must not begin. If the second completes late, persist the witness immediately before optional receipt/pin work, while still rejecting late overall acceptance as required. A later error must not delete a preserved candidate/witness. Source/tiny lifecycle review establishes those branches; an actual receipt establishes only the branches it exercised.

## Required reporting limits

The final audit states source identities, actual scope and allocation, each independently recounted artifact and U, chain completeness, move-legality/strict-decrease results, source-supported versus independently proven policy claims, final-state scan completeness, receipt/resource acceptance and unresolved gaps. It explicitly states whether any149-point zero was independently verified; otherwise the best verified construction remains156 on79, with no149 on75 or157/158 on79 established here.

The exhaustive synthetic n2..4 policy traces all reach zero. They therefore supply no genuine positive geometric fixture for the completed no-improvement terminal branch. Any test of that branch with optimizers returning current must remain explicitly labeled a control stub. Genuine positive cap-stop fixtures can test partial termination, but cannot cure this coverage limitation. Never cite a stub, an endpoint recount or cap telemetry as proof of an actual positive local minimum.
