from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import unicodedata
import config
import os
import re


def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
    return re.sub('[^a-zA-Z0-9-]+', '-', s).strip('-')


def format_post_path(post, num):
    slug = slugify(post.title)
    if num > 0:
        slug += "-" + str(num)
    return config.post_path_format % {
        'slug': slug,
        'year': post.published.year,
        'month': post.published.month,
        'day': post.published.day,
    }


def render_template(template_name, template_vals=None, theme=None):
    if not template_vals:
        template_vals = {}
    template_vals.update({
        'template_name': template_name,
        'config': config,
        'devel': os.environ['SERVER_SOFTWARE'].startswith('Devel'),
    })
    template_path = os.path.join(
        "themes", theme or config.theme, template_name)
    return template.render(template_path, template_vals)


def _get_all_paths():
    import static
    keys = []
    q = static.StaticContent.all(keys_only=True).filter('indexed', True)
    cur = q.fetch(1000)
    while len(cur) == 1000:
        keys.extend(cur)
        q = static.StaticContent.all(keys_only=True)
        q.filter('indexed', True)
        q.filter('__key__ >', cur[-1])
        cur = q.fetch(1000)
    keys.extend(cur)
    return [x.name() for x in keys]


def _regenerate_sitemap():
    import static
    import gzip
    from StringIO import StringIO
    paths = _get_all_paths()
    rendered = render_template('sitemap.xml', {'paths': paths})
    static.set('/sitemap.xml', rendered, 'application/xml', False)
    s = StringIO()
    gzip.GzipFile(fileobj=s, mode='wb').write(rendered)
    s.seek(0)
    renderedgz = s.read()
    static.set('/sitemap.xml.gz', renderedgz, 'application/x-gzip', False)
    if config.google_sitemap_ping:
        ping_googlesitemap()


def ping_googlesitemap():
    import urllib
    from google.appengine.api import urlfetch
    google_url = 'http://www.google.com/webmasters/tools/ping?sitemap=http://' + \
        config.host + '/sitemap.xml.gz'
    response = urlfetch.fetch(google_url, '', urlfetch.GET)
    if response.status_code / 100 != 2:
        raise Warning("Google Sitemap ping failed",
                      response.status_code, response.content)


def format_page_path(post):
    slug = slugify(post.title)
    return config.page_path_format % {
        'slug': slug
    }
