from app.retrieval.fusion import reciprocal_rank_fusion


def test_single_list_preserves_order() -> None:
    fused = reciprocal_rank_fusion([["a", "b", "c"]])
    assert [item_id for item_id, _ in fused] == ["a", "b", "c"]


def test_item_in_both_lists_outranks_item_in_one() -> None:
    # "b" is #2 in both lists; "a" is #1 in only the first. RRF should still
    # let cross-strategy agreement push "b" above a single-strategy top hit.
    fused = reciprocal_rank_fusion(
        [
            ["a", "b", "c"],
            ["d", "b", "e"],
        ]
    )
    ranking = [item_id for item_id, _ in fused]
    assert ranking.index("b") < ranking.index("a")
    assert ranking.index("b") < ranking.index("d")


def test_disjoint_lists_keep_all_items() -> None:
    fused = reciprocal_rank_fusion([["a", "b"], ["c", "d"]])
    assert {item_id for item_id, _ in fused} == {"a", "b", "c", "d"}


def test_empty_lists_produce_empty_result() -> None:
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []


def test_scores_are_monotonically_decreasing() -> None:
    fused = reciprocal_rank_fusion([["a", "b", "c", "d"]])
    scores = [score for _, score in fused]
    assert scores == sorted(scores, reverse=True)


def test_smaller_k_widens_the_gap_between_ranks() -> None:
    # k dampens rank differences — a smaller k means an earlier rank scores
    # relatively higher over a later one.
    small_k = dict(reciprocal_rank_fusion([["a", "b"]], k=1))
    large_k = dict(reciprocal_rank_fusion([["a", "b"]], k=1000))
    assert (small_k["a"] - small_k["b"]) > (large_k["a"] - large_k["b"])
