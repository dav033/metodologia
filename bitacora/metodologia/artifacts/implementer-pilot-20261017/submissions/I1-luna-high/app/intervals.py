def merge_intervals(intervals):
    nonempty = []
    for start, end in intervals:
        if start > end:
            raise ValueError("interval start must not exceed interval end")
        if start < end:
            nonempty.append((start, end))

    result = []
    for start, end in sorted(nonempty):
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result
