# Created by zhouwang on 2018/6/23.

from .base import BaseRequestHandler, permission
import tornado
import datetime
import time
import json
import logging

logger = logging.getLogger()


def query_valid(func):
    def _wrapper(self):
        error = {}
        self.mode = self.get_argument('mode', '')
        self.items = self.get_argument('items', '[]')
        now = datetime.datetime.now()

        if self.mode == 'interval':
            self.begin_time = self.get_argument('begin_time', '')
            self.end_time = self.get_argument('end_time', '')
            if not self.begin_time or not self.end_time:
                self.end_time = now.strftime('%Y-%m-%d %H:%M')
                self.begin_time = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
        elif self.mode == 'contrast':
            self.date = self.get_argument('date', '')
            self.dates = [date for date in self.date.split(',') if date] or [now.strftime('%Y-%m-%d')]
        else:
            error['mode'] = 'Invalid'

        try:
            self.items = json.loads(self.items)
        except:
            error['items'] = 'Must JSON'

        if error:
            return dict(code=400, msg='Bad POST data', error=error)
        return func(self)
    return _wrapper


class Handler(BaseRequestHandler):
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.mode = None
        self.items = None
        self.logfile_id = None
        self.logfile_path = None
        self.begin_time = None
        self.end_time = None
        self.dates = None
        self.monitor_items = []

    def get_interval_series(self, item):
        logfile, host, monitor_item = item.get('logfile'), item.get('host'), item.get('monitor_item')
        try:
            select_arg = (logfile, monitor_item, host, self.begin_time, self.end_time)
            self.cursor.execute(self.select_interval_sql, select_arg)
            name = '%s-%s-%s' % (logfile, host, monitor_item)
            data = self.cursor.fetchall()
        except Exception as e:
            logging.error('Get interval series: %s' % str(e))
            name = '%s-%s-%s: %s' % (logfile, host, monitor_item, str(e))
            data = []
        return dict(name=name, data=data)

    def get_contrast_series(self, item, date):
        logfile, host, monitor_item = item.get('logfile'), item.get('host'), item.get('monitor_item')
        try:
            select_arg = (time.mktime(time.strptime(date,'%Y-%m-%d')) * 1000,
                          logfile, monitor_item, host, '%s 00:00' % date, '%s 23:59' % date)
            self.cursor.execute(self.select_contrast_sql, select_arg)
            name = '%s-%s-%s-%s' % (date, logfile, host, monitor_item)
            data = self.cursor.fetchall()
        except Exception as e:
            logging.error('Get contrast series: %s' % str(e))
            name = '%s-%s-%s-%s: %s' % (date, logfile, host, monitor_item, str(e))
            data = []
        return dict(name=name, data=data)

    @permission()
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        response = yield tornado.gen.Task(self.query)
        self._write(response)

    @tornado.gen.coroutine
    @query_valid
    def query(self):
        series = []
        min_mktime, min_mktime = None, None
        if self.mode == 'interval':
            min_mktime = time.mktime(time.strptime(self.begin_time, '%Y-%m-%d %H:%M')) * 1000
            max_mktime = time.mktime(time.strptime(self.end_time, '%Y-%m-%d %H:%M')) * 1000
            for item in self.items:
                series.append(self.get_interval_series(item))
        elif self.mode == 'contrast':
            min_mktime, max_mktime = 0, 86340000
            for date in self.dates:
                for item in self.items:
                    series.append(self.get_contrast_series(item, date))

        data = dict(series=series, xAxis=dict(min=min_mktime, max=max_mktime))
        return dict(code=200, msg='Query successful', data=data)

    select_interval_sql = '''
        SELECT
          UNIX_TIMESTAMP(t3.count_time) * 1000,
          t3.count
        FROM
          logfile as t1, monitor_item as t2, monitor_count as t3
        WHERE 
          t1.name=%s AND 
          t2.logfile_id=t1.id AND 
          t2.name=%s AND
          t3.monitor_item_id=t2.id AND 
          t3.host=%s AND
          t3.count_time>=%s AND
          t3.count_time<=%s
    '''

    select_contrast_sql = '''
        SELECT
          UNIX_TIMESTAMP(t3.count_time) * 1000 - %s,
          t3.count
        FROM
          logfile as t1, monitor_item as t2, monitor_count as t3
        WHERE 
          t1.name=%s AND 
          t2.logfile_id=t1.id AND 
          t2.name=%s AND
          t3.monitor_item_id=t2.id AND 
          t3.host=%s AND
          t3.count_time>=%s AND
          t3.count_time<=%s
    '''