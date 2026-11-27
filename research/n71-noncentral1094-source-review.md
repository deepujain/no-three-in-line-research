# First noncentral repair: source and arithmetic review

Approved one Root-owned 30s/256MiB gate with soft25 for the pinned n71 fixture and its lexicographically first noncentral four-orbit only. Source SHA256 `8bcaa053a84302a70f8a243fd147d8e566df2b01761cbe5b466c45a12d0b2b69`; pins-file SHA256 `a3648ef0ab3a4ae515b841f956fbb7da3f0d8fc18521111616aa84bb9d9194a5`.

Independent fixture grouping confirms 34 noncentral full four-orbits and exact first deletion `(0,19),(19,70),(51,0),(70,51)`, inner radii 16 and 35. All five added edges lie among these and outer radii 36..39. Two orientations of each radius pair give 30 edges. Required degrees are one at each inner vertex and two at each outer vertex. Exhaustive five-edge subsets yield 1,094 choices including 51 exact readditions.

Independently ran all 18 noncentral, central, and boundary tiny tests: passed in 0.799s. Tests compare all 142,506 raw five-edge subsets against actual n13 row loads, exercise overlap rejection, exact filters, dual final checks, early witness saving and partial timeouts. The n13 test boundary is a valid prepared retained subset; it is not a claimed complete tiny source fixture. Current pins all match. No n79 geometry was run during this review.

The frozen central helper supplies exact determinant rejection and atomic saving. Retained overlap is separately rejected; every surviving candidate receives exact cardinality and row/column checks followed by both final geometry verifiers. A complete negative would close only this fixed deletion, not the other 33 noncentral cases or global n79 existence.
