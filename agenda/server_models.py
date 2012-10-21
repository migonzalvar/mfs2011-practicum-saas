import datetime

import requests
import hammock

from pytz import utc


# Server settings 

SERVER = 'http://127.0.0.1:8008'
AGENDA = '2341'
AUTH = ("user", "s3cr3ts3cr3t")

DEFAULT_SLOT_LENGTH = 1800
TIMEFORMAT = "%Y-%m-%dT%H:%M:%SZ"
FIELD_SEPARATOR = "_"


# Conversion utilities

def dtstring_to_datetime(dtstring):
    return datetime.datetime.strptime(dtstring, TIMEFORMAT).replace(tzinfo=utc)


def datetime_to_dtstring(dt):
    """Converts a datetime into a string."""
    return dt.strftime(TIMEFORMAT)


# Exceptions

class ObjectDoesNotExist(Exception):
    """The requested object does not exist"""
    pass

class GenericError(Exception):
    """Error on an operation."""
    pass

# Classes

class IResource(object):
    """A REST Resource base class interface."""
    _resource = "resources"
    _fields_definition = ((('field1',), int, str),
                          (('field2',), int, str))
    _base_request = hammock.Hammock(SERVER).agendas(AGENDA).resources

    class DoesNotExist(ObjectDoesNotExist):
        """The requested object does not exist"""
        pass

    @classmethod
    def response_to_dict(cls, resp_json):
        """Parses JSON response and creates a dictionary suitable to create
        a new resource object.
        """
        data = {}
        for name, conv, _ in cls._fields_definition:
            key = FIELD_SEPARATOR.join(name)
            value = resp_json
            for attr in name:
                value = value[attr]
            data[key] = conv(value)
        return dict(**data)

    @classmethod
    def new(cls, id=None, **kwargs):
        """Creates a new resource. If id is specified, forces id of newly
        created resource. Optionally, other fields could be initialized
        using **kwargs.
        """
        resource = cls(**kwargs)
        if id:
            resource.id = id
        return resource

    @classmethod
    def get(cls, id):
        """Get a a resource from the server and returns an object."""
        resp = cls._base_request(id).GET(auth=AUTH)
        if not resp.json:
            raise cls.DoesNotExist()
        d = cls.response_to_dict(resp.json)
        id = resp.json["id"]
        resource = cls.new(id, **d)
        return resource

    @classmethod
    def delete_id(cls, id):
        """Deletes a resource from the server."""
        resp = cls._base_request(id).DELETE(auth=AUTH)
        return None

    @classmethod
    def all(cls, **params):
        """Returns a generator with all the resources."""
        resp = cls._base_request.GET(auth=AUTH, params=params)
        for resource_json in resp.json[cls._resource]:
            d = cls.response_to_dict(resource_json)
            resource = cls(**d)
            try:
                resource.id = resource_json["id"]
            except KeyError:
                # Allow anonymous resources
                pass
            yield resource

    def __init__(self, **kwargs):
        self.id = None
        for key, value in kwargs.iteritems():
            if key in [FIELD_SEPARATOR.join(names) for names, _, _ in self._fields_definition]:
                self.__setattr__(key, value)
            else:
                msg = "'%s' is not a field name" % key
                raise KeyError(msg)

    def save(self):
        if self.id == None:
            resp = self._base_request.POST(auth=AUTH, data=self._data())
            if resp.status_code == 201:
                self.id = resp.json["id"]
            else:
                raise GenericError("Error while trying to save model. %s" % resp.json)
        else:
            raise NotImplemented("Resource '%s' update not implemented yet" %
                                 self._resource)

    def delete(self):
        if self.id == None:
            raise self.__class__.DoesNotExist()
        else:
            resp = self._base_request(self.id).DELETE(auth=AUTH)
            self.id = None

    def _data(self):
        data = {}
        for name, _, conv in self._fields_definition:
            key = FIELD_SEPARATOR.join(name)
            value = self.__getattribute__(key)
            converted = data[name[0]] = conv(value)
        data.update(auth=AUTH)
        return data


class Appointment(IResource):
    _resource = "appointments"
    _base_request = hammock.Hammock(SERVER).agendas(AGENDA).appointments
    _fields_definition = ((('start', 'datetime'), dtstring_to_datetime, datetime_to_dtstring),
                          (('end', 'datetime'), dtstring_to_datetime, datetime_to_dtstring),)


class Shift(IResource):
    _resource = "shifts"
    _base_request = hammock.Hammock(SERVER).agendas(AGENDA).shifts
    _fields_definition = ((('start', 'datetime'), dtstring_to_datetime, datetime_to_dtstring),
                          (('end', 'datetime'), dtstring_to_datetime, datetime_to_dtstring),)


class Slot(IResource):
    _resource = "freeslots"
    _base_request = hammock.Hammock(SERVER).agendas(AGENDA).freeslots
    _fields_definition = ((('start', 'datetime'), dtstring_to_datetime, datetime_to_dtstring),
                          (('end', 'datetime'), dtstring_to_datetime, datetime_to_dtstring),)

