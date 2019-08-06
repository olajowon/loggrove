# Created by zhouwang on 2018/6/4.

from .base import BaseRequestHandler
import logging

logger = logging.getLogger()


class Handler(BaseRequestHandler):
    def post(self):
        response_data = self.logout()
        self._write(response_data)

    def logout(self):
        if self.session:
            try:
                with self.transaction():
                    self.cursor.execute(self.delete_session_sql, self.session.get('session_id'))
            except Exception as e:
                logger.error('Logout failed: %s' % str(e))
                return dict(code=500, msg='Logout failed')
        if self.session_id:
            self.clear_cookie('session_id')
        return dict(code=200, msg='Logout successful')

    delete_session_sql = 'DELETE FROM session WHERE session_id=%s'