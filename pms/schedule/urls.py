from django.conf.urls.defaults import *
from schedule.views import create,admin,schedule

urlpatterns = patterns('',
	(r'admin/(?P<event>\d+)$',admin, None, 'schedule-admin'),
	(r'delete/(?P<event>\d+)$','schedule.views.delete'),
	(r'create/$', "schedule.views.create"),
	(r'changelog/$', "schedule.views.changelog"),
	(r'$',schedule, None, 'schedule-show'),
)
