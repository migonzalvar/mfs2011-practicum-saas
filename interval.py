class Interval(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __eq__(self, other):
        return (other.start == self.start and
                other.end == self.end)

    def __contains__(self, other):
        return other.start >= self.start and other.end <= self.end

    def overlaps(self, other):
        return other.end > self.start and self.end > other.start

    def __repr__(self):
        return "<Interval(%s,%s)>" % (self.start, self.end)

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