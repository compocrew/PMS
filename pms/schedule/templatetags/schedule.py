
from pms.schedule.models import Schedule,Event

from django import template
from datetime import datetime,timedelta
from django.db.models import Q

register = template.Library()



@register.inclusion_tag("schedule_list.html",takes_context=True)
def show_schedule(context,amount,party,futureonly):
    try:
        schedule = Schedule.objects.get(party=party)
    except Schedule.DoesNotExist:
        return {}
    if futureonly:
        #filter things that have ended less than 5 minutes ago
        #or if they don't have an end, that have started less than 5 minutes
        #ago
        events = Event.objects.filter(
                Q(hidden=False) & Q(schedule=schedule.pk) & 
                    ( 
                    Q(end_time__gt=(datetime.now()-timedelta(minutes=5))) |
                    (
                        Q(end_time=None) & 
                        Q(time__gt=(datetime.now()-timedelta(minutes=5)))
                    )
                    )
                )

        return { 'request' : context['request'], 'schedule' : events.order_by("time")[:amount]}
    else:
        return {'request' : context['request'], 'schedule' : schedule.events.filter(hidden=False).order_by("time")[:amount] }


