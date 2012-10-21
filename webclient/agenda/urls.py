from django.conf.urls import patterns, include, url

from views import ShiftView, AppointmentView, SlotView


urlpatterns = patterns('agenda.views',
    url(r'^$', 'index'),
    url(r'^shifts/$', ShiftView.as_view(), name="shifts"),
    url(r'^appointments/$', AppointmentView.as_view(), name="appointments"),
    url(r'^slots/$', SlotView.as_view(), name="freeslots"),
    url(r'^slots/(?P<year>\d{4})/(?P<month>[01]*\d)/(?P<day>[0-3]*\d)/$', SlotView.as_view(), name="freeslots"),
)
