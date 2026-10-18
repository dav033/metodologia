def _normalize(intervals):
    """Validate pairs and drop empty ones; raise ValueError on reversed bounds."""
    pairs = []
    for start, end in intervals:
        if end < start:
            raise ValueError(f"reversed interval: ({start}, {end})")
        if end > start:
            pairs.append((start, end))
    return pairs


def merge_intervals(intervals):
    """Merge overlapping or touching half-open intervals into a new sorted list."""
    result = []
    for start, end in sorted(_normalize(intervals)):
        if result and start <= result[-1][1]:
            if end > result[-1][1]:
                result[-1] = (result[-1][0], end)
        else:
            result.append((start, end))
    return result
