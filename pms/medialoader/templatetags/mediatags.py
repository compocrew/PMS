
from django.core.cache import cache
from django import template
import settings
from urlparse import urljoin
import hashlib
import os
from django.core.cache import cache

register = template.Library()


def get_file_hash(fname):
	stat = os.stat(fname)
	
	sha = hashlib.sha1()
	
	sha.update(str(stat.st_size))
	sha.update(str(stat.st_mtime))
	
	return sha.hexdigest()


class MediaType(object):
	def __init__(self,name):
		self.name = name
		self.reset()
		
	def reset(self):
		self.files = []

	def get_absolute_path(self,f):
		if f.startswith("http://") or f.startswith("https://") or f.startswith("/"):
			return f

		return urljoin(settings.MEDIA_URL,f)

	def get_file_path(self,f):
		return os.path.join(settings.MEDIA_ROOT,f)

	def add_file(self,f):
		if not f in self.files:
			self.files.append(f)
	
		
class MediaTypeCss(MediaType):
	def __init__(self):
		super(MediaTypeCss,self).__init__('css')

	def process(self):
		output=""
		if hasattr(settings,'NO_COMPRESS_CSS') and settings.NO_COMPRESS_CSS:
			for f in self.files:
				output += '<link rel="stylesheet" type="text/css" href="%s" />\n' % self.get_absolute_path(f)
			return output
		else:
			pass

class MediaTypeJs(MediaType):
	def __init__(self):
		super(MediaTypeJs,self).__init__('js')
		
	def process(self):
		output=""
		if hasattr(settings,'NO_COMPRESS_JS') and settings.NO_COMPRESS_JS:
			for f in self.files:
				output += '<script type="application/javascript" src="%s"></script>\n' % self.get_absolute_path(f)
		else:
			sha = hashlib.sha1()
			for f in self.files:
				sha.update(get_file_hash(self.get_file_path(f)))
			
			key = "/"+sha.hexdigest()+".js"
			if not cache.get(key):
				print "update cache %s" % key
				content = ""
				for f in self.files:
					openfile = open(self.get_file_path(f))
					content += openfile.read()
					
				cache.set(key,content,60*100)
				
			output = '<script type="application/javascript" src="/cache/%s"></script>\n' % key 
			
		return output
			
				
mediatypes = {
	'js' : MediaTypeJs(),
	'css' : MediaTypeCss(),
}

#https://psa6.valueframe.com//2.0/matkalasku_uusi/?ID=8972&henkilo=1088


@register.simple_tag
def mediafile(category,f):
	if category in mediatypes:
		mediatypes[category].add_file(f)
	return ''
	
	
@register.simple_tag
def include_mediafiles(category):
	if category in mediatypes:
		mediatype = mediatypes[category]
		output=mediatype.process()
		mediatype.reset()
		
		return output

	return ''
	