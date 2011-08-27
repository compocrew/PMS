
from django.core.urlresolvers import reverse

settings = {
	'sitetitle' : 'PMS',
#	'sitelogo' : '/media/images/pms-logo.png',
	'privacy_link' : 'http://www.assembly.org/asmorg/legal/privacy',
	'require_ticket' : True,

}

sections = (
	{ 'name' : 'Frontpage', 'url' : reverse('main.views.index') },
	{ 'name' : 'Competitions', 'url' : '/compos/' },
	{ 'name' : 'Sports / Sponsored', 'url' : '/sport/' },
	{ 'name' : 'Schedule', 'url' : '/schedules/' },
)
