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
from datetime import datetime
from django.forms.models import modelformset_factory
import xml.dom.minidom
import xml.dom
import zipfile
import tempfile
import os
import shutil
import subprocess
from lxml import etree


class InvalidCompetition(Exception):
	pass

class VoteError(Exception):
	pass

@require_party
def index(request):
	
	compolist = Competition.objects.filter(party=get_party(request))
	
	compos = []
	categories = []
	lookup = {}
	
	for compo in compolist:
		if not compo.hidden or request.user.has_perm('compo.admin'):
				
			if compo.category:
				if compo.category.name not in lookup:
					categories.append({ 'name' : compo.category.name, 'compos' : []})
					lookup[compo.category.name] = len(categories)-1
				categories[lookup[compo.category.name]]['compos'].append(compo)
			else:
				compos.append(compo)

	d = {} #dict(compos=compos)
	if len(categories) > 0:
		d['categories']=categories
	d["compos"]=compos
		
	return render_to_response("compo_index.html",d,context_instance=RequestContext(request))

	
@require_party
@login_required
def participate(request,compo):
	party = get_party(request)
	try:
		try:
			compo = Competition.objects.get(slug=compo,party=party)
		except Competition.DoesNotExist:
			raise InvalidCompetition()

	except InvalidCompetition:
		messages.add_message(request,messages.ERROR,"Invalid competition")
		return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))

	is_admin = request.user.has_perm("compo.admin")
	if (compo.can_submit() and (not party.ticket_required or request.user.get_profile().hasPartyTicket(party))) or is_admin:
	
		if request.method == "POST":	
			form = EntryForm(request.POST,request.FILES,compo=compo)
			if form.is_valid():
				entry = form.save(commit=False)
				entry.submitter = request.user
				entry.compo = compo
				entry.save()
				entry_submitted.send_robust(sender=compo,compo=compo,entry=entry,name=entry.name,credits=entry.credits)
				
				return HttpResponseRedirect(reverse('entry.views.upload_entry_version',args=[request.party,entry.id]))
		else:
			form = EntryForm(compo=compo)

		return render_to_response("compo_participate.html",{'compo' : compo,'form' : form},context_instance=RequestContext(request))
	else:
		if party.ticket_required and not request.user.get_profile().hasPartyTicket(party):
			messages.add_message(request,messages.ERROR,"You need ticket to participate.")
		else:
			messages.add_message(request,messages.ERROR,"Participation is closed.")

	return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))
	
@require_party
@login_required
def vote(request,compo):
	try:
		try:
			compo = Competition.objects.get(slug=compo,party=get_party(request))
		except:
			return HttpResponseNotFound()
		
		if not compo.can_vote():
			messages.add_message(request,messages.ERROR,"%s voting is closed" % compo.name)
			return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))
		
		num_places = len(compo.vote_points.split(','))
		entries = compo.get_qualified_entries()
		if len(entries) < num_places:
			num_places=len(entries)
		
		id_lookup = {}
		for entry in entries:
			id_lookup[str(entry.id)]=entry

		if request.method == "POST":
			try:
				uservotes = []

				for i in range(1,num_places+1):
					s = "place_%d" % i
				
					if not s in request.POST:
						messages.add_message(request,messages.ERROR,"You must vote for %d entries" % num_places)
						raise VoteException()
						
					entry_id = int(request.POST[s])
					if str(entry_id) in id_lookup:
						if str(entry_id) in uservotes:
							messages.add_message(request,messages.ERROR,"Invalid vote")
							raise VoteException()
							
						uservotes.append(str(entry_id))
						
				VotePoints.objects.filter(user=request.user,compo=compo).delete()
				v = VotePoints(user=request.user,compo=compo)
				v.votes = ','.join(uservotes)
				v.submitted = datetime.now()
				v.save()

				messages.add_message(request,messages.SUCCESS,"Votes updated")
			except:
				messages.add_message(request,messages.ERROR,"Vote update failed")
				
		data = { 'entries' : entries,
				'has_voted' : compo.user_has_voted(request.user),
				'compo' : compo,
		}
	
		data['places'] = [x for x in range(1,num_places+1)]
		data['num_places']=num_places

		votes = compo.get_user_votes(request.user)
	
		if votes:
			votes = votes.votes.split(',')
			i=1
			for v in votes:
				if str(v) in id_lookup:
					id_lookup[str(v)].voted = i
					i+=1
					
	except InvalidCompetition:
		messages.add_message(request,messages.ERROR,"Invalid competition")
		return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))
	
	return render_to_response("compo_vote.html",data,context_instance=RequestContext(request))
	
def vote_ajax(request,compo):
	pass


@require_party
@login_required
def admin(request,compo):
	if not request.user.has_perm("compo.admin"):
		return HttpResponseNotFound()

	try:
		try:
			compo = Competition.objects.get(slug=compo,party=get_party(request))
			compo.entries = compo.get_entries()
			if request.GET.get("hidden",False):
				compo.show_hidden = True
		except Competition.DoesNotExist:
			return HttpResponseNotFound()
		
		if request.method == "POST":
			form = CompoAdminForm(request.POST,instance=compo)
			if form.is_valid():
				compo = form.save()
				messages.add_message(request,messages.SUCCESS,"Compo settings updated")
			else:
				messages.add_message(request,messages.ERROR,"Settings invalid")
		else:
			form = CompoAdminForm(instance=compo)
		
		return render_to_response("compo_admin.html",dict(form=form,compo=compo),context_instance=RequestContext(request))
		
	except InvalidCompetition:
		messages.add_message(request,messages.ERROR,"Invalid competition")
		return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))
	
	
@require_party
@login_required
def admin_create_compo(request):
	if not request.user.has_perm("compo.admin"):
		return HttpResponseNotFound()
	
	if request.method == "POST":
		form = CompoAdminForm(request.POST)
		if form.is_valid():
			c = form.save()
			messages.add_message(request,messages.SUCCESS,"Compo %s created" % c.name)
			form = CompoAdminForm()
	else:
		form = CompoAdminForm()
	
	return render_to_response("compo_admin_create.html",{ 'form' : form },context_instance=RequestContext(request))
	
@require_party
@login_required
def admin_get_compo_times_json(request,compo):
	if not request.user.has_perm("compo.admin"):
		return HttpResponseNotFound()
	
	return ""


@require_party
@login_required
def admin_edit_playlist(request,compo):
	if not request.user.has_perm("compo.admin"):
		return HttpResponseNotFound()

	compo = Competition.objects.get(slug=compo,party=get_party(request))
	qentries = compo.get_qualified_entries().order_by("qualification_points")
	
	success = False
	status = ""
	if request.method == "POST":
		places={}
		print request.POST

		for entry in qentries:
			if entry.playlist_position != -1:
				places[str(entry.playlist_position)]=True
				
			key = "entry_%d" % entry.id
			place = request.POST.get(key,-1)
			if not place in places:
				places[place]=True
				entry.playlist_position=int(place)
				entry.save()
		success = True
		status = "Playlist updated."
	else:
		pass

	entries = [e for e in qentries]

	def sorter(a,b):
		if a.playlist_position == -1:
			return 1
		if b.playlist_position == -1:
			return -1
		return int(a.playlist_position - b.playlist_position)


	entries.sort(cmp=sorter)

		
	return render_to_response("compo_admin_edit_playlist.html",{'compo' : compo,'entries': entries,'success' : success,'status':status},context_instance=RequestContext(request))
	
	
@require_party
@login_required
def results(request,compo):
	party = get_party(request)
	try:
		try:
			compo = Competition.objects.get(slug=compo,party=party)
		except Competition.DoesNotExist:
			raise InvalidCompetition()

	except InvalidCompetition:
		messages.add_message(request,messages.ERROR,"Invalid competition")
		return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))

	is_admin = request.user.has_perm("compo.count_votes")
	
	if compo.results_public or is_admin:
		entries = compo.get_results()
		
		return render_to_response("compo_results.html",{'compo' : compo, 'entries' : entries},context_instance=RequestContext(request))
	else:
		return HttpResponseNotFound()


@require_party
@login_required
def admin_results(request,compo):
	party = get_party(request)
	try:
		try:
			compo = Competition.objects.get(slug=compo,party=party)
		except Competition.DoesNotExist:
			raise InvalidCompetition()

	except InvalidCompetition:
		messages.add_message(request,messages.ERROR,"Invalid competition")
		return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))

	is_admin = request.user.has_perm("compo.count_votes")

	if compo.results_public or is_admin:
		entries = compo.get_results()
		
		return render_to_response("compo_admin_results.html",{'compo' : compo, 'entries' : entries},context_instance=RequestContext(request))
	else:
		return HttpResponseNotFound()

@require_party
@login_required
def	admin_all_results(request):
	party = get_party(request)
	
	if request.user.has_perm("compo.count_votes"):
		compos = Competition.objects.filter(party=party,hidden=False)
	
		for c in compos:
			entries = c.get_results()
			c.entries = entries

		return render_to_response("compo_admin_all_results.html",{'compos' : compos},context_instance=RequestContext(request))

	
	return HttpResponseNotFound()
	
def generate_xml(content):
	dom = xml.dom.minidom.getDOMImplementation().createDocument(None,"pms-export",None)
	dom.documentElement.appendChild(content)
	return dom.toxml('utf-8')
	


@require_party
@login_required
def admin_export_list(request,compo):
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

	return render_to_response("compo_admin_export_list.html",{'compo' : compo},context_instance=RequestContext(request))


def transform_xsl(stylesheet,inputstr):
	xslt = etree.XML(stylesheet)
	transform = etree.XSLT(xslt)
	
	doc = etree.fromstring(inputstr)
	return unicode(transform(doc))
	

@require_party
@login_required
def admin_export_xsl(request,compo):
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
		dom = xml.dom.minidom.getDOMImplementation().createDocument(None,"tag",None)
		compos = dom.createElement("compos")
		compos.appendChild(compo.export_xml(compo.results_public or request.user.has_perm("compo.count_votes")))
		xmldata = generate_xml(compos)
		
		
		xsl = ""
		uploadedFile = request.FILES['xslpacket']
		for c in uploadedFile.chunks():
			xsl += c
			
		result = transform_xsl(xsl,xmldata)
		
		output_type = request.POST.get("output_type","txt")
		
		if output_type == "txt":
			return HttpResponse(result.encode('utf-8'),mimetype="text/plain")
		elif output_type == "diploma":
			tmpxsl = tempfile.NamedTemporaryFile(delete=False)
			tmpxsl.write(xsl)
			tmpxsl.close()
			tmpdata = tempfile.NamedTemporaryFile(delete=False)
			tmpdata.write(result.encode('utf-8'))
			tmpdata.close()
			tmpout,tmpoutname = tempfile.mkstemp()
			tmpout.close()
			
			retcode = subprocess.call(['fop','-xml',tmpdata.name,'-xsl',tmpxsl.name,'-pdf',tmpoutname])
			
			os.unlink(tmpxsl.name)
			os.unlink(tmpdata.name)
			if retcode == 0:
				outfile = open(tmpoutname)
				resp = HttpResponse(content_type="application/pdf")
				resp['Content-Disposition']='attachment; filename="%s_%s_diploma_export.pdf"' % (party.slug,compo.name.lower())
				resp.write(outfile.read())
				outfile.close()
				os.unlink(tmpoutname)
				return resp
			
		elif output_type == "impress":
			odpfile = tempfile.NamedTemporaryFile(delete=False)
			for c in request.FILES['odppacket'].chunks():
				odpfile.write(c)
#			odpfile.close()			
			archive = zipfile.ZipFile(odpfile,"a")
			archive.writestr("content.xml",result.encode('utf-8'))
			archive.close()
			result = open(odpfile.name,"r")
			resp = HttpResponse(content_type="application/octet-stream")
			resp['Content-Disposition']='attachment; filename="%s_%s_export.odp"' % (party.slug,compo.name.lower())
			resp.write(result.read())
			return resp

	return HttpResponseNotFound()

	
@require_party
@login_required
def admin_export_xml(request,compo):
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
	
	dom = xml.dom.minidom.getDOMImplementation().createDocument(None,"tag",None)
	compos = dom.createElement("compos")
	compos.appendChild(compo.export_xml(compo.results_public or request.user.has_perm("compo.count_votes")))
	xmldata = generate_xml(compos)
	
	resp = HttpResponse(content_type="text/xml")
	resp['Content-Disposition']='attachment; filename="%s_%s_export.xml"' % (party.slug,compo.name.lower())
	resp.write(xmldata)
	return resp


@require_party
@login_required
def admin_export_all_compos(request):
	if not request.user.has_perm("compo.admin"):
		return HttpResponseNotFound()

	party = get_party(request)
	dom = xml.dom.minidom.getDOMImplementation().createDocument(None,"tag",None)
	compos = dom.createElement("compos")
	for compo in Competition.objects.filter(party=party):
		compos.appendChild(compo.export_xml(compo.results_public or request.user.has_perm("compo.count_votes")))

	xmldata = generate_xml(compos)
	resp = HttpResponse(content_type="text/xml")
	resp['Content-Disposition']='attachment; filename="%s_compos_all_export.xml"' % party.slug.lower()
	
	resp.write(xmldata)
	return resp
	

@require_party
@login_required
def admin_edit_jury(request,compo):
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

	entries = compo.get_entries().filter(hidden=False).order_by("id")
	success = False
	status = ""
	
	if request.method == "POST":
		for entry in entries:
#			pkey = "entry_%d_points" % entry.id
			skey = "entry_%d_status" % entry.id
			rkey = "entry_%d_reason" % entry.id
			status = request.POST.get(skey,0)
#			points = request.POST.get(pkey,0)
			reason = request.POST.get(rkey,"")
			entry.qualification = int(status)
#			entry.qualification_points = float(points)
			entry.qualification_text = reason
			entry.save()
		success = True	
		status = "Points updated"

	entries = compo.get_entries().filter(hidden=False).order_by("id")

	data = {}
	
	data['entries']=entries
	data['choices']=QUALSTATUS
	data['compo']=compo
	data['success']=success
	data['status']=status
	
	return render_to_response("compo_admin_jury.html",data,context_instance=RequestContext(request))

	
def get_entry_file(dfile):
	localfile = tempfile.NamedTemporaryFile(delete=False)

	try:
		dfile.open()

		for chunk in dfile.chunks():
			localfile.write(chunk)

		dfile.close()
	except:
		pass
			
	localfile.close()
	return localfile

@require_party
def admin_download_entries(request,compo):
	party = get_party(request)
	try:
		try:
			compo = Competition.objects.get(slug=compo,party=party)
		except Competition.DoesNotExist:
			raise InvalidCompetition()

	except InvalidCompetition:
		messages.add_message(request,messages.ERROR,"Invalid competition")
		return HttpResponseRedirect(reverse('compo.views.index',args=[request.party]))

	if request.user.has_perm("entry.admin") or request.user.has_perm("compo.admin"):
		limit = request.GET.get("limit",None)
		if not limit:
			return render_to_response("compo_admin_download_entries.html",{'compo' : compo},context_instance=RequestContext(request))
		else:
			if limit == "all":
				entries = compo.get_entries().filter(hidden=False)
			elif limit == "juryed":
				entries = compo.get_entries().filter(hidden=False).filter(~Q(qualification=Qualification.Waiting))
			elif limit == "qualified":
				entries = compo.get_entries().filter(hidden=False).filter(qualification=Qualification.Qualified)
			elif limit == "publish":
				entries = compo.get_entries().filter(hidden=False).filter(~Q(qualification=Qualification.Waiting)).filter(~Q(qualification=Qualification.Disqualified))
			
			packfile = tempfile.NamedTemporaryFile(delete=False)
			pack = zipfile.ZipFile(packfile.name,"w",zipfile.ZIP_DEFLATED)

			for entry in entries:
				version = entry.get_latest_version()
				if version and version.is_file:
					lfile = get_entry_file(version.data)
					pack.write(lfile.name,entry.get_publish_filename())
					os.unlink(lfile.name)
				else:
					pack.writestr(entry.get_publish_filename(),"")

			pack.close()
			dfile = django.core.files.File(packfile)

			return serve_file(request,dfile,None,"%s_entries_%s.zip" % (compo.slug,limit),"application/octet-stream")
	return HttpResponseNotFound()



