from django.db import models
from django.contrib.auth.models import User
from django import forms
from compo.models import TriState
from sorl.thumbnail import ImageField
from mongoengine import django
import os
import xml.dom.minidom
from django.core.files.storage import FileSystemStorage
import settings
import django.dispatch

entry_submitted = django.dispatch.Signal(providing_args=['compo','entry','name','credits'])
entry_updated = django.dispatch.Signal(providing_args=['compo','entry','comments'])
entry_juried = django.dispatch.Signal()

#fs = django.GridFSStorage()
fs = FileSystemStorage(location=settings.ENTRY_UPLOAD_LOCATION)

class EntryTypes:
	File = 0
	Website = 1
	Physical = 2

ENTRYTYPE = (
	(EntryTypes.File,'File'),
	(EntryTypes.Website,'Website'),
	(EntryTypes.Physical,'Physical'),

)

class Qualification:
	Waiting = 0
	NotQualified = 1
	Disqualified = 2
	Qualified = 3

QUALSTATUS = (
	(Qualification.Waiting,'Waiting for jury'),
	(Qualification.NotQualified,'Not qualified'),
	(Qualification.Disqualified,'Disqualified'),
	(Qualification.Qualified,'Qualified'),
)

class EntryVersion(models.Model):
	
	submitter = models.ForeignKey(User)
	submittedtime = models.DateTimeField(auto_now_add=True)
	entry = models.ForeignKey('Entry')
	entryType = models.IntegerField(choices=ENTRYTYPE,default=0,verbose_name="Entry version type")

	data = models.FileField(upload_to="entries",blank=True,null=True,verbose_name="Select entry file",storage=fs)
	comments = models.CharField(max_length=256,blank=True,null=True)
	version = models.IntegerField(null=False,default=0)
	
	def is_file(self):
		return self.entryType == EntryTypes.File
		
	def typename(self):
		return ENTRYTYPE[self.entryType][1]
	
	def export_xml(self):
		dom = xml.dom.minidom.getDOMImplementation().createDocument(None,"tag",None)
		def boolean(b):
			if b:
				return "1"
			
			return "0"
		
		def w(s):
			if not s:
				return ""
				
			return unicode(s)
		
		node = dom.createElement("version")
		
		node.setAttribute("comments",w(self.comments))
		node.setAttribute("submittime",w(self.submittedtime))
		
		return node
		
	
class Entry(models.Model):
	
	
	name = models.CharField(max_length=256,help_text="Name of your entry, eg. Ronsu,Second Reality,Paimen")
	credits = models.CharField(max_length=256,help_text="Credits for the entry, eg. HiRMU, Future Crew, Ultimate Killerfighter/HiRMU")
	comments = models.CharField(max_length=1024,null=True,blank=True,help_text="Comments for organizers and jury")
	thumbnail = ImageField(upload_to="thumbnails",null=True,blank=True)
	technique = models.CharField(max_length=256,null=True,blank=True)
	platform = models.CharField(max_length=256,null=True,blank=True)
	
	submittedtime = models.DateTimeField(auto_now_add=True)
	updatetime = models.DateTimeField(auto_now=True,null=True)
	
	submitter = models.ForeignKey(User)
	compo = models.ForeignKey('compo.Competition')
	
	hidden = models.BooleanField(default=False)

	qualification = models.IntegerField(choices=QUALSTATUS,default=0)
	qualification_points = models.FloatField(null=True,blank=True)
	qualification_text = models.CharField(max_length=256,blank=True,null=True)
	playlist_position = models.IntegerField(default=-1)
	preview_link = models.URLField(verify_exists=True,null=True,blank=True,max_length=1024)
	
	def has_file(self):
		v = self.get_latest_version()
		if v:
			return v.data != None
		
		return False
		
	def is_qualified(self):
		return self.qualification == Qualification.Qualified
	
	def has_juryed(self):
		return self.qualification != Qualification.Waiting
		
	def get_qualification_status(self):
		return QUALSTATUS[self.qualification][1]
	
	def get_latest_version(self):
		try:
			return self.versions().order_by('-version')[0]
		except:
			return None

	def get_publish_filename(self,extra="",extension=True):
		version = self.get_latest_version()
		basename = u"%s" % (self.name.lower().strip(' <>@!\t\\/#?*&'))
		if self.compo.show_credits or self.compo.results_public:
			basename+="_by_%s" % (self.credits.lower().strip(' <>@!\t\\/#?*&'))
			
		basename += extra
		
		if extension:
			if not version or not version.data:
				basename+="_NO_FILES_UPLOADED"
			else:
				basename += os.path.splitext(version.data.name)[1].lower().strip(' <>@!\t\\/#?*&')
			
		basename = basename.replace(" ","_")
		return basename
		
	def versions(self):
		return EntryVersion.objects.filter(entry=self).order_by("version")
	
	def save(self,*args,**kwargs):
		if self.qualification != Qualification.Qualified:
			self.playlist_position = -1


		old = None
		try:
			old = Entry.objects.get(pk=self.pk)
		except:
			pass

		super(Entry,self).save(*args,**kwargs)

		if old and old.qualification != self.qualification:
			entry_juried.send_robust(sender=self)
			
	
	class Meta:
		verbose_name_plural = "Entries"
		permissions = (
			('admin', 'see entry before publishing'),
			('update_preview','allow user to update preview_url via api'),
			('read_api','user has access to entry read-only api'),
		)
		
	def __unicode__(self):
		return u'%s by %s' % (self.name,self.credits)


	def export_xml(self):
		dom = xml.dom.minidom.getDOMImplementation().createDocument(None,"tag",None)
		def boolean(b):
			if b:
				return "True"
			
			return "False"
		
		def w(s):
			if not s:
				return ""
				
			return unicode(s)
		
		node = dom.createElement("entry")
		
		# WriteAttribute(w, "id", e["id"]);
		#         WriteAttribute(w, "name", HttpUtility.HtmlDecode((string)e["name"]));
		#                         WriteAttribute(w, "credit", HttpUtility.HtmlDecode((string)e["credit"]));
		#                         WriteAttribute(w, "submittercomments", HttpUtility.HtmlDecode((string)e["submittercomme$
		#         WriteAttribute(w, "submittedby", e["submittedby"]);
		#         WriteAttribute(w, "platform", e["platform"]);
		#         WriteAttribute(w, "techniques", e["techniques"]);
		#         WriteAttribute(w, "previewlink", e["previewlink"]);
		#         WriteAttribute(w, "thumbnailpath", e["thumbnailpath"]);
		#         WriteAttribute(w, "qualificationstatus", e["qualificationstatus"]);
		#                         WriteAttribute(w, "jurycomments", HttpUtility.HtmlDecode((string)e["jurycomments"]));
		#         WriteAttribute(w, "jurypoints", e["jurypoints"]);
		#         WriteAttribute(w, "playlistid", e["playlistid"]);
		# 
		#         // Non-qualified or disqualified entries don't have votes
		#         if ((Qual)e["qualificationstatus"] != Qual.QUALIFIED)
		#         {
		#             WriteAttribute(w, "votepoints", "");
		#             WriteAttribute(w, "place", "");
		
		node.setAttribute("id",w(self.id))
		node.setAttribute("name",w(self.name))
		node.setAttribute("credit",w(self.credits))
		node.setAttribute("submittedby",w(self.submitter.id))
		node.setAttribute("submittercomments",w(self.comments))
		node.setAttribute("platform",w(self.platform))
		node.setAttribute("techniques",w(self.technique))
		node.setAttribute("qualificationstatus",w(self.qualification))
		node.setAttribute("jurycomments",w(self.qualification_text))
		node.setAttribute("jurypoints",w(self.qualification_points))
		node.setAttribute("playlistid",w(self.playlist_position))
		node.setAttribute("previewlink",w(self.preview_link))
		subm = dom.createElement("submitter")
		node.appendChild(subm)
		
		submitter = self.submitter
		profile = submitter.get_profile()
		subm.setAttribute("id",w(submitter.id))
		subm.setAttribute("username",w(submitter.username))
		subm.setAttribute("firstname",w(submitter.first_name))
		subm.setAttribute("surname",w(submitter.last_name))
		subm.setAttribute("handle",w(profile.handle))
		subm.setAttribute("demogroup",w(profile.group))
		subm.setAttribute("email",w(submitter.email))
		subm.setAttribute("phonenumber",w(profile.phone))
		
		versions = dom.createElement("versions")
		node.appendChild(versions)
		for version in EntryVersion.objects.filter(entry=self):
			versions.appendChild(version.export_xml())
		
		return node
		
		
		
		
		
