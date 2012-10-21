import unittest

from agenda import ds, RedisDatastore, OverlappingIntervalWarning
from dataobjects import Agenda, Shift, Appointment


class TestAgenda(unittest.TestCase):

    def setUp(self):
        ds()
        setattr(ds, 'datastore', RedisDatastore())

    def tearDown(self):
        delattr(ds, 'datastore')

    def test_agenda(self):
        agenda_input = Agenda()
        agenda_input = ds().put(agenda_input)
        agenda_output = ds().get(Agenda, agenda_input.key)

        self.assertEquals(agenda_input.key, agenda_output.key)
        self.assertEquals(agenda_input.to_dict(), agenda_output.to_dict())

        ds().delete(Agenda, agenda_input.key)

    def test_shift(self):
        agenda = Agenda()
        agenda = ds().put(agenda)

        shift_input = Shift(agenda.key, 9, 14)
        shift_input = ds().put(shift_input)
        shift_output = ds().get(Shift, shift_input.key)

        self.assertEquals(shift_input.key, shift_output.key)
        self.assertEquals(shift_input.to_dict(), shift_output.to_dict())

        ds().delete(Shift, shift_input.key)
        ds().delete(Agenda, agenda.key)

    def test_appointment(self):
        agenda = Agenda()
        agenda = ds().put(agenda)
        shift = Shift(agenda.key, 9, 14)
        shift = ds().put(shift)

        appo_input = Appointment(shift.key, 9, 10)
        appo_input = ds().put(appo_input)
        appo_output = ds().get(Appointment, appo_input.key)

        self.assertEquals(appo_input.key, appo_output.key)
        self.assertEquals(appo_input.to_dict(), appo_output.to_dict())

        # TODO: Constraint not check on data sotre
        # with self.assertRaises(NotAvailableSlotError):
        #    _ = ds().put(Appointment(shift.key, 8, 9))

        with self.assertRaises(OverlappingIntervalWarning):
            _ = ds().put(Appointment(shift.key, 9, 10))

        appos = []

        appos.append(ds().put(Appointment(shift.key, 10, 11)))
        appos.append(ds().put(Appointment(shift.key, 12, 13)))
        appos.append(ds().put(Appointment(shift.key, 11, 12)))

        with self.assertRaises(OverlappingIntervalWarning):
            _ = ds().put(Appointment(shift.key, 9, 12))

        ds().delete(Appointment, appo_input.key)

        for appo in appos:
            ds().delete(Appointment, appo.key)

        ds().delete(Shift, shift.key)
        ds().delete(Agenda, agenda.key)
