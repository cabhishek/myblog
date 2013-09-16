import datetime
import logging
import os

from google.appengine.api import memcache
from google.appengine.datastore import entity_pb
from google.appengine.ext import db
from google.appengine.ext import webapp
import models
import utils
import config
import generators
from django import newforms as forms
from google.appengine.ext.db import djangoforms

""" form for writing different personal pages"""


class PageForm(djangoforms.ModelForm):
    title = forms.CharField(widget=forms.Textarea(
        attrs={'id': 'name', 'rows': 5, 'cols': 50}))
    body = forms.CharField(widget=forms.Textarea(attrs={
                                                 'id': 'message',
                                                 'rows': 20,
                                                 'cols': 50}))

    class Meta:
        model = models.PagePost
        fields = ['title', 'body']


def with_pagepost(func):
    def decorate(self, post_key=None):
        post = None
        if post_key:
            post = models.PagePost.get_by_key_name(post_key)
            if not post:
                self.errr(404)
                return
        func(self, post)
    return decorate


class BaseHandler(webapp.RequestHandler):

    def render_to_response(self, template_name, template_folder_name, template_vals=None, theme=None):
        if not template_vals:
            template_vals = {}
        template_vals.update({
            'path': self.request.path,
            'handler_class': self.__class__.__name__,
        })
        template_name = os.path.join(template_folder_name, template_name)
        self.response.out.write(
            utils.render_template(template_name, template_vals,
                                  theme))

"""Handles form posts"""


class PageHandler(BaseHandler):

    def render_form(self, form):
        self.render_to_response("edit.html", "admin", {'form': form})

    @with_pagepost
    def get(self, post):
        self.render_form(PageForm(instance=post))

    @with_pagepost
    def post(self, post):
        form = PageForm(data=self.request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.path = utils.format_page_path(post)
            page_key = post.path[len(config.page_path):]
            """construct a new PagePost for persistence"""
            content = models.PagePost(
                key_name=page_key, path=post.path, title=post.title, body=post.body)
            content.put()
            memcache.replace(page_key, db.model_to_protobuf(content).Encode())
            self.render_to_response("published.html", "admin", {'post': post})
        else:
            self.render_form(form)

""" Generates personal pages """


class PageGenerator(webapp.RequestHandler):

    def render_page(self, values):
        self.response.out.write(utils.render_template("page.html", values,
                                                      "default"))

    def getInfoPage(self, pageKey):
        entity = memcache.get(pageKey)
        if entity:
            entity = db.model_from_protobuf(entity_pb.EntityProto(entity))
        else:
            entity = models.PagePost.get_by_key_name(pageKey)
            if entity:
                memcache.set(pageKey, db.model_to_protobuf(entity).Encode())

        return entity

    def output_content(self, page):
        template_vals = {
            'page': page,
            'tags': generators.TagGenerator.get_tags(),
            'pages': generators.PagesGenerator.get_pages()
        }
        self.render_page(template_vals)

    def get(self, pageKey):
        page = self.getInfoPage(pageKey)
        if not page:
            self.error(304)
            return
        self.output_content(page)
