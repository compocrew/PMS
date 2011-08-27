
from django.conf.urls.defaults import *


urlpatterns = patterns('',
	(r'(?P<slug>[^/]+)/participate/$','sports.views.participate'),
	(r'(?P<slug>[^/]+)/results/$','sports.views.results'),
	(r'(?P<slug>[^/]+)/admin/$','sports.views.sport_admin'),
	(r'(?P<slug>[^/]+)/admin/update_prescore/$','sports.views.update_prescore'),
	(r'(?P<slug>[^/]+)/admin/seed/$','sports.views.seed'),

	(r'$','sports.views.index'),
)
