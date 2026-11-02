# Run554 — V3 passive inventory: original denial custody

**Scope:** PR #5 Draft/unmerged, free/local/read-only readiness reporting.
Invocation work basis `0cbb4a611205cf411d79aee6a7e2b8b7d717b117`.

The unapproved snapshot placeholder inventory previously captured the four
`OfflineReadinessInventory` denial-property descriptors *only when called*.
A substituted False-only property installed before the call could become
the baseline, despite not being the original passive contract. The
inventory now retains the four descriptor identities at **module import**,
checks them before inventorying and through final result inspection, and
rejects replacements rather than adopting them as trustworthy.

The unchanged denial-only fields are external compute, Candidate generation,
protected V2 evaluation, and promotion. No field can authorize paid work.

Implementation commit: `78b0df9abf31936169b2e26d168d951138545db6`.
New regression test commit: `7e54f54d6efbcfa541971195697c1e494ee327ea`.
Seven authored parameter-expanded cases cover four preinstalled False-only
substitutions, a True substitution, reentrant hashing-time replacement, and
the unaffected original inventory. Authored count is **not** an independently
run local pytest pass count.

GitHub Actions exact source/test run:
https://github.com/Iam-2squared/ark-ai/actions/runs/41431325484
CI must be inspected after completion. This note claims neither GREEN nor
experiment approval.

**Non-goals:** snapshot syntax, placeholder absence, hashes, this report,
and even a green CI do not establish actual model/tokenizer bytes, real
dataset approval, provider cost caps, licensing signoff, trusted runtime
identities, consent, training readiness or protected V2 opening. Experiment
001, frozen V3 Contract, V1/V2 and main remain unchanged. No external GPU,
paid API, Candidate generation, training, promotion, or main merge.
