# Created by zhouwang on 2018/5/17.

from .base import permission, BaseRequestHandler


class Handler(BaseRequestHandler):
    @permission()
    def get(self, uri=None):
        htmls = {
            'logfiles': 'logfile.html',
            'users': 'user.html',
            'read': 'read.html',
            'keepread': 'keepread.html',
            'charts': 'chart.html',
            'auditlogs': 'auditlog.html'
        }
        self.render(htmls.get(uri) if uri else 'dashboard.html', **{'requser': self.requser})


class LoginHander(BaseRequestHandler):
    def get(self):
        self.logout()
        next_uri = self.get_argument('next', '/')
        self.render('login.html', **{'next': next_uri})
