
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

import settings

class Party(object):
	
	def __init__(self):
		pass
	
	def process_view(self,request,view_func,view_args,view_kwargs):
		for excl in settings.PARTY_REDIRECT_EXCLUDE_URLS:
			if request.path.startswith(excl):
				return None

		if hasattr(request,"requireparty"):
			if "party" not in view_kwargs:
#				print "requireparty"
				return HttpResponseRedirect(reverse('party.views.index'))
		print "noparty"
		# 	return None
		# 	
		# if "party" in request.session:
		# 	print "party session"
		# 	return None
		# 	
		# 
		# return HttpResponseRedirect(reverse('party.views.index'))
		return None
		
	
	# def process_request(self,request):
	# 	return None
	# 	
	# 	excluded = (
	# 		reverse('party.views.select',args=["1"]),
	# 		reverse('party.views.index'),
	# 	)
	# 	if "party" in request.session or request.path in excluded:
	# 		return None
	# 
	# 	for excl in settings.PARTY_REDIRECT_EXCLUDE_URLS:
	# 		if request.path.startswith(excl):
	# 			return None
	# 			
	# 	
	# 	return HttpResponseRedirect(reverse('party.views.index'))