# Run1375 — V3 preflight parser guard self-custody

## Exact basis

- Parent: Draft PR #5, `research/v3-learning-evaluation`.
- Parent work-basis HEAD: `49e03192b785419ba4d4a99c06f9a4c104a821e5`.
- Child branch: `research/run1375-v3-preflight-guard-self-custody-20261125`.
- Source commit: `a58589587b7f972b507cf29862ffea802c5437a3`.
- Regression commit: `d28ae38726a5696ca78b1f96315657494dc1bef8`.

## Change

The private preflight-report verifier now retains the import-original JSON parser guard in its function defaults and compares both mutable module bindings against that retained reference before invoking the guard or parsing report bytes. This closes the simultaneous-rebinding case where both the helper name and its module-level alias could otherwise be replaced with the same no-op callable.

The JSON loader, duplicate-key hook, non-standard constant rejection, finite-float policy, report schema, frozen execution snapshot, and V3 Contract 1 are unchanged.

## Regression

A synthetic test replaces both guard bindings with the same no-op and instruments the retained JSON loader. The verifier must reject before the parser is invoked.

## Evidence boundary

This is a local synthetic parser-identity regression only. It does not load a model or tokenizer, import torch for runtime work, inspect/query a GPU, execute preflight/training, generate weights or a Candidate, open protected V2 evaluation, access external services, or perform any hardware action. No V3 PASS is claimed; exact-head Windows/Linux × Python 3.11–3.13 CI is required.
