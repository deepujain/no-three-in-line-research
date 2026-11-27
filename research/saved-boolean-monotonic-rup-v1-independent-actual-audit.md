# Saved monotonic RUP check: independent actual evidence audit

Decision: **incomplete, no proof verdict and no closure**. The report records one checker child and zero SAT invocations. The child produced no stdout or checker receipt; its supervisor reported `TimeoutError: process observer timeout`, reason `supervisor_error`, return code -15, and inner cleanup `clean: false` with `unattributed new process in worker group`. The recorded failure does not show that the proof was invalid, that it was accepted, or that the checker reached a particular proof line. The outer guard later reports clean cleanup; that separate observation does not change the inner cleanup result or establish absence of an unobserved detached descendant.

The report sets `native_incomplete`, `complete: false`, `closure: false` and `identity_valid: true`. The outer receipt records worker exit 2, no monitor error, clean outer cleanup, 0.621887750 seconds and 80,080 KiB peak sampled RSS under 30 seconds/256 MiB. These are sampled guard observations, subject to sampling limitations. The receipt states its pre-run sources were unchanged. Independently hashing all 132 report pins found no mismatch, including the saved CNF and proof, frozen checker, runner, runtime and manifest. Identity matching establishes neither proof validity nor completion. No proof or SAT checker was rerun in this audit.

Evidence SHA-256:

- `data/saved-boolean-monotonic-rup-v1/report.json`: `844457dcbee53f14a0167057d74f6d570ce354be859124b76d15001b3ac91460`
- `data/experiments/shepherd-saved-boolean-monotonic-rup-v1.json`: `85898fcf0d93c321cac7c0cc22cf5fb3a12a35f79efb659c4c14224c94590c83`
- `data/saved-boolean-proof-check-source-pins.json`: `262b69fd4e5bf8e9afd7bcfb979421ecd06da284c971bed8ca9cbd9af8122617`
- Saved CNF: `855b54b7c6b05f181ff3c9153ff03c44d310747874577f520ed960a007670fc9`; saved proof: `4c1fc7141a5c889029db91c0dce0255463f472f4db60192fbfc4d016f65d439e`.

The earlier strict checker also did not accept the proof. Neither outcome supports a fixed-pool UNSAT claim. No retry is authorized by this audit.
