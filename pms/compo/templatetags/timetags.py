from django import template
from datetime import datetime,timedelta

register = template.Library()

def timeformat(value):
	now = datetime.now()
	if not value:
		return u""
	delta = value - now
	
	current_date = delta.days == 0
	
	if not current_date:
		if delta.days > 6:
			return value.strftime("at %A, %B %d, %H:%M").lower()
		return value.strftime("at %A %H:%M").lower()
	else:
		if delta.seconds < 60*60:
			if delta.seconds < 60:
				return "<1 minute"
			return u"in %d minutes" % (int(delta.seconds)/60+1)
		else:
			return u"at "+value.strftime("%H:%M")
		
register.filter("timeformat",timeformat)

