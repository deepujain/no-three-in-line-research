# Independent exterior unimodular source and tiny review

Verdict: SOURCE/GEOMETRY/TINY PASS for the exact frozen files below. This authorizes no actual selected-source inventory, affine run, or extension check. Root retains the allocation decision; lifecycle/containment and prior-scope review remain separate. No selected n74 source coordinates were read and no actual-grid geometry or solver was executed in this review.

Frozen identities:

- Production worker `research/exterior_unimodular75.py`: `c06b018195fd11f262e61c1f61aa0b18fba1cc531dc1d7cc8f64b3e4639b36df`.
- Author tiny helper `research/exterior_unimodular75_tiny.py`: `1e0565d9b458dcef96cd667bf544573360e070d7f78fa241c5ebb042f86c90e3`.
- Independent comparison helper `research/exterior_affine_independent_worker_audit.py`: `1a8835097cd88e095c195dee796c0b1de0d964d8bcdace80cff95456ee1364e3`.
- Independent oracle `research/exterior_affine_independent_oracle.py`: `a1e4d8ec79b18cfe5756384826859b4730c5ca3ba42b9c989b34da66997ede62`.
- Independent edge fixtures `research/exterior_affine_independent_edge_fixtures.py`: `af1b401a3f0780a903cf3188397a50b43b491bcfa959b03164b29e4078935ed4`.

## Source conclusions

The source gate requires n>=4, full two-point row/column loads, exact integer coordinates, uniqueness and validity by a full determinant prepass before using the width theorem. H/V and their source-member witnesses determine the coefficient domain. Every canonical primitive vector in that domain is examined; a rejected direction has a witnessed projection difference strictly above n, and an admitted direction has a full projection histogram, extrema and width n-1 or n. Inventory verification re-enumerates the coefficient domain, checks each rejection and every admitted projection, and requires exact coverage without duplicate records. The mod3 bound is checked after this complete inventory; it never replaces exhaustion.

Canonical frame pairs preserve the signed-row-permutation quotient and exclude the ordinary axes. Both determinant signs are handled by exact integer inverse arithmetic with a forward-identity check. All fitting translations and deficient intersections are enumerated, including explicit occupied-cell exclusions, with the four-choice bound applying across all placements. The closed protected box is correctly tested in original coordinates. Eligible q values are deduplicated while retaining a frame witness. An exact old-pair determinant certifies each rejected q; survivors can only emerge after full pair enumeration. Completion flags distinguish direction, candidate and pair work and are checked by the run wrapper before any conclusion.

All noncollinearity obligations are complete: the authenticated valid old source remains valid under an invertible affine map, and a new triple must contain q plus two old points. No old-triple search after mapping is needed. A negative result applies only to the selected-source exterior unimodular family and not protected preimages, other source records, nonunimodular maps or unrestricted grids. The actual CLI fixes the source/target and has no retry, coefficient expansion, repair or fallback.

## Independent executed comparisons

Executed `.venv/bin/python -m research.exterior_affine_independent_worker_audit`. Expected directions were generated from the full universal tiny coefficient box, independently of the production H/V cutoff. All11 valid full-axis n4 sources passed, including reversed input order:

- 30 admitted and70 rejected canonical directions matched exactly;164 further primitive directions outside the cutoff were independently confirmed too wide. All H/V witnesses, extrema, histograms and rejection certificates matched direct arithmetic.
- 16 nonordinary canonical frames,56 raw placement/cell choices and24 distinct exterior preimages matched the complete oracle sets. Both determinant signs, every translation, protected exclusions and inverse/forward identities were checked. All24 returned pair certificates were directly valid. None of these n4 cases supplies a valid exterior positive witness.
- 20 inventory mutations rejected: missing/duplicate directions, wrong H/V or cutoff, bad witnesses/extrema/histogram/width, nonprimitive/out-of-domain vectors and malformed rejection indices.
- All79 invalid but full-axis n4 sources rejected before coefficient enumeration. Twelve additional order/domain/type/cardinality cases rejected, including n2/n3 and the generic occupied-intersection fixture passed incorrectly through the whole-source gate.
- 36 protected-boundary cases matched. A separate generic frame fixture returned four raw choices with exactly one occupied exclusion. This fixture is explicitly not a valid full-axis source-family input.
- A clearly stubbed five-record candidate stream exercised two frame descriptions of one exterior q, another exterior q, and two protected records. The collector produced exactly two exterior q values, one duplicate exclusion and two protected exclusions, and its pair-test count showed no repeated search of the duplicate q. This tests collection semantics, not those stubbed records' source-fit geometry.
- Eight deadline injections rejected, covering six phases and partial projection/pair progress. No partial result was returned as completed family evidence.

## Lifecycle and save behavior

Independently reran all17 author lifecycle cases using an independently generated tiny source. Negative completion, partial inventory/candidate/pair rejection, wrong record, pin drift, all phase/final-pin/report-save deadlines, save failure and candidate-validator disagreement passed. Positive analysis and candidate construction are expressly stubbed to supply a genuine directly and dually verified9-on5 certificate; this is not an exterior-affine family witness.

An additional instrumented late-second-validator rerun observed `candidate_validator1`, `candidate_validator2_complete`, `witness_save`, then post-candidate pin work. The actual validators and temporary-file save ran. The final result preserved the saved witness but cleared completion and closure after the synthetic deadline. The author's subsequent reread/revalidation of that saved file is verification of persistence, not another construction. No disagreement or failed save produced a saved-witness claim.

Evidence is recorded separately in `data/exterior-affine-independent-worker-audit.json` and `data/exterior-affine-independent-lifecycle-rerun.json`; author evidence and historical design/helper files were preserved. The latter is an independently instrumented rerun of author lifecycle logic, not a claim that all lifecycle logic was authored independently.

No unresolved geometric or completeness defect was found. Actual runtime feasibility is not inferred from tiny timings. The source validation, coefficient projections, certificate rechecks, at most20 candidate preimages, pair checks, optional dual target validation, pinning and saving must all remain within the separately allocated25-second cooperative /30-second owned /256-MiB gate. A timeout or failed final identity check clears completion and closure while retaining an already saved artifact for later independent assessment.
