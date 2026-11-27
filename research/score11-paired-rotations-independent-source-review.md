# Independent source/tiny review of frozen paired rotations

PASS for one prospective Root-owned soft25s/30s256MiB evaluation, subject to
Root allocation, source pins, fresh output and no overlap. No actual score11
geometry or search was run in this review. Source
`research/score11_paired_rotations.py` SHA-256
`c8bf0c8c1b5b7681c1ef2230bb81639900cbf93ce0b1ace00976d63f32ae1b10`;
tests `003621dc3440bc03476e35e283a42c78d34255b457eaed8f0a31a60a1864efc1`.
Two tiny tests pass independently in0.012s. Complete local dependency pins are
`data/score11-paired-rotations-independent-source-pins.json`, SHA-256
`a6d7f5b29559602ec2f2ab4f8467fd38cc2ef45e184f59bd7435cdd3da2c487c`.

Both matching rotations are simultaneous; each remains a permutation, and
cross-matching collisions are tested on the combined final state. Effective
source deletion is computed after possible cancellations. The old-triple filter
soundly rejects only candidates whose surviving old conflicts have no common
one-point cover. Every survivor's complete new conflict intersection is then
computed; no conflicts means a valid158 candidate, while any common point can
be removed for157. Both independent full validators precede atomic witness
persistence. No cap-five closure is assumed or used. Full completion requires
all144,400 tuples; scope remains one decomposition/incident-row pool, not all
six-deletion or general repairs.

`processed` and `geometry_checked` increment before a geometry call finishes.
They count started combinations/checks and cannot be treated as a durable
finished prefix if geometry is interrupted. Timeout remains incomplete and
there is no resume mode. Complete validators and writes are not interrupted
internally; Root's existing owned guard supplies actual limits. A hard kill
can leave no final report. Atomic publication inherits existing file-fsync/
rename semantics without directory-fsync crash guarantees.

A separate combinatorial census used only pinned source edges and the stored
independently audited11 conflict triples, with no new collinearity/scoring or
verifier calls. It found144,400 tuples:17,190 collisions,5,466 old-conflict
rejections and121,744 geometry candidates. Of these,28,017 hit every old triple;
93,727 require a one-point common cover of surviving old triples. Effective
removed-set sizes among survivors were113,359 of size6,8,315 of size5,69 of
size4 and one of size3. This is not a measured geometry gate or improvement.

The current geometry helper materializes every triple even after the running
intersection is empty. Streaming exact normalized-slope triples and stopping
on empty intersection is sound because intersection cannot grow; a nonempty
cover or no-triple result still requires completing the scan. This is a
well-motivated separate author variant, requiring its own source/tiny review.
The frozen source above was not modified. Root may defer its baseline run in
favor of that separately reviewed variant; neither has been launched here.
