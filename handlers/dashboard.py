# Created by zhouwang on 2018/6/8.

from .base import BaseRequestHandler, permission
import datetime
import tornado


class Handler(BaseRequestHandler):
    @permission()
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        response_data = yield tornado.gen.Task(self._summary)
        self._write(response_data)

    @tornado.gen.coroutine
    def _summary(self):
        now_str_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        select_sql = '''
          SELECT * FROM
            (SELECT count(id) as logfile_count FROM logfile) t1,
            (SELECT count(*) as host_count FROM (SELECT count(id) FROM logfile_host GROUP BY host) t4) t5,
            (SELECT count(id) as monitor_item_count FROM monitor_item) t6,
            (SELECT count(id) as user_count FROM user) t7,
            (SELECT count(DISTINCT user_id) as online_user_count FROM session WHERE expire_time>"%s") t8
        ''' % now_str_time
        self.cursor.execute(select_sql)
        results = self.cursor.dictfetchall()
        return {'code': 200, 'msg': 'Query Successful', 'data': results}
