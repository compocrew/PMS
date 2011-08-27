from django.db import models
from django.db.models import Q
from datetime import datetime
from schedule.models import Event
# Create your models here.
from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django.contrib.auth.models import User,Permission
from accounts.models import Ticket,TicketType
from django.contrib.contenttypes.models import ContentType

import xml.dom.minidom

class TriState:
	Forbidden = 0
	Optional = 1
	Required = 2

from entry.models import Entry,Qualification


class VoteCacheStale(Exception):
	pass
	

TRISTATE = (
	(TriState.Forbidden,'Forbidden'),
	(TriState.Optional,'Optional'),
	(TriState.Required,'Required'),
)


class VoteCache(models.Model):
	updated = models.DateTimeField(auto_now=True)
	compo = models.ForeignKey('Competition',unique=True)
	
	entries = models.CommaSeparatedIntegerField(max_length=256)
	points = models.CommaSeparatedIntegerField(max_length=2048)


class VotePoints(models.Model):
	
	user = models.ForeignKey(User)
	compo = models.ForeignKey('Competition')
	submitted = models.DateTimeField(auto_now=True,null=True)
	
	votes = models.CommaSeparatedIntegerField(max_length=256,null=True,blank=True)


class Category(models.Model):
	
	class Meta:
		verbose_name_plural = "Categories"
	
	name = models.CharField(max_length=256)
	index = models.IntegerField(default=999,null=False)
	
	def __unicode__(self):
		return self.name

class JuryMember(models.Model):
	name = models.CharField(max_length=255,null=True,blank=True)
	user = models.ForeignKey(User,null=True,blank=True)
	compo = models.ForeignKey('Competition')
	index = models.IntegerField(default=0)
	
	def get_name(self):
		if self.user:
			return str(self.user)
		return self.name
		

class JuryPoints(models.Model):
	
	member = models.ForeignKey(JuryMember)
	entry = models.ForeignKey(Entry)
	points = models.IntegerField(null=True,blank=True)
	
class Competition(models.Model):
	name = models.CharField(max_length=256,verbose_name="Compo name")
	slug = models.SlugField(max_length=256,null=True)

	rules = models.URLField(verify_exists=False,blank=True,null=True,verbose_name="Compo rules link",help_text="URL to competition rules")
	description = models.TextField(max_length=1024,blank=True,null=True)
	party = models.ForeignKey('party.Party',null=True)
	
	category = models.ForeignKey(Category,null=True,blank=True,verbose_name="Compo category")
	
	hidden = models.BooleanField(default=True,help_text="Is compo visible only to admins")
	
	entries_public = models.BooleanField(default=False)
	results_public = models.BooleanField(default=False)
	show_credits = models.BooleanField(default=True)

	thumbnails = models.IntegerField(choices=TRISTATE,default=1)
	technique = models.IntegerField(choices=TRISTATE,default=1)
	platform = models.IntegerField(choices=TRISTATE,default=1)

	submit_start = models.DateTimeField(null=True,blank=True)
	submit_end = models.DateTimeField(null=False,blank=False)
	
	update_end = models.DateTimeField(null=False,blank=False)
	
	vote_start = models.DateTimeField(null=False,blank=False)
	vote_end = models.DateTimeField(null=False,blank=False)
	
	vote_points = models.CommaSeparatedIntegerField(max_length=256,default="10,6,3")

	admins = models.ManyToManyField(User,null=True,blank=True)
	jury_order = models.CommaSeparatedIntegerField(max_length=8192,null=True,blank=True)

	def is_playlist_valid(self):
		entries = self.get_qualified_entries()
		gaps = []
		for entry in entries:
			if entry.playlist_position < 1: #entry not positioned in playlist
				return False
			if entry.playlist_position in gaps: #multiple entries have same playlist id
				return False
			gaps.append(entry.playlist_position)
			
		for i in range(len(entries)): #playlist ids are not sequential
			if gaps[i] != i+1:
				return False
				
		return True
		
	def count_not_hidden_entries(self):
		return self.get_entries().filter(hidden=False).count()
		
	def get_entries(self):
		return Entry.objects.filter(compo=self.id)
	
	def get_qualified_entries(self):
		return self.get_entries().filter(qualification=Qualification.Qualified,hidden=False).order_by("playlist_position")
	
	def can_submit(self):
		now = datetime.now()
		return (not self.submit_start or now >= self.submit_start) and now < self.submit_end

	def submit_passed(self):
		now = datetime.now()
		return now > self.submit_end
		
	def can_update(self):
		now = datetime.now()
		return (not self.submit_start or now >= self.submit_start) and now < self.update_end

	def update_passed(self):
		now = datetime.now()
		return now > self.update_end


	def can_vote(self):
		now = datetime.now()
		return now >= self.vote_start and now < self.vote_end

	def vote_passed(self):
		now = datetime.now()
		return now > self.vote_end

	def get_user_votes(self,user):
		try:
			return VotePoints.objects.get(user=user,compo=self)
		except VotePoints.DoesNotExist:
			return None
	
	def user_has_voted(self,user):
		return self.get_user_votes(user) != None

		
	def num_vote_places(self):
		places = self.vote_points.split(",")
		numEntries = Entry.objects.filter(compo=self.id,qualification=Qualification.Qualified,hidden=False).count()
		if numEntries < places:
			places = numEntries
			
		return places
	
	def calculate_votes(self):
		import siteconfig
		
		uservotes = VotePoints.objects.filter(compo=self)
		entries = self.get_qualified_entries()
		
		
		entryvotes = {}
		points = self.vote_points.split(',')
		
		for uvote in uservotes:
			votes = uvote.votes.split(',')
			multiplier = 1
			
			if siteconfig.settings['require_ticket']:
				try:
					ticket = Ticket.objects.get(used_by=uvote.user)
				except Ticket.DoesNotExist:
					continue
				except Ticket.MultipleObjectsReturned:
					ticket = Ticket.objects.filter(used_by=uvote.user)[0]
					#get multiplier
				multiplier = ticket.ticket_type.multiplier
				
			place = 0
			for v in votes:
				vid = v
				p = int(points[place]) * multiplier
				if not vid in entryvotes:
					entryvotes[vid] = 0

				entryvotes[vid] += p
				place += 1
		
		if len(entryvotes) == 0:
			return None

		try:
			cache = VoteCache.objects.get(compo=self)
		except VoteCache.DoesNotExist:
			cache = VoteCache(compo=self)

		elist = []
		plist = []	
		for k,v in entryvotes.items():
			elist.append(str(k))
			plist.append(str(v))
			
		cache.entries = ','.join(elist)
		cache.points = ','.join(plist)
		cache.updated = datetime.now()
		cache.save()
		return cache
		
	def get_votes(self):
		try:
			try:
				votes = VoteCache.objects.get(compo=self)
				uservotes = VotePoints.objects.filter(compo=self).order_by("-submitted")
				if len(uservotes) == 0 or not votes.updated or not uservotes[0].submitted or uservotes[0].submitted > votes.updated:
					raise VoteCacheStale()
					
			except VoteCache.DoesNotExist:
				raise VoteCacheStale()
		except VoteCacheStale:
			print "update vote cache for compo %s" % self.name
			votes = self.calculate_votes()
		
		if not votes:
			return []
		
		elist = votes.entries.split(',')
		plist = votes.points.split(',')
		
		sortedPoints = []
		for i in range(len(elist)):
			sortedPoints.append([int(elist[i]),int(plist[i])])

		sortedPoints.sort(reverse=True,cmp=lambda a,b: a[1]-b[1])
		return sortedPoints
		
	def get_results(self):
		results = self.get_votes()

		qentries = self.get_qualified_entries()

		entries = []
		for result in results:
			eid = result[0]
			points = result[1]

			entry = qentries.get(id=eid)
			entry.points = points
			entries.append(entry)

		def sorter(a,b):
			return a.points - b.points
			
		entries.sort(cmp=sorter,reverse=True)
		i=1
		place = 1
		last_pts = -1
		for entry in entries:
			if entry.points == last_pts:
				entry.place = place
			else:
				entry.place = i
				place = i
				last_pts = entry.points
			i+=1
		return entries
	
	
	def calculate_jury_scores(self):
		
		for e in self.get_entries().filter(hidden=False):
			p = 0
			amount = 0
			points = JuryPoints.objects.filter(entry=e)
			for point in points:
				if point.points:
					p += point.points
					amount+=1
			if amount > 0:
				e.qualification_points = float(p)/float(amount)
			else:
				e.qualification_points = 0
			e.save()
			
		
	def __unicode__(self):
		return "%s %s" % (self.party.shortname,self.name)
	
	
	def export_xml(self,include_votes=False):
		dom = xml.dom.minidom.getDOMImplementation().createDocument(None,"tag",None)
		
		def boolean(b):
			if b:
				return "True"
			
			return "False"
		
		def w(s):
			if not s:
				return ""
			return str(s)
			
		node = dom.createElement("compo")
		node.setAttribute("party",w(self.party.slug))
		node.setAttribute("id",w(self.id))
		node.setAttribute("name",self.name)
		node.setAttribute("description",self.description)
		node.setAttribute("howmanyentriesvoted",w(len(self.vote_points.split(","))))
		node.setAttribute("previewpublic",boolean(False))
		node.setAttribute("resultspublic",boolean(self.results_public))
		node.setAttribute("playlistfrozen",boolean(self.is_playlist_valid()))
		node.setAttribute("credited",boolean(self.show_credits))
		node.setAttribute("thumbnailrequired",w(self.thumbnails))
		node.setAttribute("platformrequired",w(self.platform))
		node.setAttribute("techniquerequired",w(self.technique))
		node.setAttribute("ruleslink",self.rules)
		node.setAttribute("visible",boolean(self.hidden != True))
		node.setAttribute("category",self.category.name)
		
		entriesNode = dom.createElement("entries")
		node.appendChild(entriesNode)
		
		if include_votes:
			result_entries = self.get_results()
			lookup = {}
			for q in result_entries:
				lookup[str(q.id)]=q
				
		entries = self.get_qualified_entries()
			
		for entry in entries:
			entrynode = entry.export_xml()
			if include_votes:
				if str(entry.id) in lookup:
					rentry = lookup[str(entry.id)]
					entrynode.setAttribute("votepoints",w(rentry.points))
					entrynode.setAttribute("place",w(rentry.place))
				
			entriesNode.appendChild(entrynode)
		
		return node
		
	class Meta:
		permissions = (
			('admin','access/edit competition info'),
			('count_votes','calculate votes before results are published'),
		)
		
		
class CompoAdminForm(forms.ModelForm):
	class Meta:
		model = Competition
		exclude = ("jury_order",)
		
	name = forms.CharField(widget=forms.TextInput(attrs={'size' : 40,'id' : 'slugsource'}))
	slug = forms.CharField(widget=forms.TextInput(attrs={'id' : 'slug','size' : 40}))
#	rules = forms.URLField(widget=forms.TextInput(attrs={'size' : 80}))

	description = forms.CharField(max_length=1024,widget=forms.Textarea(),required=False)
	submit_start = forms.DateTimeField(widget=forms.TextInput(attrs={'class' : 'datetime','size' : 25}),required=False)
	submit_end = forms.DateTimeField(widget=forms.TextInput(attrs={'class' : 'datetime','size' : 25}))

	update_end = forms.DateTimeField(widget=forms.TextInput(attrs={'class' : 'datetime','size' : 25}))
	
	vote_start = forms.DateTimeField(widget=forms.TextInput(attrs={'class' : 'datetime','size' : 25}))
	vote_end = forms.DateTimeField(widget=forms.TextInput(attrs={'class' : 'datetime','size' : 25}))
	
	admins = forms.ModelMultipleChoiceField(queryset=[],required=False)
	
	
	def __init__(self,*args,**kwargs):
		super(CompoAdminForm,self).__init__(*args,**kwargs)
		
		ctype = ContentType.objects.get_for_model(Competition)
		perm = Permission.objects.get(content_type=ctype,codename='admin')
		users = User.objects.filter(Q(groups__permissions=perm) | Q(user_permissions=perm) | Q(is_superuser=True)).distinct()
		self.fields['admins'].queryset = users
		
		
	
		
