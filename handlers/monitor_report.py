# Created by zhouwang on 2019/7/28.

from .base import BaseRequestHandler
import json
import logging

logger = logging.getLogger()


def report_valid(func):
    def _wrapper(self):
        error = {}
        host = self.get_argument('host', '')
        counts = self.get_argument('counts', '')

        if not host:
            error['host'] = 'Required'

        if not counts:
            error['counts'] = 'Required'
        else:
            try:
                counts = json.loads(counts)
            except:
                error['counts'] = 'Must JSON'

        if error:
            return {'code': 400, 'msg': 'Bad POST data', 'error': error}

        self.reqdata = dict(
            host=host,
            counts=counts,
        )
        return func(self)

    return _wrapper


class Handler(BaseRequestHandler):
    def post(self):
        response_data = self._report()
        self._write(response_data)

    @report_valid
    def _report(self):
        inserts = self.reqdata['counts']
        insert_sql = '''
          INSERT INTO 
            monitor_count (logfile_id, host, monitor_item_id, count, count_time) 
          VALUES
            (%s, %s, %s, %s, %s)
        '''

        try:
            with self.transaction():
                self.cursor.executemany(insert_sql, inserts)
        except Exception as e:
            logger.error('Report failed[%s]: %s' % (self.reqdata['host'], str(e)))
            return {'code': 500, 'msg': 'Report failed'}
        else:
            return {'code': 200, 'msg': 'Report successful'}
