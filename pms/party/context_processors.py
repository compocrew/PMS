
from models import Party

def party(request):
	if hasattr(request,'party'):
		name = request.party
	else:
		name = "asm11"
		
	try:
		party = Party.objects.get(slug=name)
		if party.active or request.user.has_perm("party.admin"):
			return {'party' :  party }
	except Party.DoesNotExist:
		pass
	return { }