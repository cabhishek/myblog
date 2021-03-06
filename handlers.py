from django import newforms as forms
from google.appengine.ext.db import djangoforms
from google.appengine.ext import deferred
from google.appengine.ext import webapp
from google.appengine.api import memcache
import models
import post_deploy
import utils
import datetime
import os


class PostForm(djangoforms.ModelForm):
    title = forms.CharField(widget=forms.Textarea(
        attrs={'id': 'name', 'rows': 5, 'cols': 50}))
    body = forms.CharField(widget=forms.Textarea(attrs={
        'id': 'message',
        'rows': 20,
        'cols': 50}))
    tags = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'cols': 20}))
    draft = forms.BooleanField(required=False)

    class Meta:
        model = models.BlogPost
        fields = ['title', 'body', 'tags']


def with_post(fun):
    def decorate(self, post_id=None):
        post = None
        if post_id:
            post = models.BlogPost.get_by_id(int(post_id))
            if not post:
                self.error(404)
                return
        fun(self, post)
    return decorate


class BaseHandler(webapp.RequestHandler):
    def render_to_response(self, template_name, template_vals=None, theme=None):
        if not template_vals:
            template_vals = {}
        template_vals.update({
            'path': self.request.path,
            'handler_class': self.__class__.__name__,
        })
        template_name = os.path.join("admin", template_name)
        self.response.out.write(
            utils.render_template(template_name, template_vals,
                                  theme))


class AdminHandler(BaseHandler):

    def get(self):
        offset = int(self.request.get('start', 0))
        count = int(self.request.get('count', 20))
        posts = models.BlogPost.all().order('-published').fetch(count, offset)
        pagePosts = models.PagePost.all()
        template_vals = {
            'offset': offset,
            'count': count,
            'last_post': offset + len(posts) - 1,
            'prev_offset': max(0, offset - count),
            'next_offset': offset + count,
            'posts': posts,
            'pagePosts': pagePosts
        }
        self.render_to_response("index.html", template_vals)


class PostHandler(BaseHandler):

    def render_form(self, form):
        self.render_to_response("edit.html", {'form': form})

    @with_post
    def get(self, post):
        self.render_form(PostForm(
            instance=post,
            initial={'draft': post and post.published is None}))

    @with_post
    def post(self, post):
        form = PostForm(data=self.request.POST, instance=post,
                        initial={'draft': post and post.published is None})
        if form.is_valid():
            post = form.save(commit=False)
            if form.clean_data['draft']:
                post.put()
            else:
                post.published = post.published or datetime.datetime.now()
                post.publish()
            self.render_to_response("published.html", {
                'post': post,
                'draft': form.clean_data['draft']})
        else:
            self.render_form(form)


class DeleteHandler(BaseHandler):

    @with_post
    def post(self, post):
        if post.path:  # published post
            post.remove()
        else:  # Draft
            post.delete()
        self.render_to_response("deleted.html")


class RegenerateHandler(BaseHandler):

    def post(self):
        regen = post_deploy.PostRegenerator()
        deferred.defer(regen.regenerate)
        deferred.defer(post_deploy.post_deploy, post_deploy.BLOGGART_VERSION)
        self.render_to_response("regenerating.html")


class FlushMemCacheHandler(BaseHandler):

    def post(self):
        memcache.flush_all()
