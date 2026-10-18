def _validated_nonempty_pairs(intervals):
    """Return (start, end) tuples with empty intervals removed.

    Raises ValueError if any interval has end < start. Consumes the input
    exactly once, so generators are supported, and never mutates it.
    """
    pairs = []
    for start, end in intervals:
        if end < start:
            raise ValueError(f"reversed interval bounds: ({start}, {end})")
        if start < end:
            pairs.append((start, end))
    return pairs


def _merge_sorted(pairs):
    """Merge overlapping or touching half-open intervals sorted by start."""
    merged = []
    for start, end in pairs:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def merge_intervals(intervals):
    """Return a new sorted list of merged half-open (start, end) tuples.

    Overlapping and touching intervals are merged; empty intervals are
    dropped; reversed intervals raise ValueError. The input is not modified.
    """
    pairs = _validated_nonempty_pairs(intervals)
    return _merge_sorted(sorted(pairs))
