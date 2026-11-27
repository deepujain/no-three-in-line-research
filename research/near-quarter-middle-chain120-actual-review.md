# Independent actual review: middle-1541 120-second caller

PASS. Run `475c12e8f2ba29f9d22c2de220f7b629` accepted all eleven attempted stages, adding 2,750 nodes to the prior 250-node frontier and ending at 3,000 nodes. It stopped with `total_budget_cutoff`, no error, and no writer lease. Complete caller time was 95.345197000 seconds; pool outer elapsed was 96.8205883329938 seconds with exit zero.

Every deterministic stage ID, full prior accepted record, job/report/checkpoint/receipt hash, exact 250-node increment, source manifest, declaration, 30-second / 256 MiB / 2-second-reserve limit, and owned cleanup gate was independently checked. All eleven stages began with at least 32 seconds remaining; the final cutoff leaves less than 32 seconds. Start and final immutable records bind the approved template and caller; stdout agrees with the final summary apart from documented return-only fields. The accepted sequence reconstructs exactly the current HEAD.

| Artifact | SHA-256 |
| --- | --- |
| Start record | `c37392b4174b3f2ef587d2a9f86ccd97189004c3844a5f50b0d1d06c70b228c6` |
| Final summary | `b90c90c6b97e9fc7dcebbeefffdc34b61f29487b5f2896af7f2ed764cd02edf8` |
| Final HEAD | `714660b4814c0463401c5eb2dc7598fbe76796e1274bff4284c6d53b1ca3f22e` |
| Final checkpoint | `0ccbfc291e202866b541af6339be64e9ae4e721a44206b84166ba73523f335f9` |
| Final stage receipt | `b9197c77db6fc71d80eeec814b6b313a503bad004ce697feeba066b9e53ac8a7` |
| Detailed independent audit JSON | `140a145cf04b792105d531bd8573d749e447705c37359a1f76690e9da4759114` |

Detailed evidence is in `data/packed-middle-d1541-chain120-r1-independent-audit.json`. Final counters are `(3000,0,3666,666,2,1574,0)` with twelve frames, ACTIVE in the singleton diagonal-1541 slice. No leaf, target closure, witness or completed slice was obtained. Query totals are 14,239,013 domain probes, 3,368 batch probes, 15,459 cursor checks, 403,410 restore probes and zero interrupted scans. Helper elapsed ranged from 8.002738667 to 8.983122833 seconds; maximum sampled RSS was 53,872 KiB, with clean cleanup throughout.

The fresh middle-600 template `data/packed-readonly-n79-middle-d1541-chain600-template.json`, SHA-256 `7b519da71d657e216cd148239a54b26bda5f3decb37c5b94e993b7f18a94f86c`, independently passes strict/source/HEAD checks. Only `start_accepted_record` differs from the prior template; it is exactly the 3,000-node HEAD above, confirmed by a second read with no lease. Approve one Root-allocated 600-second continuation with ordinary 630-second pool reservation, fresh unique run ID, fixed quota 250 and unchanged caps, after Root's no-active-process check. Use the existing single-worker packed-only window and stop conditions; no implicit retry. Distinct slice coverage is the justification, not a claim of greater viability. This review launched no search and changed no source.
