from django.conf.urls.defaults import *


urlpatterns = patterns('',
	(r'(?P<compo>[^/]+)/participate/$','compo.views.participate'),
	(r'(?P<compo>[^/]+)/vote/$','compo.views.vote'),
	(r'(?P<compo>[^/]+)/results/$','compo.views.results'),
	(r'(?P<compo>[^/]+)/admin_results/$','compo.views.admin_results'),
	(r'(?P<compo>[^/]+)/admin/$','compo.views.admin'),
	(r'(?P<compo>[^/]+)/admin/playlist/edit$','compo.views.admin_edit_playlist'),
	(r'(?P<compo>[^/]+)/admin/edit_jury/$','compo.views.admin_edit_jury'),
	url(r'(?P<compo>[^/]+)/admin/jury/add_member/$','compo.jury_views.add_jury_member',name="compo_jury_add_member"),
	url(r'(?P<compo>[^/]+)/admin/jury/reorder_entries/$','compo.jury_views.reorder_entries',name="compo_jury_reorder_entries"),
	url(r'(?P<compo>[^/]+)/admin/jury/reorder_members/$','compo.jury_views.reorder_jury_members',name="compo_jury_reorder_members"),
	url(r'(?P<compo>[^/]+)/admin/jury/delete_member/(?P<id>\d+)$','compo.jury_views.delete_jury_member',name="compo_jury_delete_member"),
	url(r'(?P<compo>[^/]+)/admin/jury/update/$','compo.jury_views.update_jury_score',name="compo_jury_update_score"),
	url(r'(?P<compo>[^/]+)/admin/jury/$','compo.jury_views.index',name="compo_jury"),
	(r'(?P<compo>[^/]+)/admin/export_list/$','compo.views.admin_export_list'),
	(r'(?P<compo>[^/]+)/admin/export/xml/$','compo.views.admin_export_xml'),
	(r'(?P<compo>[^/]+)/admin/export/xsl/$','compo.views.admin_export_xsl'),
	(r'(?P<compo>[^/]+)/admin/download/','compo.views.admin_download_entries'),
	(r'admin/export/$','compo.views.admin_export_all_compos'),
	(r'admin/create/$','compo.views.admin_create_compo'),
	(r'admin/adminresults/$','compo.views.admin_all_results'),
	(r'$','compo.views.index'),

)