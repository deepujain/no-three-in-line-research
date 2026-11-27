# Independent actual-host review: middle diagonal 1541

The fresh root and following 250-node probe PASS retained-artifact audit. The root audit is recorded in `near-quarter-middle-d1541-root-review.md` (SHA-256 `503110f57e4c10faf6ab5b67236c807c6eeb5109716a41aec41743cfe298f721`). The reviewer performed bounded structural parsing and hashing only, with no n79 geometry construction or search launch.

The probe preserves singleton diagonal 1541, canonical four-orbit order 1..1521, row order 0..78, the historical ordered map, and the frozen readonly nine-source identity. Stage limits remain 30 seconds / 256 MiB / 2-second reserve. Current `validate_receipt`, `validate_job`, structural `validate_report`, and `validate_gate` pass, with direct job/report hashes, exact accepted parent, and checkpoint authority matching. Saved stdout equals the accepted structured return, exit code is zero, and no writer lease remains.

| Probe artifact | SHA-256 |
| --- | --- |
| Request | `2095ee655c439fab36e47e606a73ef10397d72407b80917eda849d0725b3e0a2` |
| Job | `3e99069b25ea5e5371a5c5129f13968d9c69f0f1e0022de719cd910f06663731` |
| Report | `1e96251ca7bbb246e4d4352340e0846f8f36c24ab5c9ba6b812b1b55674fd3b9` |
| Receipt | `cfdbaf20582b63a8f97d8a9738d98b0b9105cb028756358eb46b03798bff66f6` |
| Exact root parent | `515ddb812ba7c7cba03ccab1a5fc3d3f4d6badd801e87f125dc47766db434496` |
| Accepted checkpoint | `3790fef31b89b2779e5ae785d3e81997d4d0bec7a0958d721bbf30dedae05b77` |
| HEAD at audit | `4e0031a62fd395484ec608cf9c2850f08e4fcc289b79c4e6b2a731bbc5c36eb9` |

Stage `4eb846c9cc43427b940d48bb4723c035` advances zero to 250 nodes and ends `node_limit_checkpointed`, ACTIVE, thirteen frames, top ENTER. Counts are `(250,0,298,48,0,125,0)`. Zero of the one declared slice has completed; no witness/event is reported. The chain is `93ed8661b4d052125cb9e8227180b6de9cc984f389f57b088a4715b8ec858f46`.

Query counters: 1,270,262 domain probes; 298 batch probes; 1,620 cursor checks; 18,131 restore probes; zero interrupted scans. Physical mutation-engine totals are 1,031,300 cell increments, 970,898 inverse cells, 540 orbit attempts, 154,446 pair lines, 2,012 point attempts, 1,776 points undone, 48 rejected orbits, and zero aborted orbits. As declared, these exclude readonly-query line walks, reads, and determinants.

Child seconds: construct/restore 0.013478666; map check 0.004420541; operation 7.607394667; save/validation/publication 0.231454083; through report preparation 7.873284167. Helper elapsed was 7.9314724580035545 seconds, 172 samples, peak 52,016 KiB, and clean one-sample cleanup in 0.012454374998924322 seconds. Supervisor time was 7.958536125 seconds; outer experiment time was 8.006661499995971 seconds. Root outer time was 0.17651699999987613 seconds.

Observed cost is comparable to bounded main-chain 250-node stages, but this does not establish greater viability or comparable fraction of search covered. No witness, leaf, completed slice, or infeasibility result was obtained. Preserve this accepted exploratory frontier while the already approved main 600-second window runs. Further allocation remains Root's decision after its terminal audit; no additional host allocation is implied here.
