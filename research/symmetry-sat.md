# Exact symmetry-restricted SAT branches

Implementation configuration: `gpt-6.1-sol`, reasoning `high`. These are restricted finite search models, with no novelty claim and no global nonexistence claim. No numerical search or benchmark was launched for this handoff; only small correctness tests ran while the shepherd's three numerical lanes were occupied.

## Worker design and scope

`src/symmetric_sat.py` compiles a named invariant family and delegates all SAT solving, timer interruption, target cardinality, lazy geometry separation and geometry-checkpoint validation to `src/lazy_sat.py`. The base engine received a backward-compatible explicit `extra_clauses` and `scope` interface. Extra clauses may contain only signed real-cell variables `1..n²`, and explicit scope metadata is mandatory whenever they are supplied. They enter only the initial formula. Unrestricted calls retain their previous default behavior.

The existing allowlisted entrypoint now accepts `--symmetry diagonal|halfturn` and delegates to the wrapper through an explicitly supplied engine callable. This avoids monkeypatching globals or import-time solver side effects. The separate wrapper CLI also supports `--symmetry diagonal|half-turn`.

Every report includes the restricted family, symmetry map, target, initial scope-clause counts, and an explicit statement that solver-reported UNSAT applies only to that family. A timeout remains incomplete. UNSAT is not accompanied by an independently checked solver proof. Any accepted witness is checked for the target count, symmetry invariance and absence of collinear triples with both independent exact geometry verifiers. An unrestricted no-three-in-line witness can always be accepted as a lower-bound certificate, but failure in an invariant family does not exclude nonsymmetric witnesses.

## Main-diagonal reflection, target 2n−1

The map is `(x,y) -> (y,x)`, encoded by two implication clauses for each nonfixed orbit. Fixed cells lie on `y=x`. Since the target is odd and all nonfixed orbits have two cells, the number of selected fixed cells is odd. A valid set can have at most two points on that diagonal, hence exactly one fixed cell is selected. The model imposes exactly one diagonal cell directly through a positive clause and pairwise exclusions.

The unique deficient row and deficient column have the same index by reflection. This follows from the real-cell equalities and the shared axis-deficit model; no additional auxiliary-variable coupling is required. The selected diagonal point's index is not forced equal to, or different from, that deficit index. Both possibilities are tested with valid examples:

- n=3: `{(0,0),(0,1),(1,0),(1,2),(2,1)}` has diagonal index 0 and deficit index 2.
- n=4: `{(0,1),(1,0),(0,2),(2,0),(1,2),(2,1),(3,3)}` has both indices 3.

An off-diagonal orbit `{(x,y),(y,x)}` occupies two points of the line `x+y=s`. Selecting two different orbits with the same sum would put four points on that line, so at most one such orbit is selected. If diagonal point `(t,t)` is selected, no selected off-diagonal orbit may have sum `2t`, which would form a collinear triple with it. These exclusions are safe binary clauses only because complete orbits are selected under reflection.

At n=79, target 157 therefore has one selected diagonal point and 78 selected off-diagonal orbits. The branch imposes neither the diagonal point's location nor a particular deficit index.

## Half-turn rotation, target 2n

The map is `(x,y) -> (n-1-x,n-1-y)`, again encoded by orbit equalities. The target is even, so any fixed center cell on an odd grid must be absent. Nonfixed orbits are antipodal pairs. Two distinct selected orbits on the same line through the board center would put four selected points on that line. The compiler groups their exact doubled integer directions and allows at most one orbit per center line.

At n=79, target 158 selects 79 antipodal orbits and excludes center `(39,39)`. This is a viable invariant family to search. The wrapper intentionally does not offer half-turn target 157: on an odd grid, odd invariant size would require the center, and any other selected antipodal orbit would then form a collinear triple with it. On an even grid there are no fixed cells, so an odd invariant target is already impossible by parity.

## Checkpoints, duration and memory

Symmetry-induced clauses are never exported as reusable geometry cuts. In particular, collapsed binary orbit exclusions and orbit equalities are not generally valid outside their family. Geometry checkpoints retain only actual three-distinct-real-cell collinear triples, with the existing independent validation on load. They remain reusable across targets and invariant families after the previous writer has stopped. Every live worker must own separate checkpoint, progress and output paths; no concurrent append sharing is permitted.

The new branch should begin with a fresh geometry checkpoint, following the shepherd's memory observation on the existing large unrestricted worker. No large checkpoint was loaded or copied during this handoff.

The base engine's monotonic deadline accounts for axis encoding, checkpoint load and solving. Its timer interrupts the native solve after initialization, subject to the previously documented caveat that initialization itself is not forcibly interrupted. Symmetry compilation and final independent audits add overhead, separately recorded as `symmetry_compile_seconds` and `wrapper_elapsed_seconds`. The wrapper records peak process RSS in bytes using platform-correct units. Resident-memory limits are enforced by the external process supervisor, not falsely claimed as an internal RSS hard limit. `--max-cuts` can bound new geometry-clause growth; checkpoint input is streamed. The compiler and wrapper create no worker threads; the inherited base engine has its timer/interrupt control thread.

## Correctness tests and frozen sources

The local optional-dependency command passed all 14 SAT tests:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_*sat.py' -v
```

The seven symmetry tests exhaust every real-cell assignment for n=2,3,4 in both invariant families (132,128 assignments), combining the axis model, symmetry clauses and all tiny-grid geometry clauses. SAT agrees exactly with independent direct symmetry, target and determinant checks. This validates positive and negative cases and checks that the optional orbit strengthenings do not exclude any valid small invariant set. Further tests cover both diagonal/deficit index examples, dual-verified invariant witnesses, invalid families and targets, restricted UNSAT reporting, rejection of auxiliary or malformed extra literals, actual delegation through the existing CLI, and sequential geometry-checkpoint reuse across diagonal, half-turn and unrestricted calls. Every saved checkpoint record is checked to remain a real-cell collinear triple.

Frozen review/queue hashes:

| Source | SHA-256 |
|---|---|
| `src/lazy_sat.py` | `a13420853e26e2cd497e88c26d960d95b3bbc76a93279b22a8faa09686ae0415` |
| `src/symmetric_sat.py` | `d18f9ca791ec7c5f5ff22edeb0e35dc7e85caf07825b609b7ee4d7b00c4a9b4e` |
| `tests/test_symmetric_sat.py` | `35f0f512c30140004e1ef9efa83acbaa7565f712514f78f64bcbe98c12a4ca4c` |

Both independent reviewers were sent these versions. No queue or supervisor file was edited. Suggested bounded commands, for the shepherd to queue only after review:

```sh
.venv/bin/python src/lazy_sat.py --n 79 --target 157 --symmetry diagonal --seconds 600 --checkpoint data/sat-diagonal157-cuts.jsonl --progress data/sat-diagonal157-progress.jsonl --output data/sat-diagonal157-run.json
.venv/bin/python src/lazy_sat.py --n 79 --target 158 --symmetry halfturn --seconds 600 --checkpoint data/sat-halfturn158-cuts.jsonl --progress data/sat-halfturn158-progress.jsonl --output data/sat-halfturn158-run.json
```

Only one newly available numerical lane should be assigned at a time within the shepherd's global resource and deadline limits. Existing workers already imported the preceding base implementation; the announced source change applies to newly executed jobs.
