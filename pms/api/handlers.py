
from piston.handler import BaseHandler
from piston.utils import rc, throttle
from piston.doc import generate_doc
from compo.models import *
from entry.models import *
from party.models import *
from schedule.models import *

class PartyHandler(BaseHandler):
	allowed_methods = ('GET',)
	fields = ('name','slug','start_date','end_date','url','privacy_link')
	model = Party

	def read(self,request):
		return Party.objects.filter(active=True)


class CompoHandler(BaseHandler):
	allowed_methods = ('GET',)
	fields = ('name','slug','show_credits','description','submit_start','submit_end','vote_start','vote_end',('party',('name','slug')),('category',('name',)))
	model = Competition
	
	def read(self,request,slug):
		party = Party.objects.get(slug=slug)
		return Competition.objects.filter(party=party,hidden=False)

			
class EntryHandler(BaseHandler):
	allowed_methods = ('GET','PUT')
	fields = ('id','name','credits','preview_link','comments',('compo',('name','slug')))
	model = Entry


	def _censorEntry(self,compo,entry):
#		if compo.show_credits:
#			entry.name = "%s by %s" % (entry.name,entry.credits)
		return entry
		
	def _censor(self,compo,entries):
		nentries = []
		for entry in entries:
			nentries.append(self._censorEntry(compo,entry))
		
		return nentries
		
	def read(self,request,partyslug,slug,id=None):
		if request.user.has_perm('entry.read_api'):
			party = Party.objects.get(slug=partyslug)
			compo = Competition.objects.get(party=party,slug=slug,hidden=False)
			if not id:
				return self._censor(compo,Entry.objects.filter(compo=compo,hidden=False,qualification=Qualification.Qualified))
			else:
				return self._censorEntry(compo,Entry.objects.get(compo=compo,hidden=False,id=id,qualification=Qualification.Qualified))


	def update(self,request,partyslug,slug,id):
		party = Party.objects.get(slug=partyslug)
		compo = Competition.objects.get(party=party,hidden=False,slug=slug)

		if request.user.has_perm('entry.update_preview'):
			entry = Entry.objects.get(compo=compo,hidden=False,id=id)
		
			entry.preview_link = request.PUT.get('preview_link',None)
			entry.save()
		
			return self._censorEntry(compo,entry)
		
		return rc.FORBIDDEN
		
	
class ScheduleHandler(BaseHandler):
	allowed_methods = ('GET',)
	fields = ('name','slug','start_date','end_date','url','privacy_link')
	exclude = ('hidden')
	model = Event

	def read(self,request,party):
		party = Party.objects.get(slug=party)
		schedules = Schedule.objects.filter(party=party)
		
		events = []
	
		for schedule in schedules:
			e = schedule.events.filter(hidden=False)
			

		