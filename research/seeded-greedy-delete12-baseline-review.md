# Independent seeded greedy deletion baseline audit

The corrected 25-second trial completed with exit code 0 and clean monitored cleanup; receipt SHA-256 `425012c36aa4d1e5d607292e8cdb5acbabfbbab2a985f6b8642ddb08228b6d0d`. The pinned source, verifier, helper and input hashes match current files and the receipt before/after manifests. Guard elapsed 25.152 seconds with peak sampled RSS 47,072 KiB across 591 samples; sampled RSS is not a kernel hard limit.

I independently ran both exact validators on the retained certificate, whose file SHA-256 is `42323174ef1985a2c96be2e8fc723282cccb89f540952fffc0e5fa84d7029621`. It contains 156 points, exactly the original seed coordinates embedded in n79, normalized hash `974921b9f18e25e40f46c61b0ee7ed69955a992dafed1a38881244bd4f41c145`. Metadata records 617,216 candidate evaluations, 102 passes, seed 279106 and time-budget stop. The maximum deletion count was 12, but actual sizes and distinct trial states were not recorded. No improvement, exploration coverage or nonexistence conclusion follows.

The earlier rejected 65-second helper request failed before a worker was spawned; it is not a numerical trial. This audit did not launch a search.
