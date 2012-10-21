import datetime
import re

from behave import then, given, when


UTCTIMEFORMAT = "%Y-%m-%dT%H:%M:%SZ"
#
# Helper functions
#

def parse_date(expression):
    if expression == "today":
        return datetime.date.today()
    elif expression == "tomorrow":
        return datetime.date.today() + datetime.timedelta(days=1)
    else:
        raise ValueError

def parse_time(expression):
    res = re.match(r"(\d+):(\d+)", expression)
    hour, minute = (int(i) for i in res.groups())
    return datetime.time(hour=hour, minute=minute)

def datetime_to_dtstring(dt):
    """Converts a datetime into a string."""
    return dt.strftime(UTCTIMEFORMAT)


#
# Steps
#

@then("I succeed")
def succeed(context):
    status = context.response.status == '200 OK'
    assert status, 'Status is not 200, is {status}\nResponse:{response}'.format(
            status=status, response=context.response)

@then("I succeed with {code}")
def succeed_with_code(context, code):
    status_code = context.response.status[0:3]
    assert status_code == code, 'Status is not {code}, is {status_code}\nResponse:{response}'.format(
            code=code, status_code=status_code, response=context.response)

@then("I fail")
def fail(context):
    status = context.response.status[0] == '4'
    assert status, 'Status is not 4xx, is {status}\n{response}'.format(
            status=status, response=context.response)

@given("I have a shift {date} from {start} to {end}")
def given_shift(context, date, start, end):
    context.execute_steps(u'''
        When I create a shift on {date} from {start} to {end}
        '''.format(date=date, start=start, end=end))


@when("I get agenda")
def get_agenda(context):
    context.response = context.client.get('/agendas/' + context.agenda_id)


@then("I see {key} is {value}")
def see_key_value(context, key, value):
    resp = context.response.json
    assert key in resp, ("Not found {key} in response".format(key=key))
    assert resp[key] == value, ("{resp} is not '{value}'". format(resp=resp[key],
                                                                  value=value))

@when(u'I make an appointment {date} at {start}')
def make_appointment(context, date, start):
    start_dt = datetime.datetime.combine(parse_date(date), parse_time(start))
    end_dt = start_dt + datetime.timedelta(minutes=30)
    start, end = datetime_to_dtstring(start_dt), datetime_to_dtstring(end_dt)
    params = {'start': start, 'end': end}
    context.response = context.client.post('/agendas/' + context.agenda_id + '/appointments', params, status="*")

@when(u'I create a shift on {date} from {start} to {end}')
def create_shift(context, date, start, end):
    start_dt = datetime.datetime.combine(parse_date(date), parse_time(start))
    end_dt = datetime.datetime.combine(parse_date(date), parse_time(end))
    start, end = datetime_to_dtstring(start_dt), datetime_to_dtstring(end_dt)
    params = {'start': start, 'end': end}
    context.response = context.client.post('/agendas/' + context.agenda_id + '/shifts', params)

@given(u'I have these shifts')
def given_shifts(context):
    for shift in context.table:
        d = dict(shift.items())
        context.execute_steps(u"""
            When I create a shift on {date} from {start} to {end}
        """.format(**d))

