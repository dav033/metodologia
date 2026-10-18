def _validate(pairs):
    """Return (start, end) tuples, raising ValueError on any reversed bounds."""
    checked = []
    for start, end in pairs:
        if start > end:
            raise ValueError(f"reversed interval: ({start}, {end})")
        checked.append((start, end))
    return checked


def merge_intervals(intervals):
    """Merge half-open integer intervals that overlap or touch.

    Empty intervals (start == end) are dropped. Reversed intervals
    (start > end) raise ValueError, even when other intervals are empty.
    The input is not modified and may be any iterable, including generators.
    """
    # Materialize and validate every pair before filtering, so a reversed
    # bound is reported regardless of the rest of the input.
    pairs = _validate(intervals)
    non_empty = sorted(pair for pair in pairs if pair[0] < pair[1])

    merged = []
    for start, end in non_empty:
        # Touching boundaries (start == previous end) merge as well.
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
