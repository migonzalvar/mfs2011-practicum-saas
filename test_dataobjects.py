import unittest

from dataobjects import Agenda, Shift, Appointment
from interval import Interval


class TestDataobject(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_interval_dataobject(self):
        shift = Shift(None, 9, 14)
        self.assertEquals(shift.interval, Interval(9, 14))

    def test_agenda_dataobject_to_dict(self):
        agenda1 = Agenda()
        d1 = agenda1.to_dict()
        self.assertEquals(d1, {'minimum_length': 1})
        agenda2 = Agenda.from_dict(d1)
        d2 = agenda2.to_dict()
        self.assertEquals(d2, d1)

    def test_dataobjects_to_dict(self):
        for obj_a in (Agenda(),
                    Shift(None, 9, 14),
                    Appointment(None, 9, 10)):
            dict_a = obj_a.to_dict()
            obj_b = obj_a.__class__.from_dict(dict_a)
            dict_b = obj_b.to_dict()
            self.assertEquals(dict_a, dict_b,
                "Fails to_dict() from_dict() on %s" % obj_a.__class__)
