import unittest

from interval import Interval
from operations import slots_in_interval, interval_overlaps


class TestOperations(unittest.TestCase):

    def test_find_free_slots(self):
        shift = Interval(9, 14)
        appointments = [Interval(9, 10), Interval(10, 11), Interval(13, 14)]

        slots = slots_in_interval(1, shift)
        free = [s for s in slots if not interval_overlaps(s, appointments)]

        self.assertEqual(free, [Interval(11, 12), Interval(12, 13)])
