# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect,HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse

from models import NewsArticle,ArticleForm

def news(request):
	return render_to_response("news.html",context_instance=RequestContext(request))


def admin(request,article,success=False,status=None):
	try:
		article = NewsArticle.objects.get(id=article)
	except NewsArticle.DoesNotExist:
		return HttpResponseNotFound()

	if request.method == "POST" and not success:
		form = ArticleForm(request.POST,instance=article)
		if form.is_valid():
			form.save()
			success=True
			status = 'News updated'
	else:
		form = ArticleForm(instance=article)

	return render_to_response("news_adminform.html",{'form' : form,'success' : success,'article' : article,'status' : status},context_instance=RequestContext(request))

def create(request):
	success = False
	try:
		if request.method == "POST":
			form = ArticleForm(request.POST)
			if form.is_valid():
				try:
					article = form.save(commit=False)
					article.user = request.user
					article.save()
				except Exception as e:
					print e
				success=True
				return admin(request,article.id,True,'News created')
		else:
			form = ArticleForm()
	
		return render_to_response("news_createform.html",{'form' : form,'success' : success},context_instance=RequestContext(request))
	except Exception as e:
		print e

def delete(request,article):
	try:
		article = NewsArticle.objects.get(id=article)
	except Article.DoesNotExist:
		return HttpResponseNotFound()
	
	article.delete()
	
	return HttpResponse("News deleted")
	