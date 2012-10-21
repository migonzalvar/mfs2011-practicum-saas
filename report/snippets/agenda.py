from interval import Interval
from operations import interval_overlaps, slots_in_interval


class ShiftNotEmptyError(Exception):
    pass


class NotAvailableSlotError(Exception):
    pass


class Agenda(object):

    def __init__(self, minimum_length=1):
        self._shifts = {}
        self._appointments = {}
        self._min_length = minimum_length

    def add_shift(self, start, end):
        interval = Interval(start, end)
        shift_id = id(interval)
        self._shifts[shift_id] = {
                "interval": interval,
                "appointments": {}}
        return shift_id

    def del_shift(self, shift_id):
        if self._shifts[shift_id]["appointments"] == {}:
            del self._shifts[shift_id]
        else:
            raise ShiftNotEmptyError

    def get_shift(self, shift_id):
        return self._shifts[shift_id]["interval"]

    def get_shifts_iter(self):
        for shift_id, shift in self._shifts.iteritems():
            yield shift_id, shift["interval"]

    def add_appointment(self, start, end):
        app_interval = Interval(start, end)
        app_id = id(app_interval)
        length = app_interval.end - app_interval.start
        for sid, shift in self._shifts.iteritems():
            interval = shift["interval"]
            appointments = shift["appointments"].values()
            slots = slots_in_interval(length, interval, self._min_length)
            for slot in slots:
                if slot == app_interval and \
                           not interval_overlaps(slot, appointments):
                    self._appointments[app_id] = sid
                    self._shifts[sid]["appointments"][app_id] \
                        = app_interval
                    return app_id
        raise NotAvailableSlotError

    def del_appointment(self, app_id):
        shift_id = self._appointments[app_id]
        del self._shifts[shift_id]["appointments"][app_id]
        del self._appointments[app_id]

    def get_appointment(self, app_id):
        sid = self._appointments[app_id]
        return self._shifts[sid]["appointments"][app_id]
