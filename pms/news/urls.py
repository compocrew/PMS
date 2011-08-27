from django.conf.urls.defaults import *


urlpatterns = patterns('',
	(r'admin/(?P<article>\d+)$','news.views.admin'),
	(r'delete/(?P<article>\d+)$','news.views.delete'),
	(r'create/$','news.views.create'),
	(r'$','news.views.news'),

)