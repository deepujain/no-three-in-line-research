# Independent actual-run review: 120-second packed caller

PASS. Run `3d5da69de88b464aab12edbb96b9fae4` accepted all eleven attempted 250-node stages, advancing 511 to 3,261 nodes. The caller stopped with `total_budget_cutoff`, no error, no retained writer lease, and no witness or completed slice. Pool outer elapsed was 92.62428045900015 seconds; returned complete caller time was 91.407582167 seconds. The difference includes pool observation overhead. Inner timings are evidence, not separate aggregate charges.

Start record SHA-256: `c484388639c62f511fbc97e1170be7bf7b505f48e81803b9c78c58e4ce9243f6`.
Final summary: `8b6549635e33601e07cba2c4c02b2349cb061f4c564600e9378e0cd63d682ec4`.
Final HEAD: `97d35e3e76c115eb46822cc61f492f789d3a3d8bcee57a84822375beb2f46c0a`.
Final checkpoint: `fbda63bd63f52f39bbe60beae532d99f5fe387966a8ee8abcb5295f636cf9660`.
Final stage receipt: `d6eb576bc2113e92e170b48aaae316fa30d488ec8e109ae2a30499160ea2d93b`.

Every deterministic run/index stage ID, exact previous accepted record, job/report/checkpoint/receipt hash, source manifest, unchanged identity and declaration, 250-node increment, and resulting accepted record was independently checked. Structural checkpoint parsing performed no broad-grid construction or search. The eleven reconstructed accepted records end at the exact live HEAD. The final summary matches the returned log after excluding the documented return-only timing and summary hash fields; the pool receipt reports completed with exit zero.

Every stage retained 30 seconds / 256 MiB / 2-second reserve, began with at least 32 seconds remaining in the caller budget, passed its owned-resource gate, and had clean cleanup. Helper elapsed ranged from 7.990667333 to 8.700721750 seconds; maximum sampled RSS was 53,984 KiB. At final summary preparation less than 32 seconds remained, consistent with stopping before another stage. Caller and current nine-source hashes equal their approved frozen identities.

Final checkpoint counters are `(3261,0,4012,751,1,1764,0)` with twelve frames and ACTIVE state. Complete per-stage parent/checkpoint hashes, query counters, timings, and gate measurements are retained in `data/packed-readonly-chain-r1-120-independent-audit.json`. No witness or infeasibility conclusion follows from this partial frontier.

Approve one further Root-allocated 600-second packed-only single-worker caller window, with unchanged 250-node stages and 630-second ordinary pool reservation. The fresh template `data/packed-readonly-n79-r1-chain-main600-template.json`, SHA-256 `f5463d4d1713b4ba017f43692d0fec29efbed1442e3d7161dc48cedd0f58d42f`, was independently checked: only `start_accepted_record` differs from the prior template and it is exactly the audited 3,261-node HEAD. Use a unique run ID, preserve all existing stop conditions, and do not retry implicitly. This reviewer launches no host work.
