# Independent actual-run review: main 600-second continuation

PASS. Run `a2a4aa47792f98846b4df5d5c835c26b` accepted all 68 attempted stages, adding 17,000 nodes to the audited 3,261-node parent and ending at 20,261 nodes. The caller stopped with `total_budget_cutoff`, no error, and no retained writer lease. The completed pool record has exit zero and outer elapsed 577.2421989169961 seconds; returned complete caller time is 575.689409666 seconds. Inner times are evidence, not additional aggregate charges.

| Artifact | SHA-256 |
| --- | --- |
| Start record | `1b62c7adb602d16087300b30343e0bbc3e8b1b30ee4e92f858c2d1995f01b4f8` |
| Final summary | `20a3320202ac7bdbf1865982a62b90f898fa92a0819ab04988383dd8297c0eb0` |
| Final accepted HEAD | `cd3977d726cbd374ca0fa75c5526eb62db0eb096983f7c8c505d3ead779cfa24` |
| Final checkpoint | `6e1d4279da8a2a0123435e76ee3b4e83693706e82c915ff7cec74552f1811862` |
| Final stage receipt | `a285b9c657315e40c11cab0a76103614adf13981c2814b0ba3e8e59dfb8fc6db` |
| Detailed independent audit JSON | `5a7d4c14ece999dfab491b2310608d1993798aba9277c21254fd19c747891b50` |

Detailed per-stage evidence is saved in `data/packed-readonly-chain-main600-r2-independent-audit.json`. Every deterministic run/index stage ID, exact prior accepted record, job/report/checkpoint/receipt hash, current nine-source manifest, caller source, declaration, and 250-node increment was independently checked. All reconstructed accepted records form one continuous chain ending at the exact current HEAD. The final immutable summary matches stdout after excluding its documented return-only fields. The start record matches approved template `f5463d4d1713b4ba017f43692d0fec29efbed1442e3d7161dc48cedd0f58d42f` and its 600-second deadline.

Every stage retained 30 seconds / 256 MiB / 2-second save reserve, began with at least 32 seconds remaining in the caller budget, passed the owned-resource gate, and recorded clean cleanup. Helper elapsed ranged from 7.788244208000833 to 9.63544929100317 seconds; peak sampled RSS was at most 54,192 KiB. Less than 32 seconds remained at final summary preparation. The source manifest and caller `a5fcb6ad8ee5777fa8d2c44cca5e595c617c1c221fe1ac04bb57b067fd9ea182` remain unchanged.

Final counters are `(20261,0,24792,4531,12,11189,0)`, ACTIVE with eleven frames, diagonal index zero / ID 1522. No leaf, target closure, witness, or completed slice was obtained. Invocation query totals are 87,934,111 domain probes, 20,780 batch probes, 98,426 cursor checks, 2,323,418 restore probes, and zero interrupted scans. Node growth is partial search evidence, not a percentage of family coverage or a feasibility conclusion.

This clears the terminal-audit condition for the separately approved middle-1541 120-second caller template `86d7a2efef28261bb6eb22f8b43e394120db3214f2a6ee4a71ab4736537d71fa`, subject to Root's no-active-process check and unchanged single-worker allocation. No additional main-chain allocation is made by this review. The reviewer performed retained-artifact hashing and structural parsing only; no geometry construction, numerical launch, or source change occurred.
