from django import forms
from django.utils.translation import ugettext_lazy as _

import datetime

from server_models import TIMEFORMAT

def date_list(days=7):
    choices = []
    for i in range(days):
        date = datetime.date.today() + datetime.timedelta(days=i)
        date_value = date.strftime("%Y-%m-%d")
        date_string = date.strftime("%d-%b")
        choices.append((date_value, date_string))
    return choices


def time_list(start=8 * 3600, end=22 * 3600, length=1800):
    choices = []
    for i in range(start, end, length):
        hour, minute, second = i / 3600, i % 3600 / 60, i % 60
        time = datetime.time(hour, minute, second)
        time_value = time_string = time.strftime("%H:%M")
        choices.append((time_value, time_string))
    return choices


class ShiftForm(forms.Form):
    date = forms.ChoiceField(date_list(), label=_("Date"))
    start = forms.ChoiceField(time_list(), label=_("From"))
    end = forms.ChoiceField(time_list(), label=_("To"))


class AppointmentForm(forms.Form):
    date = forms.ChoiceField(date_list(), label=_("Date"))
    start = forms.ChoiceField(time_list()[:-1], label=_("From"))
    end = forms.ChoiceField(time_list()[1:], label=_("To"))


class QuickAppointmentForm(forms.Form):
    start_dt = forms.DateTimeField(label=_("From"))
    end_dt = forms.DateTimeField(label=_("To"))