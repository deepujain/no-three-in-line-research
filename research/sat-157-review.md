# Independent review of the 157-point SAT model

Reviewer: Mathematician transitioning to Mathematical Reviewer of the Research
Software Engineer's SAT implementation. Assigned model `gpt-6-astra`, reasoning
`high`. Date: 2026-11-26. This review contains no new large numerical search.

Status: **approved** after independent implementation inspection and rerunning
the seven small-instance SAT tests. No correction was required. This approves
the stated encoding and witness checks, not any claim of a new order-79
witness or an independently certified UNSAT result.

## Exact deficit equivalence

For an n-square, let X_(x,y) be the Boolean for a real selected grid point.
Write R_y=sum_x X_(x,y) and C_x=sum_y X_(x,y). Suppose all row and column
counts are at most two, and the total real-point count is 2n−1. Then

    sum_y (2−R_y) = 2n−(2n−1) = 1.

Each summand is a nonnegative integer. Exactly one is one, and every other
summand is zero. Therefore exactly one row has one point and all others have
two; no row is empty. The identical argument applies to columns. At n=79,
this characterizes 157 points under the axis-line caps.

Introduce independent Boolean row deficits d_y and column deficits e_x, with

    sum_y d_y = 1,       R_y + d_y = 2 for every y;
    sum_x e_x = 1,       C_x + e_x = 2 for every x.

Every real configuration with total 2n−1 and axis caps has a unique assignment
to these deficit variables: d_y=2−R_y and e_x=2−C_x. Conversely the displayed
constraints force R_y,C_x to be one or two, and summing the row equations
forces exactly 2n−1 real points. Thus the projection of this Boolean formula
onto the real cell variables is exactly the desired axis-constrained set.
Column constraints are consistent with the row-derived cardinality; they
enforce the additional necessary column cap.

This argument is about actual real-point counts. Auxiliary counter variables
and deficit variables are not grid points and must not be counted or sent to
the geometry verifier. Exactly-two rows and columns continue to be the
appropriate separate model for target 2n.

## The deficit intersection may already be occupied

The unique deficient row and deficient column need not meet at an empty cell.
An explicit valid five-point configuration in the 3-square is

    {(0,1), (1,0), (2,0), (1,2), (2,2)}.

Its deficient row is y=1 and its deficient column is x=0. Their intersection
(0,1) is itself a real selected point. The other four points form a rectangle:
their pair-lines have x=1, x=2, y=0, y=2, y=2x−2, or y=−2x+4. None contains
(0,1), and the rectangle has no collinear triple. This verifies the example
without a search.

Consequently a model that insists on inserting one distinct empty "ghost
cell" to complete row/column degrees would exclude legitimate solutions.
Independent row and column deficit Booleans avoid that restriction. The model
must also avoid fixing the deficient row or column at an arbitrary position;
square symmetries do not act transitively on all row indices.

## Geometry cuts are shared by both target cardinalities

For any three distinct real cells a,b,c on one integer line, the clause

    not X_a or not X_b or not X_c

is necessary for every no-three-in-line witness, irrespective of whether its
cardinality is 157 or 158. A checkpoint containing only correctly validated
real-cell geometry triples may therefore be reused across both targets on
the same grid and the same real-variable mapping. This does not justify
reusing target-specific cardinality clauses, SAT internal learned clauses,
auxiliary IDs, or a native solver state from another model.

An axis-plus-partial-geometry formula is a relaxation containing every valid
target witness. A verified SAT witness establishes existence. A timeout,
cut limit, or interrupted solve establishes neither existence nor
nonexistence. Solver-reported UNSAT remains conditional on the encoding and
solver unless an independent proof certificate is checked. The current
research program does not claim such a checked UNSAT proof.

## Stable implementation reviewed

- `src/lazy_sat.py`, SHA-256:
  `467b3d9b3b76ef5bf381723050fe117d6c70705da318b49cfcf73e960f40eab1`
- `tests/test_lazy_sat.py`, SHA-256:
  `a74a4e99538f867f340a37fdbf2149e507c306c87439b91072ba229625c7e80a`

`axis_encoding(n, target)` reserves IDs 1 through n² for real cells by
starting one shared `IDPool` at n²+1. For target 2n−1, all n row-deficit and n
column-deficit indicators are allocated through that pool before any
cardinality counters are built. Both exactly-one constraints and every
exactly-two axis constraint use the same pool. Thus deficit IDs, real IDs,
and generated counter auxiliaries cannot collide. The exactly-two target
continues to omit deficit indicators entirely.

The code includes no arbitrary deficit-location fixing and no assumption
about vacancy at the deficient row/column intersection. Model decoding keeps
only positive IDs at most n². Generated and loaded geometry cuts likewise
refer only to IDs 1 through n²; loaded triples are checked for type, bounds,
distinctness, and actual integer collinearity. Target-specific auxiliary
variables never enter these geometry checkpoints.

`search` and the CLI accept exactly 2n or 2n−1 as the target, retaining 2n as
the default. Boolean, noninteger, and unsupported target values are rejected.
Decoded candidates must have the requested real-point count. Both geometry
verifiers and both cardinality checks must pass before `valid_witness` is
returned. Witness metadata, reports, and progress records use the actual
requested target rather than a hard-coded 2n count. The CLI turns invalid
target errors into argument errors.

Timeout, cut-limit, and solver-reported-UNSAT statuses remain distinct from
verified witness success. The native solver timer and cleanup path were
preserved. As already documented by the engineer, formula construction and
native solver bootstrap precede the interrupt timer, so the time budget is
not an operating-system hard kill during initialization. This review did not
introduce a new large numerical search or assert stronger runtime guarantees.

## Independently rerun validation

The reviewer ran:

```sh
.venv/bin/python -m unittest discover -s tests -p test_lazy_sat.py -v
```

All seven tests passed in 0.675 seconds. The axis test checks **every real-cell
assignment** for n=2,3,4 and both targets, totaling 132,128 assignment/target
checks. Under complete real-cell assumptions, SAT agrees exactly with the
direct predicate "total equals the target and every row/column has at most
two points." Auxiliary variables remain existentially free, so this tests
the projection of the actual cardinality CNF, including possible ID errors.

The explicit five-point occupied-intersection example passes both independent
geometry verifiers and the deficit CNF. Its decoded deficit indicators are
exactly row 1 and column 0, while real point (0,1) remains selected.

The checkpoint test reuses one validated real-cell geometry file in the
sequence target 5, target 6, target 5 on n=3; each run produces a witness of
the requested count accepted by both geometry validators. The saved cut IDs
remain within the real-cell range. Other tests cover invalid targets, exact
full/lazy tiny-grid witnesses, checkpoint rejection/resume, and interruption
of a live native solve.

These exhaustive tiny-instance checks supplement the general equivalence
proof and source inspection. They do not replace the mandatory full exact
verification of any future 157-point order-79 certificate.
