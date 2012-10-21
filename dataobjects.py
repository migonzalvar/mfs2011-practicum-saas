from interval import Interval


class IBaseDataobject(object):
    _fields = []

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def to_dict(self):
        d = {}
        for field in self._fields:
            d[field] = getattr(self, field)
        return d

    def __init__(self, *args, **kwargs):
        self._key = None

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value


class IntervalDataobjectMixin(IBaseDataobject):

    def __init__(self, start, end, *args, **kwargs):
        super(IntervalDataobjectMixin, self).__init__(*args, **kwargs)
        #self._fields.append("_interval")
        self._interval = Interval(start, end)

    @property
    def interval(self):
        return self._interval

    def to_dict(self):
        d = super(IntervalDataobjectMixin, self).to_dict()
        d["start"] = self._interval.start
        d["end"] = self._interval.end
        return d


class CollectionDataobjectMixin(IBaseDataobject):

    _collection_class = None

    def __init__(self, *args, **kwargs):
        super(CollectionDataobjectMixin, self).__init__(*args, **kwargs)
        self._collection = {}

        def iteritems():
            for item in self._collection.iteritems():
                yield item
        self.iteritems = iteritems

        def iteritems_filter(start=None, end=None):
            for item in self._collection.iteritems():
                if item in range(start, end):
                    yield item
        self.iteritems_filter = iteritems_filter

    @property
    def collection_class(self):
        return self._collection_class

    def set_iterator(self, callback):
        self.iteritems = callback

    def set_iteritems_filter(self, callback):
        self.iteritems_filter = callback


class ParentkeyDataobjectMixin(IBaseDataobject):

    _parent_class = None

    def __init__(self, parent_key, *args, **kwargs):
        super(ParentkeyDataobjectMixin, self).__init__(*args, **kwargs)
        self._parent_key = parent_key

    @property
    def parent_class(self):
        return self._parent_class

    @property
    def parent_key(self):
        return self._parent_key

    @parent_key.setter
    def parent_key(self, value):
        self._parent_key = value

    def to_dict(self):
        d = super(ParentkeyDataobjectMixin, self).to_dict()
        d["parent_key"] = self.parent_key
        return d


class Appointment(ParentkeyDataobjectMixin, IntervalDataobjectMixin,
                  IBaseDataobject):

    def __init__(self, *args, **kwargs):
        super(Appointment, self).__init__(*args, **kwargs)


class Shift(ParentkeyDataobjectMixin, IntervalDataobjectMixin,
            CollectionDataobjectMixin, IBaseDataobject):
    _collection_class = Appointment

    def __init__(self, *args, **kwargs):
        super(Shift, self).__init__(*args, **kwargs)


class Agenda(CollectionDataobjectMixin, IBaseDataobject):
    _fields = ["minimum_length", ]
    _collection_class = Shift

    def __init__(self, minimum_length=None, *args, **kwargs):
        super(Agenda, self).__init__(*args, **kwargs)
        self._minimun_length = minimum_length or 1

    @property
    def minimum_length(self):
        return self._minimun_length

    @minimum_length.setter
    def minimum_length(self, value):
        self._minimun_length = value


Shift._parent_class = Agenda
Appointment._parent_class = Shift
Shift._collection_class = Appointment
Agenda._collection_class = Shift
