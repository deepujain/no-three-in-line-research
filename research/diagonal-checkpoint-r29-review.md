# Independent r29 checkpoint evidence audit

Both n=79 jobs completed normally with exit zero, a clean owned guard and cleanup, source hashes matching current bound files, and `node_limit` with `complete=false`. Their witness directories contain no certificate files and their recorded witness counts are zero. This audit read artifacts and reconstructed current stack paths; it performed no search and does not independently replay previously visited nodes.

The `(d,t)=(0,0)` continuation records 20,000 new and 27,000 cumulative nodes. The command, report and checkpoint predecessor agree with r28's accepted `00a8e6f410038d8d4cfe5f05ab13d7f34e8ca7f864279de67794f894243bbb23`. The current checkpoint bytes match its accepted and published digest `f8a536c6957b7f8af4d62c010e53c52a3e7341b01c0587b576cb7841a71636a0`; identity, counters, source and orbit-order hashes match. Reconstructed all 42 stack frames and 41 pair insertions under the declared MRV rule. The helper records 19.6281 seconds and 55,616 KiB sampled peak over 463 samples; the wrapper reports 19.7069 seconds and the supervisor 20.1612 seconds.

The distinct `(0,1)` pilot records 1,000 nodes and no predecessor. Its current checkpoint bytes match accepted/published digest `9e23a5f2208ca76cb0e4f13b15db6e7276d31bc0b66667af6f24824038881957`; identity, counters, source and orbit-order hashes match. Reconstructed all 40 stack frames and 39 pair insertions. The helper records 1.0105 seconds and 55,456 KiB sampled peak over 23 samples; the wrapper reports 1.0860 seconds and the supervisor 2.0444 seconds.

Both slices remain open; neither a node limit nor the absence of witnesses is an infeasibility result. RSS was sampled, so observed peaks are not hard limits or predictions of later work.

SHA-256 evidence:

- `(0,0)` report `66c05c5d504e557fc792a42afa06ccc9dc1577f3f03bb3309118df0fd2f3ddb5`; receipt `e5553cbcef287fe776174d66f4959e1356a35f1e5b0206ed1d3d80a7c5377a24`.
- `(0,1)` report `acf7242e45be3c6c02af0ae5fda01c48e0c3cfc28cd160d14c1154d8954a4b89`; receipt `100d311d3c812633f6530d99a3ed00c267a85eed48081ec80d9ee65101011e75`.
