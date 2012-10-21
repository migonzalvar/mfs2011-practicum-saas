import json
import redis

from interval import interval_overlaps, slots_in_interval, Interval
from dataobjects import (Agenda, Shift, Appointment,
                         CollectionDataobjectMixin, ParentkeyDataobjectMixin)


class ConcurrencyWarning(Exception):
    pass


class OverlappingIntervalWarning(Exception):
    pass


class NotEmptyError(Exception):
    pass


class ShiftNotEmptyError(NotEmptyError):
    pass


class NotAvailableSlotError(Exception):
    pass


class Datastore(object):

    def __init__(self):
        self._items = {'Agenda': {}, 'Shift': {}, 'Appointment': {}}
        self._collection = {'Agenda': {}, 'Shift': {}, 'Appointment': {}}

    def put(self, obj):
        obj.key = id(obj)
        self._items[obj.__class__.__name__][obj.key] = obj
        if issubclass(obj.__class__, ParentkeyDataobjectMixin):
            parent_obj = self.get(obj.parent_class, obj.parent_key)
            self._collection[parent_obj.__class__.__name__][parent_obj.key][obj.key] = obj
        if issubclass(obj.__class__, CollectionDataobjectMixin):
            if obj.key not in self._collection[obj.__class__.__name__]:
                self._collection[obj.__class__.__name__][obj.key] = {}
            self._set_collection_methods(obj)
        return obj

    def delete(self, cls, key):
        obj = self.get(cls, key)
        if cls == Shift:
            if list(obj.iteritems()):
                raise ShiftNotEmptyError
        if issubclass(cls, ParentkeyDataobjectMixin):
            parent_obj = self.get(obj.parent_class, obj.parent_key)
            try:
                del self._collection[parent_obj.__class__.__name__][parent_obj.key][obj.key]
            except KeyError:
                pass
        del self._items[cls.__name__][key]
        return

    def get(self, cls, key):
        obj = self._items[cls.__name__][key]
        if issubclass(obj.__class__, CollectionDataobjectMixin):
            self._set_collection_methods(obj)
        return obj

    def _set_collection_methods(self, obj):
        def _iter():
            for key, item in self._collection[obj.__class__.__name__][obj.key].iteritems():
                yield key, item
        obj.set_iterator(_iter)

        def _filter(start=None, end=None):
            start = start or 0
            end = end or 2147483647
            for key, item in self._collection[obj.__class__.__name__][obj.key].iteritems():
                if item.interval.start < end and item.interval.end > start:
                    yield key, item
        obj.set_iteritems_filter(_filter)


def to_key(obj):
    if isinstance(obj, type):
        return obj.__name__
    else:
        return str(obj)


def k(*args):
    return ":".join([to_key(arg) for arg in args])


class RedisDatastore(object):

    def __init__(self):
        redis_host = '127.0.0.1'
        redis_port = 6379
        redis_db = 0
        self._rds = redis.StrictRedis(host=redis_host,
                                      port=redis_port, db=redis_db)

    def _sequence(self):
        return str(self._rds.incr('sequence.agenda'))

    def put(self, obj):
        if obj.key == None:
            obj.key = self._sequence()
        rkey = k(obj.__class__, obj.key)
        payload = json.dumps(obj.to_dict())

        if issubclass(obj.__class__, ParentkeyDataobjectMixin):
            parent_rkey = k(obj.parent_class, obj.parent_key, obj.__class__)
            # Here begins appointment overlapping control
            if obj.__class__ == Appointment:
                watch_rkey = k(obj.parent_class, obj.parent_key, obj.__class__)
                pipe = self._rds.pipeline(transaction=True)
                pipe.watch(watch_rkey)
                start_rkey = watch_rkey
                end_rkey = k(watch_rkey, "end")
                start_after = self._rds.zrangebyscore(
                                start_rkey, "-Inf", "(%d" % obj.interval.end)
                end_before = self._rds.zrangebyscore(
                                end_rkey, "(%d" % obj.interval.start, "+Inf")
                overlapping = set(start_after) & set(end_before)
                if overlapping != set():
                    pipe.reset()
                    raise OverlappingIntervalWarning
                try:
                    pipe.multi()
                    pipe.zadd(parent_rkey, obj.interval.start, obj.key)
                    pipe.zadd(k(parent_rkey, "end"), obj.interval.end, obj.key)
                    pipe.execute()
                except redis.WatchError:
                    raise ConcurrencyWarning
                finally:
                    pipe.reset()
            else:
                self._rds.zadd(parent_rkey, obj.interval.start, obj.key)
                self._rds.zadd(k(parent_rkey, "end"), obj.interval.end, obj.key)

        if issubclass(obj.__class__, CollectionDataobjectMixin):
            self._set_collection_methods(obj)
        self._rds.set(rkey, payload)
        return obj

    def delete(self, cls, key):
        rkey = k(cls, key)
        obj = None
        if issubclass(cls, ParentkeyDataobjectMixin):
            obj = self.get(cls, key)
            parent_rkey = k(obj.parent_class, obj.parent_key, cls)
            self._rds.zrem(parent_rkey, key)
            self._rds.zrem(k(parent_rkey, "end"), key)
        if issubclass(cls, CollectionDataobjectMixin):
            if not obj:
                obj = self.get(cls, key)
            collection_rkey = k(cls, key, obj.collection_class)
            count = self._rds.zcard(collection_rkey)
            if count != 0:
                # FIX: raise specific exception
                raise ShiftNotEmptyError
        self._rds.delete(rkey)
        return

    def get(self, cls, key):
        rkey = k(cls, key)
        payload = self._rds.get(rkey)
        if payload == None:
            raise KeyError
        d = json.loads(payload)
        obj = cls.from_dict(d)
        obj.key = key
        if issubclass(obj.__class__, CollectionDataobjectMixin):
            self._set_collection_methods(obj)
        return obj

    def _set_collection_methods(self, obj):
        collection_rkey = k(obj.__class__, obj.key, obj.collection_class)

        def _iter():
            for res in self._rds.zrangebyscore(collection_rkey, "-inf", "+inf"):
                yield res, self.get(obj.collection_class, res)
        obj.set_iterator(_iter)

        def _filter(start=None, end=None):
            start = "-Inf" if start == None else "(%s" % start
            end = "+Inf" if end == None else "(%s" % end
            start_rkey = collection_rkey
            end_rkey = k(collection_rkey, "end")
            start_after = self._rds.zrangebyscore(start_rkey, "-Inf", end)
            end_before = self._rds.zrangebyscore(end_rkey, start, "+Inf")
            for key in set(start_after) & set(end_before):
                yield key, self.get(obj.collection_class, key)
        obj.set_iteritems_filter(_filter)


def ds():
    if not hasattr(ds, "datastore"):
        ds.datastore = Datastore()
    return ds.datastore


class AgendaController(object):

    def __init__(self, key=None, minimum_length=None):
        if key:
            self._agenda = ds().get(Agenda, key)
        else:
            self._agenda = Agenda(minimum_length)
            self._agenda = ds().put(self._agenda)

    @property
    def key(self):
        return self._agenda.key

    @property
    def minimum_length(self):
        return self._agenda.minimum_length

    @minimum_length.setter
    def minimum_length(self, value):
        self._agenda.minimum_length = value
        self._agenda = ds().put(self._agenda)

    def add_shift(self, start, end):
        shift = Shift(self.key, start, end)
        shift = ds().put(shift)
        return shift

    def del_shift(self, shift_key):
        ds().delete(Shift, shift_key)

    def get_shift(self, shift_key):
        return ds().get(Shift, shift_key)

    def get_shifts_iteritems(self, start=None, end=None):
        for key, shift in self._agenda.iteritems_filter(start, end):
            yield (key, shift)

    def get_shifts_itervalues(self, start=None, end=None):
        for _, shift in self._agenda.iteritems():
            yield shift

    def add_appointment(self, start, end):
        appo = Appointment(None, start, end)
        length = appo.interval.end - appo.interval.start
        for _, shift in self._agenda.iteritems():
            if appo.interval not in shift.interval:
                continue
            if appo.interval not in slots_in_interval(
                                length, shift.interval, self.minimum_length):
                continue
            appos_in_shift = [a.interval for (_, a) in shift.iteritems()]
            if not interval_overlaps(appo.interval, appos_in_shift):
                appo.parent_key = shift.key
                try:
                    appo = ds().put(appo)
                except (OverlappingIntervalWarning, ConcurrencyWarning):
                    appo.parent_key = None
                    continue
                return appo
        raise NotAvailableSlotError

    def del_appointment(self, appo_key):
        ds().delete(Appointment, appo_key)

    def get_appointment(self, appo_key):
        return ds().get(Appointment, appo_key)

    def get_appointments_in_shift_iteritems(self, shift_key):
        for key, appo in ds().get(Shift, shift_key).iteritems():
            yield key, appo

    def get_appointments_iteritems(self, start=None, end=None):
        for _, shift in self._agenda.iteritems_filter(start, end):
            for key, appo in shift.iteritems_filter(start, end):
                yield key, appo

    def get_appointments_itervalues(self, start=None, end=None):
        for _, shift in self._agenda.iteritems():
            for _, appo in shift.iteritems():
                yield appo

    def get_free_slots(self, start, end, length=None):
        """Return slots in shifts which does not overlaps with its
        appointments.
        """
        length = length or self.minimum_length
        interval = Interval(start, end)
        for slot in slots_in_interval(length, interval, length):
            for shift_key, shift in self.get_shifts_iteritems():
                if slot not in shift.interval:
                    continue
                overlapping_appointment = False
                for _, appo in self.get_appointments_in_shift_iteritems(shift_key):
                    if slot.overlaps(appo.interval):
                        overlapping_appointment = True
                        break
                if overlapping_appointment == False:
                    yield slot
                    break

    def destroy(self):
        for (key, shift) in list(self._agenda.iteritems()):
            for (appo_key, _) in list(shift.iteritems()):
                ds().delete(Appointment, appo_key)
            ds().delete(Shift, key)
        ds().delete(Agenda, self.key)
