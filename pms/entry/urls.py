from django.conf.urls.defaults import *


urlpatterns = patterns('',
	(r'(?P<entryid>\d+)/edit/$','entry.views.admin_edit_entry'),
	(r'(?P<entryid>\d+)/upload/$','entry.views.upload_entry_version'),
	(r'(?P<entryid>\d+)/download$','entry.views.download'),
	(r'(?P<entryid>\d+)/download/admin/$','entry.views.admin_download'),
	(r'(?P<entryid>\d+)/download/admin/(?P<version>\d+)$','entry.views.admin_download_version'),

)