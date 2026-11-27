# Mathematical SOURCE acceptance addendum: harness v3

Verdict: SOURCE PASS for producer SHA-256 `36f4639fededa4fd0e239e397acb43478e7131ee4a1d0f798079d73cf34b5b8e`, harness SHA-256 `5d8e5ecbdb419cd9fa8c118e7ce4b2d788344fc7c247c4bee1995c4755fc9fb5` and the exact 72-byte fixture SHA-256 `5be21073f6b07bc18969b91f9dd9b9196ebe42288cfa9342468171a3c9ef8f37`. This supersedes the harness identity accepted in the preserved v2 mathematical review; it does not claim a normal geometric PASS.

The prior full mathematical source analysis is `research/full-complement-row-domain-n5-independent-mathematical-source-review-v2.md`, SHA-256 `855c89f22e35ada7d4b608a6b0269be4544169d70f365d8e5c330798e4519a3f`. The accepted design remains SHA-256 `9a50e2a36b154a1a3fa0cccde4b221e90e567c4042e0c4611b309697c9f81239`.

I authenticated the preserved v2 harness and inspected its exact diff against v3. The only changes add best-effort failure identity capture, two synthetic read-failure checks and use of that capture in the exception handler. Producer, normal geometric code, all direct/line/unary arithmetic, lexical ties, domain construction, K embedding and operation accounting are unchanged. The v2 mathematical conclusions therefore apply to these exact v3 identities.

Failure identity capture now records a null digest and bounded read error independently for each unreadable producer, harness or fixture file, rather than letting a secondary source-read failure prevent failure evidence. This fixes the identified source-read failure path; it cannot promise successful persistence if the output destination itself is unwritable. The normal CLI still compares fresh identities immediately before its immutable success write. A caller bypassing `main` must perform that final comparison itself.

Independent runner `research/full_complement_row_domain_n5_independent_pregeometry_v3.py`, SHA-256 `98260649c6daccc8542105ed2c2b3aabac88515effed42e58d3133ae47038da8`, produced immutable evidence `data/full-complement-row-domain-n5-pregeometry-independent-v3.json`, SHA-256 `86c116ce4fa19588b88b3f92f5708530622a3e7c7068a2a100da87e90a9dc061`.

Evidence confirms two syntax compile passes, 10 invalid-input rejections, three seeded quota boundary checks, four pure drift-comparison rejections, two injected source-read failure captures and two exhausted-budget sentinel checks stopping before coordinate access. Producer collinearity, direct scoring, line mapping and the normal runner were trapped during pregeometry checks; trap calls were zero. All bound source and fixture digests were identical before and after. Real geometric operations: zero.

Root retains sole ownership of any separately authorized normal pass, its exact pre/post source and fixture bindings and resource gate. No normal fixture evaluation, alternate fixture, actual input, old-family continuation or optimizer was run by this review. Any later failure remains evidence and stops that gate without retry or scope expansion.
