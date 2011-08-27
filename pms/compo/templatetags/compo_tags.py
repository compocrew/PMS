
from django import template
from compo.models import Competition

register = template.Library()

class UserHasVoted(template.Node):
	def __init__(self,compo,user,var):
		self.compo = template.Variable(compo)
		self.user = template.Variable(user)
		self.var = var
	def render(self,context):

		compo = self.compo.resolve(context)
		user = self.user.resolve(context)
		context[self.var]=compo.user_has_voted(user)
		
		return ''
		
		
def do_user_voted(parser, token):
	# This version uses a regular expression to parse tag contents.
	tag_name, arg,user,var = token.split_contents()
	
	return UserHasVoted(arg,user,var)


@register.simple_tag(takes_context=True)
def get_jury_points(context,arg1,arg2):
	key = "points_%d_entry_%d" % (arg1,arg2)
	points = context['jury_points']
	if key in points:
		return points[key]
	return ""

@register.simple_tag(takes_context=True)
def get_jury_points_class(context,arg1,arg2):
	if not 'jury_points_class' in context:
		return ""

	key = "points_%d_entry_%d" % (arg1,arg2)
	points = context['jury_points_class']
	if key in points:
		return points[key]
	return ""


	
register.tag('user_voted',do_user_voted)

