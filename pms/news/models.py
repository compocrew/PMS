from django.db import models
from django import forms
from django.contrib.auth.models import User

from datetime import datetime
from party.models import Party

class NewsArticle(models.Model):
	headline = models.CharField(max_length=256,blank=False,null=False)
	content = models.TextField(max_length=65535,blank=True)
	slug = models.SlugField(max_length=256)
	
	user = models.ForeignKey(User)
	author = models.CharField(max_length=64,null=True,blank=True)
	date = models.DateTimeField(auto_now_add=True)
	
	published = models.BooleanField(default=False)
	expiretime = models.DateTimeField(blank=True,null=True,help_text="If defined, makes news item expire at this time")
	
	party = models.ForeignKey(Party,null=True,blank=True,help_text="Set to none if news item is not for any party")
	
	def is_expired(self):
		return self.expiretime and self.expiretime < datetime.now()
	
	class Meta:
		permissions = (
		 	('admin','manage news posts'),
		)
		
	def __unicode__(self):
		s = "published"
		if not self.published:
			s = "not " + s
		if self.is_expired():
			s += ", expired"
			
		return u"%s (%s)" % (self.headline,s)
		
class ArticleForm(forms.ModelForm):
	class Meta:
		model = NewsArticle
		exclude = ('user')
	headline = forms.CharField(widget=forms.TextInput(attrs={'size' : 40,'id' : 'slugsource'}))
	slug = forms.SlugField(widget=forms.TextInput(attrs={'id' : 'slug','size' : 40}))
	author = forms.CharField(widget=forms.TextInput(attrs={'id' : 'author'}))