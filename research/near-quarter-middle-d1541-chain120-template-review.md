# Independent review: middle-1541 120-second caller template

PASS. Template `data/packed-readonly-n79-middle-d1541-chain120-template.json`, SHA-256 `86d7a2efef28261bb6eb22f8b43e394120db3214f2a6ee4a71ab4736537d71fa`, is 6,981 bytes and passes current strict loading, source checks and bounded accepted-HEAD audit.

It fixes exactly the previously audited 250-node HEAD `4e0031a62fd395484ec608cf9c2850f08e4fcc289b79c4e6b2a731bbc5c36eb9`, checkpoint `3790fef31b89b2779e5ae785d3e81997d4d0bec7a0958d721bbf30dedae05b77`, and receipt `cfdbaf20582b63a8f97d8a9738d98b0b9105cb028756358eb46b03798bff66f6`. No writer lease exists, and a second HEAD read is identical.

Compared with approved main-600 template `f5463d4d1713b4ba017f43692d0fec29efbed1442e3d7161dc48cedd0f58d42f`, only `chain_dir`, `start_accepted_record`, and `declaration_b64` differ. Arithmetic parsing verifies singleton diagonal 1541, all four-orbit IDs 1..1521 in canonical order, and all rows 0..78 in canonical order. The n79 grid, historical ordered map, nine-source manifest, 250-new-node quota, 30-second stage limit and 256 MiB cap are unchanged. The reviewed worker retains its 2-second save reserve. Caller source remains `a5fcb6ad8ee5777fa8d2c44cca5e595c617c1c221fe1ac04bb57b067fd9ea182`.

Approve one Root-allocated 120-second caller invocation with 150-second ordinary pool reservation, a unique run ID, and existing single-worker pool semantics, only after the active main-600 invocation passes its terminal audit and no numerical process remains active. Preserve all caller stop conditions and do not retry implicitly. This template approval performs no host allocation, geometry construction, numerical search, or source modification.
