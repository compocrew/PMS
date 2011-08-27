

import siteconfig


def site_config(request):
	return siteconfig.settings
	
def site_sections(request):
	return {'sections' : siteconfig.sections }
	