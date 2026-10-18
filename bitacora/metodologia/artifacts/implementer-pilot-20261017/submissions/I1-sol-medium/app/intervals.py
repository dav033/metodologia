def merge_intervals(intervals):
    """Return sorted, nonempty intervals with overlaps and touching bounds merged.

    Raise ValueError for reversed bounds without modifying the input pairs.
    """
    nonempty = []
    for start, end in intervals:
        if start > end:
            raise ValueError("interval start must not exceed end")
        if start < end:
            nonempty.append((start, end))

    result = []
    for start, end in sorted(nonempty):
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result
