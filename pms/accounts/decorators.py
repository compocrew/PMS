
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect,HttpResponseNotFound

from party.util import get_party


class NoTicketError(Exception):
	pass

class NoPermissionError(Exception):
	pass

def ticket_required(func):
	def check_ticket(request,*args,**kwargs):
		try:
		 	profile = request.user.get_profile()
			require_ticket = False
			party = get_party(request)
			if party:
				require_ticket = party.ticket_required

			if require_ticket:
				raise NoTicketError
		except NoTicketError:
			return HttpResponseRedirect(reverse('accounts.views.tickets'))
			
		return func(request,*args,**kwargs)
		
	return check_ticket
