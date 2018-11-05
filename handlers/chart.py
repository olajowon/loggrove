# Created by zhouwang on 2018/6/23.

from .base import BaseRequestHandler, permission
import datetime
import time


def get_valid(func):
    def _wrapper(self):
        error = {}
        self.mode = self.get_argument('mode', 'interval')
        self.logfile_id = self.get_argument('logfile_id', '')
        self.monitor_item_ids = [item_id for item_id in self.get_arguments('monitor_item_id') if item_id]
        now = datetime.datetime.now()
        if self.mode == 'interval':
            self.begin_time = self.get_argument('begin_time', '')
            self.end_time = self.get_argument('end_time', '')

            if not self.begin_time or not self.end_time:
                self.end_time = now.strftime('%Y-%m-%d %H:%M')
                self.begin_time = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
        elif self.mode == 'contrast':
            self.dates = [date for date in self.get_arguments('date') if date] or [now.strftime('%Y-%m-%d')]

        if not self.logfile_id:
            error['logfile_id'] = 'Required'
        else:
            select_sql = 'SELECT id,path FROM logfile WHERE id="%s"' % self.logfile_id
            count = self.mysqldb_cursor.execute(select_sql)
            if count:
                self.logfile_id, self.logfile_path = self.mysqldb_cursor.fetchone()
                if self.monitor_item_ids:
                    if '0' in self.monitor_item_ids and len(self.monitor_item_ids) == 1:
                        self.monitor_items = ((0, 'total'),)
                    else:
                        select_sql = 'SELECT id, search_pattern FROM monitor_item ' \
                                     'WHERE logfile_id="%s" AND id IN (%s)' % \
                                     (self.logfile_id, ','.join(self.monitor_item_ids))
                        self.mysqldb_cursor.execute(select_sql)
                        self.monitor_items = self.mysqldb_cursor.fetchall()

                        if '0' in self.monitor_item_ids:
                            self.monitor_items = ((0, 'total'),) + self.monitor_items
                        elif not self.monitor_items:
                            error['monitor_item_id'] = 'Invalid'
                else:
                    select_sql = 'SELECT id, search_pattern FROM monitor_item WHERE logfile_id="%s"' % \
                                 self.logfile_id
                    self.mysqldb_cursor.execute(select_sql)
                    self.monitor_items = ((0, 'total'),) + self.mysqldb_cursor.fetchall()

            else:
                error['logfile_id'] = 'Not exist'

        if error:
            self._write({'code': 400, 'msg': 'Bad POST data', 'error': error})
            return
        return func(self)
    return _wrapper


class Handler(BaseRequestHandler):
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.mode = None
        self.logfile_id = None
        self.logfile_path = None
        self.begin_time = None
        self.end_time = None
        self.dates = None
        self.monitor_items = []
        self.mysqldb_cursor.close()
        self.mysqldb_cursor = self.mysqldb_conn.cursor()

    @permission()
    @get_valid
    def get(self):
        data = []
        series = []
        if self.mode == 'interval':
            min_mktime = time.mktime(time.strptime(self.begin_time, '%Y-%m-%d %H:%M')) * 1000
            max_mktime = time.mktime(time.strptime(self.end_time, '%Y-%m-%d %H:%M')) * 1000

            for item_id, search_pattern in self.monitor_items:
                select_sql = '''
                    SELECT
                      UNIX_TIMESTAMP(count_time) * 1000,
                      count
                    FROM    
                      monitor_count
                    WHERE 
                      count_time>='%s' AND count_time<='%s' AND monitor_item_id='%s' AND logfile_id='%d'
                    ORDER BY count_time
                ''' % (self.begin_time, self.end_time, item_id, self.logfile_id)
                self.mysqldb_cursor.execute(select_sql)
                results = self.mysqldb_cursor.fetchall()
                series.append({'name': search_pattern, 'data': results})
        elif self.mode == 'contrast':
            min_mktime = time.mktime(time.strptime('2000-1-1 00:00', '%Y-%m-%d %H:%M')) * 1000
            max_mktime = time.mktime(time.strptime('2000-1-1 23:59', '%Y-%m-%d %H:%M')) * 1000
            for date in self.dates:
                for item_id, search_pattern in self.monitor_items:
                    select_sql = '''
                        SELECT
                          UNIX_TIMESTAMP(date_format(count_time, "2000-1-1 %%H:%%i:%%s")) * 1000,
                          count
                        FROM    
                          monitor_count
                        WHERE 
                          count_time>='%s' AND count_time<='%s' AND monitor_item_id='%s' AND logfile_id='%d'
                        ORDER BY count_time
                    ''' % ('%s 00:00' % date, '%s 23:59' % date, item_id, self.logfile_id)
                    self.mysqldb_cursor.execute(select_sql)
                    results = self.mysqldb_cursor.fetchall()
                    series.append({'name': '%s %s' % (date, search_pattern), 'data': results})

        data.append({'series': series, 'xAxis': {'min': min_mktime, 'max': max_mktime}})
        self._write({'code': 200, 'msg': 'Query successful', 'data': data})
