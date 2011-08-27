from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to

from django_messages.views import *

urlpatterns = patterns('',
    url(r'^$', redirect_to, {'url': 'inbox/'}, name='messages_redirect'),
    url(r'^inbox/$', inbox, name='messages_inbox'),
    url(r'^view/(?P<message_id>[\d]+)/$', view, name='messages_detail'),
    url(r'^delete/(?P<message_id>[\d]+)/$', delete, name='messages_delete'),
)
