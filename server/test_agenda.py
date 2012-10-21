import unittest

from agenda import (ds, RedisDatastore, AgendaController,
                    NotAvailableSlotError, ShiftNotEmptyError)
from interval import Interval


class TestAgenda(unittest.TestCase):

    def setUp(self):
        ds()

    def tearDown(self):
        delattr(ds, 'datastore')

    def test_shift(self):
        agenda = AgendaController()
        shift = agenda.add_shift(9, 14)
        shift = agenda.get_shift(shift.key)
        self.assertEqual(shift.interval, Interval(9, 14))
        shifts = list(agenda.get_shifts_itervalues())
        self.assertEqual([s.key for s in shifts], [shift.key, ])
        self.assertEqual([s.interval for s in shifts], [shift.interval, ])
        agenda.del_shift(shift.key)
        shifts = list(agenda.get_shifts_itervalues())
        self.assertEqual(shifts, [])
        agenda.destroy()

    def test_appointment(self):
        agenda = AgendaController()
        shift = agenda.add_shift(9, 14)

        with self.assertRaises(NotAvailableSlotError):
            agenda.add_appointment(8, 9)

        app1 = agenda.add_appointment(9, 10)
        app1 = agenda.get_appointment(app1.key)
        self.assertEqual(app1.interval, Interval(9, 10))

        agenda.del_appointment(app1.key)
        with self.assertRaises(KeyError):
            app1 = agenda.get_appointment(app1.key)

        app2 = agenda.add_appointment(9, 10)
        app2 = agenda.get_appointment(app2.key)
        self.assertEqual(app2.interval, Interval(9, 10))

        appos = list(agenda.get_appointments_in_shift_iteritems(shift.key))
        print appos

        with self.assertRaises(NotAvailableSlotError):
            agenda.add_appointment(9, 11)

        with self.assertRaises(NotAvailableSlotError):
            agenda.add_appointment(9, 11)

        with self.assertRaises(ShiftNotEmptyError):
            agenda.del_shift(shift.key)

        agenda.del_appointment(app2.key)
        with self.assertRaises(KeyError):
            app1 = agenda.get_appointment(app1)

        agenda.del_shift(shift.key)
        agenda.destroy()

    def test_all_appointments_in_agenda(self):
        agenda = AgendaController()

        shifts_intervals = ((9, 14), (16, 19), (22, 24))

        for start, end in shifts_intervals:
            agenda.add_shift(start, end)

        appos_intervals = [(interval_start, interval_start + 1)
                           for start, end in shifts_intervals
                           for interval_start in range(start, end, 1)]

        for start, end in appos_intervals:
            agenda.add_appointment(start, end)

        for _, appo in agenda.get_appointments_iteritems():
            interval = (appo.interval.start, appo.interval.end)
            self.assertIn(interval, appos_intervals, "Obtained appointments no it inserted")

        agenda.destroy()

    def test_filter_shifts(self):
        agenda = AgendaController()

        shifts_intervals = ((9, 14), (16, 19), (22, 24), (12, 17))
        shifts = []

        for start, end in shifts_intervals:
            s = agenda.add_shift(start, end)
            shifts.append((s.key, s))

        test_array = (
            (0, 9, []),
            (9, 24, shifts),
            (9, 22, [shifts[i] for i in (0, 1, 3)]),
            (12, 17, [shifts[i] for i in (0, 1, 3)]),
            (16, 24, [shifts[i] for i in (1, 2, 3)]),
            (24, 99, []),
        )
        for start, end, result in test_array:
            shifts_in_interval = list(agenda.get_shifts_iteritems(start, end))

            self.assertEquals(
                              [k for k, _ in shifts_in_interval].sort(),
                              [k for k, _ in result].sort())

        agenda.destroy()

    def test_filter_appos(self):
        agenda = AgendaController()

        shifts_intervals = ((9, 14), (16, 19), (12, 17))

        for start, end in shifts_intervals:
            agenda.add_shift(start, end)

        appos_intervals = [(interval_start, interval_start + 1)
                           for start, end in shifts_intervals
                           for interval_start in range(start, end, 1)]

        appos = []
        for start, end in appos_intervals:
            appo = agenda.add_appointment(start, end)
            appos.append((appo.key, appo))

        test_array = (
            (0, 9, []),
            (9, 19, appos),
            (19, 99, []),
        )
        for start, end, result in test_array:
            appos_in_interval = list(agenda.get_appointments_iteritems(start, end))

            self.assertEquals(
                              [k for k, _ in appos_in_interval].sort(),
                              [k for k, _ in result].sort())


        agenda.destroy()

    def test_free_slots(self):
        agenda = AgendaController()
        agenda.add_shift(9, 14)
        agenda.add_shift(13, 14)

        free_expected = [Interval(s, e) for s, e in (9, 10), (10, 11), (11, 12), (12, 13), (13, 14)]
        free_slots = list(agenda.get_free_slots(0, 20, 1))

        self.assertEqual(
             free_slots,
             free_expected,
             "Error calculating free slots")

        agenda.destroy()

    def test_minimum_length(self):
        agenda = AgendaController()
        agenda.minimum_length = 2
        _ = agenda.add_shift(10, 14)

        with self.assertRaises(NotAvailableSlotError):
            agenda.add_appointment(11, 14)


class TestAgendaRedis(TestAgenda):

    def setUp(self):
        ds()
        setattr(ds, 'datastore', RedisDatastore())

    def tearDown(self):
        #ds()._rds.flushdb()
        delattr(ds, 'datastore')
