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
