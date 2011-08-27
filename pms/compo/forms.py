
from django import forms
from compo.models import *

class JuryMemberForm(forms.ModelForm):
	class Meta:
		model = JuryMember
		exclude = ("compo","user",'index')
		
	

