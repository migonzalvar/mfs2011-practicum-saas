"""HTTP REST API server. """

from collections import OrderedDict

import calendar
import datetime
import json
import time

import pytz

from bottle import Bottle, run, request, response, debug, HTTPResponse

from agenda import ds, RedisDatastore, AgendaController, ShiftNotEmptyError, NotAvailableSlotError

# Settings

AUTH = ("user", "s3cr3ts3cr3t")

DEFAULT_TZ = "Europe/Madrid"
DEFAULT_PATH = "http://localhos:8008/agendas/shifts/%s"

UTCTIMEFORMAT = "%Y-%m-%dT%H:%M:%SZ"
LOCALTIMEFORMAT = "%Y-%m-%d %H:%M:%S"


# Converters

def epoch(a_dtstring):
    tt = time.strptime(a_dtstring, UTCTIMEFORMAT)
    return int(calendar.timegm(tt))


def today(context=None):
    context = context or {}
    zone = context.get("zone", DEFAULT_TZ)
    localtz = pytz.timezone(zone)
    dt = datetime.date.today()
    dt = datetime.datetime.combine(dt, datetime.time(0))
    dt = dt.replace(tzinfo=localtz).astimezone(pytz.utc)
    return calendar.timegm(dt.timetuple())


def tomorrow(context=None):
    context = context or {}
    zone = context.get("zone", DEFAULT_TZ)
    localtz = pytz.timezone(zone)
    dt = datetime.date.today() + datetime.timedelta(days=1)
    dt = datetime.datetime.combine(dt, datetime.time(0))
    dt = dt.replace(tzinfo=localtz).astimezone(pytz.utc)
    return calendar.timegm(dt.timetuple())


def epoch2datetime(an_epoch):
    return datetime.datetime.utcfromtimestamp(an_epoch).replace(tzinfo=pytz.utc)


def filter_request(form_dict, name, to_python, default=None):
    try:
        return to_python(form_dict[name])
    except KeyError:
        return None
    except (ValueError, TypeError):
        return default


# Authentication

def require_authentication(fn):
    def new_function(*args, **kwargs):
        if request.auth == AUTH:
            return fn(*args, **kwargs)
        else:
            return render_to_error(403, "Incorrect credentials.")
    return new_function


# Helpers

def dict_to_response(items, status=200, headers=None):
    """Returns a HTTPResponse with ``items`` as a JSON.

    The parameter ``data``could be a mapping or a sequence, a container
    that supports iteration, or an iterator object. The elements of the
    argument must each also be of one of those kinds, and each must in
    turn contain exactly two objects. The first is used as a key in the
    new dictionary, and the second as the key's value.
    """
    headers = headers or {}
    payload = OrderedDict(items)
    payload["status"] = status
    output = json.dumps(payload, indent=2)
    for key, value in headers.iteritems():
        response.headers[key] = value
    response.set_header('Content-Type', 'application/json')
    headers = {'Content-Type': 'application/json',
               'Access-Control-Allow-Origin': '*', }
    return HTTPResponse(status=status, body=output, **headers)


def render_epoch(an_epoch, context=None):
    context = context or {}
    zone = context.get("zone", DEFAULT_TZ)
    localtz = pytz.timezone(zone)
    dt = epoch2datetime(an_epoch)
    return OrderedDict((
        ("datetime", dt.strftime(UTCTIMEFORMAT)),
        ("timestamp", an_epoch),
        ("localtime", dt.astimezone(localtz).strftime(LOCALTIMEFORMAT)),
        ("timezone", zone)
    ))


def render_shift(shift, context=None):
    context = context or {}
    return OrderedDict((
        ("kind", "shift"),
        ("id", shift.key),
        ("name", "Testing"),
        ("href", context.get("href", "")),
        ("start", render_epoch(shift.interval.start, context)),
        ("end", render_epoch(shift.interval.end, context))
    ))


def render_shifts(shifts, context=None):
    context = context or {}
    return OrderedDict((
        ("kind", "shifts"),
        ("shifts", [render_shift(shift, context) for shift in shifts])
    ))


def render_agenda(agenda, context=None):
    context = context or {}
    return OrderedDict((
        ("id", agenda.key),
        ("name", "Testing"),
    ))


def render_slot(slot, context=None):
    context = context or {}
    path = context.get("path", DEFAULT_PATH)
    return OrderedDict((
        ("kind", "freeslot"),
        ("href", path),
        ("start", render_epoch(slot.start, context)),
        ("end", render_epoch(slot.end, context))
    ))


def render_slots(slots, context=None):
    context = context or {}
    return OrderedDict((
        ("kind", "freeslots"),
        ("freeslots", [render_slot(slot, context) for slot in slots])
    ))


def render_appointments(appos, context=None):
    context = context or {}
    return OrderedDict((
        ("kind", "appointments"),
        ("appointments", [render_appointment(appo, context) for appo in appos])
    ))


def render_appointment(appo, context=None):
    context = context or {}
    return OrderedDict((
        ("kind", "appointment"),
        ("id", appo.key),
        ("shift_id", appo.parent_key),
        ("href", context.get("href", "")),
        ("start", render_epoch(appo.interval.start, context)),
        ("end", render_epoch(appo.interval.end, context))
    ))


def render_to_error(status, message):
    headers = {'Content-Type': 'application/json',
               'Access-Control-Allow-Origin': '*', }
    output = json.dumps({"status": status, "message": message})
    return HTTPResponse(status=status, body=output, **headers)


# Shortcuts

def get_agenda_or_404(aid):
    try:
        agenda = AgendaController(aid)
    except KeyError:
        raise render_to_error(404, "Agenda was not found.")
    return agenda


class Context(dict):

    def __init__(self, request, *args, **kwargs):
        super(Context, self).__init__(*args, **kwargs)
        self.process_request(request)

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __setattr__(self, key, value):
        return self.__setitem__(key, value)

    def process_request(self, request):
        (scheme, host, _, _, _) = request.urlparts
        self.update(url=scheme + "://" + host)




def error404(error):
    return render_to_error(error.status, "The URL is not found ")


def error500(error):
    return render_to_error(error.status, "Internal error.")


# Routes

def options():
    response.headers["Allow"] = "GET,HEAD,POST,OPTIONS,DELETE"
    return HTTPResponse(status=200, output="")


def test():
    """Test the server.

    Echoes string and integer and converts a string datetime to epoch."""
    if request.method == "GET":
        my_string = filter_request(request.query, 'string', str)
        my_integer = filter_request(request.query, 'integer', int)
        my_epoch = filter_request(request.query, 'datetime', epoch)
        return dict_to_response(dict(string=my_string, integer=my_integer, epoch=my_epoch))
    elif request.method == "POST":
        my_string = filter_request(request.forms, 'string', str)
        my_integer = filter_request(request.forms, 'integer', int)
        my_epoch = filter_request(request.forms, 'datetime', epoch)
        return dict_to_response(dict(string=my_string, integer=my_integer, epoch=my_epoch))



def test_post():
    """Test the server.

    Echoes string and integer and converts a string datetime to epoch."""

    if request.content_type == "application/x-www-form-urlencoded":
        my_string = filter_request(request.forms, 'string', str)
        my_integer = filter_request(request.forms, 'integer', int)
        my_epoch = filter_request(request.forms, 'datetime', epoch)
        d = dict(string=my_string, integer=my_integer, epoch=my_epoch)
    elif request.content_type == "application/json":
        d = request.json

    # Query
    d["query"] = filter_request(request.query, 'query', str)

    return dict_to_response(d)


@require_authentication
def get_agenda(aid):
    agenda = get_agenda_or_404(aid)
    return dict_to_response(render_agenda(agenda))


@require_authentication
def post_agenda():
    agenda = AgendaController()
    context = Context(request)
    path = "/agendas/{agenda}".format(agenda=agenda.key)
    href = context.url + path
    context["href"] = href
    headers = {"Location": href}
    return dict_to_response(render_agenda(agenda, context), 201, headers)


@require_authentication
def get_slots(aid):
    length = filter_request(request.query, "length", int)
    start_from = filter_request(request.query, "start", epoch)
    start_until = filter_request(request.query, "end", epoch)
    agenda = get_agenda_or_404(aid)
    intervals = agenda.get_slots(length, start_from, start_until)
    return dict_to_response(render_slots(intervals))


@require_authentication
def get_free_slots(aid):
    length = filter_request(request.query, "length", int)
    start = filter_request(request.query, "start", epoch) or today()
    end = filter_request(request.query, "end", epoch) or tomorrow()
    agenda = get_agenda_or_404(aid)
    intervals = agenda.get_free_slots(start, end, length)
    return dict_to_response(render_slots(intervals))


@require_authentication
def get_appointment(aid, app_id):
    agenda = get_agenda_or_404(aid)
    appo = agenda.get_appointment(app_id)
    return dict_to_response(render_appointment(appo))


@require_authentication
def get_appointments(aid):
    agenda = get_agenda_or_404(aid)
    appos = agenda.get_appointments_itervalues()
    return dict_to_response(render_appointments(appos))


@require_authentication
def delete_appointment(aid, app_id):
    agenda = get_agenda_or_404(aid)
    try:
        agenda.del_appointment(app_id)
    except KeyError:
        return render_to_error(404, "Appointment was not found.")
    return dict_to_response((), 204)


@require_authentication
def get_shifts(aid):
    agenda = get_agenda_or_404(aid)
    shifts = agenda.get_shifts_itervalues()
    return dict_to_response(render_shifts(shifts))


@require_authentication
def get_shift(aid, sid):
    agenda = get_agenda_or_404(aid)
    shift = agenda.get_shift(sid)
    return dict_to_response(render_shift(shift))


@require_authentication
def post_shift(aid):
    start = filter_request(request.forms, "start", epoch)
    end = filter_request(request.forms, "end", epoch)
    if start == None or end == None:
        return render_to_error(403, "Incorrect parameter value.")
    agenda = get_agenda_or_404(aid)
    shift = agenda.add_shift(start, end)
    context = Context(request)
    path = "/agendas/{aid}/shifts/{sid}".format(aid=aid, sid=shift.key)
    href = context.url + path
    context["href"] = href
    headers = {"Location": href}
    return dict_to_response(render_shift(shift, context), 201, headers)


@require_authentication
def delete_shift(aid, sid):
    agenda = get_agenda_or_404(aid)
    try:
        _ = agenda.del_shift(sid)
    except KeyError:
        return render_to_error(404, "Shift %s was not found." % sid)
    except ShiftNotEmptyError:
        return render_to_error(409, "Shift %s is not empty. Please, first delete all appointments." % sid)
    return dict_to_response((), 204)


@require_authentication
def post_appointment(aid):
    start = filter_request(request.forms, "start", epoch)
    end = filter_request(request.forms, "end", epoch)
    if start == None or end == None:
        return render_to_error(400, "Incorrect parameter value.")
    agenda = get_agenda_or_404(aid)
    try:
        appo = agenda.add_appointment(start, end)
    except NotAvailableSlotError:
        return render_to_error(409, "Appointment overlaps. Please, choose another slot.")
    context = Context(request)
    path = "/agendas/{agenda}/shifts/{shift}/appointments/{appo}".format(
        agenda=aid, shift=appo.parent_key, appo=appo.key)
    href = context.url + path
    context["href"] = href
    headers = {"Location": href}
    return dict_to_response(render_appointment(appo, context), 201, headers)


def setup_routing(app):
    app.route('/test', ['GET', ], test)
    app.route('/test', ['POST', ], test_post)

    app.route("/*", "OPTIONS", options)

    app.route('/agendas/<aid:int>', "GET" , get_agenda)
    app.route('/agendas', "POST", post_agenda)

    app.route('/agendas/<aid:int>/shifts', "GET", get_shifts)
    app.route('/agendas/<aid:int>/shifts/<sid:int>', "GET", get_shift)
    app.route('/agendas/<aid:int>/shifts', "POST", post_shift)
    app.route('/agendas/<aid:int>/shifts/<sid:int>', "DELETE", delete_shift)

    app.route('/agendas/<aid:int>/appointments/<app_id:int>', "GET", get_appointment)
    app.route('/agendas/<aid:int>/appointments', "GET", get_appointments)
    app.route('/agendas/<aid:int>/appointments/<app_id:int>', "DELETE", delete_appointment)
    app.route('/agendas/<aid:int>/appointments', "POST", post_appointment)

    app.route('/agendas/<aid:int>/slots', "GET", get_slots)
    app.route('/agendas/<aid:int>/freeslots', "GET", get_free_slots)


def setup_error_handling(app):
    app.error_handler[404] = error404
    app.error_handler[500] = error500


# Main
debug(True)

setattr(ds, 'datastore', RedisDatastore())

app = Bottle()
setup_routing(app)
setup_error_handling(app)




if __name__ == '__main__':
    run(app, host='localhost', port=8008, reloader=True)
