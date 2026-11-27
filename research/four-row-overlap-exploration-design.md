# Four-row overlap: exploration design assessment

Status: EXPLORATION DESIGN ONLY. No source, cap or historical artifact is changed. No actual coordinates, index, ranking, domain, fixture search, loader or optimizer is inspected or run. The conditional immutable64 continuation in `research/restricted-three-row64-conditional-continuation-design.md` remains a separate candidate. This memo grants no numerical allocation, fallback or implementation permission.

## One distinct hypothesis

Hypothesis: two old conflict triples that share two row labels may require coordinated changes in their four-row union to obtain a strict raw-score decrease within fixed finite domains, even when every replacement changing at most three of those rows fails to improve. The fourth row could remove conflicts introduced by repairing the overlapping triple. This is an existence/mechanism hypothesis; there is no evidence yet that the actual64 state has such a barrier.

An eventual structural family could consider only four-row sets formed by the union of two current K-positive row triples sharing exactly two rows. This excludes enumerating every four-row set. If U is at most64, at most64 distinct K-positive triples and at most C(64,2) such edge pairs exist, before duplicate unions are removed. That ceiling is symbolic; no actual candidate set is computed here. It changes simultaneous row support and eligibility rather than extending an old prefix, choosing another seed or increasing four-column domains.

The accepted actual three-row-selected move supplies no necessity evidence for this hypothesis. Root additionally reports that only two of the three selected rows changed; the third retained its current assignment. Treat that observation as selection-route progress, pending the applicable independent acceptance, never as escape from pair-stuck behavior or proof that three-row simultaneity was necessary. Prior pair coverage was partial. The same caution would apply to a four-row-selected improvement changing only two or three rows.

The new mechanism does not require a quartic objective. Conflict counts concern triples, so deleting four rows still gives an exact decomposition into retained base, four unary vectors, six retained-point cross tables and four all-new ternary tables. There is no four-new conflict term. Equal-column diagonals and every ternary table remain mandatory. A proposed implementation that adds or assumes an irreducible four-point collinearity penalty would be testing the wrong objective.

With four fixed four-column domains, legal loads are 2/2/2/2 for total8 or all four permutations of 1/2/2/2 for total7. These yield 6^4=1,296 and 4*4*6^3=3,456 assignments, respectively. Current assignments remain eligible. This is a separate finite neighborhood, not a claim that its independently recomputed unary domains contain the production three-row neighborhoods: removing a fourth row changes those unaries and therefore can change the chosen domains.

## Falsifiable separating test

A useful real-grid witness must establish more than “a selected four-row block improves.” For one fixed row-valid synthetic state P, four-row block B and common per-row domains D containing current columns, compute exact raw minima for the full four-row neighborhood and for each of its four faces obtained by holding one row at its current columns. Keep all legal singleton orientations on each face. Require:

    minimum_four < U(P)
    minimum_each_of_the_four_three_active_row_faces = U(P).

Every assignment changing at most three selected rows lies on one of those faces. Thus these inequalities prove a genuine need to change all four rows for that state and those common domains. They prove no unrestricted three-row exclusion or actual64 barrier. Global lexical ties and current inclusion must be independently checked by direct determinant enumeration. Comparators with separately recomputed three-row domains cannot substitute for the common-domain faces.

For evidence specifically against the existing production policy, require one additional comparison: on the same state, every eligible K-positive production three-row neighborhood, using its own reviewed current-plus-unary domains, has minimum U(P). This is distinct from the face test. Passing just one comparator does not establish the other. A four-row candidate that improves because its removal-dependent domains expose a different column is domain-route evidence, not evidence of four-row coordination.

The reviewed n<=4 family is a poor place to seek this separation. There are fewer than four rows below n4. At n4, a four-row four-column neighborhood is the whole grid's row-valid family, and any existing reviewed three-row zero assignment lies on one of its four common-domain faces. For every positive state covered by such a trace, the face minimum is zero, so the displayed separation is impossible there. Root reports the exhausted small-order full-policy traces reach zero directly; their exact coverage should be cited from the existing review rather than rerunning the family or upgrading a selected-fixture result into a broader theorem. Existing n4 examples are useful negative controls, not a new positive escape experiment. The earlier absence of a genuine positive full pair-local minimum at n<=4 also supplies no larger-order four-row witness.

An optional abstract mechanism check can enumerate exactly sixteen binary row-choice vectors with energy

    E(x) = 1-x0 + sum over cycle edges (i,j) of [xi != xj],
    cycle = (0,1),(1,2),(2,3),(3,0).

At all-zero its energy is1; all-one has0; any proper nonempty flip has at least two cycle boundaries and cannot improve. This is a nonnegative unary/pair energy and demonstrates the abstract coordination mechanism without any quartic term. It is not a collinearity configuration, geometry witness, current-source result or reason to allocate an actual run. Its exact sixteen-value test would falsify a mistaken mechanism derivation, but cannot establish that this energy embeds in a legal grid state. No enumeration is performed here.

## Bounded future evidence and rejection

There is presently no authenticated real-grid separating fixture for this hypothesis. Do not silently search n5+, try seeds, reuse actual coordinates as a fixture, or widen a synthetic family to obtain one. A future SOURCE/TINY request would first need an independently reviewed immutable input specification for exactly one explicit synthetic state with 5<=n<=8, one explicit four-row block and its selection rationale. Fixture construction or search, if separately desired, needs its own finite design and explicit allocation. This memo does not authorize it or select that input.

Given such a fixed input, a one-case oracle validation can have a finite work contract: at most3,456 four-row assignments plus at most4*432 face assignments, and at most C(8,3) production three-row blocks with at most432 assignments each. With at most15 points, direct raw scoring uses at most C(15,3) determinants per assignment. The displayed comparisons therefore fit below fourteen million raw-score determinant tests; reserve a hard fifteen-million total determinant budget for baseline/table checks as well, with explicit accounting that stops rather than overruns. A later proposal could request a separately owned fifteen-second/128-MiB SOURCE/TINY gate; neither this budget nor that gate is reserved here. One predetermined input, one block, no retries and no adaptive fixture expansion are essential. All new tables, multiplicities and legal orientations must match the independent direct scores before any controller design is considered.

Reject promotion if any score/table/current-inclusion/tie check fails, if any common-domain face improves, if an eligible production three-row neighborhood improves, if the fixed block is outside the proposed overlap family, or if no strict four-row gain appears. A resource interruption is incomplete evidence, not a positive result and not permission for another case. An abstract energy check, control stub or four-row move changing fewer rows cannot pass the geometric promotion criterion. Failure on one fixed input rejects that proposed evidence; it does not prove that no larger-order witness exists. Do not extend the search automatically after a negative result.

This is not another chunk of a curtailed row/pair/induced-three-row prefix: the intended new question is strict separation by simultaneous row support, with both domain effects and selector effects controlled. It is also not currently ready for an actual branch. Without a real geometric separating witness, the four-row idea remains lower-priority exploration. The independently accepted new64 state, if available, is still a reason to review the separate bounded unchanged-policy continuation, not to run both candidates or to append an automatic structural fallback.
