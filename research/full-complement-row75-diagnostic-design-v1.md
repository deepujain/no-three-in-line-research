# One fixed n75 full-complement row diagnostic

Status: DESIGN ONLY. No source implementation, actual input access, geometry, enumeration, numerical allocation or retry is performed. This is a proposed certificate/diagnostic on one state, not a continuation of the curtailed K-positive/four-column triple family. No result becomes the next input, and no row/pair/triple controller is called. All75 rows are included; there is no45-row subset.

The mathematical mechanism is the exact same-load row replacement from `research/full-complement-row-domain-n5-implementation-spec-v1.md`, SHA-256 `9a50e2a36b154a1a3fa0cccde4b221e90e567c4042e0c4611b309697c9f81239`. This design changes the computation for scalability and adds an independent all-cell verification path. It preserves the distinction between a tiny diagnostic, actual acceptance and any later algorithm decision.

## Fixed question and input boundary

Conditional on Root's independent acceptance and separately frozen input handoff, use exactly the n75,149-cell, raw64 state with normalized identity `b72f8f1ad19c2d06e97bd31de96ab57ed7d4d96af19429b27e5b223b82e444f7`. It has74 rows of load2 and one row of load1. The question is the exact minimum full raw score obtained by replacing **each** row by every same-load column subset of0..74, holding every other row fixed. Domains are the full75 columns for this diagnostic; no production domain is searched or widened, since no production neighborhood is executed at all. The singleton remains in its current row.

The point-file bytes and byte digest are intentionally not invented here. Root would first prepare one canonical x/y-sorted ASCII point document (at most16KiB) and a small coordinate-free handoff acceptance record (at most16KiB) from the already independently accepted immutable state. Freeze their exact byte identities and normalized-state interpretation before source review closes. The handoff record must bind the point-file digest/size, n75,149 cells, raw64, normalized identity, accepted provenance identity and Root's acceptance review. A mismatch blocks this proposed input; it does not select another state.

Historical association is a separate prerequisite, not part of this diagnostic algorithm. Reuse the already accepted normalized64 anchor and Root-owned provenance decision. Do not import/run the old51-artifact loader, old report adapter, old authority validator, resume entry point or chain audit in the new worker; do not inherit an old manifest blindly or rebuild its dependency graph. Root must independently review that the new detached canonical snapshot represents that accepted identity. The new entry point then authenticates only its fixed snapshot/acceptance record and its own complete source/runtime closure, structurally validates it and freshly checks raw64. The old history remains preserved and referenced by fixed identities, without being reparsed to compute new unaries. This separation requires an explicit accepted handoff; a merely asserted sidecar is insufficient.

## Exact primary computation

For a row r, current columns A_r, load k_r and full complement R_r, define u_r(x) as the number of unordered retained point pairs collinear with (x,r). The exact replacement score is U(R_r)+sum_{x in X}u_r(x), since two points on row r cannot form a conflicting triple with a retained point. Hence B_r consists of the k_r cheapest (u_r(x),x) pairs, returned in increasing column order. It is the lexical least exact minimum for that row. Its full score is

    V_r = 64 - sum_{x in A_r} u_r(x) + sum_{x in B_r} u_r(x).

Current columns are eligible, so0<=V_r<=64. The overall strict candidate is the least tuple (V_r,r,B_r) with V_r<64. There is at most one candidate point set. Optional current-union-best domains with deterministic increasing-column fill would be output metadata only; omit them from the minimal diagnostic, since no triple optimizer consumes them.

Build one canonical integer line table from all C(149,2)=11,026 unordered current point pairs. Store a pair count q_L for each primitive signed line key a*x+b*y+c=0. All pairs on one line occur, so q_L=C(m_L,2). Recover m_L using exact integer square root of1+8*q_L; require an odd perfect square and an exact triangular equality. Never infer multiplicity from a rounded float. Require valid nonzero primitive line keys,2<=m_L<=149, and sum q_L=11,026. Horizontal lines must have multiplicity2 under the row-valid input. Their raw score contribution is zero.

The fresh line-based baseline is sum_L C(m_L,3), and must equal64. An independent direct determinant census over all C(149,3)=540,274 triples must also give64, on the identical normalized input. These establish the baseline through two formulations; neither historical recorded64 nor the primary unary formula substitutes for this check.

Allocate a75-by75 integer unary matrix initialized to zero. For each nonhorizontal line (a!=0) and each row r, form t=-(b*r+c). If t is divisible by a and x=t/a is in0..74, let e=1 when x is a current column in row r and0 otherwise. Add C(m_L-e,2) to u_r(x). There is no second point from a nonhorizontal line in row r. All pairs contributing to a retained unary have a line in the global pair table, and the correction removes precisely the current row's point on that line. A horizontal line either misses the candidate's row or loses all its points when that row is removed; it never contributes. This gives all5,625 costs without scoring75*75 retained-pair sets independently.

Visit at most11,026*75=826,950 line-row intersections, including conservative allowance for horizontal/invalid intersections. Each cost is an integer between0 and C(148,2)=10,878. Check the independent counting identity sum_r sum_{x in A_r}u_r(x)=3*64=192: each old conflict is counted once for each of its three distinct rows. This is an internal consistency check, not the independent all-cell oracle below.

Release the entire primary pair table before building any independent retained table or candidate validation table. Keep only the input, the5,625 costs and compact scalar records. At no time should a wrapper/prepared alias retain a released table.

## Independent every-cell verification without a five-deep loop

An independently written verifier must not reuse the primary line normalization, pair counts, multiplicity inversion or current-point subtraction implementation. For each row r, construct the actual R_r points and build canonical retained-line endpoint masks from its unordered pairs. Normalize lines by independently implemented primitive direction/intercept rules. The union of endpoint bits on a line gives its true retained multiplicity directly by popcount. This verifies each full complement by construction and requires no subtraction of a current point.

For each retained nonhorizontal line, intersect it once with row r; if the intersection is an in-grid integer column x, add C(popcount(mask),2) to an independent length75 cost vector. Compare all75 costs to the primary row before releasing the retained map and proceeding to the next row. A line-map score U(R_r)=sum C(popcount(mask),3) must also satisfy U(R_r)+sum_{x in A_r}u_r(x)=64. Require equality of every one of the5,625 costs before accepting a complete all-row profile. A sampled row/cell check cannot support a negative certificate.

For74 full rows the complement has147 points, and for the singleton row148. The verifier therefore constructs at most

    74*C(147,2) + C(148,2) = 804,972 retained pair-line keys

and performs at most804,972 retained-line/target-row checks. It retains one row's map at a time, at most10,878 keys. There is no75-column inner pair loop and no C(75,2) row-placement enumeration. The two paths share the mathematical definition and bounded input only; they must have separately reviewed code and geometric encodings.

After complete cost verification, a single pass per row selects its one/two cheapest (cost,x) values. At most5,625 column visits and11,250 ordered-pair comparisons suffice. Complete all75 V_r records before concluding that none improves. Ties use score, then row, then increasing column tuple; current membership receives no unstated tie preference.

## Candidate validation and zero priority

There is no candidate loop, state update, restart or descent. For a positive strict global winner, construct only its149-point replacement. Require the same individual row loads and identical unselected points. Two fresh independent full raw validators—one direct triple determinant census and one independently normalized endpoint-line census—must agree with the predicted V_r and normalized candidate identity before saving the immutable proposal. Release the current pair table first, as required above. Saving a positive proposal does not adopt it as authority, change the input, prove a construction or authorize another diagnostic.

Zero has stronger persistence priority. After the complete primary cost matrix and current baseline checks, screen rows in increasing order. If the first zero row minimum appears, its lexical B_r is the first zero under the global row/column tie rule. Start both independent candidate validators in time; if both confirm zero, immediately save the durable witness and mark its exact reference before optional all-cell/profile/report bookkeeping. A successful second validator finishing late must not cause a validated zero witness to be discarded. A zero-only return may omit the independent75-row cost-profile verification and must say so; it makes a witness claim, not an accepted complete unary-profile claim. Independent actual witness acceptance remains required.

For nonzero output, require all75 independent retained-row checks and the entire profile before selecting/saving the sole positive candidate or reporting no strict replacement. Any candidate validation disagreement rejects the run. No alternate row is tried after disagreement. If an error, source drift or later metadata/publication failure follows a saved witness, preserve the artifact but reject the complete receipt as applicable; artifact existence alone is not accepted evidence.

## Finite work and memory contract

The largest normal path contains at most these geometric work units:

| Unit | Derivation | Ceiling |
|---|---|---:|
| Direct raw triple tests | current plus at most one candidate,2*C(149,3) | 1,080,548 |
| Canonical pair-line constructions | current11,026 + retained804,972 + candidate11,026 | 827,024 |
| Line-row intersection checks | primary826,950 + independent retained804,972 | 1,631,922 |
| Cost columns visited for best-row choices | 75*75 | 5,625 |
| Best-row ordered comparisons | at most2 per cost column | 11,250 |

Proposed shared hard caps, checked **before** each corresponding operation, are1,100,000 raw triple tests,900,000 pair-line constructions and1,700,000 line-row intersections. Multiplicity recovery is at most827,024 fixed-width integer operations across the counted line tables, and coordinates remain0..74 with raw line coefficients |a|,|b|<=74,|c|<=5,476. Row-intersection numerators are bounded by10,952 in magnitude before division. Count normalization/coefficient construction under pair-line work; count line/candidate incidence under intersection work, without disguising either as an uncharged alternate determinant routine. Report primary, independent-retained, baseline and candidate components separately. No counter resets or refunds occur.

There is at most one current/candidate/retained line map live, with at most11,026 keys, a5,625-integer matrix, at most75 row records,149 input points, at most149 candidate points and a constant-size current raw-triple iteration. Retained endpoint masks need at most148 bits. Bound the measured retained object graph by16MiB/100,000 distinct nodes/depth64, with a separate16MiB quota-walker allowance. These quotas require source/runtime-specific checking before actual use; they are not a physical-memory proof. Do not retain all75 retained maps, raw point triples, all possible replacements or old historical graphs. Explicitly verify release of map owners in tiny/source review.

Propose a separate one-shot reservation of25 soft/23 work/30 owned seconds and256MiB, including input authentication, source checks, baseline validators, both cost paths, candidate validation and persistence. This is a proposed ceiling, not an allocation or a forecast from old timings. Both zero validators must start before the25-second soft boundary; immediate validated-zero saving takes precedence over optional bookkeeping even if validator two completes later, subject to the outer30-second owned limit. Positive/certificate completion must respect the work/shutdown policy. Deadline or operation/memory cap failure is incomplete evidence and stops without retry.

Component byte caps: fixed input16KiB, handoff acceptance record16KiB, new source manifest64KiB/256 entries with paths<=1,024 characters, unary artifact64KiB, candidate/witness16KiB and report128KiB. No unbounded descriptive fields or legacy pin-map copies appear in the report. Use at most one immutable unary artifact, one immutable positive-candidate-or-zero-witness artifact and one immutable success report; at most one additional immutable failure report. File and directory fsync are required where claiming durable saves. No mutable search authority, pending cursor or resumable checkpoint is needed. Orphan artifacts are preserved but never adopted by a later invocation.

## Proposed source and validation plan

Only after DESIGN acceptance and explicit source authorization, prepare a pure primary module, a separately authored retained-row/candidate verifier and a small fixed-input driver; paths and hashes will be frozen before tests. No production search-module import is necessary. A pure canonical state-identity helper must exactly match the accepted normalized serialization and be source-pinned; do not approximate that contract. The own source manifest must require **presence and digest** of every direct dependency, runtime/verifier identity, fixed input/handoff record, driver and reviewed evidence. Test mandatory omissions independently of matching listed pins; the earlier three-helper omission is a preserved warning against present-pin-only checks. Pre/post source checks and best-effort failure identity recording are required.

Reuse only the approved fixed n5 two-rail diagnostic for later tiny parity, with separately authorized execution: exact costs, independent retained-map equality, deterministic best rows and a validated embedded one-row gain. Do not introduce another point fixture. Source-only checks may test schema rejection before geometry, synthetic budget boundaries, identity drift and unavailable-source failure preservation. Artificial memory/persistence checks may use declared opaque tables under a separately owned finite gate, and must not masquerade as valid geometry. Freeze exact final source, input and evidence, obtain independent mathematical/lifecycle review, and require Root's complete byte/presence preflight before deciding on a single actual gate. This document performs none of those stages.

## Meaning of a future result

An independently accepted complete no-gain profile would establish that **this exact state** admits no strict same-load single-row replacement over all75 columns, including every two-column choice on full rows. The old partial pair scans and16-block restricted triple scans do not by themselves give that complete certificate. This can therefore add bounded, precise negative evidence without claiming pair/triple locality or global exclusion.

An independently accepted positive candidate would exhibit a strict full-complement one-row repair and exact best same-load row score. It would not prove that the old policy could not find it, that its four-column domains excluded it, that a completed old block failed on the same state, or that simultaneous multirow movement is necessary. The expensive original-production comparator is unnecessary for the diagnostic question and is excluded.

A validated and independently accepted zero would be a construction result requiring its own witness acceptance. An interrupted/error run supplies neither the full no-gain certificate nor permission to repeat. Every outcome returns to Root; there is no new seed, widened neighborhood, third triple chunk, automatic candidate adoption or second fixed-state diagnostic.
