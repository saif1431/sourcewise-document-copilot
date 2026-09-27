"""Reciprocal Rank Fusion — combines multiple ranked ID lists into one ranking.

Used to merge the pgvector semantic search ranking with the Postgres full-text
search ranking without needing their scores to be on comparable scales (cosine
distance and ts_rank aren't). RRF only looks at rank position within each list.
"""

from typing import Hashable, TypeVar

DEFAULT_K = 60  # standard RRF damping constant from the original paper

ItemId = TypeVar("ItemId", bound=Hashable)


def reciprocal_rank_fusion(
    ranked_lists: list[list[ItemId]],
    *,
    k: int = DEFAULT_K,
) -> list[tuple[ItemId, float]]:
    """Fuse ranked lists of IDs into one ranking, highest score first.

    score(id) = sum, over lists containing id, of 1 / (k + rank_in_that_list)
    (rank is 1-based). An id present in multiple lists accumulates a score
    from each — it doesn't need to be *retrieved* via just one strategy to
    surface, but ranking well in either strategy pushes it up.
    """
    scores: dict[ItemId, float] = {}
    for ranked_list in ranked_lists:
        for rank, item_id in enumerate(ranked_list, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
