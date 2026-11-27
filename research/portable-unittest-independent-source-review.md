# Independent portable test runner review

Decision: PASS for the narrow CI portability change. No n79 experiment, geometry construction, solver replay, package installation, or network operation was performed for this review.

Reviewed frozen files:

- `research/portable_unittest.py`: `45e13a3c581c6d6a8d74deef19004cdda83ce2e0f8560a723c63073413baff25`
- `tests/test_portable_unittest.py`: `9664b0c81ba7ef85b404c9b098939d3cfe6f7a1febe23aefa934e14a715150f7`
- `.github/workflows/verify.yml`: `81bef1a00d6fd66c3b54079a2fc7f86f1008face8031b75815cf8cfa504c40fd`

The original runner and tests remain byte-identical to the accepted freeze: source `845f0e815773df8963b7c78d94e29d9e6dcba045d834071f7878c7b8f3abc958`, tests `f9035ae91d874a008390144e6c8f1213c199c8bd96dba34ac304fd60c8908db9`. The workflow changes only its two unittest invocation lines.

The portable runner discovers the whole test suite. It requires exactly one occurrence of the actual-anchor host integration, accepting the two normal unittest module naming forms. It replaces only that test instance's method. Missing or duplicate target discovery fails closed. Every synthetic constraint, loader provenance, execution provenance, resource guard, input mutation, and deadline/cleanup test remains selected.

Before deciding that original runtime files are unavailable, the runner hashes every fixed anchor artifact, including the receipt. It then checks every receipt source pin. Only a missing path under `.venv/lib/python3.14/site-packages/` is collected as an eligible absence. Missing nonruntime files, changed fixed artifacts, changed present runtime files, and changed present nonruntime files raise errors. Checking continues after an eligible absence, so another mismatch cannot be hidden behind the skip. The absence is reported explicitly through unittest's skip reason. If all original files exist and match, the actual integration executes normally with its unchanged checks.

Independent verification used the existing local interpreter and tiny synthetic fixtures. The seven new runner tests and six original synthetic tests all passed (13 executed, one deliberately skipped integration, 14 discovered; 0.090 seconds). For this review only, the availability callback was replaced with an explicit review-only sentinel to avoid executing actual n79 integration work; this does not represent an observed missing host file. A separate fixed-file hashing-only availability check returned an empty missing-file list on this host. Additional independent temporary-fixture probes confirmed that a changed or absent fixed artifact fails even when an original runtime file is absent.

No full-suite or cross-platform execution claim is made by this review. The full-suite execution belongs to the implementation handoff. The review establishes the narrow skip selection and fail-closed provenance behavior from source and tiny tests.
