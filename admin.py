import webapp2
import post_deploy
import pageshandler
import handlers

post_deploy.run_deploy_task()


app = webapp2.WSGIApplication([
  ('/admin/', handlers.AdminHandler),
  ('/admin/newpost', handlers.PostHandler),
  ('/admin/post/(\d+)', handlers.PostHandler),
  ('/admin/regenerate', handlers.RegenerateHandler),
  ('/admin/flushmemcache', handlers.FlushMemCacheHandler),
  ('/admin/pagepost/(\w+)', pageshandler.PageHandler),
  ('/admin/post/delete/(\d+)', handlers.DeleteHandler)
])
