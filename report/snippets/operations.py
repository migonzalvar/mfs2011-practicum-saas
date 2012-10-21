from interval import Interval


def slots_in_interval(length, interval, step=None):
    step = length if step == None else step
    return (Interval(s, s + length)
            for s in range(interval.start, interval.end, step)
            if s + length <= interval.end)


def interval_overlaps(interval, intervals):
    for i in intervals:
        if interval.overlaps(i):
            return True
    return False
