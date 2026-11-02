# Run560 — Import-original denial custody for synthetic privacy and due previews

**Scope:** reversible, local-only review of disconnected fixtures. This note is not
an authorization, human consent record, trusted-clock proof, OS notification,
tool dispatch, retained-memory erasure, or evidence of external effects.

## Privacy fixture preflight

`src/ark/offline_context_redaction.py` now captures the **original imported
property descriptors** of `RedactedOfflinePreview` for consent, erasure,
external export and Tool execution. A substituted property returning `False`
is still arbitrary executable callback code. The review now rejects altered
descriptors **before reading or hashing source text**, and checks their
identity at each subsequent source/callback epoch instead of rebasing from
already-tampered properties. Existing tests expecting harmless injected
`False` getters were corrected to require the fail-closed behavior.

New tests `tests/test_offline_redaction_import_denial_custody_run560.py`
cover four preinstalled getter substitutions, one swap during source digest
calculation, and one unchanged full-mask fixture (**six authored cases**).
They assert no substituted property is called during early rejection.
No automatic PII detection or external disclosure permission is implied.

## Offline recurrence preflight

`src/ark/disconnected_schedule_preview.py` likewise retains import-time
descriptors for the five denied clock/notification/Tool/replay/consent
properties. It rejects preinstalled callback substitutions before processing
the synthetic recurrence policy or caller-asserted time and rechecks after
hash/construction callbacks. Fingerprints, occurrence state classification,
and quarantine labels retain their previous logic.

New tests `tests/test_schedule_preview_import_denial_custody_run560.py`
cover five preinstalled substitutions, one substitution during recurrence
fingerprint hashing, and unchanged DUE/EXPIRED_QUARANTINE behavior
(**seven authored cases**). No OS timer or real notification is started.

## Evidence and limitations

- Privacy source change: `3bcc9403acc3becb828f8b7e2278c2067b70986c`;
  regressions through `70eac3562110dd93fa2395c38ceb3685a8158d82`.
- Recurrence source change: `5e4f92e263530476094636f2f56c0bf9889a1b75`;
  regressions `33cb6a84039a0c1baba08d7382f81412d37550e3`.
- **13 authored parameter-expanded pytest cases** across both packages; these
  are not an independently executed local pytest PASS count. CI conclusions
  must be looked up at their **exact** source+test HEADs, not assumed.
- Import-original properties are a diagnostic integrity boundary, not a
  defense against arbitrary malicious Python execution, module replacement,
  external effects, malicious inputs before module import, or process-level
  compromise. GitHub Actions tests exercise synthetic fixtures only.
- Frozen V1/V2/Local UI/Launcher contracts/evidence, `main`, live ToolBackend,
  protected V2 evaluation and external services remain untouched.
