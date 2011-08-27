from django.conf.urls.defaults import *
from piston.authentication import HttpBasicAuthentication
from piston.resource import Resource
from handlers import *
auth = HttpBasicAuthentication(realm="PMS")
ad = {'authentication' : auth}

partyhandler = Resource(handler=PartyHandler,**ad)
compohandler = Resource(handler=CompoHandler,**ad)
entryhandler = Resource(handler=EntryHandler,**ad)
schedulehandler = Resource(handler=ScheduleHandler,**ad)

urlpatterns = patterns('',

	(r'parties/$',partyhandler),
	(r'party/(?P<slug>[^/]+)/compos/$',compohandler),
	(r'party/(?P<slug>[^/]+)/schedule/$',schedulehandler),
	(r'party/(?P<partyslug>[^/]+)/compo/(?P<slug>[^/]+)/entries/$',entryhandler),
	(r'party/(?P<partyslug>[^/]+)/compo/(?P<slug>[^/]+)/entry/(?P<id>\d+)/$',entryhandler),
	

)