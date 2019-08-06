# Created by zhouwang on 2019/7/26.

from .base import BaseRequestHandler
import logging

logger = logging.getLogger()

def get_valid(func):
    def _wrapper(self):
        error = {}
        host = self.get_argument('host', '')

        if not host:
            error['host'] = 'Required'

        if error:
            self._write({'code': 400, 'msg': 'Bad GET param', 'error': error})
            return

        self.reqdata = dict(host=host)

        return func(self)
    return _wrapper


class Handler(BaseRequestHandler):
    @get_valid
    def get(self):
        host_logfiles = []
        host = self.reqdata.get('host')
        try:
            self.cursor.execute(self.select_logfile_sql, host)
            logfiles = self.cursor.dictfetchall()
            for logfile in logfiles:
                self.cursor.execute(self.select_monitor_sql, logfile['id'])
                monitor_items = self.cursor.dictfetchall()
                logfile['monitor_items'] = monitor_items
                host_logfiles.append(logfile)
        except Exception as e:
            response_data = dict(code=500, msg='Query failed', detail=str(e))
        else:
            response_data = dict(code=200, msg='Query successful', data=host_logfiles)
        self._write(response_data)

    select_logfile_sql = '''SELECT t2.id as id, t2.path as path, t2.name as name, t2.monitor_choice as monitor_choice
        FROM logfile_host t1, logfile t2 WHERE t1.host=%s and t1.logfile_id=t2.id
    '''

    select_monitor_sql = '''SELECT id, name, match_regex, alert, intervals, expression, webhook
        FROM monitor_item WHERE logfile_id=%s 
    '''