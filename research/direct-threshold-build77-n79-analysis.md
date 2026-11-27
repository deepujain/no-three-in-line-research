# r30 direct (7,7) native build: saved-report audit

The supervisor-owned build completed the exact selected threshold formula:
2,193,179 emitted and inserted clauses, 281,121 variables, 6,335,924 literals.
The complete formula digest is
`0db9f90c8b76e6b25d071598d156964e600b0b047c4c50b03cd4fe5c31ef931a`.
The observed totals equal the prior count-only prediction. No solve was called,
and solver result is null.

The guarded interval was 13.531026 seconds with 317 ordinary RSS samples,
228,752 KiB sampled peak (223.390625 MiB), no monitor error, exit zero and clean
one-sample cleanup (0.012348 seconds). The outer receipt completed with exit
zero in 14.092207 seconds. Both retain sampled gate semantics, not a kernel cap.

Measured build headroom is 32.609375 MiB below the unchanged 256 MiB threshold.
This build peak is 5,040 KiB (4.921875 MiB) higher than the preceding row-floor
build peak of 223,712 KiB (218.46875 MiB). The experiment therefore did not
improve measured construction memory. The 194,587 fewer variables could change
subsequent native solve allocation, but this build provides no measurement of
that allocation and no evidence that search or returned-model decoding fits.

All ten current source bindings match the report; the receipt entrypoint hash
matches. This worker inspected saved reports and performed arithmetic only.
No source change, new numerical build or solve was performed in this audit.

| Bound source | SHA-256 |
| --- | --- |
| `cli_entrypoint_sha256` | `da2bd2585ebe76ac624cfd608b56b7401ad9bfbe8656b49005777c5f8f4b1d03` |
| `compact_source_sha256` | `f2b5840a160d51fc8e5d663cad42f5416286f4b2535cda7ab3cd7c4598b281f1` |
| `guard_source_sha256` | `c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48` |
| `line_generator_sha256` | `d789d1b4924676886a950757fcf98994f221a0ad1ee7ca12874667ecfa034897` |
| `model_source_sha256` | `b53adcf159cd7d32416e02ae970a339afcb40442107c966ef6393680d479838a` |
| `original_guard_utilities_sha256` | `1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27` |
| `preflight_source_sha256` | `4b9a4d0d07a46a9a572a54c6f6ec01b83a18ac1c6af53c01d81b4db92c9c6b92` |
| `row_quota_source_sha256` | `dcd3468bcea630848a2743c7450ec5027a0df640fb9495b701f68352c23ca704` |
| `threshold_source_sha256` | `57a00fe19b711a184e89f6fc31ae429671d34cef42c4c21bc974dce58e0825eb` |
| `verifier_source_sha256` | `e995c2367481bc63174b8f80d63048bdae6ebf75232e026509c6012157c11c4c` |

| Saved evidence | SHA-256 |
| --- | --- |
| `data/direct-threshold-build77-n79.json` | `6bcb73206f1415ff6bef9411edfa596b8b3e843688b9b26f185f0611e83e91d2` |
| `data/experiments/r30-direct-threshold-build77-n79.json` | `46599c5b6428b322ef5bc85b9d3358e397111c453a9a1ae4d387e836ff7fc6b9` |

The Lead separately authorized implementation of a new explicit-threshold
owned solve adapter using this mandatory full digest, the unchanged 30-second
helper and 256 MiB gate. Historical sources stay intact. Any n79 solve remains
with the supervisor after independent source review and tiny actual-host gates;
this completed build alone authorizes no conclusion, retry or cap increase.

Analysis: Research Software Engineer, `gpt-6.1-sol`, reasoning `high`.
