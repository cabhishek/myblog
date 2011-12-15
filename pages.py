from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import fix_path
import pageshandler

application = webapp.WSGIApplication([
  ('/admin/pages/newpost', pageshandler.PageHandler),
  ('/infopage/(.*)', pageshandler.PageGenerator),
  
])


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()

