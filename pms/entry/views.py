# Create your views here.
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect,HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render_to_response,get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.core.urlresolvers import reverse
import django.core.files

from models import Entry,EntryVersion,entry_submitted,entry_updated
from forms import AdminEntryForm,EntryForm,EntryVersionForm
from party.decorators import require_party
from datetime import datetime
from filetransfers.api import serve_file
import zipfile
import os
import settings
import tempfile

@require_party
@login_required
def admin_edit_entry(request,entryid):
	if not request.user.has_perm("compo.admin") and not request.user.has_perm("entry.admin"):
		return HttpResponseNotFound()
	
	try:
		entry = Entry.objects.get(id=entryid)
		versions = EntryVersion.objects.filter(entry=entry)
	except Entry.DoesNotExist:
		return HttpResponseNotFound()
	
	success = False
	status = None
	if request.method == "POST":
		
		form = AdminEntryForm(request.POST,request.FILES,instance=entry)
		if form.is_valid():
			form.save()
			entry.save()
			success = True
			status = "Entry updated"
	else:
		form = AdminEntryForm(instance=entry)
		
	return render_to_response("admin_edit_entry.html",{'entry' : entry,'entryversions' : versions,'form' : form,'success':success,'status':status },context_instance=RequestContext(request))
	
@require_party
@login_required
def upload_entry_version(request,entryid):
	entry = get_object_or_404(Entry,id=entryid)
		
	success = False
	info = {}

	if (entry.submitter == request.user and entry.compo.can_update()) or (request.user.has_perm('compo.admin') or request.user.has_perm("entry.admin")):
		if request.method == "POST":

			form = EntryVersionForm(request.POST,request.FILES)
			if form.is_valid():
				v = form.save(commit=False)
				v.entry = entry
				v.submitter = request.user
				v.version = EntryVersion.objects.filter(entry=entry).count()+1
				v.save()
				entry.updatetime = datetime.now()
				entry.save()
				success = True
				info = {
					'version' : v,
					'compo' : entry.compo,
				}
				entry_updated.send_robust(sender=entry,compo=entry.compo,entry=entry,comments=v.comments)
		else:
			form = EntryVersionForm()

		return render_to_response("entry_upload_version.html",{'entry' : entry,'form' : form,'success' : success,'info' : info },context_instance=RequestContext(request))
	else:
		return HttpResponseNotFound()
		
@require_party	
def download(request,entryid):
	entry = get_object_or_404(Entry,id=entryid)
	if entry.compo.entries_public or request.user.has_perm("entry.admin") or request.user.has_perm("compo.admin"):
		version = entry.get_latest_version()
		if version and version.data:
			return serve_file(request,version.data,None,entry.get_publish_filename())

		return HttpResponseNotFound()
			
#		response = HttpResponse(mimetype="application/octet-stream")
#		response['Content-Disposition']="filename=%s" % entry.get_publish_filename()
#		return response
	else:
		return HttpResponseNotFound()
		
		
def get_entry_file(dfile):
	localfile = tempfile.NamedTemporaryFile(delete=False)
	
	dfile.open()

	for chunk in dfile.chunks():
		localfile.write(chunk)

	dfile.close()
	localfile.close()
	return localfile

@require_party
def admin_download_version(request,entryid,version):
	entry = get_object_or_404(Entry,id=entryid)
	if request.user.has_perm("entry.admin") or request.user.has_perm("compo.admin"):
		if version == str(0): #download all versions
			packfile = tempfile.NamedTemporaryFile(delete=False)
			pack = zipfile.ZipFile(packfile.name,"w",zipfile.ZIP_DEFLATED)
			
			for version in entry.versions():
				if version.is_file:
					lfile = get_entry_file(version.data)
					pack.write(lfile.name,entry.get_publish_filename("_v%s" % version.version))
					os.unlink(lfile.name)
					
			pack.close()
			dfile = django.core.files.File(packfile)
			
			return serve_file(request,dfile,None,entry.get_publish_filename("_all.zip",False),"application/octet-stream")
		else:
			try:
				eversion = entry.versions().get(version=version)
				if eversion.data:
					return serve_file(request,eversion.data,None,entry.get_publish_filename("_v%s" % version),"application/octet-stream")
			except EntryVersion.DoesNotExist:
				pass
	return HttpResponseNotFound()
		

@require_party
def admin_download(request,entryid):
	entry = get_object_or_404(Entry,id=entryid)
	if request.user.has_perm("entry.admin") or request.user.has_perm("compo.admin"):
		versions = entry.versions()
		
		return render_to_response("admin_download_entry.html",{'entry' : entry,'versions':versions},context_instance=RequestContext(request))
	else:
		return HttpResponseNotFound()
		
	
	