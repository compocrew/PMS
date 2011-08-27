





from django.conf.urls.defaults import *


urlpatterns = patterns('',
	url(r'login/$','accounts.views.login_user',name="login"),
	url(r'lost_password/$','accounts.extra_views.password_reset',{'template_name' : "lost_password.html"},name="lost_password"),
	url(r'lost_password/done/$','accounts.extra_views.password_reset_done'),
	(r'lost_password/reset/(?P<uidb36>[^/]+)/(?P<token>[^/]+)$','accounts.extra_views.password_reset_confirm'),
	(r'create/$','accounts.views.create_account'),
#	url(r'login/$', 'django.contrib.auth.views.login', {'template_name' : 'login.html'},name="login"),
	(r'logout/$','accounts.views.logout_user'),
	(r'tickets/(?P<party>[^/]+)/$','accounts.views.tickets'),
	(r'view/admin/(?P<id>\d+)/$','accounts.views.admin_user_details'),
	(r'view/$','accounts.views.user_details'),
	(r'password_change/$','accounts.views.user_password_change'),
	(r'search_json/$','accounts.views.search_users_json'),
	(r'messages/',include('django_messages.urls')),
)