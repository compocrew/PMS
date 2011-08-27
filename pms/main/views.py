# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseServerError
from django.utils import simplejson
from party.decorators import require_party
from party.models import Party
from party.util import get_party

import sms.views

def index(request):
	p = {}
	parties = Party.objects.filter(active=True)
	if len(parties) == 1:
		return HttpResponseRedirect(parties[0].slug)

	p['parties'] = parties
	p['has_parties'] = len(parties) > 0
	
	return render_to_response("main.html",p,context_instance=RequestContext(request))
	
@require_party
def party_index(request):
	party = get_party(request)
	if party.maintenance:
		if not request.user.is_staff:
			return render_to_response("maintenance.html",context_instance=RequestContext(request))
	return render_to_response("main.html",context_instance=RequestContext(request))
	
	
# A view to report back on upload progress:
def upload_progress(request):
    """
    Return JSON object with information about the progress of an upload.
    """
    progress_id = None
    if 'X-Progress-ID' in request.GET:
        progress_id = request.GET['X-Progress-ID']
    elif 'X-Progress-ID' in request.META:
        progress_id = request.META['X-Progress-ID']
    if progress_id:
        from django.utils import simplejson
        cache_key = "%s_%s" % (request.META['REMOTE_ADDR'], progress_id)
        data = cache.get(cache_key)
        json = simplejson.dumps(data)
        return HttpResponse(json)
    else:
        return HttpResponseServerError('Server Error: You must provide X-Progress-ID header or query param.')
