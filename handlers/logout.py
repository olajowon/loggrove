# Created by zhouwang on 2018/6/4.

from .base import BaseRequestHandler

class Handler(BaseRequestHandler):
    def post(self):
        self._write(self.logout())
