
from models import Party

def get_party(request):
	if hasattr(request,'party'):
		try:
			party = Party.objects.get(slug=request.party)
			return party
		except Party.DoesNotExist:
			pass
			
	return None
	
	