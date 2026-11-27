# Fixed adapter metadata preparation addendum

The frozen adapter `research/two_row_suffix75_actual_authority_adapter.py` (`e9a3af55e0f6b84ace02eb7930da4b39fd8e55b6396d845451a9f74a9f92739b`) now has a synthetic metadata-only test, supplementing the protocol's earlier parsed-only preparation statement. Its production source is unchanged.

The test replaces every adapter digest/input read with explicit synthetic mappings and replaces the direct chain audit with a disclosed result stub. There are no actual artifact reads or n75 coordinates or geometry. One fully associated synthetic metadata case passes;23 corruptions reject, including wrong argv, return code/type, dirty cleanup, excessive wall/RSS, changed sources, manifest association, rejected report, uncertain authority, publication/hash/byte errors, metadata failure, state/pin mismatch, initial order/prefix/handoff mismatch and wrong accepted-chain/endpoint/count/pending results.

Test source: `research/two_row_suffix_independent_adapter_preparation.py`, SHA256 `4c5ce7cda4dd8ebf6fb2a74175923ad6024eb183e1e7f8a5f575b066601e51fc`.
Evidence: `data/two-row-suffix-independent-adapter-preparation.json`, SHA256 `16daf582574c3eb0cbb8b841463ae8c52aceb584025ce0006e004d6dca316374`.

These tests exercise report/receipt/pin association logic, not actual byte hashing, endpoint geometry, guard runtime behavior or filesystem crash semantics. The adapter output writer fsyncs the file and replaces its output path but does not fsync the parent directory. This preparation makes no crash-durable directory-publication claim for the audit report. Actual acceptance requires Root's bounded owned audit to finish cleanly and subsequent artifact re-read/hash verification. Worker authority/witness durability remains separately reviewed evidence.
