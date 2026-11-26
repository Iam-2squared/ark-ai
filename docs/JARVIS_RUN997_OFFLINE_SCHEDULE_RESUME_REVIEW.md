# Run997 — Offline proactive schedule restart review

**Work basis:** Draft PR #8 exact head `c1d88da0ac9bd9b793911f8607b9a04390926302`, whose exact-head CI run [#44550194612](https://github.com/Iam-2squared/ark-ai/actions/runs/44550194612) completed successfully.

**Isolated branch:** `research/offline-schedule-resume-review-run997`, based on PR #8. No scheduler service, UI, or real notification path is introduced.

## Regression coverage

Eight synthetic cases exercise the existing read-only `review_offline_schedule_resume` bridge:

- Reconstruct `NOT_DUE`, `DUE_UNVERIFIED`, `EXPIRED_QUARANTINE`, and `EXHAUSTED` next-slot classifications from a retained durable quarantine prefix.
- Verify the restart cursor and retained chain witness are not advanced or rewritten by the review.
- Verify all notification, tool-execution, automatic-replay, consent and trusted-clock claims remain false.
- Reject a cursor whose index or previous occurrence identity does not match the retained quarantine prefix.
- Reject caller time earlier than the latest persisted quarantine observation.
- Append a second expired occurrence reentrantly after the first history inspection and require the final history recheck to reject the stale resume projection.

The fixtures use a disposable SQLite database, synthetic recurrence policy and caller-asserted timestamps. The review remains diagnostic only; a locally coherent prefix is not an authenticated schedule, trusted clock, or permission to notify or execute.

## Safety and limitations

No OS timer, background scheduler, notification, ToolBackend, model, network, external account, paid service, or real personal data is used. The caller-owned cursor is not made durable by this package. No frozen contract, V1/V2/V3 evidence, Memory/Planner source, UI branch, or main branch is modified.

**Validation:** tests and this report are saved. Exact-head CI is pending; no PASS is claimed. No local pytest or physical-machine result is claimed.
