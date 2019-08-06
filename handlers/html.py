# Created by zhouwang on 2018/5/17.

from .base import permission, BaseRequestHandler


class Handler(BaseRequestHandler):
    @permission()
    def get(self, uri=None):
        html_map = dict(
            logfiles='logfile.html',
            read='read.html',
            keepread='keepread.html',
            charts='chart.html',
            auditlogs='auditlog.html',
            users='user.html'
        )
        html = html_map.get(uri) if uri else 'dashboard.html'
        self.render(html, **{'requser': self.requser})


class LoginHander(BaseRequestHandler):
    def get(self):
        next_uri = self.get_argument('next', '/')
        self.render('login.html', **{'next': next_uri})
