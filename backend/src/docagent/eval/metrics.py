from collections.abc import Hashable, Sequence
from collections.abc import Set as AbstractSet
from math import log2


def hit_rate_at_k[T: Hashable](retrieved: Sequence[T], relevant: AbstractSet[T], k: int) -> float:
    return 1.0 if any(r in relevant for r in retrieved[:k]) else 0.0


def recall_at_k[T: Hashable](retrieved: Sequence[T], relevant: AbstractSet[T], k: int) -> float:
    if not relevant:
        return 0.0
    return len(relevant & set(retrieved[:k])) / len(relevant)


def reciprocal_rank[T: Hashable](retrieved: Sequence[T], relevant: AbstractSet[T], k: int) -> float:
    for rank, r in enumerate(retrieved[:k], start=1):
        if r in relevant:
            return 1.0 / rank
    return 0.0


def precision_at_k[T: Hashable](retrieved: Sequence[T], relevant: AbstractSet[T], k: int) -> float:
    return sum(r in relevant for r in retrieved[:k]) / k


def ndcg_at_k[T: Hashable](retrieved: Sequence[T], relevant: AbstractSet[T], k: int) -> float:
    dcg = sum(1.0 / log2(rank + 1) for rank, r in enumerate(retrieved[:k], 1) if r in relevant)
    ideal = sum(1.0 / log2(rank + 1) for rank in range(1, min(len(relevant), k) + 1))
    return dcg / ideal if ideal else 0.0


def unique[T](items: list[T]) -> list[T]:
    return list(dict.fromkeys(items))
