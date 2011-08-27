from django.db import models
from django import forms

# Create your models here.

class Party(models.Model):
	
	class Meta:
		verbose_name_plural = "Parties"
	
	name = models.CharField(max_length=1024,null=False,blank=False)
	shortname = models.CharField(max_length=16)
	slug = models.SlugField()
	description = models.TextField(max_length=1024,blank=True)
	url = models.URLField(blank=True, verify_exists=False,verbose_name="Party website URL")
	start_date = models.DateField(null=True,blank=True)
	end_date = models.DateField(null=True,blank=True)
	big_icon = models.URLField(blank=True,null=True,verify_exists=False)
	header_icon = models.URLField(blank=True,null=True)
	
	privacy_link = models.URLField(verify_exists=False,blank=True,null=True)
	
	ticket_required = models.BooleanField(default=True,help_text="If checked, users need to enter their ticket code in order to participate/vote")
	name_visible = models.BooleanField(default=True,help_text="If unchecked, displays only header icon on top of web page")
	active = models.BooleanField(default=False,help_text="If unchecked, party does not show to users")
	maintenance = models.BooleanField(default=False,help_text="If checked, will display maintenance page to normal users")
	
	css = models.URLField(verify_exists=False,max_length=256,null=True,blank=True)
	
	def __unicode__(self):
		return self.name
		
		
	class Meta:
		permissions = (
			('admin', 'Party administrator'),
		)
		verbose_name_plural = "parties"
		
		
class PartyForm(forms.ModelForm):
	
	class Meta:
		model = Party
		
	url = forms.URLField(widget=forms.TextInput(attrs={'size' : 60}))
	
	big_icon = forms.URLField(widget=forms.TextInput(attrs={'size' : 60}))
	header_icon = forms.URLField(widget=forms.TextInput(attrs={'size' : 60}))
	privacy_link = forms.URLField(widget=forms.TextInput(attrs={'size' : 60}))
