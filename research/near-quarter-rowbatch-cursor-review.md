# Independent bounded row-batch cursor review

Reviewer: Mathematical Reviewer (`gpt-6-astra`, high). Cursor source
`research/near_quarter_rowbatch_cursor.py`, SHA-256
`738a545abc1909bc126ca916d225dfef90bea8b974142a5885cb9e2f632e2422`,
is approved as a component of design `4fec375e...`. This approval does not cover
the then-unfrozen core, codec, adapter or any numerical/host allocation.

Domain construction consumes at most 1,522 values before rejecting an oversize
sequence, validates equal ID/weight lengths, unique integer IDs, weights one or
two, deficit one/two and remaining count zero through39, and stores immutable
tuples. Cursor fields must be exact integers and canonical: SINGLE identifies
a matching-weight entry, PAIR identifies ordered local indices i<j with weight
one and sufficient remaining count, and END has zero indices. NONE is not an
active domain cursor. The generic domain's ID bound includes the whole family;
the core remains responsible for restricting actual branch IDs to four-orbits.

First/successor enumerate every matching singleton in local order, then every
eligible weight-one pair in lexicographic local-index order. A pair's successor
advances j and then i, skipping ineligible entries. No global ID ordering or
flattened uint16 pair count is used. Each scan step calls the supplied check.
Frozen cursors/domains are not mutated, so an exception during successor leaves
the prior cursor authoritative. END is absorbing.

Reviewer-only direct component checks independently tested all504 combinations
of domain lengths0..5, weight patterns, deficits and remaining counts0..3
against explicit singleton/combinations sequences. Seventeen injected successor
interruption points preserved immutable inputs and produced the same successor
on retry. Invalid NONE, equal pair indices, boolean indices, mismatched weight
and noncanonical END cases rejected. Arithmetic-only boundary checks verify
PAIR(1519,1520) maps to IDs1520/1521 and then END in a length1521 domain; no n79
grid, geometry, enumeration or search was constructed. The source hash was
rechecked after this validation.
