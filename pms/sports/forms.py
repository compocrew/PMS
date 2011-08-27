from django import forms
from models import *

class SeedType:
	Random = 0
	Prescore = 1
	 

SEED_CHOICES = (
	(SeedType.Random,"Random"),
	(SeedType.Prescore,"Prescore"),
)


class SportsAdminForm(forms.ModelForm):
	
	class Meta:
		model = Sports
		exclude = ('results','party','category')
		
	join_time_start = forms.DateTimeField(widget=forms.TextInput(attrs={'class' : 'datetime','size' : 25}),required=False)
	join_time_end = forms.DateTimeField(widget=forms.TextInput(attrs={'class' : 'datetime','size' : 25}))
	description = forms.CharField(widget=forms.Textarea(attrs={'rows' : 5, 'cols' : 30,'maxlength' : 4096}),required=False)
	
	
	
class SportsParticipateForm(forms.ModelForm):
	class Meta:
		model = SportsParticipant
		exclude = ('pre_score','user','sport')
		
	name = forms.CharField(required=True,label="Your name / team name")
	comment = forms.CharField(required=False)
	data = forms.FileField(required=False)
	
	def __init__(self,sports,*args,**kwargs):
		super(SportsParticipateForm,self).__init__(*args,**kwargs)
		
		if sports.show_comment:
			self.fields['comment'].label = sports.comment_description
			self.fields['comment'].required = True
		else:
			del self.fields['comment']
			
		if sports.show_file:
			self.fields['data'].label = sports.file_description
			self.fields['data'].required = True
		else:
			del self.fields['data']
	

class SeedForm(forms.Form):
	
	num = forms.IntegerField(label="Number of participants")
	seedtype = forms.ChoiceField(label="Seeding type",choices=SEED_CHOICES)
	minscore = forms.IntegerField(label="Minimum prescore",required=False,initial=0)
	