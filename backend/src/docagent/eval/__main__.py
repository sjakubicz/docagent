import argparse
import json
import time
from pathlib import Path

from docagent.db import SessionLocal
from docagent.eval.metrics import (
    hit_rate_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    unique,
)
from docagent.search.bm25 import bm25_index
from docagent.search.hybrid import search
from docagent.search.modes import Mode

MODES: tuple[Mode, ...] = ("bm25", "vector", "hybrid")
METRICS = {
    "hit@1": lambda r, rel, k: hit_rate_at_k(r, rel, 1),
    "P@k": precision_at_k,
    "R@k": recall_at_k,
    "MRR@k": reciprocal_rank,
    "nDCG@k": ndcg_at_k,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("questions", nargs="?", default="../data/eval/questions.json")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    questions = json.loads(Path(args.questions).read_text())
    n = len(questions)
    with SessionLocal() as session:
        bm25_index.rebuild(session)
        print(f"{n} questions, k={args.k}, relevance = expected (filename, page)\n")
        print(f"{'mode':<8}" + "".join(f"{name:>8}" for name in METRICS) + f"{'ms/q':>8}")
        for mode in MODES:
            totals = dict.fromkeys(METRICS, 0.0)
            start = time.perf_counter()
            for q in questions:
                hits = search(session, q["question"], k=args.k, mode=mode)
                retrieved = unique([(h.filename, h.page) for h in hits])
                relevant = {(q["filename"], q["page"])}
                for name, metric in METRICS.items():
                    totals[name] += metric(retrieved, relevant, args.k)
            ms = (time.perf_counter() - start) * 1000 / n
            row = "".join(f"{totals[name] / n:>8.3f}" for name in METRICS)
            print(f"{mode:<8}{row}{ms:>8.1f}")


if __name__ == "__main__":
    main()
