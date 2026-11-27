# Best-single-row domains: independent theorem and one fixed diagnostic design

Status: DESIGN ONLY. This is an independent mathematical review of `research/four-row-overlap-predetermined-fixture-assessment-v2.md`; the Engineer owns any separate implementation design. No fixture was constructed in executable code, enumerated by a program or geometrically evaluated. No actual64 input, optimizer, loader, audit, allocation or continuation was accessed or run. All scores and operation counts below are hand derivations. Earlier memos remain unchanged.

## The theorem is valid, with one proof-wording repair

Let P have2n−1 distinct grid cells, exactly one singleton row and two points in every other row. For row r, let A_r be its current columns and k_r=|A_r|. Let B_r be the lexically first k_r-subset minimizing full raw score while all other rows remain fixed. The domain A_r∪B_r, filled by increasing missing columns to min(4,n), contains both complete assignments and never exceeds four columns.

If any same-load row replacement is strict, B_r is strict because its candidate set contains that replacement and the current assignment. At least one old conflicting triple must disappear: otherwise every old conflict persists and newly introduced conflicts are nonnegative. This repairs step2's sentence claiming that, without removal, old conflicts involving the row would contribute zero. Such conflicts can instead remain present; their persistence is enough to rule out a strict decrease. The theorem's conclusion does not depend on the erroneous stronger wording.

Every disappeared triple contains a point from the changed row, because all other points remain fixed. A collinear triple cannot use two points from that row: their line is horizontal, it contains no point in another row, and the row has no third point. Thus a disappeared conflict occupies three distinct rows r,s,t with current K_rst>0. In that eligible block, put B_r in row r and retain A_s,A_t. Each domain contains these assignments, current loads are preserved, selected total is5 or6 and the singleton invariant remains valid. The resulting full point set equals the strict one-row replacement. This proves existence of a feasible gain in some current eligible block, not visitation by a finite prefix or selection of that gain by a block optimizer.

Consequently, exhaustively certifying no gain for every current K-positive block under these domains would exclude all strict same-load single-row replacements. A partial scan cannot make that conclusion. The theorem does not exclude singleton relocation, arbitrary three-row improvements or improvements after another state change. Comparing with the frozen production selector additionally requires its baseline score ceiling U≤65. None of this reopens the curtailed actual search family.

## A simpler exact row objective

Put R=P\row(r), and define u_r(x) as the number of unordered retained pairs collinear with the candidate(x,r). For any legal distinct-column k_r-set C,

    U(R ∪ {(x,r):x∈C}) = U(R) + Σ[x∈C] u_r(x).

There is no two-new-point/one-retained-point term: two new points have row r and hence a horizontal line, whereas every retained point has another row. There is no all-new triple because k_r≤2. Thus B_r consists of the k_r cheapest columns ordered by(u_r(x),x). This also yields the stated global lexical tie rule for the unordered subset represented as an increasing tuple. It is not necessary to implement a pair-placement optimizer to produce B_r. An independent test can still enumerate all k_r-subsets to verify every value and tie.

The relevant complement here contains every unchanged row. It differs from the production unary ranking after removing all three selected rows. Therefore the theorem is a guarantee for this different domain certificate; it is not already supplied by the old unary ranking. A direct same-load row diagnostic could compute the same B_r without any three-row controller.

## The one predetermined fixture

Fix n=5, singleton row4, and exactly

    P = {(0,0),(0,1),(0,2),(0,3),(0,4),
         (1,0),(1,1),(1,2),(1,3)}.

For a future byte specification, use this exact increasing(x,y) point order. The proposed canonical ASCII content, without a trailing newline, is:

    {"n":5,"points":[[0,0],[0,1],[0,2],[0,3],[0,4],[1,0],[1,1],[1,2],[1,3]]}

No canonical fixture file or executable fixture generator is created by this memo. Its immutable digest would be frozen only with a separately authorized SOURCE/TINY implementation. There is one proposed state, not a seed family, transformed family, actual-state subset or adaptive replacement plan.

All9 points are in the5×5 grid. Rows0..3 each have two points and row4 has one. Every nonvertical line intersects each of the two occupied columns in at most one point, so it contains at most two points of P. The only conflicts are vertical: five points at x0 contribute C(5,3)=10 and four points at x1 contribute C(4,3)=4. Hence U(P)=14≤65, proved without execution. Every three-row set has a conflict at x0; a triple avoiding row4 has K=2, while a triple containing row4 has K=1.

Remove the singleton(0,4). The retained set has four points in each occupied column, so its score is2C(4,3)=8. For a replacement at column c>1, a new conflict must use one point(0,a) and one point(1,b), with0≤a,b≤3. Collinearity with(c,4) is the integer equation

    4 = c b − (c−1)a.

For c2 its solutions are(a,b)=(0,2),(2,3); for c3 the sole solution is(1,2); for c4 the sole solution is(0,1). At c0 or c1 the new point joins a vertical group of four retained points, adding C(4,2)=6. The five possible singleton scores, in column order0..4, are therefore14,14,10,9,9. The lexical winner is B_4={3}, with strict score9. Its new domain is{0,1,2,3}. The lexically first current conflict-row triple containing row4 is(0,1,4), and retaining the complete assignments on rows0 and1 gives the exact score9 embedded repair promised by the theorem.

This state deliberately has **no positive barrier or new-domain separation promise**. In fact, it fails the stronger old-policy exclusion requirement by proof. For the old block(0,1,4), removing those rows leaves columns0,1 on rows2,3. Its singleton-row retained-pair unary costs at columns0..4 are1,1,1,0,0: the two vertical retained pairs give columns0,1; the ascending retained diagonal gives column2; the other diagonal reaches column−1. The production rule therefore adds missing columns3,4,1 to current column0, giving old domain{0,1,3,4}. It already contains B_4. Other selected rows retain their current columns by construction. Thus that original production block has minimum at most9<14. The fixture cannot be promoted as a new-domain-route witness, a production-family local minimum or a four-row coordination barrier, regardless of a later oracle result.

## Main one-input comparator bounds

The proposed primary purpose is checking exact row winners, ties, domain construction and theorem embedding, not searching for a separator. All bounds count calls even if a cache could reuse a repeated state.

The producer's baseline census uses C(9,3)=84 determinants and records U and each row's incident-conflict count. This supplies U(R)=U(P)−I_r. A full row leaves7 retained points; a singleton row leaves8. Computing all five column costs for each row therefore needs exactly the fixed-loop ceiling

    5[4C(7,2)+C(8,2)] = 5(84+28) = 560 determinants.

Producer total:84+560=644 determinants. Selection, lexical ties and increasing-column filler need no further geometric scoring.

The independent determinant oracle scores the baseline, every same-load placement and at most one theorem embedding per strict row. There are4C(5,2)+5=45 placements, including current placements, so at most1+45+5=51 full raw scores. Each contains9 points and uses84 determinants:51×84=4,284. Producer plus independent oracle therefore fits **4,928 determinants**. These are elementary bounded loops; no optimizer, state expansion or fixture search is involved.

A second independent oracle canonicalizes the exact integer line through every unordered pair and groups the union of endpoint identities for each line. A line with m distinct points contributes C(m,3) once. Counting pair multiplicities as though they were point multiplicities would be incorrect. Canonical coefficients(A,B,C), for Ax+By+C=0, are divided by the gcd of absolute coefficients with the first nonzero coefficient positive; vertical and horizontal lines require no special floating-point cases.

Each full9-point score constructs C(9,2)=36 pair-line keys. The51 full-state comparator calls therefore construct at most1,836 keys. To check every producer unary cell independently as well, build retained-line endpoint sets for each of the five row complements:4C(7,2)+C(8,2)=112 further pair-line constructions. For each candidate, sum C(m,2) over retained lines incident to it. There are at most5×112=560 exact line-point incidence checks. The combined line-oracle ceiling is **1,948 pair-line constructions plus560 line-point incidences**.

A future implementation can consequently declare stop-before-work hard caps of6,000 determinants,2,000 pair-line constructions and600 line-point incidences. The Engineer independently proposed the6,000/2,000 primary caps; the retained-line unary check above fits within them and makes its additional incidence counter explicit. These are operation ceilings, not runtime, process-RSS or durability guarantees. No owned gate or execution is allocated by this memo.

## Optional old-comparator arithmetic, outside the primary proposal

There is no reason to execute the old production comparator to decide separation for this fixture: the explicit feasible score9 assignment already decides it negatively. For clarity, if a different future authorization nevertheless requested an exhaustive comparator on this same immutable input, its complete additional accounting is finite and must be separate.

All10 current triples are eligible. Six contain the singleton and have selected total5, giving at most3×4×C(4,2)^2=432 assignments each. Four have selected total6, giving C(4,2)^3=216 each. Thus all old neighborhoods add at most6×432+4×216=3,456 full-state scores. Their direct retained-only unary construction needs at most

    6×3×5×C(4,2) + 4×3×5×C(3,2) = 720 determinants.

Together with the primary51 independent raw scores, that comparator requires3,507×84+720=295,308 independent/direct determinants, before adding the primary producer644; the total including that producer is **295,952 determinants**. Its full-state line keys total3,507×36=126,252. Independent old-unary line tables add6C(4,2)+4C(3,2)=48 pair-line constructions and at most720 line-point incidences. Including the primary unary verifier's112 line constructions and560 incidences gives **126,412 pair-line constructions and1,280 line-point incidences**. This larger comparison is explicitly excluded from the6,000/2,000/600 primary proposal; no cap may silently cover both.

## Meaning of success and failure

A successful future primary test would show that, on this one predetermined state, independent scores agree, the producer chooses the exact lexical row winners, domains are current-inclusive and bounded, and each strict winner embeds in the chosen eligible triple with identical full point set and score. The singleton repair14→9 is already a mathematical expected result. Other row results need not be predicted in advance; they must not trigger adaptation of the input or a second fixture.

A wrong baseline, missing strict singleton winner, wrong lexical tie, disagreement between determinant and line counts, invalid load/domain/identity or exhausted accounting cap rejects that test. An implementation failure does not refute the proven theorem unless the mathematical assumptions or proof are actually invalidated. It grants no replacement state, widened cap, second seed or automatic retry. A clean result supplies a correctness diagnostic only. The stronger new-domain-route criterion is already known to fail here, and no positive result from this state can revive it.

The theorem establishes existence preservation for same-load row repairs. This fixture establishes a concrete in-grid instance within the score ceiling and an honest negative separation control. Neither supports actual64 execution, another chunk of the curtailed family, a three/four-row necessity claim, a149-on-75 construction or a157/158-on-79 construction. Best verified construction remains156 on79.
