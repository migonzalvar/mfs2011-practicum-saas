import datetime
import time

from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.utils.timezone import utc, get_current_timezone


import socket
import requests
import pytz

from forms import ShiftForm, AppointmentForm, QuickAppointmentForm
from server_models import (Shift, Appointment, Slot, datetime_to_dtstring,
                           DEFAULT_SLOT_LENGTH, TIMEFORMAT, FIELD_SEPARATOR)


# API helpers


def str_to_datetime(str_date, str_time):
    """Converts a local date and a time strings into datetime UTC."""
    tz = get_current_timezone()
    isostring_naive_local = str_date + "T" + str_time
    dt_naive_local = datetime.datetime.strptime(isostring_naive_local, "%Y-%m-%dT%H:%M")
    dt_aware_local = tz.localize(dt_naive_local)
    dt_aware_utc = dt_aware_local.astimezone(utc)
    return dt_aware_utc


# Actual views


def index(request):
    data_dict = dict(version=1)
    return render_to_response('agenda/index.html', data_dict,
                              context_instance=RequestContext(request))


class ResourceView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(ResourceView, self).get_context_data(**kwargs)
        context[self.resource] = list(self.Model.all())
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["form"] = self.Form()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if request.POST.get("method", "") == "delete":
            return self.pseudodelete(request, *args, **kwargs)
        form = self.Form(request.POST)
        if form.is_valid():
            d = self.prepare_form_data(form)
            resource = self.SaveModel(**d)
            resource.save()
            messages.success(request,
                             _('Resource %(id)s saved.') % {"id": resource.id})
            redirect_url = request.POST.get("redirect", reverse(self.resource))
            return redirect(redirect_url)
        else:
            messages.error(request, "Error validating data: %s" % repr(form))
            context = self.get_context_data(**kwargs)
            context["form"] = form
            return self.render_to_response(context)

    def pseudodelete(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        oid = request.POST.get("id", None)
        try:
            resource = self.Model.delete_id(oid)
        except self.Model.DoesNotExist:
            raise Http404
        messages.success(request,
                         _('Resource %(id)s deleted.') % {"id": oid})
        return redirect(reverse(self.resource))

    def prepare_form_data(self, form):
        raise NotImplemented


class ShiftView(ResourceView):
    resource = "shifts"
    Model = Shift
    Form = ShiftForm
    SaveModel = Shift
    template_name = 'agenda/shifts.html'

    def prepare_form_data(self, form):
        date = form.cleaned_data["date"]
        start = str_to_datetime(date, form.cleaned_data["start"])
        end = str_to_datetime(date, form.cleaned_data["end"])
        return {FIELD_SEPARATOR.join(("start", "datetime")): start,
                FIELD_SEPARATOR.join(("end", "datetime")): end}


class AppointmentView(ResourceView):
    resource = "appointments"
    Model = Appointment
    Form = AppointmentForm
    SaveModel = Appointment
    template_name = 'agenda/appointments.html'

    def prepare_form_data(self, form):
        date = form.cleaned_data["date"]
        start = str_to_datetime(date, form.cleaned_data["start"])
        end = str_to_datetime(date, form.cleaned_data["end"])
        return {
                FIELD_SEPARATOR.join(("start", "datetime")): start,
                FIELD_SEPARATOR.join(("end", "datetime")): end}


class SlotView(ResourceView):
    resource = "freeslots"
    Model = Slot
    Form = QuickAppointmentForm
    SaveModel = Appointment
    template_name = "agenda/slots.html"

    def get_context_data(self, **kwargs):
        context = super(ResourceView, self).get_context_data(**kwargs)
        try:
            year = int(kwargs['year'])
            month = int(kwargs['month'])
            day = int(kwargs['day'])
            basedate = datetime.date(year, month, day)
        except:
            basedate = datetime.date.today()
        prev = basedate - datetime.timedelta(days=1)
        next = basedate + datetime.timedelta(days=1)
        selectdate = [basedate + datetime.timedelta(days=i) for i in range(-1, 7)]
        start = datetime.datetime.combine(basedate, datetime.time(0))
        end = datetime.datetime.combine(basedate, datetime.time.max)
        context["basedate"] = basedate
        context["prev"] = prev
        context["next"] = next
        context["selectdate"] = selectdate
        context[self.resource] = self.Model.all(length=DEFAULT_SLOT_LENGTH,
                                                start=datetime_to_dtstring(start),
                                                end=datetime_to_dtstring(end))
        return context

    def prepare_form_data(self, form):
        start = form.cleaned_data["start_dt"].astimezone(utc)
        end = form.cleaned_data["end_dt"].astimezone(utc)
        return {
            FIELD_SEPARATOR.join(("start", "datetime")): start,
            FIELD_SEPARATOR.join(("end", "datetime")): end, }
