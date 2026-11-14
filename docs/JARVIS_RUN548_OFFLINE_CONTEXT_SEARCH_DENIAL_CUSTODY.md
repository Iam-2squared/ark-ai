# Offline Personal Context search: original denial descriptors (Run548)

This hardens a local-only, caller-supplied synthetic search preview. Source commit `39553d5738bd430dcb01d0de68d69a2c33ae1e64`, regression cases `5e51f527def452dccbfdef51af3a04a656690f4a` in Draft PR [#8](https://github.com/Iam-2squared/ark-ai/pull/8).

The previous private search already required the four authorization getters to return `False` and rechecked the result's exact field carriers. But an attacker-controlled Python callback could substitute a different property that also returns `False`, leaving the authority descriptor itself changed. The module now pins the original `OfflineContextSearchPreview` denial properties at import time. Each synthetic getter callback must return the exact `False` singleton; original descriptors and source/result fields are rechecked after every callback, including the final getter.

Eight authored pytest cases exercise preinstalled false-valued descriptor swaps, attempted prior-descriptor substitutions and an unchanged inert search. This note is not independent local execution evidence. A static mock fixture does **not** authenticate consent, row ownership, privacy revocation, retrieval provenance, disclosure permission, ToolRegistry registration, or a trusted clock.

No external context store, user data, paid API, credential, notification, real ToolBackend, protected evaluation, or main merge is touched. Frozen contracts remain unchanged. The broader privacy lifecycle and independent custody remain unresolved.
