import unittest

from interval import Interval, slots_in_interval, interval_overlaps


class TestInterval(unittest.TestCase):

    def test_contains(self):
        morning = Interval(9, 14)
        meeting1 = Interval(10, 12)
        meeting2 = Interval(12, 14)
        meeting3 = Interval(13, 15)
        meeting4 = Interval(16, 19)

        self.assertIn(meeting1, morning)
        self.assertIn(meeting2, morning)
        self.assertNotIn(meeting3, morning)
        self.assertNotIn(meeting4, morning)

    def test_overlaps(self):
        lunch = Interval(14, 16)
        meeting2 = Interval(12, 14)
        meeting3 = Interval(13, 15)

        self.assertFalse(meeting2.overlaps(lunch))
        self.assertTrue(meeting2.overlaps(meeting3))
        self.assertTrue(meeting3.overlaps(lunch))

    def test_equals(self):
        morning = Interval(9, 14)
        afternoon = Interval(16, 19)
        meeting4 = Interval(16, 19)

        self.assertEqual(afternoon, meeting4)
        self.assertNotEqual(morning, afternoon)


class TestOperations(unittest.TestCase):

    def test_find_free_slots(self):
        shift = Interval(9, 14)
        appointments = [Interval(9, 10), Interval(10, 11), Interval(13, 14)]

        slots = slots_in_interval(1, shift)
        free = [s for s in slots if not interval_overlaps(s, appointments)]

        self.assertEqual(free, [Interval(11, 12), Interval(12, 13)])

    def test_slots_in_interval_with_steps(self):
        shift = Interval(10, 14)
        slots = list(slots_in_interval(1, shift, 2))

        self.assertEquals(slots, [Interval(10, 11), Interval(12, 13)])

