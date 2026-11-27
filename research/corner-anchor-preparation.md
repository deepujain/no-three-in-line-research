# Corner exact-five anchor preparation

Prepared2026-11-26 by the Mathematician agent. No numerical repair case was run
as part of preparation. The mathematical coverage proof and memory bounds are
in `research/symmetry-next.md`; the runtime worker is unchanged.

`research/corner_anchor_frontier.py` derives blocker pairs from the actual
cut(0,0) embedding, which translates every source point by(+1,+1). There are410
eligible new cells with at most five disjoint blocker pairs. Their10,440
endpoint covers are distinct. Removing covers that properly contain another
cover leaves10,304 anchors:

| Base size | Anchors | Exact-five supersets per anchor |
| --- | ---: | ---: |
| 2 | 8 | 596,904 |
| 3 | 224 | 11,628 |
| 4 | 1,936 | 152 |
| 5 | 8,136 | 1 |

The sum is7,682,312 cases **counting duplicates between anchors**. It is not the
number of distinct deletion sets. All anchors must finish to close this
exact-five corner family; a handful of completed anchors does not do that.
The already-completed<=4 neighborhood is a separate result.

The immutable `data/corner-anchor-frontier/manifest.json` contains the full
antichain, witness new cells, source and ordered-source hashes, sizes, and
distinct origin/tip names. Its SHA-256 is
`e45bfeaed19f5b519a8cdda3ab411bbf874ca365903d46c7cadd802ab64137a1`.
Preparation generated only three initial one-case origins00000..00002.

Following the parent's request, three additional size-two origins10296..10298
were generated directly with the existing `stream_cover_repairs` function and
`max_cases=0`. Their bases are[40,52], [40,88], and[52,70]. Each contains596,904
exact-five supersets. All three passed `load_gapless_chain` at offset zero.
Their file hashes and absolute worker input/output paths are recorded in
`data/corner-anchor-frontier/additional-size2-origins.json`; the original
manifest was not modified. Seed input is `data/published-n78.json` and scan
input is `data/embedding-audit.json`. Source point order must remain unchanged.

The three focused author tests in `tests/test_corner_anchor_frontier.py` passed:
synthetic endpoint-cover versus direct blocker-hitting equivalence, all tiny
corner deletions versus the derived antichain, and zero origins versus the
existing engine plus gapless-chain validation. These tests do not enumerate
the n79 five-deletion neighborhood. Independent reviewer approval is tracked
separately and is not implied by these author checks.

Preparation alone is not a queue action. No running code or queue was edited.
