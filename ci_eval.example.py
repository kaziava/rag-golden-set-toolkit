"""Three-verdict runner for RAG negative tests.

Verdicts:
  pass             - trap retrieved AND the model refused as expected
  fail             - trap retrieved BUT the model answered anyway
  test did not run - the trap chunk never reached the model

Every run stamps the trap's retrieved rank back into the row, so the last
run before a swap is the pre-swap baseline and the re-validation queue
sorts itself from the repo alone. Companion code to the Dev.to post "The
Negative Test That Passed for the Wrong Reason". Not a library: copy the
pieces you need.
"""

import json
from datetime import date


def load_golden_set(path="golden_set.example.json"):
    """Load negative-test rows from the golden set file."""
    with open(path) as f:
        return json.load(f)["tests"]


def save_golden_set(rows, path="golden_set.example.json"):
    """Persist row stamps (last_rank, last_validated) back to the file."""
    with open(path, "w") as f:
        json.dump({"tests": rows}, f, indent=2)
        f.write("\n")


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


def rank_of(test, retrieved_ids):
    """1-indexed position of the trap in the retrieved order, or None.

    Rank 1 is the first item the retriever returned. A trap that never
    arrived has no rank, which is the "test did not run" case; the absence
    is itself the information the re-validation queue needs.
    """
    if test["trap_chunk_id"] not in retrieved_ids:
        return None
    return retrieved_ids.index(test["trap_chunk_id"]) + 1


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


def revalidation_queue(rows, cutoff=5):
    """Order rows boundary-neighbors-first using the stamped ranks.

    Rows whose last_rank sat closest to the retrieval cutoff are the ones a
    small shift drops entirely, so they re-run first. Rows with no stamped
    rank (the trap never arrived) go to the front: their verdict is the
    least known. Needs nothing but the repo.
    """
    def key(row):
        rank = row.get("last_rank")
        if rank is None:
            return (0, 0)
        return (1, abs(rank - cutoff))
    return sorted(rows, key=key)


def run(retrieve_fn, ask_fn, index_chunks, current_embedder="bge-large-v1.5",
        write_back=False, path="golden_set.example.json"):
    """Run the whole negative suite and print one line per row.

    retrieve_fn(question) -> list of chunk dicts with "id" and "text"
    ask_fn(question, retrieved) -> the model's answer string
    index_chunks -> the current full index, for anchor re-resolution
    write_back -> stamp last_rank and last_validated into the rows on disk

    With write_back on, every run is the pre-swap baseline for the next
    swap: the rank the trap held today is the rank the re-run queue will
    sort by tomorrow, with no chunk-diff sidecar.
    """
    rows = load_golden_set(path)
    results = []
    for test in rows:
        retrieved = retrieve_fn(test["question"])
        ids = [c["id"] for c in retrieved]
        answer = ask_fn(test["question"], retrieved)
        verdict = evaluate(test, ids, answer)
        stale = is_stale(test, current_embedder)
        anchor = resolve_anchor(index_chunks, test)
        rank = rank_of(test, ids)
        if anchor != "STALE" and anchor != test["trap_chunk_id"]:
            verdict = "re-stamp needed"
        if write_back:
            test["last_rank"] = rank
            test["last_validated"] = date.today().isoformat()
        results.append((test["question_id"], verdict, stale, anchor, rank))
        print(f"{test['question_id']:8} {verdict:16} stale={stale} rank={rank} anchor={anchor}")
    if write_back:
        save_golden_set(rows, path)
    return results


if __name__ == "__main__":
    print("Wire retrieve_fn, ask_fn and index_chunks to your pipeline,")
    print("then call run(write_back=True). See README.md for the design rules.")
