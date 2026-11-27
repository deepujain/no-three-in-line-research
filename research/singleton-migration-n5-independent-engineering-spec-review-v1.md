# Independent engineering review of the migration n5 specification

Verdict: SOURCE/SPECIFICATION PASS with the two narrow contract clarifications explicitly accepted by Root below. Reviewed specification: `research/singleton-migration-n5-source-tiny-spec-v1.md`, SHA-256 `e00ed95695cd77cd6986938557279755c3cd41a1fef940f642107e7f9260dcf3` (6,538 bytes). The mathematical design `9348e40a25c2c57a3bcbc117262cc93901f0b0ea0ff30309346ce240d40809b3` was also inspected. This review performs no implementation, fixture decoding, migration geometry, numerical evaluation or resource allocation.

The removal/insertion score is exact: deleting p removes d(p) old conflicts, and insertion adds c(q) minus exactly h(p,q) old pairs containing deleted p. Since that difference is nonnegative, d(p)=0 cannot give a strict gain. The fixed n5 input gives exactly eight removable cells and four empty destinations, hence 32 legal moves. The stated key uniquely identifies each move and supplies a deterministic complete tie order without a claim about lexical complete-state order. Independent reconstruction of every d/c/h value and all 32 scalar scores supports the declared minimum without scoring 32 candidate point sets. Only the sole selected strict candidate receives fresh direct and endpoint raw checks.

The stated conservative work ceilings are consistent: 312 determinants, 72 pair-line constructions, 144 line/destination incidences, 72 cached multiplicity recoveries, 360 current-line endpoint visits, and at most 64 scalar move evaluations and 64 move-key comparisons across producer and oracle. The endpoint bound follows from the total endpoint incidences being at most twice the number of current point pairs, for each of the five d/h passes. Candidate raw line scoring needs multiplicity recovery but no per-endpoint d/h pass. A later implementation must charge these declared operations before performing them and must not hide geometric work inside an uncharged helper.

Root accepted these implementation limits directly; they require no new design cycle:

- In addition to the producer's nine d values, four c values and 36 h values, the independent checker may retain nine independent d values and one reusable nine-value h vector. It may verify c and h one destination at a time. This resolves the original storage list's omission of independent accumulator workspace.
- The shared hard publication ceiling is **three attempted writes**: at most one evidence artifact, one candidate-or-witness artifact, and one separate failure artifact. Failed attempts count. Existing artifacts are preserved; no automatic retry, candidate substitution or partial acceptance is permitted.

The fixture already has same-load gains, so a successful tiny gate would verify this mechanism and its bookkeeping only. It would establish neither migration escape from a same-load local minimum nor a result on the actual n75 state. Exact-source review and Root's separately owned tiny gate remain required before geometry.

## Conditional actual-state handoff and arithmetic bounds

This appendix is planning arithmetic only and allocates no actual migration run. Reuse the accepted detached snapshot `data/full-complement-row75-fixed64-points-v1.json`: 1,166 bytes, normalized/byte SHA-256 `b72f8f1ad19c2d06e97bd31de96ab57ed7d4d96af19429b27e5b223b82e444f7`, together with its existing handoff `6fc5cea2902fc361421238dbfb9d02513e0ff390d122a81b2238ca83a64c0a3c` and independent handoff acceptance `f6a0165b0c3ffa2d367a8226abe9bbd2899977cee7f6ffb7953d3cb3b575e1ad`. A later loader would authenticate that same fixed identity, independently validate its shape and freshly require raw score 64. It must not open the handoff's three historical provenance files, inherit the old history graph, adopt the all-row output as a new state or select a replacement fixture. Root's final accepted all-row receipt can supply the separate no-gain prerequisite; that receipt does not replace fresh migration baseline checks.

For n75, N=149, there are 148 removable cells and 74 empty singleton-row destinations, hence 10,952 legal relocations. A direct scaling of this exact mechanism gives these conservative maxima:

| Work unit | Maximum |
| --- | ---: |
| Producer baseline triples | 540,274 |
| Producer destination/pair determinants | 815,924 |
| Sole candidate direct triples | 540,274 |
| Shared determinants total | 1,896,472 |
| Current plus sole candidate pair-line constructions | 22,052 |
| Current line/destination incidences | 815,924 |
| Cached current/candidate multiplicity recoveries | 22,052 |
| Current-line d and all h endpoint visits | 1,653,900 |
| Producer plus independent scalar scores | 21,904 |
| Producer plus independent move-key comparisons | 21,904 |

Producer storage would be d[149], c[74], h[74][149] (11,026 h values), plus independent d[149] and reusable h[149], fixed input, at most one candidate and one line map of at most 11,026 keys. These are arithmetic/storage ceilings, not a timing or physical-memory proof. A later actual proposal must freeze its exact sources, numeric pre-operation caps, bounded artifact sizes and Root-owned time/memory limits before execution. No controller, new history adapter or broader algorithm framework is needed.
