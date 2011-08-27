# Create your views here.


from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect,HttpResponseNotFound
from django.core.urlresolvers import reverse

from models import Party,PartyForm

def index(request):
	
	if hasattr(request.session,'party'):
		del request.session['party']
	
	if request.user.has_perm("party.admin"):
		parties = Party.objects.all()
	else:
		parties = Party.objects.filter(active=True)
	
	return render_to_response("list_parties.html",{'parties' : parties},context_instance=RequestContext(request))
	
def select(request,party):
	try:
		p = Party.objects.get(slug=party)
		request.session['party']=p.id
	except Party.DoesNotExist:
		return HttpResponseNotFound()
		
	return HttpResponseRedirect("/")

	
def admin(request,party):
	try:
#		if not request.user.has_perm("party.admin"):
#			raise Party.DoesNotExist()
			
		party = Party.objects.get(slug=party)
	except Party.DoesNotExist:
		return HttpResponseNotFound()
		
	data = { 'party' : party}
	
	if request.method == "POST":
		form = PartyForm(request.POST,instance=party)
		if form.is_valid():
			form.save()
			data['success']=True
	else:
		form = PartyForm(instance=party)
	
	data['form']=form
		
	return render_to_response("party_admin.html",data,context_instance=RequestContext(request))
	