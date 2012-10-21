import base64

from webtest import TestApp
import server
from agenda import ds, RedisDatastore, AgendaController

USER = "user"
PASS = "s3cr3ts3cr3t"

def auth(user=USER, password=PASS):
    return "Basic " + base64.b64encode("%s:%s" % (user, password))


def before_all(context):
    context.client = TestApp(server.app,
                             extra_environ=dict(HTTP_AUTHORIZATION=auth())
                             )
    setattr(ds, 'datastore', RedisDatastore())

def before_scenario(context, scenario):
    agenda = AgendaController()
    context.agenda_id = str(agenda.key)

def after_scenario(context, scenario):
    agenda = AgendaController(int(context.agenda_id))
    agenda.destroy()

