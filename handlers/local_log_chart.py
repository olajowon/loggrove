# Created by zhouwang on 2018/6/23.

from .base import BaseRequestHandler, permission
import datetime
import time

def get_valid(func):
    def _wrapper(self):
        error = {}
        self.mode = self.get_argument('mode', 'interval')
        self.local_log_file_id = self.get_argument('local_log_file_id', '')
        self.monitor_item_ids = [item_id for item_id in self.get_arguments('monitor_item_id') if item_id]
        now = datetime.datetime.now()
        if self.mode == 'interval':
            self.begin_time = self.get_argument('begin_time', '')
            self.end_time = self.get_argument('end_time', '')

            if not self.begin_time or not self.end_time:
                self.end_time = now.strftime('%Y-%m-%d %H:%M')
                self.begin_time = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
        elif self.mode == 'contrast':
            self.dates = [date for date in self.get_arguments('total') if date] or [now.strftime('%Y-%m-%d')]

        if not self.local_log_file_id:
            error['local_log_file_id'] = '日志文件是必填项'
        else:
            select_sql = 'SELECT id,path FROM local_log_file WHERE id="%s"' % self.local_log_file_id
            count = self.mysqldb_cursor.execute(select_sql)
            if count:
                self.local_log_file_id, self.local_log_file_path = self.mysqldb_cursor.fetchone()
                if self.monitor_item_ids:
                    if '0' in self.monitor_item_ids and len(self.monitor_item_ids)==1:
                        self.monitor_items = ((0, 'total'),)
                    else:
                        select_sql = 'SELECT id, search_pattern FROM local_log_monitor_item ' \
                                     'WHERE local_log_file_id="%s" AND id IN (%s)' % \
                                     (self.local_log_file_id, ','.join(self.monitor_item_ids))
                        self.mysqldb_cursor.execute(select_sql)
                        self.monitor_items = self.mysqldb_cursor.fetchall()

                        if '0' in self.monitor_item_ids:
                            self.monitor_items = ((0, 'total'),) + self.monitor_items
                        elif not self.monitor_items:
                            error['monitor_item_id'] = '监控项无效'
                else:
                    select_sql = 'SELECT id, search_pattern FROM local_log_monitor_item WHERE local_log_file_id="%s"' % \
                                 self.local_log_file_id
                    self.mysqldb_cursor.execute(select_sql)
                    self.monitor_items = ((0, 'total'),) + self.mysqldb_cursor.fetchall()

            else:
                error['local_log_file_id'] = '日志文件不存在'

        if error:
            self._write({'code': 400, 'msg': 'Bad POST data', 'error': error})
            return
        return func(self)
    return _wrapper


class Handler(BaseRequestHandler):
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.mode = None
        self.local_log_file_id = None
        self.local_log_file_path = None
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
                      local_log_monitor_count
                    WHERE 
                      count_time>='%s' AND count_time<='%s' AND monitor_item_id='%s' AND local_log_file_id='%d'
                    ORDER BY count_time
                ''' % (self.begin_time, self.end_time, item_id, self.local_log_file_id)
                self.mysqldb_cursor.execute(select_sql)
                results = self.mysqldb_cursor.fetchall()
                series.append({'name': search_pattern, 'data': results,})
        elif self.mode == 'contrast':
            min_mktime = time.mktime(time.strptime('1970-1-1 00:00', '%Y-%m-%d %H:%M')) * 1000
            max_mktime = time.mktime(time.strptime('1970-1-1 23:59', '%Y-%m-%d %H:%M')) * 1000
            for date in self.dates:
                for item_id, search_pattern in self.monitor_items:
                    select_sql = '''
                        SELECT
                          UNIX_TIMESTAMP(date_format(count_time, "1970-1-1 %%H:%%i:%%s")) * 1000,
                          count
                        FROM    
                          local_log_monitor_count
                        WHERE 
                          count_time>='%s' AND count_time<='%s' AND monitor_item_id='%s' AND local_log_file_id='%d'
                        ORDER BY count_time
                    ''' % ('%s 00:00' % date, '%s 23:59' % date, item_id, self.local_log_file_id)
                    self.mysqldb_cursor.execute(select_sql)
                    results = self.mysqldb_cursor.fetchall()
                    series.append({'name': '%s %s' % (date, search_pattern), 'data': results})

        data.append({'series' : series, 'xAxis':{'min':min_mktime, 'max':max_mktime}})
        self._write({'code': 200, 'msg': 'Query successful', 'data': data})

