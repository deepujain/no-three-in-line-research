# Independent actual audit: conflict-focused tabu pilot

Decision: PASS for the saved artifacts and completed bounded policy receipt. The best remains exactly the initial invalid157-point state with five conflicts. The separately saved D=13 state has45 conflicts and is only a source-distance diagnostic. No157-point witness, score improvement, exhaustive closure or automatic continuation follows.

Report `data/score11-conflict-focused-tabu-v1/report.json`: SHA-256 `37b320a4682a6f18a281b6f4937566b6ac0c3c8994bc16a55b036018d6affa27`.

Receipt `data/experiments/shepherd-score11-conflict-focused-tabu-v1.json`: SHA-256 `58bb81fa946752978aa8f70eabae92fca2417f69f9e3ba994d993ca54e61cd13`.

The initial/best artifact `candidate-0000.json` has SHA-256 `fb4ba4322529a10601de8070bb6748f4e30e61ac35b672718e081d74079ce8fc` and normalized identity `adf88a13c3a52a5907e5d0661153d02d8c06a08660eea8dba7d954c5e11e952c`. Its points equal the previously accepted A exactly, namely S minus (78,78). Independent determinant enumeration gives five conflicts; it retains157 source points, deletes one and adds none. Its deficient row and column are both78. It is not a search improvement.

The distance artifact `candidate-0001.json` has SHA-256 `7ce150c35565d9e7e95ea934faab79ec0d6a7a758b2fcc4760c1e3beb89b92b0` and normalized identity `00bfac3003de860088a8a418e702fb228acd0efb6bc9325a2b96b40f2a6ef791`. Its157 distinct in-bounds cells have exactly45 collinear triples by independent integer determinants. It retains145 source points, deletes13 and introduces12; deficient row55 and column21 have degree1 and every other axis has degree2. Positive score means the state remains invalid. Merely reaching D=13 does not supply a feasible endpoint outside prior source-retention scopes, and the9..12 search was a timeout rather than a proved closed family.

For both fixed saved sets, both existing full validators were independently rerun and reproduce their saved reports exactly, including complete coordinate-canonicalized conflict lists, normalized identities, counts and validity=false. A separately authored determinant enumeration agrees on every conflicting triple. Together the direct enumerations check1265420 triples. Report pointers and labels match the artifacts' metadata exactly: the best has only `initial_best`, and the distance state has only `distance_exit`. The output directory contains just these two candidates and the report; no witness exists.

The report's reviewed-source execution history records2000 complete steps,64000 attempted/completed proposals and2000 accepted transitions. Accepted moves divide into834 uphill,510 neutral and656 downhill; they sum exactly. The128-entry accepted-score histogram sums to2000 and ranges from8 to154, consistent with no improvement over initial5. The class counters sum to1415 illegal attempts,860 duplicates,126 tabu rejections and61599 admissible candidates. Their sum is64000, with row/column/rectangle attempt totals16000/16000/32000. FIFO eviction count1937 equals2001 stored-state arrivals minus capacity64. These are consistency-checked source-pinned counters, not an independently replayed trajectory. In particular the saved state's D=13 and score45 are independently established, while its being the first threshold crossing is accepted only as reviewed-source history.

All16 receipt pins,15 manifest entries and8 report/artifact pins match current bytes. Both accepted chain heads remain unchanged. Exact argv records seed279179,25 soft seconds and2000 maximum steps. The owned30-second/256-MiB gate validates directly: exit0,22.368399750 seconds total,48464 KiB peak sampled RSS, clean cleanup, no hard trigger and no monitor error. The worker's22.315063-second measurement lies inside the outer measurement. `step_cap` completes the bounded policy run, not an exhaustive search or mathematical negative.

Independent audit `data/score11-conflict-focused-tabu-v1-independent-actual-audit.json`: SHA-256 `7437a4467c3c550feab20aba6db44e607c2672d20013a532eac52733a8a438b0`.

Independent script `research/score11_conflict_focused_tabu_independent_actual_audit.py`: SHA-256 `74d1e86f8a34d0f04d19e0b1ae2efc55d5dac12272a9b10adacc2a6e14c9ad20`.

This audit read and validated only the completed fixed artifacts. It did not replay the2000-step walk, score any new candidate, reconstruct unretained states or allocate further work. Artifact and receipt hashes were checked again after validation. No unchanged repeat is justified by this audit.
