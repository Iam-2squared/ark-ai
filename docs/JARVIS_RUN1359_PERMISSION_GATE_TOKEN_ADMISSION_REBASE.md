# ARK Run1359 — PermissionGate exact one-shot token admission rebase

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `884bd3df8a6966065d0861677bf50eb63db2f9a9`.
- Rebased child branch: `research/run1359-permission-gate-token-admission-rebase-20261125`.
- Rebased from Draft PR #529, source child HEAD `e21100195d68535956527d664448f1ebaad49ff0`.
- Historical child CI `45530953609` was GREEN on its prior base only; it does not transfer.

## Finding and change

The frozen `OneShotAuthorization` constructor validates primitive fields at creation, but a frozen slotted instance can be reflectively mutated before use. PermissionGate previously captured/read the mutated token fields before exact primitive admission, allowing subclass callbacks or malformed expiry values to reach authorization callbacks.

The rebase retains an import-original admission helper and validates exact built-in token ID/request ID strings plus an exact non-bool SQLite-range integer expiry before grant iteration, registered registry binding, hashing or token consumption. It uses identity-first post-callback checks so hostile subclass equality/hash/ordering methods do not execute during epoch validation.

The public `OneShotAuthorization`, `PermissionGate`, `ToolCall`, `ToolSpec`, `CapabilityGrant`, registry identity, audit schema and executor contracts are unchanged. This package covers PermissionGate only; durable occurrence-ledger token admission remains a separate follow-up.

## Regression coverage

Synthetic tests cover token-ID and request-ID subclasses, blank/malformed values, bool/int-subclass/negative/overflow expiries, direct and registered gate denial before grant iteration, and substituted admission-helper refusal. The backend is an inert sentinel and must never execute.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.

## Evidence boundary

Local-only authorization-input admission. No authenticated issuer, human consent, trusted time, restart-safe token ledger, independent custody, cross-store atomicity or exactly-once external effect is claimed. No live data, real backend, network/device I/O, paid/external compute, credentials, hardware, destructive operation, frozen-contract change, protected V2 evaluation, Candidate promotion, main merge or UI work occurred. PR #5 remains Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
