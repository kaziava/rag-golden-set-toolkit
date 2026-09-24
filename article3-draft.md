# Chunk-id vs Sentinel vs Hybrid: Whose Assertion Survives a Re-chunk

**Byline:** Hardcore Engineer with Edward Izgorodin
**Status:** skeleton. The first full draft lands as the next commit.
**Review contract:** Edward reads before publish; every round of edits is
its own commit, so review is a diff, not a re-read.

## Abstract (working)

A negative test that passes because the trap never reached the model is a
green lie. This post compares three ways to keep a test's assertion stable
across re-chunks and embedder swaps: content-anchored sentinels (Max
Quimby), the chunk-identity vs content-identity axis (mthburnsbarber-web),
and our hybrid loudness rule — with Edward Izgorodin's counterfactual pair
and rank ordering as the methods that make the hybrid affordable.

## Sections (planned)

1. The twin green lie — Edward Izgorodin.
   "Pass" can mean trap-caused refusal or model-caused refusal; only a
   counterfactual pair (same index, second query filters the trap chunk
   out via metadata) splits the cell. One index, two queries: the
   counterfactual costs a filter clause, not an ingest.
2. Assertion identity, not chunk identity — synthesis of the thread.
   Max Quimby's sentinel strings; mthburnsbarber-web's identity axis; our
   rule: any silent change to what the test asserts is a failure.
3. The loudness rule in production.
   Eleven of thirty-four re-runs after the last swap, both flips at rank
   four; boundary neighbors first; the reproducibility note — the rank
   ordering is free only because ranks were recorded pre-swap.
4. Mortal anchors.
   A verbatim substring from the source doc, never injected; STALE when
   the document moves on; the half-trap incident: green, wrong, quiet.
5. Cross-domain check: memory as a retrieval layer (hypothesis, not
   result).
   Edward's replay form of the negative test; the vendor tag split by
   operation (retrieval-only vs write); cited by link, not by dependency,
   when his memory-side results publish.

## Credited framings

- Max Quimby — sentinel strings; "the test's precondition is itself
  probabilistic".
- mthburnsbarber-web — chunk identity vs content identity.
- Ahmet Özel — false green; green history across a swap is not comparable
  evidence.
- Igor Eduardo — retrieval precondition vs generation contract; measure
  the path, not only the final string.
- Edward Izgorodin — the assertion; the twin green lie; the counterfactual
  pair; the rank ordering; the replay form.

## Open questions parked for the draft

- Max Quimby: does his sentinel resolution run in CI or offline, and does
  a mid-day re-chunk race the next eval run?
- mthburnsbarber-web: hard gate on every swap at Black Label, or a sampled
  canary set first?
- Mikhail Makeev: broaden=false semantics — our answer is an empty page in
  no_match (a verdict), with 4xx reserved for contradictory params.
