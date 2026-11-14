# Foundation Prototype Evidence — 2026-09-29

Status: isolated local validation for Draft PR #8. This is not source implementation evidence and not a roadmap PASS.

Work basis: `de71ed4b9b8a1809b7c8ecdf542719e985c26ae3`.

## Coherent Memory snapshot

A minimal local SQLite prototype compared separate namespace reads with a single read transaction while another connection committed an atomic update between reads.

Results:

- separate transaction per namespace: 30/30 rounds observed a mixed old/new view;
- one read transaction for both namespaces: 30/30 rounds observed one coherent snapshot.

This supports the source contract in `MEMORY_COHERENT_SNAPSHOT_CONTRACT.md`.

## Deterministic Tool Registry identity

The canonical registry hashing rules reproduced the existing two-tool fixture exactly:

- `tools_e3fec8092546d8f7a67eee140d90ca4fcb076965953031ec176d5be4a605f146`;
- request vector `act_2d08b6d18b9952951d04d23cfb91e3ea5d2a23f8985e97bf8a7e07d5c64d0481`;
- bound vector `bound_e1ede52438411a87e0287186be607d5b501e4aeda0e7522d821ca61f8b7af8b5`.

A four-tool registry was shuffled 1,000 times before canonical sorting. All permutations produced one revision:

`tools_692a85e35942e3262224ce3f3a1b0b95a8a4a1b239d657cd0406eaee6409cec8`.

These checks remain prototype evidence until matching repository source/tests are committed and exact-head CI is GREEN.

No paid or external compute, Candidate generation, protected evaluation, or main merge occurred.
