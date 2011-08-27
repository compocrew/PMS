
from models import Competition


def get_compo_schedule_times(compo):
	
	d = {
		'update_end' : compo.update_end,
		'vote_start' : compo.vote_start,
	}
	return d
	
	
