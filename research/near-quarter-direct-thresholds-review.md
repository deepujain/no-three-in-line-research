# Independent direct-capacity threshold review

Approved for projected formula equivalence and the stated tiny/per-support
count evidence. This review does not approve a large run or predict memory
usage. Reviewer: independent Mathematical Reviewer, `gpt-6-astra`, high.

## Frozen identities

| File | SHA-256 |
| --- | --- |
| `src/near_quarter_direct_thresholds.py` | `57a00fe19b711a184e89f6fc31ae429671d34cef42c4c21bc974dce58e0825eb` |
| `tests/test_near_quarter_direct_thresholds.py` | `30d5a3de9c14f325955c2163bc08a6e2c3af05d49fd8790c8d1f9a324f594e32` |
| `research/direct_threshold_estimates.py` | `08222fde0881221702adbb5edc659787bc42a8694c553b00b2e3e20017cd2eb2` |
| `data/direct-threshold-tiny-estimates.json` | `36f1eff33da1a2273849e7ba80cc9e0000f24228ed706c4ac3030e006e01387f` |

## Mathematical assessment

For positive integral weights, the unchanged forced-false and heavy-variable
rules reduce the weighted capacity to the light-variable AM2 requirement and
the guarded light AM1 requirements. Excluding every selected triple is exactly
AM2. For each guard, excluding every selected pair conditional on that guard
is exactly the required implication. The sequential alternatives have the
same projection onto real variables. With several guards, their implications
to a shared gate force AM1 when necessary; when all guards are false, a false
gate provides the required existential extension without restricting lights.
Independent thresholds therefore preserve every real assignment for all
permitted settings, including the trivial support cases.

The full stream retains the frozen diagonal-pair equality, row floors, line
groups and special-diagonal omission. The preceding row-floor and shared-line
proofs consequently continue to apply. Configuration `(5,5)` retains the exact
historical clause sequence and auxiliary IDs; the deliberately new header
still yields a distinct formula identity.

## Independent verification

All six author tests passed independently in 0.190 seconds. These cover every
real assignment on n3/n5/n7, synthetic supports through eight for all nine
cutoff pairs in `{5,6,7}^2`, mixed weights, invalid inputs and baseline stream
identity. The complete tiny grids alone do not distinguish the new cutoffs;
the synthetic tests exercise the changed branches.

I regenerated the count report, restricted by its implementation to complete
n3/n5/n7/n9 clause counts and synthetic supports through twelve. The resulting
object exactly matched the saved report, including all six source bindings
and 1,170 algebra-versus-emission comparisons. No native solver or n79 model
was constructed by this count reproduction.

The support-six/seven costs agree with direct binomial counts and the observed
sequential boundary formulas. In particular, changing both thresholds to
seven for seven lights and two guards changes 42 clauses/17 auxiliaries to
77 clauses/no auxiliaries: 35 additional clauses, an 83.3% increase. Independent
cutoffs permit avoiding that guarded-pair expansion. These finite checks
confirm changed-support arithmetic; they are not a universal native-counter
implementation audit.

## Limits

No n79 geometry generation, enumeration, build, search or benchmark was run by
this reviewer. Fewer auxiliaries do not establish lower resident memory or
faster solving. A separately reviewed, configured, source-bound guarded
build is required for large-model resource measurements. There is no new
witness, exhaustion, UNSAT, novelty or unrestricted infeasibility conclusion.
