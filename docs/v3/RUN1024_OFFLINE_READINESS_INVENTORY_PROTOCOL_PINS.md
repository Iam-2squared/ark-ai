# Run1024 — passive V3 readiness inventory protocol pins

## Scope

This free-only validation package hardens `src/ark/learning/offline_readiness_inventory.py` without changing V3 Contract 1, the frozen experiment snapshot template, approval fields, or any training/export behavior.

The inventory is a passive diagnostic that lists literal unresolved identity/budget fields. A snapshot with no placeholders is still not authenticated readiness and never authorizes external compute, Candidate generation, protected evaluation, or promotion.

## Change

- The fixed section-to-field inventory is now a read-only mapping with immutable tuple values.
- Placeholder, input-denial, and output-authority vectors are pinned by import-time identity.
- The inventory result class, field descriptors, constructor/lookup hooks, and false-only authority descriptors are pinned before any snapshot traversal.
- The module's JSON/hash functions and imported snapshot-tree epoch helpers are pinned before use; substitutions fail closed rather than producing a plausible-looking diagnostic digest.
- Existing exact False authorization requirements and placeholder classification remain unchanged.

## Regression coverage

`tests/v3/test_offline_readiness_inventory_protocol_pins_run1024.py` covers equal-valued vector rebinding, in-place section mutation, digest/snapshot-helper substitution before callback execution, replaced false-only authority getters, and the unchanged passive inventory result.

## Limits

These are local process-integrity checks, not a sandbox against arbitrary code already executing in the process, authenticated snapshot provenance, human approval, consent, provider billing caps, trusted time, hardware identity, or permission to run training. No Candidate adapter or weights are created. No model, tokenizer, converter, quantizer, subprocess, GPU, paid service, or external compute is invoked.

PR #5 remains gated Draft/unmerged. This child branch remains Draft and isolated pending exact-head six-job CI. No protected V2 evaluation, frozen-contract change, UI work, PR #9 change, or main merge occurs.
