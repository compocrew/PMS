
from party.models import Party
from party.util import get_party

def user_info(request):
	d = dict()
	if request.user.is_authenticated():
		try:
			profile = request.user.get_profile()

			d['require_ticket']=False
			if hasattr(request,'party'):
				d['require_ticket']=get_party(request).ticket_required
				d['user_has_ticket'] = request.user.get_profile().hasPartyTicket(Party.objects.get(slug=request.party))

			d['is_organizer'] = request.user.has_perm('accounts.organizer')
		except:
			pass
	return d
