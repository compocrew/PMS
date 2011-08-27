# Create your views here.

from django.shortcuts import render_to_response
from django.template import RequestContext
from pms.party.models import Party
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, permission_required
from party.decorators import require_party
from party.util import get_party
from schedule.models import Schedule,Event,EventForm,EventHistory
from django.http import HttpResponse,HttpResponseNotFound
from django.db.models import Q
from datetime import datetime,timedelta


@require_party
def schedule(request,futureonly=True):
    """simple view. futureonly=True shows only things that are in the future
    or don't have an end time and started less than 5 minutes ago."""
    party = Party.objects.get(slug=request.party)
    try:
        schedule = Schedule.objects.get(party=party)
    except Schedule.DoesNotExist:
        return {}
    if futureonly:
        #filter things that have ended less than 5 minutes ago
        #or if they don't have an end, that have started less than 5 minutes
        #ago
        events = Event.objects.filter(Q(schedule=schedule),
                    (
                    Q(end_time__gt=(datetime.now()-timedelta(minutes=5))) |
                    (
                        Q(end_time=None) &
                        Q(time__gt=(datetime.now()-timedelta(minutes=5)))
                    )
                    )
                )
    else:
        events = Event.objects.filter(schedule=schedule).order_by("time")
    return render_to_response('schedule_index.html',
                            {'party':party,'events':events}
                            ,context_instance=RequestContext(request))

@require_party
@permission_required('schedule.admin')
def admin(request, event,success=False,status=None):
    """
    Basic handling of event objects-
    """
    try:
        event = Event.objects.get(pk=event)
    except Event.DoesNotExist:
        return HttpResponseNotFound
    if request.method == 'POST' and not success:
        form = EventForm(request.POST,instance=event)
        if form.is_valid():
            form.save()
            success=True
            status='Event updated'
    else:
        form = EventForm(instance=event)

    return render_to_response("events_adminform.html",{'form':form,'success':success,'event' :event, 'status':status},context_instance=RequestContext(request))

@require_party
@permission_required('schedule.admin')
def create(request):
    success = False
    try:
        if request.method == 'POST':
            form = EventForm(request.POST)
            if form.is_valid():
                try:
#                    party = Party.objects.get(slug=request.party)
#                    schedule = Schedule.objects.get(party=party)
                    event = form.save(commit=False)
                    party = Party.objects.get(slug=request.party)
                    event.save()
                   # schedule.events.add(event)
                except Exception as e:
                    print e
                success = True
                return admin(request, event.pk, True, 'Event created',
                party=request.party)
        
        else:
            form = EventForm()

        return render_to_response("events_createform.html",{'form':form,
        'success':success},context_instance=RequestContext(request))
    except Exception as e:
        pass
    party = Party.objects.get(slug=party)
    return render_to_response('schedule_index.html', {'party':party},context_instance=RequestContext(request))

@require_party
@permission_required('schedule.admin')
def delete(request, event=0):
    try:
        event = Event.objects.get(id=event)
    except Event.DoesNotExist:
        return HttpResponseNotFound()

    event.delete()
    return HttpResponse("Event has been terminated with extreme prejudice.")

@require_party
@permission_required('schedule.admin')
def changelog(request):
    """
    Show changes from EventHistory. This is going to be a huge list. 
    Worry about pagination later.
    """
    try:
        party = Party.objects.get(slug=request.party)
        schedule = Schedule.objects.get(party=party)
    except Party.DoesNotExist:
        return HttpResponseNotFound()
    except Schedule.DoesNotExist:
        return HttpResponseNotFound()

    histories = EventHistory.objects.filter(schedule=schedule).order_by('-time')

    return render_to_response(
        "schedule_changelog.html",
        {'histories': histories},
        context_instance=RequestContext(request)
        )

