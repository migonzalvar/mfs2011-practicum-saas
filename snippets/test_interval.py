import unittest

from interval import Interval


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
