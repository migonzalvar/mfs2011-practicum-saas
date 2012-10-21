import unittest

from agenda import Agenda, NotAvailableSlotError, ShiftNotEmptyError
from interval import Interval


class TestAgenda(unittest.TestCase):

    def test_shift(self):
        agenda = Agenda()
        shift = agenda.add_shift(9, 14)
        self.assertEqual(Interval(9, 14), agenda.get_shift(shift))
        shifts = list(agenda.get_shifts_iter())
        self.assertEqual(shifts, [(shift, Interval(9, 14)), ])
        agenda.del_shift(shift)
        shifts = list(agenda.get_shifts_iter())
        self.assertEqual(shifts, [])

    def test_appointment(self):
        agenda = Agenda()
        shift = agenda.add_shift(9, 14)

        app1 = agenda.add_appointment(9, 10)
        self.assertEqual(Interval(9, 10), agenda.get_appointment(app1))

        agenda.del_appointment(app1)

        app2 = agenda.add_appointment(9, 10)
        self.assertEqual(Interval(9, 10), agenda.get_appointment(app2))

        with self.assertRaises(NotAvailableSlotError):
            agenda.add_appointment(9, 11)

        with self.assertRaises(ShiftNotEmptyError):
            agenda.del_shift(shift)
