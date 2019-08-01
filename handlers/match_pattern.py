# Created by zhouwang on 2019/7/17.

from .base import BaseRequestHandler, permission
import datetime
import re
import logging

logger = logging.getLogger()

def get_valid(func):
    def _wrapper(self):
        error = {}
        logfile = self.get_argument('logfile', '')
        match = self.get_argument('match', '')

        if not logfile:
            error['logfile'] = 'Required'
        else:
            select_sql = 'SELECT * FROM logfile WHERE name="%s"' % logfile
            self.cursor.execute(select_sql)
            logfile = self.cursor.dictfetchone()
            if not logfile:
                error['logfile'] = 'Not exist'

        if error:
            self._write(dict(code=400, msg='Bad GET param', error=error))
            return

        self.cleaned_param = dict(
            logfile=logfile,
            match=match,
        )

        return func(self)
    return _wrapper


class Handler(BaseRequestHandler):
    @permission()
    @get_valid
    def get(self, *args, **kwargs):
        self.select_sql = 'SELECT search_pattern FROM monitor_item WHERE logfile_id=%d' % \
                          self.cleaned_param['logfile']['id']
        self.select_sql += (' AND search_pattern like "%%%s%%"' % self.cleaned_param['match']
                            if self.cleaned_param['match'] else '')

        self.cursor.execute(self.select_sql)
        results = self.cursor.fetchall()
        match_pattern = [result[0] for result in results]
        response_data = dict(code=200, msg='Query Successful', data=match_pattern)
        return self._write(response_data)