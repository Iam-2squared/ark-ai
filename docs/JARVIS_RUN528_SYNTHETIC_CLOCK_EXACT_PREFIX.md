# Run528 — Synthetic clock retained-prefix exact-field review

**PR #8, research/jarvis-foundations — isolated/free-only diagnostic.** Synthetic samples are caller controlled. This does not authenticate a clock, unlock Tool execution, notification, scheduler replay, human approval or any real action.

- **Source:** `src/ark/agency/synthetic_clock_sequence_review.py`, commit `6112c1e3acc60d090144a0b9cb83a9a7e00b09dd`.
- **Tests:** `tests/test_synthetic_clock_prefix_exact_fields_run528.py`, combined source+test HEAD `76e33a9c245e4bb441686c8527869b54bcd4ad3a`.
- **Change:** a retained history prefix is validated against the exact captured field tuple, not the mutable `SyntheticClockWitness.__eq__` method. A patchable dataclass comparison must neither accept a forged retained hash/wall time nor reject a matching prefix.
- **Tests:** four authored synthetic cases: forged hash, forged wall time, forced `__eq__ == False`, and an equality callback that raises if called. No host clock, network, GPU, external Tool, or personal data is read.
- **Limits:** only same-process, untrusted, bounded, caller-supplied sequence continuity. An equality-independent digest comparison does not attest original source, monotonic hardware or physical effects. The existing no-authority properties remain false. Changes do not touch frozen contracts.
- **Evidence:** authored test count is not a standalone PASS. Evaluate GitHub Actions only at exact source+test head. V1/V2 and V3 protected evaluation gates remain unchanged; overall ARK/JARVIS NOT_PASSED.
