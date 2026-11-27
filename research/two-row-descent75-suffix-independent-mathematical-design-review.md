# Cursor-aware suffix: independent mathematical design review

Decision: DESIGN PASS for the bounded suffix protocol in the two documents below, with their explicit source-supported historical coverage basis and separate implementation/resource gates. This is not SOURCE/TINY acceptance, an allocation, permission to increase production caps, or a recommendation to run without Root's separate decision. No actual coordinates, current-state rankings, pair outcomes or geometry were read/computed for this review.

Design bindings:

- `research/two-row-descent75-suffix-continuation-design.md`: `c5b500d632995ed147c16bb6a008c079fc3c1ffd4fc509eeda999be6a6e56d09`.
- `research/two-row-descent75-cursor-ledger-design-addendum.md`: `a61f27e5739aa7c1579313db03a206440ef866a1a046b3cd425ee626952ca427`.
- Prior actual acceptance review: `19f4f83d095da0f82039655bba3aee585a586a646c1f8a62e389a326ce2987d1`.
- Frozen existing worker: `0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c`.

## Historical coverage and deterministic suffix

The accepted saved chain establishes28 legal strict row moves from97 to65 and no pair acceptance. Under the frozen controller, Stage2 either accepts a pair and restarts Stage1, finishes the pair list and terminates, or stops at cap/deadline/error. Therefore there cannot have been an earlier Stage2 followed by a later row acceptance without an intervening accepted pair. Conditional on the source-bound accepted execution, all32 completed pair decisions belong to the final unchanged65 state and form the first32 eligible pairs in its deterministic `(-M,r,s)` list. A genuine `pair_cap` return from inside the loop also implies another eligible pair exists.

That inference is sound at its stated assurance level. It is not an independent proof of the32 minima. Recomputing the exact state's I/J/M ranking and list identity establishes the new ranking, not the old optimization outcomes. The design correctly refuses to invent historical per-pair records or relabel the skip as independent exclusion. It requires the full accepted provenance chain, exact final normalized identity, expected counters/status and no pending old operation before importing cursor32. An independent historical-exclusion requirement would need a different explicitly allocated certificate/replay scope.

Once a new move is accepted, every old cursor and coverage result belongs to the old state. The proposed atomic reset of both cursors, both flags and all stale ranking identities, followed by Stage1 on the new state, is necessary and sound. Reusing the same row labels after a state change is a different neighborhood; preserving old-state skips on that new state would be unsound. Global started/completed counters remain cumulative.

## Strict decrease, caps and finite bounds

The proposed new allowance is64 pair starts beyond32, yielding cumulative96; the original row ceiling512 leaves204 starts beyond308. These are shared totals across every accepted state, not per-state allowances. Current eligibility and strict integer raw decrease remain unchanged. From U65 there can be at most65 additional accepted moves and hence at most93 total accepted moves after the observed28. Interrupted starts remain charged and do not advance coverage.

The stated additional pair ceilings are correct:13680000 partner-column visits,700800 mixed intersections and705664 retained-line visits. Remaining row work is bounded by2249304 retained-line visits and566100 choices. At most66 accepted-state initial/rebuilt indexes plus one pending interrupted build is a conservative bound. These counts do not predict wall time and exclude separately charged input validation, priority rebuilding, hashing and persistence.

The addendum corrects the original64-record ambiguity: all204 possible new row attempts and64 pair attempts require at most268 attempt records, or536 immutable start/result events. The inline component bounds sum below1MiB:268×1024 +2775×64 +75×16 +65×512 +4096 +65536 =556144 bytes before the additional full-payload cap is enforced. Initialization/final publication plus two publications per attempt give538 checkpoint publications. A finite write envelope is not evidence that fsync work fits25 seconds; fresh synthetic persistence/resource measurement remains mandatory before any actual gate.

The proposed stop after64 further nonimproving pairs on the same65 state is a bounded experimental decision, not an exclusion theorem. Ranking by M orders removed old triples, not exact achievable minima; smaller-M later pairs can still improve. Neither this review nor the first32 results supplies a success probability or exact coverage fraction. A useful invalid incumbent does not automatically justify a third allocation.

## Atomic authority and zero exception

The clarified single authoritative tuple binds current points/score/identity, accepted ordinal, phase, state-specific list identities/cursors, flags, cumulative counters, pending attempt and artifact references. Persisting the whole tuple prevents a hybrid of new points and old coverage. A durable pending start precedes kernel work. A completed exact nonimprovement preserves points and advances one cursor only after durable publication. Since current is eligible, its exact nonimproving minimum must equal current U.

A positive acceptance writes its immutable move artifact before the authoritative checkpoint references it, then adopts/notifies the new state only after checkpoint publication. Failure before replacement leaves the old state and charged pending attempt; the candidate artifact is an orphan. Failure after replacement recovers the new whole authority. Uncertain fsync/replace durability fails overall acceptance and requires later explicit review of the single checkpoint actually present. No automatic orphan adoption, retry or counter reset is admissible.

The exact-zero exception remains separate from ordinary durable acceptance: a fully scored zero goes directly to timely validator one/two and immediate witness persistence after successful validator two, even late. Optional ledger/index/raw/report work cannot precede that validation attempt or intervene after successful validator two. A saved witness can survive ledger failure while the last durable active state remains positive and its start remains pending. Those are distinct truthful outcomes; witness preservation does not make a failed receipt accepted. These lifecycle semantics still require independent source tests, beyond this design reasoning.

## Synthetic obligations and three-row sketch

The finite87-fixture parity plan comprises4 n2 states,81 n3 states and two stated n4 states. Split/reload comparison must preserve the entire oracle decision sequence without repeating covered prefixes. Pending retries carry an extra charge and must be compared with that adjusted reference rather than pretending their counters equal uninterrupted execution. The prescribed state/order tampering, publication/crash boundaries, positive-pair orchestration stub and real zero lifecycle cases target the new behavior. The positive completed-no-improvement terminal remains explicitly stub-only; these fixtures produce no genuine positive full-policy local minimum.

The separate three-row score sketch is algebraically correct. With retained R and one/two selected points per row, triples partition into: no-new retained triples; one-new unary terms; two-new cross terms from different selected rows with one retained point; and one-new-point-per-selected-row ternary terms. Two new points on one row plus an off-row point cannot be collinear. The ternary term is essential: three new points `(0,0),(1,1),(2,2)` already form a triple even when all unary/pair-with-retained contributions vanish. Its table is a Boolean determinant result for each4×4×4 combination, including vertical triples.

Four-column restricted domains containing current yield216 full-row assignments (`6^3`) or432 deficient assignments (`3×4×6×6`), with all three1/2/2 orientations. Lexically merging the complete legal assignment set permits first-zero termination with the correct `(U,X,Y,Z)` tie rule. At16 total started blocks,6912 assignments,110592 retained-point pair-cross checks,1024 ternary checks and176416 retained-line visits are conservative bounds. The addendum clarifies that16 is shared across states and interruptions, never renewed after acceptance.

That three-row material remains a structural sketch, not an approved controller or fallback. Unary-chosen four-column domains and16 induced blocks can exclude useful candidates; their exact minimum is only within that restricted family. No genuine reachable pair-stuck/three-row-improving falsifier has been established here, and selection/restart/row-followup policy still requires its own design review. No implementation, point selection or actual geometry for that alternative follows from this PASS.

The design review leaves the existing sources, caps and accepted diagnostic artifacts unchanged. Implementation requires Root's next explicit scope and independent SOURCE/TINY, persistence and resource acceptance before any actual suffix reservation.
