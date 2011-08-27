from django.db import models
from django.contrib.auth.models import User
# Create your models here.
from django import forms
from main.fields import COUNTRIES
from django.forms.extras.widgets import SelectDateWidget
from party.models import Party
from django.core.exceptions import ValidationError
from django.core import validators
from datetime import date

GENDERS = (
	('U','Unknown'),
	('M','Male'),
	('F','Female'),
)

YEAR_CHOICES = [x for x in range(1920,date.today().year)]


class TicketType(models.Model):
	name = models.CharField(max_length = 256)
	multiplier = models.IntegerField(default=1)
	party = models.ForeignKey(Party)
	
	def __unicode__(self):
		return "%s %s" % (self.party.name,self.name.lower())

class Ticket(models.Model):
	code = models.CharField(max_length=256)
	ticket_type = models.ForeignKey(TicketType)
	used_by = models.ForeignKey(User,null=True) 
	
	party = models.ForeignKey(Party)
	
	def __unicode__(self):
		return self.code

class UserProfile(models.Model):
	
	class Meta:
		permissions = (
			('organizer','is organizer'),
			('admin', 'see / edit user information'),
			('sensitive','see sensitive data like ssn and bank details'),
		)
	
	user = models.OneToOneField(User)

	address1 = models.CharField(max_length=256)
	address2 = models.CharField(max_length=256,blank=True,null=True)
	postcode = models.CharField(max_length=10)
	city = models.CharField(max_length=256)
	country = models.CharField(max_length=3,choices=COUNTRIES,default='FIN')
	handle = models.CharField(max_length=256,blank=True,null=True)
	group = models.CharField(max_length=256,blank=True,null=True)
	extra1 = models.CharField(max_length=256,blank=True,null=True)
	extra2 = models.CharField(max_length=256,blank=True,null=True)
	phone = models.CharField(max_length=256,blank=True)
	gender = models.CharField(max_length=1,default='U',choices = GENDERS)
	birthdate = models.DateField()

	ssn = models.CharField(max_length=256,blank=True,null=True,help_text="Your social security number if you are participating in any competitions")
	bank_account = models.CharField(max_length=256,blank=True,null=True,help_text="Your bank account number if you are participating in any competitions")
		
	def hasPartyTicket(self,party):
		return Ticket.objects.filter(party=party,used_by=self.user).count() > 0
			
	def __unicode__(self):
		return u"%s (%s / %s) %s %s" % (self.user.username,self.handle,self.group,self.user.first_name,self.user.last_name)
	
			
	
class UserForm(forms.ModelForm):

	username = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}),help_text="Your login name")
	password = forms.CharField(widget=forms.PasswordInput(attrs={'size' : 40}))
	verify_password = forms.CharField(widget=forms.PasswordInput(attrs={'size' : 40}))
	email = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}))
	
	def clean_password(self):
		if self.data['password'] != self.data['verify_password']:
		            raise forms.ValidationError('Passwords are not the same')
		return self.data['password']
	
	def save(self,**kwargs):
		u = User.objects.create_user(self.cleaned_data['username'],self.cleaned_data['email'],self.cleaned_data['password'])
		commit = kwargs.pop("commit",True)
		if commit:
			u.save()
		return u
		
	class Meta:
		model = User
		fields=('username','password','verify_password','email')
		
		
class UserProfileForm(forms.ModelForm):
	error_css_class = 'error'
	required_css_class = 'required'

	first_name = forms.CharField(widget=forms.TextInput(attrs={'size' : 40,'maxlength': 30}))
	last_name = forms.CharField(widget=forms.TextInput(attrs={'size' : 40,'maxlength': 30}))
	address1 = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}))
	address2 = forms.CharField(required=False,widget=forms.TextInput(attrs={'size' : 40}))
	city = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}))
	handle = forms.CharField(required=False,widget=forms.TextInput(attrs={'size' : 40}))
	group = forms.CharField(required=False,widget=forms.TextInput(attrs={'size' : 40}))
	phone = forms.CharField(widget=forms.TextInput(attrs={'size' : 40}))
#	ssn = forms.CharField(required=False,widget=forms.TextInput(attrs={'size' : 40}),help_text="Your social security number if you are participating in any competitions")
#	bank_account = forms.CharField(required=False,widget=forms.TextInput(attrs={'size' : 40}),help_text="Your bank account number if you are participating in any competitions")

	def __init__(self,*args,**kwargs):
		user = kwargs.pop("user",None)
		super(UserProfileForm,self).__init__(*args,**kwargs)
		self.fields.keyOrder = [
			'first_name',
			'last_name',
			'phone',
			'address1',
			'address2',
			'postcode',
			'city',
			'birthdate',
			'handle',
			'group',
#			'ssn',
#			'bank_account',
		]
		if user:
			self.fields['first_name'].initial=user.first_name.capitalize()
			self.fields['last_name'].initial=user.last_name.capitalize()
		

	class Meta:
		model = UserProfile
		exclude = ('ticket','user','extra1','extra2','ssn','bank_account')
		
	birthdate = forms.DateField(widget = SelectDateWidget(years=YEAR_CHOICES))
