import webapp2
import pageshandler
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


app = webapp2.WSGIApplication([
                                     ('/admin/pages/newpost',
                                      pageshandler.PageHandler),
    ('/infopage/(.*)', pageshandler.PageGenerator),

])
