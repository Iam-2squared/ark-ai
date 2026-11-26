# Run1454 — post-load staged HF snapshot revalidation

**Parent:** Draft PR #623, branch `research/run1435-v3-local-snapshot-staging-20261126`.
**Exact parent work-basis HEAD:** `3f10e395e92b90706286ebc384dae07edbc9f09d`.
**Child:** `research/run1454-v3-postload-staged-snapshot-revalidation-20261126`.

## Change

The local-only Hugging Face staging path already verifies the copied snapshot before handing it to the tokenizer and model loaders. This child adds one further check immediately after `AutoModelForCausalLM.from_pretrained()` returns and before device placement or PEFT wrapping.

If the staged tree's base-file, tokenizer-file, or chat-template identity no longer matches the reviewed execution snapshot after the model loader, the helper raises `LoRARuntimeError`. The enclosing loader scope cleans the temporary stage and does not move the returned model to an accelerator or wrap it for training.

## Synthetic regression

A fake model loader changes the staged `model.safetensors` bytes while loading. The regression requires:

- post-load staged identity revalidation to reject the changed bytes;
- no device placement;
- no PEFT configuration or wrapping;
- cleanup of the temporary staged tree on the failure path.

The test uses small synthetic files and fake tokenizer/model loaders. It does not import torch, open a model, query a GPU, execute preflight, train, write weights, create a Candidate, or use external compute.

## Evidence limits

This is a **post-load drift detector**, not proof of the exact bytes consumed internally by Transformers. It detects persistent staged-tree changes visible at the post-load rehash. It cannot detect a hostile same-user writer that changes bytes during the load and restores them before revalidation. It does not establish atomic dirfd custody, ACL isolation, fsync/power-loss durability, or immutable storage. The original local staging limitations remain in force.

No frozen contract, execution snapshot schema, training recipe, dataset, Candidate policy, V2 evaluation gate, or main branch is changed. PR #5 remains gated Draft/unmerged; PR #623 remains Draft/unmerged. No paid/external compute, credentials, hardware action, protected evaluation, Candidate generation/promotion, or UI/frontend work occurred.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No PASS or runtime authorization is claimed.
