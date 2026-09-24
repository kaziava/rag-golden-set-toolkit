"""Three-verdict runner for RAG negative tests.

Verdicts:
  pass             - trap retrieved AND the model refused as expected
  fail             - trap retrieved BUT the model answered anyway
  test did not run - the trap chunk never reached the model

Companion code to the Dev.to post "The Negative Test That Passed for the
Wrong Reason". Not a library: copy the pieces you need.
"""

import json


def load_golden_set(path="golden_set.example.json"):
    """Load negative-test rows from the golden set file."""
    with open(path) as f:
        return json.load(f)["tests"]


def evaluate(test, retrieved_chunk_ids, model_answer):
    """Return the verdict for one negative test.

    The retrieval gate is asserted before the generation gate: a missing
    trap chunk means the test never exercised the path it claims to cover.
    """
    if test["trap_chunk_id"] not in retrieved_chunk_ids:
        return "test did not run"
    if model_answer.strip().lower() == test["expected_answer"].strip().lower():
        return "pass"
    return "fail"


def is_stale(test, current_embedder):
    """True when the row was validated under a different embedder.

    The embedder tag has the form "model-name@YYYY-MM-DD"; everything before
    the @ is the model that earned the verdict.
    """
    return test["embedder_tag"].split("@")[0] != current_embedder


def resolve_anchor(index_chunks, test):
    """Loudness rule: verbatim anchor -> current chunk id, or STALE.

    The anchor is a substring that already exists in the source document.
    If no chunk contains it, the document changed and the row must be
    re-stamped by a human instead of silently re-pointing.
    """
    hits = [c["id"] for c in index_chunks if test["trap_anchor"] in c["text"]]
    return hits[0] if hits else "STALE"


def run(retrieve_fn, ask_fn, index_chunks, current_embedder="bge-large-v1.5"):
    """Run the whole negative suite and print one line per row.

    retrieve_fn(question) -> list of chunk dicts with "id" and "text"
    ask_fn(question, retrieved) -> the model's answer string
    index_chunks -> the current full index, for anchor re-resolution
    """
    results = []
    for test in load_golden_set():
        retrieved = retrieve_fn(test["question"])
        answer = ask_fn(test["question"], retrieved)
        verdict = evaluate(test, [c["id"] for c in retrieved], answer)
        stale = is_stale(test, current_embedder)
        anchor = resolve_anchor(index_chunks, test)
        if anchor != "STALE" and anchor != test["trap_chunk_id"]:
            verdict = "re-stamp needed"
        results.append((test["question_id"], verdict, stale, anchor))
        print(f"{test['question_id']:8} {verdict:16} stale={stale} anchor={anchor}")
    return results


if __name__ == "__main__":
    print("Wire retrieve_fn, ask_fn and index_chunks to your pipeline,")
    print("then call run(). See README.md for the design rules.")
