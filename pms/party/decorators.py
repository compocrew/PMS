
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from party.models import Party



def optional_party(view):
	def _deco(request,*args,**kwargs):
		if "party" in kwargs:
			request.party = kwargs.pop('party')

		return view(request,*args,**kwargs)
		
	return _deco

def require_party(view):
	def _deco(request,*args,**kwargs):
		if "party" not in kwargs:
			return HttpResponseRedirect(reverse('main.views.index'))
		else:
			request.party = kwargs.pop('party')
			try:
				request.party_instance = Party.objects.get(slug=request.party)
				if request.party_instance.maintenance and not request.user.is_staff:
					if request.path != reverse("main.views.party_index",args=[request.party_instance.slug]):
						return HttpResponseRedirect(reverse('main.views.index'))
			except Party.DoesNotExist:
				return HttpResponseRedirect(reverse('main.views.index'))
				
		return view(request,*args,**kwargs)
		
	return _deco