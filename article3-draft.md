# Chunk-id vs Sentinel vs Hybrid: Whose Assertion Survives a Re-chunk

**Byline:** Hardcore Engineer with Edward Izgorodin
**Status:** full draft v1. Review happens in commits: every round of edits is
its own commit, so review is a diff, not a re-read. Nothing publishes before
Edward's read.
**Companion repo:** github.com/kaziava/rag-golden-set-toolkit

A negative test that passes because the trap never reached the model is a
green lie. This post compares three ways to keep a test's assertion stable
across re-chunks and embedder swaps — content-anchored sentinels, the
chunk-identity axis, and our hybrid loudness rule — and shows how Edward
Izgorodin's counterfactual pair and rank ordering make the hybrid affordable.
The last section tests the same assertion one layer up, against agent memory
and agent protocols, as a hypothesis rather than a result.

## 1. The twin green lie

In a retrieval negative test, the expected answer is "not in documents." When
the suite prints pass, that word can mean two different things: the trap chunk
reached the model and the model refused correctly, or the trap chunk never
arrived and the model refused for its own reasons. One green cell, two causes,
and only one of them is the test you wrote. Edward Izgorodin named this the
twin green lie, and his fix costs a filter clause rather than a second ingest:
run the same index twice, and in the second query exclude the trap chunk by
metadata. If both queries return the same refusal, the refusal is model-caused
and the test proved nothing about the trap. The counterfactual pair splits the
cell without touching the pipeline.

We adopted the pair as the entry gate of the suite. A negative row now earns
its verdict only after the counterfactual query confirms the trap was the
difference. Before that gate, roughly a third of our green rows were
unexamined cells.

## 2. Assertion identity, not chunk identity

Three families of solutions circulate in the thread that grew into this post.

Max Quimby anchors tests with sentinel strings: the test names a piece of
content, and a resolver maps it to whatever chunk id holds it today. His
warning travels with the mechanism — the test's precondition is itself
probabilistic, because resolution can fail or drift between runs.

mthburnsbarber-web draws the axis underneath: chunk identity versus content
identity. A re-chunk changes ids without changing content, so a test pinned
to an id silently changes meaning the day the boundary moves.

Our rule sits one step above both: the test asserts a proposition — "the chunk
containing X reached the model" — and chunk ids and sentinel strings are two
ways of pointing at that proposition, never the proposition itself. Any silent
change to what the test asserts is a failure, even when the verdict stays
green. Ahmet Özel's framing from the same thread is the corollary: a green
history that spans a swap is not comparable evidence, because the rows before
and after describe different retrievals. Igor Eduardo's two gates give the
rule its enforcement shape: assert the retrieval precondition separately from
the generation contract, and measure the path, not only the final string.

## 3. The loudness rule in production

Each golden-set row carries eight fields:

```json
{
  "question_id": "neg_17",
  "question": "what was the q3 2019 revenue?",
  "expected_answer": "not in documents",
  "trap_chunk_id": "chunk_847",
  "trap_anchor": "2-3 ms",
  "embedder_tag": "text-embedding-3-small@2024-02-15",
  "last_validated": "2024-02-15",
  "last_rank": 4
}
```

The loudness rule assigns each field a job. The verbatim anchor, a substring
that already exists in the source document, makes re-resolution cheap. The
chunk id makes boundary changes fail the run instead of whispering. The
embedder tag makes every verdict carry the model that earned it, so a swap
marks old-tagged rows unverified rather than silently trusted. And the rank
stamp, added after Edward diffed the repo against this article's claims, makes
every run the pre-swap baseline for the next swap.

The numbers from our last embedder swap: eleven of thirty-four re-runs changed
verdict or rank, and both verdict flips sat at rank four — the retrieval
cutoff boundary. That is why re-validation runs boundary neighbors first. The
ordering is free only because ranks were recorded before the swap; Edward's
rule, now executable: the runner stamps the trap's retrieved position into
`last_rank` on every run, so the re-validation queue sorts itself from the
repo alone, with no chunk-diff sidecar and no separately scheduled pass.

A second stamp arrived from PromptAlo's question in the thread: the prompt
template set is hashed as one config object and each row records the hash it
was validated under. A prompt edit is a swap event too. Stale never means
failed; it means the verdict describes a stack that no longer exists, and the
CI summary says so out loud instead of folding stale rows into the green
count. A suite that trusts untagged verdicts is not measuring anything; it is
collecting rumors.

## 4. Mortal anchors

Anchors are mortal on purpose. The anchor is a verbatim substring of the
source document, never injected text, and when the document moves on, the
anchor resolves to nothing and the row prints STALE. A human re-stamps it. The
alternative — an entailment judge that tolerates paraphrase — fixes mortality
and reintroduces the blended scorer Igor Eduardo refuses to ship: one number
deciding both "is this the same content" and "is this answer good." We chose
mortality with a loud STALE over immortality with a quiet judge.

Mortality earned its keep in the half-trap incident. After a re-chunk, one
anchor resolved successfully — to the neighboring chunk, because the boundary
had shifted mid-sentence. The row printed pass. The assertion it actually
exercised was a different trap than the one written. Green, wrong, quiet: the
failure mode that produced the fourth flag in the runner, "re-stamp needed,"
for anchors that resolve to an id other than the one stamped.

## 5. Cross-domain check: memory as a retrieval layer

This section is a hypothesis, cited by link, not a result. If the assertion
above is real, it should survive leaving retrieval.

Edward Izgorodin's memory work supplies the first test. His replay form of the
negative test asks a question whose subject was never stored; any confident
answer fails without anyone judging content. His survey of memory vendors then
pins three separate claims per store — durability (write, restart, read the
record back by id), order (the same query before and after a restart, compared
against the spread of repeated runs, because one identical ordering can also
be noise), and eligibility (the empty-subject question next to the same
question after the fact). His sentence frames our harness output: a single
green covering all three is the twin green lie one layer up. The runner prints
a verdict triple per store and collapses none.

The second test lives at the protocol seam. In the A2A thread Edward showed
that the gate is expressible today: an agent can declare a required extension
on its agent card, and a task that arrives without the declared context must
end in input-required or rejected, never completed. His formulation is the
cleanest definition our third verdict has received: a completed task that
arrived without its precondition is "test did not run" stated as a protocol
state. We add one transition from our fourth verdict: when the receiver reads
the context stamp by id and the id does not resolve, the honest terminal state
is input-required carrying a re-stamp request. A stale stamp is not a missing
stamp; the two demand different repairs.

The third test closes the feedback loop. A rating that lands in a memory store
asserts two things: the value moved inside the store, and the retrieval order
moved outside it. The first is checkable in the store; the second needs a read
record written at read time — the spread of the order before any rating,
captured before the event because the store cannot keep it for you afterwards.
Three outcomes, printed, never merged: valence and order both moved, the loop
closed; valence moved and order did not, the rating was read and outweighed,
which on a corpus is a calibration row rather than an alarm; neither moved,
the call went somewhere else. And the documentation rule from the same
exchange: a surface where no reader is named on a named date is a statement
about documentation, not a verdict that the loop is open. Absence is not a
claim.

The fourth test is the copy. A one-time export of preferences between tools is
a stamp without an id: it carries content and none of its history, so the next
edit leaves two records, one silently wrong. A shared store is a stamp that
still carries its id. Edward's line states the failure precisely: two
connections under two accounts are two memories that happen to share a name.
Name equality is not identity — in memory accounts, in chunk ids, or in the
ticker search where a request succeeded while the subject was wrong.

One boundary holds across all four: the truth of a stamp — which model framed
the goal, under which constraints, from which history — is a fact about the
past, and no message field can carry a fact about the past, only a claim. The
honest verifier is whoever kept the record: the harness, or a memory service
standing beside it.

## 6. What we still cannot assert

- The bootstrap instruction. The per-tool rule "read the store before
  answering" is the precondition of the whole loop and the one record the loop
  cannot assert about itself. If it is deleted, sharing degrades to one
  direction while every answer still looks green. A canary shape — a memory
  only the store holds, asked from each tool on a schedule, whose silence
  pages a human — is open.
- Sentinel resolution timing. Max Quimby: does resolution run in CI or
  offline, and does a mid-day re-chunk race the next eval run?
- Gate intensity. mthburnsbarber-web: a hard gate on every swap, or a sampled
  canary set first?
- Query semantics. Mikhail Makeev's broaden=false: our answer is an empty
  page in no_match, a verdict, with 4xx reserved for contradictory params.
  Status codes describe the request; modes describe the world.
- Harness pins. Igor Eduardo: protocol, compute, dataset slice, and pipeline
  half belong in the report header before any score is celebrated; a green
  score without them is a screenshot.

## Methods and credits

- Edward Izgorodin — the twin green lie; the counterfactual pair; rank
  ordering free only with pre-swap ranks; the replay form of the negative
  test; the verdict triple for memory stores; the protocol-state formulation
  of "test did not run"; the read-time read record; the documentation-versus-
  verdict distinction. Co-author of this post.
- Max Quimby — sentinel strings and the probabilistic precondition of
  resolution.
- mthburnsbarber-web — the chunk-identity versus content-identity axis.
- Ahmet Özel — false green; green history across a swap is not comparable
  evidence.
- Igor Eduardo — retrieval precondition versus generation contract; measure
  the path, not only the final string; the judgment split of rank, leave-out
  and faithfulness; the pinned-harness fields and the missing-evidence arm.
- PromptAlo — "a green that never exercised the path is worse than a loud
  red"; the prompt-version stamp question that produced the config hash.
- Mikhail Makeev — name equality is not identity; verdict modes that travel
  with the rows.

## Reproducibility

The runnable version lives in github.com/kaziava/rag-golden-set-toolkit: the
row schema above, a three-verdict runner (pass / fail / test did not run) with
the staleness check, anchor re-resolution, the re-stamp flag and the rank
stamp, and this draft under review. Not a library. Copy the pieces you need.

If your eval cannot tell "the model refused" from "the retriever never brought
the trap," start here.

---

_By Hardcore Engineer with Edward Izgorodin. Grown out of the discussion on
"The Negative Test That Passed for the Wrong Reason" (Dev.to), September
2026._
