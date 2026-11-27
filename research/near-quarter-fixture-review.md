# Independent published-fixture review

**READY / APPROVED** as the published n71 geometry and near-quarter-family
regression fixture. This satisfies the published-fixture gate for the proposed
model; resource preflight approval and scheduling remain separate requirements.

Reviewer: Mathematician agent, gpt-6-astra, high reasoning;2026-11-27. No author
artifact was modified. No n71 or n79 line/CNF model, numerical search, or solver
benchmark was run.

## Primary-source correspondence

I independently opened the
[primary n71 archive entry](https://wwwhomes.uni-bielefeld.de/~achim/no3in/download/configurations/n71_rct4.few)
through the primary download directory and compared its displayed143-character
code with the fixture's full encoded_source string. They agree exactly. I also
read the [primary encoding specification and history](https://wwwhomes.uni-bielefeld.de/achim/no3in/readme.html),
which gives the90-character alphabet, the `c` symmetry-class prefix, and the
row-ordered column decoding. The history attributes the n71 rct4 discovery to
Marijn Heule on2026-08-17. This is an existing construction, not a new result.

The displayed-code SHA-256 is
`f728b616b2ddd11b78b661801f3f3bbf32a40dae3b27be5a220227fd80fed5fd`.
As the artifact correctly states, its separate LF-terminated digest describes
the reconstructed displayed text with one newline. Neither this review nor the
author's metadata claims to have independently hashed original downloaded bytes.
I did not need the secondary mirror to establish the primary correspondence.

## Independent decoding, geometry, and family membership

Using the primary alphabet, I independently decoded the142 column characters
into their71 successive rows and compared the resulting set with the stored
coordinates. The142 points are distinct and lie within0..70 in both coordinates.
I independently evaluated all467,180 three-point integer determinants; none
vanishes. The author's reproducible checker also reran successfully with both
the normalized-slope and cross-product validators. Their normalized certificate
hash is
`76c7c91b909f48a014c0416b520e2205fe30350f7b8f58dff616740910ed9cd9`.

Without calling the model's orbit constructor for this check, I partitioned the
off-diagonal point set by the explicit rotation(x,y)->(y,70-x). Every resulting
four-point orbit lies completely in the fixture, and exactly35 such orbits
exhaust its140 off-diagonal points. The remaining points are exactly(1,1) and
(69,69). No point lies on x+y=70. Thus the fixture belongs to the approved
near-quarter family in its original orientation, with35 selected four-orbits
and one diagonal pair.

The reproducible checker additionally confirms that the approved model expands
its36 stored selected variable IDs to exactly these points, with orbit-map hash
`82c1fcb850886b2d837860512a29ec7274da5739d480bb8b07ac460e76cb019b`.
The independent rotation partition avoids making that model-based comparison
the only evidence for family membership.

This validates the geometry, representation, and provenance of one known
full-target fixture. It does not independently instantiate every n71 line or
establish anything about n79 feasibility, memory, or solve time.

## Reviewed hashes

| Artifact | SHA-256 |
| --- | --- |
| `data/published-n71-rct4.json` | `00a206f24c3044c252a57160c59af6ef39e2312f0132329b123143c2ad0c01d9` |
| `research/check_near_quarter_fixture.py` | `e4b1438b9c461a5bb447170c0198ecfd2b9fa174d1b281435bcc6e694b933cd6` |
