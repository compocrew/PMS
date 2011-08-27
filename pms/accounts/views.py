# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django import forms
from models import UserProfile,UserForm,UserProfileForm,Ticket,TicketType
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm,PasswordChangeForm,SetPasswordForm
from django.db.models import Q
from django.utils import simplejson
from django.core.urlresolvers import reverse
from entry.models import Entry,EntryVersion
from datetime import timedelta, datetime
from party.decorators import require_party
from party.util import get_party

class LoginForm(forms.Form):
	username = forms.CharField(max_length=256,required=True,label="Username")
	password = forms.CharField(max_length=256,required=True,label="Password",widget=forms.PasswordInput)

def login_user(request):
	url = request.GET.get('next','/')
	
	if url == reverse('accounts.views.create_account'):
		url = "/"

	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			user = authenticate(username = form.cleaned_data['username'],password = form.cleaned_data['password'])
			
			if user:
				if user.is_active:
					try:
						user.get_profile()
					except UserProfile.DoesNotExist:
						profile = UserProfile(user=user)
						profile.save()
						
					login(request,user)
					return HttpResponseRedirect(url)
				else:
					messages.add_message(request,messages.WARNING,'Your account has been disabled')
					return HttpResponseRedirect("/")
			else:
				messages.add_message(request,messages.ERROR,'Username / password do not match')
		else:
			messages.add_message(request,messages.ERROR,'Username / password do not match')
		
	else:
		form = LoginForm()
		
	return render_to_response("login.html",{ 'form' : form,'next' : url },context_instance=RequestContext(request))

def create_account(request):
	if request.method == 'POST':
		form = UserForm(request.POST)
		form2 = UserProfileForm(request.POST)
		if form.is_valid() and form2.is_valid():
			user = form.save(commit=False)
			user.first_name = form2.cleaned_data['first_name']
			user.last_name = form2.cleaned_data['last_name']
			user.save()
			
			profile = form2.save(commit=False)
			profile.user = user
			profile.save()
			messages.add_message(request,messages.SUCCESS,"Account created")
			return HttpResponseRedirect(reverse("accounts.views.login_user"))
	else:
		form = UserForm()
		form2 = UserProfileForm()
	
	return render_to_response('create_account.html',{'form' : form,'form2' : form2},context_instance=RequestContext(request))

def logout_user(request):
	logout(request)
	
	return HttpResponseRedirect('/')


@require_party
@login_required
def tickets(request):
	party = get_party(request)
	
	if request.method == "POST":
		code = request.POST.get("code","").lstrip().rstrip()
		try:
			ticket = Ticket.objects.get(code=code)
			if ticket.used_by:
				messages.add_message(request,messages.ERROR,"Ticket is already in use")
			else:
				ticket.used_by = request.user
				ticket.save()
				messages.add_message(request,messages.SUCCESS,"Ticket added")
				
		except Ticket.DoesNotExist:
			messages.add_message(request,messages.ERROR,"Invalid ticket code")
			
	tickets = Ticket.objects.filter(used_by=request.user,party=party)
	
	return render_to_response("tickets.html",{'tickets' : tickets},context_instance=RequestContext(request))
	
@login_required
def user_details(request):
	ago = datetime.now()-timedelta(days=182)
	entries = Entry.objects.filter(submitter=request.user,hidden=False,submittedtime__gte=ago).order_by('submittedtime')
	
	if request.method == "POST":
		profileform = UserProfileForm(request.POST,user=request.user,instance=request.user.get_profile())
		passwordform = PasswordChangeForm(request.user)
		if profileform.is_valid():
			request.user.first_name = profileform.cleaned_data['first_name'].capitalize()
			request.user.last_name = profileform.cleaned_data['last_name'].capitalize()
			request.user.save()		
			profileform.save()
			messages.add_message(request,messages.SUCCESS,"Info updated")
	else:
		passwordform = PasswordChangeForm(user=request.user)
		profileform = UserProfileForm(user=request.user,instance=request.user.get_profile())
	
	return render_to_response("details.html",{'profileform' : profileform,'passwordform' : passwordform, 'entries' : entries},context_instance=RequestContext(request))


@login_required
def admin_user_details(request,id):
	if request.user.has_perm("accounts.admin"):
		
		try:
			user = User.objects.get(id=id)
		except User.DoesNotExist:
			return HttpResponseNotFound()
			
		ago = datetime.now()-timedelta(days=182)
		entries = Entry.objects.filter(submitter=user,hidden=False,submittedtime__gte=ago).order_by('submittedtime')


		passwordform = PasswordChangeForm(user=user)
		profileform = UserProfileForm(user=user,instance=user.get_profile())

		return render_to_response("details.html",{'profileform' : profileform,'passwordform' : passwordform, 'entries' : entries},context_instance=RequestContext(request))
	
	return HttpResponseNotFound()
	

@login_required
def user_password_change(request):	
	if request.method == "POST":
		form = PasswordChangeForm(request.user,request.POST)
		if form.is_valid():
			form.save()
			messages.add_message(request,messages.SUCCESS,"Password changed")
		else:
			messages.add_message(request,messages.ERROR,"Password change failed. Wrong old password?")
			
	return HttpResponseRedirect(reverse('accounts.views.user_details'))

def search_users_json(request):
	if not request.user.has_perm('accounts.admin'):
		return HttpResponseNotFound()
		
	term = request.GET['term']

	
	users = User.objects.filter(Q(username__startswith=term)|Q(first_name__startswith=term)|Q(last_name__startswith=term))
	
	r = []
	for u in users:
		d = { 'label' : '%s (%s %s)' % (u.username,u.first_name,u.last_name),'id' : u.id }
		r.append(d)
		
	return HttpResponse(simplejson.dumps(r),mimetype="application/javascript")
	
	
	
