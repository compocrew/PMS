from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.template.loader import render_to_string
from django.utils.http import int_to_base36

class UserAutoCompleteWidget(forms.MultiWidget):
	
	def __init__(self):
		widgets = (forms.HiddenInput(attrs={'id' : 'user'}),
					forms.TextInput(attrs={'id' : 'user_search'}))
		super(UserAutoCompleteWidget,self).__init__(widgets)
					
	def decompress(self,value):
		if value:
			return [value,None]
			
		return [None,None]

class UserAutocompleteFormField(forms.CharField):
	
	widget = UserAutoCompleteWidget
	
	def clean(self,value):
		value = super(UserAutocompleteField,self).clean(value)
		try:
			return User.objects.get(id=value)
		except User.DoesNotExist:
			raise forms.ValidationError('submitter id is invalid')

class PasswordResetForm(forms.Form):
	email = forms.EmailField(label="E-mail", max_length=75)

	def clean_email(self):
		"""
		Validates that an active user exists with the given e-mail address.
		"""
		email = self.cleaned_data["email"]
		self.users_cache = User.objects.filter(
								email__iexact=email,
								is_active=True
							)
		if len(self.users_cache) == 0:
			raise forms.ValidationError("That e-mail address doesn't have an associated user account. Are you sure you've registered?")
		return email

	def save(self, domain_override=None, email_template_name='registration/password_reset_email.html',
			 use_https=False, token_generator=default_token_generator, from_email=None, request=None):
		"""
		Generates a one-use only link for resetting password and sends to the user
		"""
		from django.core.mail import send_mail
		for user in self.users_cache:
			if not domain_override:
				current_site = get_current_site(request)
				site_name = current_site.name
				domain = current_site.domain
			else:
				site_name = domain = domain_override
			c = {
				'email': user.email,
				'domain': domain,
				'site_name': site_name,
				'uid': int_to_base36(user.id),
				'user': user,
				'token': token_generator.make_token(user),
				'protocol': use_https and 'https' or 'http',
			}
			send_mail("Password reset on %s" % site_name,
				render_to_string(email_template_name,c), from_email, [user.email])
