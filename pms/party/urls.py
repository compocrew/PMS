from django.conf.urls.defaults import *


urlpatterns = patterns('',
	(r'(?P<party>[^/]+)/edit/$','party.views.admin'),

	(r'(?P<party>[^/]+)/$','party.views.select'),

	(r'$','party.views.index'),

)