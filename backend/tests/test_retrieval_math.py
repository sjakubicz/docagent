from math import isclose, log2

from docagent.eval.metrics import (
    hit_rate_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    unique,
)
from docagent.search.hybrid import reciprocal_rank_fusion


def test_rrf_rewards_items_ranked_high_in_both_lists():
    fused = reciprocal_rank_fusion([[1, 2, 3], [3, 1, 4]], k=60)
    assert [item for item, _ in fused][:2] == [1, 3]
    assert {item for item, _ in fused} == {1, 2, 3, 4}


def test_metrics():
    retrieved = ["a", "b", "c"]
    assert hit_rate_at_k(retrieved, {"c"}, 2) == 0.0
    assert hit_rate_at_k(retrieved, {"c"}, 3) == 1.0
    assert reciprocal_rank(retrieved, {"b"}, 3) == 0.5
    assert reciprocal_rank(retrieved, {"z"}, 3) == 0.0
    assert recall_at_k(retrieved, {"a", "z"}, 3) == 0.5


def test_precision_and_ndcg():
    retrieved = ["a", "b", "c", "d"]
    assert precision_at_k(retrieved, {"b", "d"}, 4) == 0.5
    assert ndcg_at_k(["b", "a"], {"b"}, 2) == 1.0
    assert isclose(ndcg_at_k(["a", "b"], {"b"}, 2), 1 / log2(3))
    assert ndcg_at_k(["a"], set(), 1) == 0.0
    assert recall_at_k(retrieved, set(), 4) == 0.0


def test_unique_keeps_first_occurrence_order():
    assert unique([("a", 1), ("b", 2), ("a", 1)]) == [("a", 1), ("b", 2)]
