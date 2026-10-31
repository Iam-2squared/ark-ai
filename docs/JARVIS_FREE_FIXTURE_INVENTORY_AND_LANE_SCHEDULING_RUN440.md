# JARVIS Run440 — bounded offline fixture inventory and independent work-lane selection

**Scope:** source-level and isolated local tests only. No real Candidate, weights, dataset download, hardware action, paid compute, external API, tool dispatch, file mutation of a user-owned artifact, or credential connection. The two new modules are isolated/reversible foundations under Draft PR #8 and do not amend frozen V1/V2/Local UI/Launcher, Memory v1, ActionAudit v1 or V3 Contract 1.

## Source and exact local evidence

| Package | New source blob SHA | New regression-test blob SHA | Isolated local evidence |
|---|---|---|---|
| Read-only synthetic fixture inventory | `6d7cf62f1017778135a7b98771ad425f569d0e28` | `68de9e30981efdf84612e80de253f4c58fd08c6c` | Python 3.13.5, **36 passed** |
| Deny-only synthetic independent work-lane selector | `83d0c88f0e9f9327ade76d74df94d24406a71488` | `64674e67f0708c92f40bfbe8e9c9825a70ac1c74` | Python 3.13.5, **23 passed** |

Both test modules were executed together with `PYTHONPATH=/mnt/data/ark_run440/src pytest -q /mnt/data/ark_run440/tests`: **59 passed** in an isolated container copy. Python `compileall` also passed. GitHub-returned blob SHAs match the locally tested byte-for-byte text of each of the four new files. This is **not** a full repository test run, GitHub Actions matrix PASS, or Ruff PASS. `ruff` is unavailable in the isolated container and public `github.com` cannot resolve for a full checkout. Exact-head GitHub Actions validation is QUEUED at the time of writing.

## Package A: explicit local fixture content inventory

New `src/ark/synthetic_local_fixture_inventory_review.py` reads only explicitly named `.json`, `.txt` and `.fixture` files under a caller-supplied local root; it does not enumerate a directory, write files, load models or start compute. Canonical relative POSIX paths are required. Absolute, parent, backslash, alternate-stream, hidden-component, non-NFC, Windows-device, duplicate or case-fold alias paths are rejected. The checked path components must be local non-symlink directories and a regular file. Each file is capped at 8 MiB, an inventory at 16 MiB and 64 paths, with SHA-256 content and a deterministic domain-separated local witness.

Pre-open, open-file, and post-read inode/size/mtime/mode checks catch ordinary replacement/truncation races. A retained independent witness rejects same-sized but different byte content. The witness stores only relative names, sizes and content hashes, not plaintext contents or absolute root paths. **It is not signed provenance, owner authority, malicious filesystem protection or comprehensive TOCTOU prevention.** The caller chooses the root and files; only ephemeral test fixtures were read during this run.

Negative regression categories: 20 unsafe path parameters, six malformed ordering/size sets, symlink/parent denial, missing files without recreation, changed same-size payloads, synthetic witness mutation, malformed witness, nonregular files, and rooted symlink denial. No private content or model weights were accessed.

## Package B: deterministic free-only task-lane diagnosis

New `src/ark/agency_synthetic_lane_selector_review.py` accepts an exact, bounded, caller-declared graph of lanes. It rejects unknown dependencies/cycles/duplicate identifiers, invalid normalized paths, unsupported cost classes, ill-typed approval/reversibility flags and oversized graphs. It chooses at most five mutually path-independent, priority-ordered candidates, excluding claimed-billable or unknown-cost work, approval-needed work, irreversible work, unmet dependencies, unmet claimed-GREEN gates, and overlaps with explicitly declared in-flight CI paths.

The result is a **diagnostic work queue only**, not a scheduler that runs tools. `execution_authorized`, `github_write_authorized` and `spending_authorized` are **always False**. A caller can lie about CI GREEN, cost, or path touches; this module **never verifies GitHub jobs or licenses spending**. Future integration must use separately authenticated source-of-truth reads before any real action. Negative regressions include cost unknown, approval/irreversibility, dependency gating, graph cycles, CI conflicts, exact path-prefix false positives, capacity limits, type restrictions and deterministic order. This foundational module is independent of the new inventory: neither module imports the other or any unverified Run434/Run439 code.

## CI forensics, concurrency and remaining gates

At inspection, PR #8's source/test HEAD `0b51ce3018c8c558a74028c7c7be4eb5e029f5d6` has workflow **#1267 / run 40257968115**, all six Ubuntu/Windows 3.11–3.13 jobs **QUEUED**; newer source CI is not GREEN. Earlier concurrent Run439 HEAD `c1f5cf9a37c2f2cdd5c64fdcd7c15025f5795126` has **#1261 / 40256028959**, all six jobs **QUEUED**. Older #1259 and previous Run438 checks also remain queued, so neither detached bundle nor its independent membership path is eligible for unguarded integration. No equivalent CI was manually rerun, cancelled or duplicated.

The exact-work-basis HEAD at Run440 opening was `c1f5cf9a37c2f2cdd5c64fdcd7c15025f5795126`, reflecting concurrent uncheckpointed Run439 source and tests; canonical `PROJECT_STATUS.md` still reported Run438 then. All four new files are newly added, isolated paths. Existing frozen code was not modified. Two initial GitHub Contents creates contained a Python backslash-escape transcription fault; each was repaired immediately through the *normal* GitHub Contents update route, and Git blob SHA matches the passing local files. Their intermediate failed-head CI is not evidence of success.

**Do not integrate these diagnostic foundations into action, Candidate, training, authorization, or export workflows without exact-head GREEN tests and independent authority.**

## Next / 今後の方針

1. Inspect exact-head #1267, #1261, and the forthcoming checkpoint CI after runner execution; verify **Ruff + pytest** on Ubuntu and Windows. If FAIL, inspect actual trace and change the smallest path through normal GitHub Contents. Avoid duplicate workflow dispatch, polling loops, test skipping or weakening.
2. Preserve the original-plan independent WRITE membership boundary. After the Run434 detached bundle's specific dependent CI is GREEN, add an independent expected-membership check for missing/recomputed archive steps; retain UNKNOWN/RUNNING/reserved PENDING quarantine, no external replay.
3. Independently continue Memory CAS/expiry/continuity and privacy revocation/read freshness, and propose trusted issuer/clock audit-before-action in deny-only reversible fixtures; do not infer authentication from local SHA hashes.
4. Keep PR #5 Draft/unmerged/NOT_PASSED and PR #8 Draft/unmerged until explicit gates; no paid or potentially billable action, Candidate promotion, protected final evaluation, main merge, hardware, credentials or irreversible architecture without authorization.
