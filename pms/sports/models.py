from django.db import models

from party.models import Party
from django.contrib.auth.models import User
from datetime import datetime
from random import sample,shuffle
from django.core.files.storage import FileSystemStorage
import settings

fs = FileSystemStorage(location=settings.ENTRY_UPLOAD_LOCATION)

class SportsType:
	Single = 0
	SingleElimination = 1
	DoubleElimination = 2
	
SPORTSTYPES = (
	(SportsType.Single,"Single"),
	(SportsType.SingleElimination,"Single elimination"),
	(SportsType.DoubleElimination,"Double elimination"),
)


class SportsCategory(models.Model):
	name = models.CharField(max_length=255,blank=False,null=False)
	index = models.IntegerField(default=999,null=False,blank=False)
	party = models.ForeignKey(Party)
	
	def __unicode__(self):
		return u"%s %s" % (self.party.name,self.name.lower())

	class Meta:
		verbose_name_plural = "Sports categories"



class Sports(models.Model):
	
	name = models.CharField(max_length=255,blank=False,null=False)
	description = models.CharField(max_length=4096,blank=True,default="")
	slug = models.SlugField()
	link = models.URLField(null=True,blank=True)
	sportstype = models.IntegerField(max_length=1,null=False,blank=False,default=0,choices=SPORTSTYPES)
	
	category = models.ForeignKey(SportsCategory,null=False,blank=False)
	party = models.ForeignKey(Party,null=False)

	max_participants = models.IntegerField(null=False,blank=False)

	join_time_start = models.DateTimeField(null=True,blank=True)
	join_time_end = models.DateTimeField(null=False,blank=False)
	
	finished = models.BooleanField(default=False)
	results = models.ManyToManyField('SportsParticipant',through="ParticipantResult")
	
	hidden = models.BooleanField(default=True)
	
	show_comment = models.BooleanField(default=True)
	show_file = models.BooleanField(default=False)
	comment_description = models.CharField(max_length=128,null=True,blank=True)
	file_description = models.CharField(max_length=128,null=True,blank=True)
	
	def has_results(self):
		return len(self.results.all()) > 0
	
	def get_participants(self):
		return SportsParticipant.objects.filter(sport=self)
	
	def can_join(self):
		now = datetime.now()
		
		if (not self.join_time_start or now > self.join_time_start) and (now < self.join_time_end):
			return True
		return False
		
	def opens_later(self):
		now = datetime.now()
		return not self.join_time_start or now < self.join_time_start
		
	def accept_more(self):
		return SportsParticipant.objects.filter(sport=self).count() < self.max_participants
	
	def add_result(self,participant,score):
		pass
		
	def reset_results(self):
		self.results.clear()
		self.save()

	def get_results(self,max_places=3):
		return self.results
	
	def __unicode__(self):
		return u"%s %s" % (self.party.name,self.name.lower())
		
	class Meta:
		verbose_name_plural = "Sports"
		permissions = (
			('admin','allow user to admin sports'),
		)

	
class SportsParticipant(models.Model):
	
	user = models.ForeignKey(User,null=False,blank=True)
	sport = models.ForeignKey(Sports)

	name = models.CharField(max_length=50,null=False,blank=False)
	comment = models.CharField(max_length=1024,null=True,blank=True)
	data = models.ImageField(null=True,blank=True,upload_to="sports",storage=fs)
	pre_score = models.IntegerField(null=False,blank=True,default=0)
	
	def real_name(self):
		return self.user.get_full_name()
	
	def __unicode__(self):
		return u"%s %s: %s (prescore %d)" % (self.sport.party.slug,self.sport.name.lower(),self.name,self.pre_score)
	
	
class SportsSeeding(models.Model):
	
	sport = models.ForeignKey(Sports,unique=True)
	
	max_participants = models.IntegerField(null=False)
	participants = models.ManyToManyField(SportsParticipant,null=True,blank=True)
	

	def seed(self,random=True,min_score=0):
		self.participants.clear()
		
		potentials = [p for p in SportsParticipant.objects.filter(sport=self.sport,pre_score__gte=min_score).order_by("-pre_score")]
		left = self.max_participants
		if len(potentials) < left:
			selected = potentials
			shuffle(selected)
		else:	
			if random:
				selected = sample(potentials,left)
				shuffle(selected)
			else:
				selected = potentials[:left]
				
		for s in selected:
			self.participants.add(s)


class ParticipantResult(models.Model):
	participant = models.ForeignKey(SportsParticipant)
	sport = models.ForeignKey(Sports)
	
	show_score = models.BooleanField(default=False)
	score = models.FloatField(default=0)
	
	class Meta:
		ordering = ['-score']
		
