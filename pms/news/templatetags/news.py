
from django import template
from pms.news.models import NewsArticle
from siteconfig import settings

from party.models import Party

register = template.Library()

class NewsHeadlines(template.Node):
	def __init__(self,amount=5,party=None):
		self.amount = amount
		if party:
			self.partyslug = template.Variable(party)
		else: 
			self.partyslug = None
	def render(self,context):
		try:
			slug=None
			if self.partyslug:
				slug = self.partyslug.resolve(context)

			party = Party.objects.get(slug=slug)
			
		except Party.DoesNotExist:
			party = None
			
		items = NewsArticle.objects.filter(party=party).order_by('-date')[:self.amount]
		i = []
		for item in items:
			i.append(item)
		context['news_items'] = i

		return ''
		
		
def do_news_items(parser, token):
	# This version uses a regular expression to parse tag contents.
	try:
		tag_name, arg,party = token.split_contents()
	except ValueError:
		tag_name,arg = token.split_contents()
		party = None
		
	return NewsHeadlines(int(arg),party)


register.tag('news_articles',do_news_items)

