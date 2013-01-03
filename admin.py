from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import fix_path
import post_deploy
import handlers
import pageshandler

post_deploy.run_deploy_task()


application = webapp.WSGIApplication([
  ('/admin/', handlers.AdminHandler),
  ('/admin/newpost', handlers.PostHandler),
  ('/admin/post/(\d+)', handlers.PostHandler),
  ('/admin/regenerate', handlers.RegenerateHandler),
  ('/admin/flushmemcache', handlers.FlushMemCacheHandler),
  ('/admin/pagepost/(\w+)', pageshandler.PageHandler),
  ('/admin/post/delete/(\d+)', handlers.DeleteHandler)
])


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
