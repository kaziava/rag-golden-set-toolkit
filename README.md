# rag-golden-set-toolkit

Companion repo to the Dev.to post "The Negative Test That Passed for the
Wrong Reason", and the working home of its follow-up, co-authored with
Edward Izgorodin.

Not a library. Copy the pieces you need.

## What is here

- `golden_set.example.json` — negative-test row schema: `trap_chunk_id`,
  `trap_anchor`, `embedder_tag`, `last_validated`.
- `ci_eval.example.py` — the three-verdict runner: pass / fail /
  "test did not run", plus the staleness check, anchor re-resolution and
  the "re-stamp needed" flag for moved boundaries.
- `article3-draft.md` — working skeleton of the follow-up post
  "Chunk-id vs Sentinel vs Hybrid: Whose Assertion Survives a Re-chunk".
  Review happens in commits: every round of edits is its own commit, so a
  co-author diffs instead of re-reading.

## The design rules

1. Assert the precondition, not the conclusion. A negative test only means
   something if the trap chunk actually reached the model.
2. The loudness rule: a verbatim anchor for cheap re-resolution, a chunk id
   so boundary changes fail the run, a stale flag so a vanished anchor
   cannot whisper.
3. Tag every verdict with the embedder that earned it. After a swap,
   old-tagged rows are stale by default, not silently trusted.
4. Rank ordering is free only if ranks were recorded before the swap.
   Without a chunk-diff sidecar, run one extra pass pre-swap to capture
   them; after the swap the ordering costs nothing.

If your eval cannot tell "the model refused" from "the retriever never
brought the trap," start here.
