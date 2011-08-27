from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt,csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import base36_to_int
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from forms import PasswordResetForm
# 4 views for password reset:
# - password_reset sends the mail
# - password_reset_done shows a success message for the above
# - password_reset_confirm checks the link the user clicked and
#	prompts for a new password
# - password_reset_complete shows a success message for the above

@csrf_protect
def password_reset(request,
				   template_name='lost_password.html',
				   email_template_name='lost_password_email.txt',
				   password_reset_form=PasswordResetForm,
				   token_generator=default_token_generator,
				   post_reset_redirect=None,
				   from_email="pms@assembly.org",
				   extra_context=None):
	if post_reset_redirect is None:
		post_reset_redirect = reverse('accounts.extra_views.password_reset_done')
	if request.method == "POST":
		form = password_reset_form(request.POST)
		if form.is_valid():
			opts = {
				'use_https': request.is_secure(),
				'token_generator': token_generator,
				'from_email': from_email,
				'email_template_name': email_template_name,
				'request': request,
			}
			form.save(**opts)
			return HttpResponseRedirect(post_reset_redirect)
	else:
		form = password_reset_form()
	context = {
		'form': form,
	}
	context.update(extra_context or {})
	return render_to_response(template_name, context,
							  context_instance=RequestContext(request))

def password_reset_done(request,
						template_name='lost_password_done.html',
						current_app=None, extra_context=None):
	context = {}
	context.update(extra_context or {})
	return render_to_response(template_name, context,
							  context_instance=RequestContext(request, current_app=current_app))

# Doesn't need csrf_protect since no-one can guess the URL
@never_cache
def password_reset_confirm(request, uidb36=None, token=None,
						   template_name='lost_password_confirm.html',
						   token_generator=default_token_generator,
						   set_password_form=SetPasswordForm,
						   post_reset_redirect=None,
						   current_app=None, extra_context=None):
	"""
	View that checks the hash in a password reset link and presents a
	form for entering a new password.
	"""
	assert uidb36 is not None and token is not None # checked by URLconf
	if post_reset_redirect is None:
		post_reset_redirect = reverse('accounts.views.login_user')
	try:
		uid_int = base36_to_int(uidb36)
		user = User.objects.get(id=uid_int)
	except (ValueError, User.DoesNotExist):
		user = None

	if user is not None and token_generator.check_token(user, token):
		validlink = True
		if request.method == 'POST':
			form = set_password_form(user, request.POST)
			if form.is_valid():
				form.save()
				messages.add_message(request,messages.SUCCESS,"Your password has been changed.")
				return HttpResponseRedirect(post_reset_redirect)
		else:
			form = set_password_form(None)
	else:
		validlink = False
		form = None
	context = {
		'form': form,
		'validlink': validlink,
	}
	context.update(extra_context or {})
	return render_to_response(template_name, context,
							  context_instance=RequestContext(request, current_app=current_app))

