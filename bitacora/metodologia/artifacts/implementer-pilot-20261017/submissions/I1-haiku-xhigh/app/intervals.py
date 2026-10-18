def merge_intervals(intervals):
    """Return sorted, merged half-open (start, end) intervals as a new list.

    Overlapping and touching intervals are merged. Empty intervals are dropped.
    A reversed interval (end < start) raises ValueError.
    """
    pairs = _validated_nonempty(intervals)
    result = []
    for start, end in sorted(pairs):
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result


def _validated_nonempty(intervals):
    """Consume the input once, rejecting reversed bounds and dropping empty intervals."""
    kept = []
    for start, end in intervals:
        if end < start:
            raise ValueError(f"reversed interval: ({start}, {end})")
        if start < end:
            kept.append((start, end))
    return kept
