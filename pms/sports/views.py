from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect,HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render_to_response,get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.core.urlresolvers import reverse
from models import *
from forms import SportsAdminForm,SportsParticipateForm,SeedType,SeedForm
from party.decorators import require_party
from party.util import get_party
from django.views.decorators.cache import never_cache

@require_party
def index(request):
	party = get_party(request)
	
	categories = SportsCategory.objects.filter(party=party).order_by("index")

	show_hidden = request.user.has_perm("sports.admin")
	for cat in categories:
		if show_hidden:
			sports = Sports.objects.filter(party=party,category=cat)
		else:
			sports = Sports.objects.filter(party=party,category=cat,hidden=False)
			
		if sports.count() > 0:
			cat.sports = sports
		else:
			cat.sports = None
	
	data = {'categories' : categories}
	
	return render_to_response("sports_index.html",data,context_instance=RequestContext(request))
	

@require_party
def results(request,slug):
	party = get_party(request)
	sport = get_object_or_404(Sports,slug=slug)
	
	if (sport.finished and sport.has_results()) or request.user.has_perm("sports.admin"):
#		return HttpResponse("")
		pass
	
	return HttpResponseNotFound()
	

@require_party
@never_cache
@permission_required('sports.admin')
def sport_admin(request,slug):
	party = get_party(request)
	
	sport = get_object_or_404(Sports,slug=slug)
	
	try: 
		seed = SportsSeeding.objects.get(sport=sport)
	except SportsSeeding.DoesNotExist:
		seed = None
		
	participants = SportsParticipant.objects.filter(sport=sport).order_by("-pre_score")
	
	if request.method == "POST":
		form = SportsAdminForm(request.POST,instance=sport)
		if form.is_valid():
			form.save()
			messages.add_message(request,messages.SUCCESS,"Compo info updated.")
	else:
		form = SportsAdminForm(instance=sport)

	seedform = SeedForm()

	return render_to_response("sports_admin.html",{'form' : form,'sport' : sport,'participants' : participants,'seed' : seed,'seedform' : seedform },context_instance=RequestContext(request))
	
	
@require_party
@login_required
def participate(request,slug):
	party = get_party(request)
	sport = get_object_or_404(Sports,slug=slug)

	try:
		existing = SportsParticipant.objects.get(sport=sport,user=request.user)
	except SportsParticipant.DoesNotExist:
		existing = None
		
	if request.method == "POST":
		if existing:
			form = SportsParticipateForm(sport,request.POST,request.FILES,instance=existing)
		else:
			form = SportsParticipateForm(sport,request.POST,request.FILES)

		if form.is_valid():
			part = form.save(commit=False)
			part.user = request.user
			part.sport = sport
			part.save()
			messages.add_message(request,messages.SUCCESS,"Your participation was accepted.")
			return HttpResponseRedirect(reverse('sports.views.index',args=[party.slug]))
			
	else:
		form = SportsParticipateForm(sport)
	
	return render_to_response("sports_participate.html",{'form' : form, 'sport' : sport},context_instance=RequestContext(request))
	
@require_party
@permission_required('sports.admin')
def update_prescore(request,slug):
	party = get_party(request)
	sport = get_object_or_404(Sports,slug=slug)


@require_party
@permission_required('sports.admin')
def seed(request,slug):
	party = get_party(request)
	sport = get_object_or_404(Sports,slug=slug)

	if request.method == "POST":
		form = SeedForm(request.POST)
		if form.is_valid():
			seedtype = form.cleaned_data['seedtype']
			num = form.cleaned_data['num']
			minscore = form.cleaned_data['minscore']
			
			participants = sport.get_participants()
			if num > len(participants):
				num = len(participants)
			
			if num == 0:
				messages.add_message(request,messages.ERROR,"Cannot seed. No participants")
				return HttpResponseRedirect(reverse('sports.views.sport_admin',args=[party.slug,sport.slug]))

			try:
				seed = SportsSeeding.objects.get(sport=sport)
			except SportsSeeding.DoesNotExist:
				seed = SportsSeeding(sport=sport)
			
			seed.max_participants = num
			seed.save()

			seed.seed(seedtype == SeedType.Random,minscore)
			seed.save()
			
			messages.add_message(request,messages.SUCCESS,"Seeding done.")
		else:
			messages.add_message(request,messages.ERROR,"Error in seedform")
	
	return HttpResponseRedirect(reverse('sports.views.sport_admin',args=[party.slug,sport.slug]))

	
	

