# Independent mathematical review: tiny near-quarter packed state and MRV

Reviewer: Mathematical Reviewer (`gpt-6-astra`, high). Scope: source/proof review,
four tiny correctness tests, saved-evidence comparison and arithmetic only. No
n79 construction, enumeration, search or benchmark was run by this reviewer.

## Frozen approval

| Artifact | SHA-256 |
| --- | --- |
| `research/near_quarter_tiny_secants.py` | `305562c35e305a975ad8232b478c082aa44040b8e6b7bf26a3e99ef1a59e232a` |
| `tests/test_near_quarter_tiny_secants.py` | `24406fb3660c2c6822e613023ed07996ca2aa904de16fde8feb6b24a4918954e` |
| `data/near-quarter-tiny-secants-evidence.json` | `ce40a8fb1651afc755516ea9ec09710b8d68dd287aeb1822a721d583504c0a00` |
| `research/near-quarter-packed-mrv-proposal.md` | `2d107069223b49ce57346a4c25e66421381d6aff2c0f6704f5eb82d59b48c246` |
| `research/near-quarter-mrv-order-addendum.md` | `431dfcf8ffae435d4a771a2109b2f60597f1e9070cfbdf7b5380b7acadb1b76f` |

Approved as a tiny reversible-state/MRV correctness prototype and analytical
proposal. This is not approval of a production engine, checkpoint/resumer,
large-grid allocation or runtime/memory forecast. The only requested correction
was the module header's misleading “no DFS,” now “no production DFS.” Evidence
was regenerated because the order identity binds the complete source hash.

## Invariant and completeness

Primitive gcd stepping enumerates the entire lattice line. Each cell's counter
counts unordered selected pairs whose lines contain it, including endpoints.
Only fresh unoccupied cells are queried; a positive counter then exactly detects
a new triple with an old pair. Sequential insertion also catches triples with
two or three points from the new orbit. Reverse point removal subtracts exactly
the newly introduced pair incidences. Failed pushes restore the prior selected
state, row/column loads, occupancy and counters. The target/type caps imply at
most 158 selected points at n79, and hence counter bound C(158,2)=12,403, safely
within uint16. This is a width bound, not a process-memory measurement.

With a fixed diagonal pair, every valid full extension contains exactly the
remaining number of four-orbits. Each is individually admissible at every
prefix. Thus the global viable-orbit shortfall and optimistic top-r row-load
shortfall prunes are necessary conditions. Every full extension contributes
some orbit to the selected underfilled row; visiting every orbit in that domain
preserves a completion path. No global increasing-ID constraint is imposed.
Probe push/pop restores state, so domains are recomputed from exact geometry.

## Independent tiny validation

Four tests independently passed after the docstring correction in 0.755 s. The
entire regenerated census, including six source-bound permutation identities,
exactly matches the saved evidence. Its four source bindings also match disk.
An earlier independent pass before that correction took 0.742 s.

At n3/n5/n7, all 4/64/4,096 orbit subsets yield respectively 4/17/100 valid
partial subsets and 1/0/0 full sets. All 8/102/1,200 extensions are checked,
with determinant-based counter reconstruction and exact rollback snapshots.
All tiny point-pair grid lines match independent determinant membership.
Forward/reverse MRV trees each visit 2/5/17 nodes and 1/0/0 full leaves; global
shortfall prunes are 0/3/10 and row shortfall prunes 0/0/1. Tiny node limits
report incompleteness. Both state and traversal reject n9/n79.

The proposed packed payload arithmetic totals 68,700 bytes; the conservative
path update bound is 79*C(158,2)=979,837 cell increments plus comparable undo.
Python/native/runtime/stack/allocator/serialization/monitor costs are explicitly
excluded, and neither calculation predicts RSS or throughput.

## Order addendum

The current one-orbit MRV rule can visit a full set along multiple paths. For
any fixed full extension, its remaining contributors to the chosen row number
at most two. The stated recurrence and coarse min(m!,2^m) multiplicity bound
are sound. Changing orbit order reorders an exhaustive tree; changing row ties
can change its tree and multiplicities. Any permutation can change a limited
prefix. Tiny 1/0/0 full-set counts do not establish general uniqueness.

The proposed full-row unordered-batch alternative has a sound uniqueness and
completeness argument: a valid extension uniquely determines the singleton or
pair that fills the deterministic chosen row. Distinct batches at a divergence
cannot later merge into an admissible state because their union exceeds that
row's remaining capacity. This proof assumes exact transactional batch validity,
set-determined row choice and once-only batch generation. The alternative is
unimplemented and requires separate tiny rollback/census/frontier tests. A new
batch cursor and node-phase schema cannot inherit approval from the one-orbit
proposal. No production checkpoint mechanism has yet been validated here.
