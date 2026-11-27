# Independent direct-threshold count/build preflight review

Adapter source and final CLI route approved for actual-host tiny validation.
The actual-host gate remains pending. Reviewer: Mathematical Reviewer,
`gpt-6-astra`, high. No n79 geometry,
model construction, enumeration, search or benchmark was run by this reviewer.

## Frozen identities

| File | SHA-256 |
| --- | --- |
| `research/near_quarter_direct_preflight.py` | `4b9a4d0d07a46a9a572a54c6f6ec01b83a18ac1c6af53c01d81b4db92c9c6b92` |
| `tests/test_near_quarter_direct_preflight.py` | `033a8ab8e94847200ecd5d9293560ef9a58afd91c7fde8560283b33e43115102` |
| `src/lazy_sat.py` | `da2bd2585ebe76ac624cfd608b56b7401ad9bfbe8656b49005777c5f8f4b1d03` |
| `src/near_quarter_direct_thresholds.py` | `57a00fe19b711a184e89f6fc31ae429671d34cef42c4c21bc974dce58e0825eb` |
| `research/owned_process_guard.py` | `c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48` |

The final dispatcher adds an isolated `--near-quarter-direct-preflight` route
forwarding the remaining arguments to this adapter before ordinary parsing.
The existing checkpoint route preserves its process-start clock handling.
The new preflight route retains the historical helper-interval timing scope.

## Exact aggregation argument

The streamed C4 groups are the frozen reviewed groups. Omitting only special
diagonals, each group is classified by counts of light coefficients, heavy
coefficients, forced-false coefficients and distinct diagonal guards.
Coefficients greater than two each emit exactly one unary clause, irrespective
of their original magnitude. Every other capacity construction depends for
its clause count, literal count and fresh auxiliary count only on these four
class sizes and the two explicit thresholds. Renaming distinct real variables
and translating fresh auxiliary IDs do not change those costs.

The adapter measures installed encoder emissions for one synthetic group of
each observed class and multiplies by the histogram frequency. This is exact
count aggregation, not a modeled RSS estimate. The fixed diagonal equality is
measured directly with the same counter. For n=2m+1, each of m noncentral row
representatives has n-1 distinct light variables, contributing n-1 clauses of
length n-2. The central row has m heavy variables and contributes one clause
of length m. Thus the added row totals are m(n-1)+1 clauses and
m(n-1)(n-2)+m literals, with no auxiliaries. Fresh per-group counter ranges
make the aggregate auxiliary sum equal to the full stream's allocation.

Count mode evaluates all nine threshold pairs in `{5,6,7}^2` from one complete
histogram. It never constructs a Solver or a complete formula, and correctly
leaves both full-formula digest and native-build flags unset. Build mode emits
the selected complete stream into Glucose, hashes the explicit header and
ordered clauses, and cross-checks clause, variable and literal totals against
the histogram result before reporting completion. Neither mode calls solve.

## Guards and acceptance

The adapter binds ten sources and checks them before encoder import, after
worker completion and in the parent. The reviewed owned-process helper
enforces the unchanged sampled 256 MiB and 30-second maximum gate over its
worker/cleanup interval. Parent setup and final receipt serialization fall
outside that interval; neither an end-to-end hard wall cap nor a continuous
hard memory cap follows. The cooperative worker deadline and parent-alive
checks add early stopping but do not replace the external helper.

Worker exceptions and cooperative stops clear count/histogram acceptance and
formula/build completion while retaining diagnostic rows. Parent helper or
source failures also override worker completion, clear accepted totals and
the full model digest, and preserve counters only as diagnostics. A worker
can emit a terminal state before solver deletion, but a deletion failure or
overrun is still rejected by the helper/parent. The helper's observed-session,
sampling and cleanup limitations remain as documented in its own review.

## Independent checks

The initial nine tests independently passed, with one explicit actual-host
test skipped, in 0.195 seconds. After the final forwarding test was added,
all ten non-host tests passed again in 0.216 seconds, with the same host test
skipped. Final dispatcher and test hashes were independently checked.
Count mode matched clause/variable/literal totals from full
tiny n3/n5/n7/n9 streams for every threshold pair while Solver construction
was forbidden. Native n3/n5/n9 builds matched exact formula digests while both
solve entrypoints were forbidden. Tests also exercise aggregate mismatch,
source changes before/after counting and in the parent, expired deadlines,
parent disappearance, signal handling, explicit configuration requirements,
and all helper failure statuses overriding acceptance.
The final test additionally verifies isolated CLI forwarding and rejection of
solve mode.

No full-model digest follows from count mode. A successful build establishes
only construction under its measured interval, not solve-time memory safety,
SAT, UNSAT, a witness, search exhaustion or unrestricted infeasibility.
