from django.conf.urls.defaults import *

import settings
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	# Example:
	# (r'^pms/', include('pms.foo.urls')),


	(r'^accounts/',include('accounts.urls')),
	(r'^api/',include('api.urls')),
	(r'^(?P<party>[^/]+)/compos/',include('compo.urls')),
	(r'^(?P<party>[^/]+)/entries/',include('entry.urls')),
	(r'^(?P<party>[^/]+)/sport/',include('sports.urls')),
	(r'^(?P<party>[^/]+)/schedules/',include('schedule.urls')),
	(r'^parties/',include('party.urls')),
	(r'^news/',include('news.urls')),
	(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT,'show_indexes': False }),
	(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': settings.MEDIA_URL+'favicon.ico'}),
	# Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
	# to INSTALLED_APPS to enable admin documentation:
	# (r'^admin/doc/', include('django.contrib.admindocs.urls')),
	# Uncomment the next line to enable the admin:
	#(r'^upload_progress/$','upload_progress'),
	(r'^admin/', include(admin.site.urls)),
	(r'^$','main.views.index'),
	(r'^(?P<party>[^/]+)/$','main.views.party_index'),

)
