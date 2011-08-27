# Create your views here.
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect,HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
import django.core.files
from entry.models import Entry,EntryVersion,QUALSTATUS,entry_submitted,Qualification
from entry.forms import EntryForm,EntryVersionForm,EntryPlaylistForm

from party.decorators import require_party
from party.util import get_party
from filetransfers.api import serve_file
from accounts.decorators import ticket_required

from compo.models import Competition,Category,CompoAdminForm,VotePoints,JuryMember,JuryPoints
from compo.forms import *
from datetime import datetime
from django.forms.models import modelformset_factory


def get_jury_context(compo):
	entries = compo.get_entries().filter(hidden=False).order_by("id")
	
	members = JuryMember.objects.filter(compo=compo).order_by("index")
	jury_order = compo.jury_order
	if jury_order:
		order = jury_order.split(',')
		try:
			for n in order:
				i = int(n)
		except ValueError:
			order = [str(e.id) for e in entries]
			
	else:
		order = [str(e.id) for e in entries]

	print order

	jury_points = {}
	entrylookup = {}
	for e in entries:
		entrylookup[str(e.id)]=e
		
		for p in JuryPoints.objects.filter(entry=e.id):
			key = "points_%d_entry_%d" % (p.member.id,e.id)
			jury_points[key]=p.points or ""
		
	juryentries = []
	for o in order:
		if o in entrylookup:
			juryentries.append(entrylookup[o])
		else:
			print o,"not in entrylookup"
			
	data = {}

	data['entries']=juryentries
	data['members']=members
	data['choices']=QUALSTATUS
	data['compo']=compo
	data['num_entries']=len(entries)
	data['jurymemberform']=JuryMemberForm()
	data['jury_points']=jury_points
	return data


@require_party
@login_required
def index(request,compo):
	if not request.user.has_perm("compo.admin"):
		return HttpResponseNotFound()

	party = get_party(request)
	try:
		try:
			compo = Competition.objects.get(slug=compo,party=party)
		except Competition.DoesNotExist:
			raise InvalidCompetition()

	except InvalidCompetition:
		messages.add_message(request,messages.ERROR,"Invalid competition")
		return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))

	data = get_jury_context(compo)
	
	return render_to_response("jury/index.html",data,context_instance=RequestContext(request))


@require_party
@login_required
def update_jury_score(request,compo):
	if not request.user.has_perm("compo.admin"):
		return HttpResponseNotFound()

	party = get_party(request)
	try:
		try:
			compo = Competition.objects.get(slug=compo,party=party)
		except Competition.DoesNotExist:
			raise InvalidCompetition()

	except InvalidCompetition:
		messages.add_message(request,messages.ERROR,"Invalid competition")
		return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))
	
	if request.method == "POST":
		entries = compo.get_entries().filter(hidden=False).order_by("id")
		members = JuryMember.objects.filter(compo=compo).order_by("index")
		jury_order = compo.jury_order
		if not jury_order:
			order = [e.id for e in entries]
		else:
			order = jury_order.split(',')

		jury_points_class = {}
		for e in entries:
			for m in members:
				key = "points_%d_entry_%d" % (m.id,e.id)
				points = request.POST.get(key,None)
				try:
					point = JuryPoints.objects.get(member=m,entry=e)
				except JuryPoints.DoesNotExist:
					point = JuryPoints(member=m,entry=e)
#				print key,points
				
				if points and points != "":
					try:
						point.points = int(points)
					except ValueError:
						jury_points_class[key]="error"
						point.points = None
				else:
					point.points = None
					
				point.save()
			
		compo.calculate_jury_scores()
		data = get_jury_context(compo)
		data['jury_points_class']=jury_points_class
#		return render_to_response("jury/jury_points_table.html",data,context_instance=RequestContext(request))
		
		messages.add_message(request,messages.SUCCESS,"Jury scores updated")
	
	return HttpResponseRedirect(reverse('compo_jury',args=[party.slug,compo.slug]))

@require_party
@login_required
def add_jury_member(request,compo):
	if not request.user.has_perm("compo.admin"):
		return HttpResponseNotFound()

	party = get_party(request)
	try:
		try:
			compo = Competition.objects.get(slug=compo,party=party)
		except Competition.DoesNotExist:
			raise InvalidCompetition()

	except InvalidCompetition:
		messages.add_message(request,messages.ERROR,"Invalid competition")
		return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))
	
	if request.method == "POST":
		form = JuryMemberForm(request.POST)
		if form.is_valid():
			member = form.save(commit=False)
			member.compo = compo
			member.index = JuryMember.objects.filter(compo=compo).count()
			member.save()
			messages.add_message(request,messages.SUCCESS,"Jury member '%s' added" % member.get_name())
		else:
			messages.add_message(request.messages.ERROR,"Adding jury member failed")
			
	return HttpResponseRedirect(reverse('compo_jury',args=[party.slug,compo.slug]))
	
@require_party
@login_required
def delete_jury_member(request,compo,id):
	if not request.user.has_perm("compo.admin"):
		return HttpResponseNotFound()

	party = get_party(request)
	try:
		try:
			compo = Competition.objects.get(slug=compo,party=party)
		except Competition.DoesNotExist:
			raise InvalidCompetition()

	except InvalidCompetition:
		messages.add_message(request,messages.ERROR,"Invalid competition")
		return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))

	try:
		member = JuryMember.objects.get(id=id)
		
		JuryPoints.objects.filter(member=member).delete()	
		member.delete()
		compo.calculate_jury_scores()
		
		messages.add_message(request,messages.SUCCESS,"jury member deleted")
	except JuryMember.DoesNotExist:
		pass
		
	return HttpResponseRedirect(reverse('compo_jury',args=[party.slug,compo.slug]))

@require_party
@login_required
def reorder_jury_members(request,compo):
	if not request.user.has_perm("compo.admin"):
		return HttpResponseNotFound()

	party = get_party(request)
	try:
		try:
			compo = Competition.objects.get(slug=compo,party=party)
		except Competition.DoesNotExist:
			raise InvalidCompetition()

	except InvalidCompetition:
		messages.add_message(request,messages.ERROR,"Invalid competition")
		return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))

	if request.method == "POST":
		order = request.POST.get("jury_member_order",None)
		members = JuryMember.objects.filter(compo=compo).order_by("index")
		
		i=0
		lookup = {}
		for m in members:
			lookup[str(m.id)]=m
			
		if order:
			order = order.split(',')
			for o in order:
				lookup[o].index=i
				i+=1
				lookup[o].save()
				
			messages.add_message(request,messages.SUCCESS,"Jury member order updated.")

	return HttpResponseRedirect(reverse('compo_jury',args=[party.slug,compo.slug]))


@require_party
@login_required
def reorder_entries(request,compo):
	if not request.user.has_perm("compo.admin"):
		return HttpResponseNotFound()

	party = get_party(request)
	try:
		try:
			compo = Competition.objects.get(slug=compo,party=party)
		except Competition.DoesNotExist:
			raise InvalidCompetition()

	except InvalidCompetition:
		messages.add_message(request,messages.ERROR,"Invalid competition")
		return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))
	

	if request.method == "POST":
		order = request.POST.get("entry_order",None)
		if order:
			compo.jury_order = order
			compo.save()
#			messages.add_message(request,messages.SUCCESS,"Entry order updated.")
			
#	return HttpResponseRedirect(reverse('compo_jury',args=[party.slug,compo.slug]))
	return HttpResponse("ok")
