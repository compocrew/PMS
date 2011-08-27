
from django import forms
from models import Entry,EntryVersion,TriState,EntryTypes
from django.contrib.auth.models import User
import pdb

class EntryPlaylistForm(forms.ModelForm):
	class Meta:
		model = Entry

class EntryForm(forms.ModelForm):

	def __init__(self,*args,**kwargs):
		if "instance" in kwargs:
			self.compo = kwargs['instance'].compo
		else:
			self.compo = kwargs['compo']
			del kwargs['compo']
			
		super(EntryForm,self).__init__(*args,**kwargs)
		
		if self.compo.thumbnails == TriState.Forbidden:
			del self.fields['thumbnail']
		elif self.compo.thumbnails == TriState.Required:
			self.fields['thumbnail'].required = True
		else:
			self.fields['thumbnail'].required = False
			
		if self.compo.technique == TriState.Forbidden:
			del self.fields['technique']
		elif self.compo.technique == TriState.Required:
			self.fields['technique'].required = True
		else:
			self.fields['technique'].required = False
			
		if self.compo.platform == TriState.Forbidden:
			del self.fields['platform']
		elif self.compo.platform == TriState.Required:
			self.fields['platform'].required = True
		else:
			self.fields['platform'].required = False
			
	class Meta:
		model = Entry
		exclude = ('preview_link','submitter','submittedtime','updatetime','qualification','qualification_points','qualification_text','playlist_position','hidden','compo')
		
	name = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}),help_text="Name of your entry, eg. Ronsu,Second Reality,Paimen")
	credits = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}),help_text="Credits for the entry, eg. HiRMU, Future Crew, Ultimate Killerfighter/HiRMU")
	technique = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}),help_text="Techniques used to make this entry, eg. 16 colors, Protracker, skill")
	platform = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}),help_text="Entry platform, eg. C-64, PC, Xbox360")
	comments = forms.CharField(required=False,widget=forms.Textarea(attrs={'rows' : 5, 'cols' : 30,'maxlength' : 255}),help_text="Comments for organizers and jury")


class AdminEntryForm(forms.ModelForm):

	def __init__(self,*args,**kwargs):
		if "instance" in kwargs:
			self.compo = kwargs['instance'].compo
		else:
			self.compo = kwargs['compo']

		if 'compo' in kwargs:
			del kwargs['compo']

		super(AdminEntryForm,self).__init__(*args,**kwargs)
	
		u = self.instance.submitter
		self.fields['submitter_search'].initial = u.username

	def clean_submitter(self):
		try:
			u = User.objects.get(id=self.cleaned_data['submitter'])
		except User.DoesNotExist:
			raise forms.ValidationError('submitter id is invalid')
		
		return u
			
	class Meta:
		model = Entry
		exclude = ('submittedtime','updatetime')

	name = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}))
	credits = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}))
	technique = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}),required=False)
	platform = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}),required=False)
	comments = forms.CharField(widget=forms.Textarea(attrs={'rows' : 5, 'cols' : 30,'maxlength' : 255}),required=False)
	submitter = forms.IntegerField(widget=forms.HiddenInput(attrs={'id' : 'submitter'}))
	submitter_search = forms.CharField(label='Submitter',widget=forms.TextInput(attrs={'id' : 'submitter_search','size' : 40}))
	
	
class EntryVersionForm(forms.ModelForm):
	class Meta:
		model = EntryVersion
		exclude = ('entry','submitter','submittedtime','version')
		
	comments = forms.CharField(widget=forms.Textarea(attrs={'rows' : 3,'cols' : 30,'maxlength' : 255}),required=False,help_text="If your entry is an website, enter the website url in comments")
	
	def clean(self):
		entryType = int(self.cleaned_data['entryType'])
		if entryType == EntryTypes.File:
			if not self.cleaned_data['data']:
				self._errors['data'] = self.error_class("You must select file")
		elif entryType == EntryTypes.Website:
			del self.cleaned_data['data']
			if len(self.cleaned_data['comments']) == 0:
				self._errors['comments'] = self.error_class("Enter website url in comments")
			
		return self.cleaned_data
		
		