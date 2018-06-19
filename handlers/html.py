# Created by zhouwang on 2018/5/17.

from .base import permission, BaseRequestHandler

class Handler(BaseRequestHandler):
    @permission()
    def get(self, uri=None):
        html_path = '%s.html' % (uri.replace('/', '_') if uri else 'dashboard')
        self.render(html_path, **{'requser': self.requser})

class LoginHander(BaseRequestHandler):
    def get(self):
        self.logout()
        next_uri = self.get_argument('next', '/')
        self.render('login.html', **{'next': next_uri})