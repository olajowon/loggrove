# Created by zhouwang on 2018/6/8.

from .base import BaseRequestHandler, permission
import datetime

class Dashboard():
    def __init__(self):
        pass

    def _summary(self):
        now_str_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        select_sql = '''
          SELECT * FROM
            (SELECT count(id) as local_log_file_count FROM local_log_file) t1,
            (SELECT count(id) as local_log_dir_count FROM local_log_dir) t2,
            (SELECT count(id) as local_log_monitor_item_count FROM local_log_monitor_item) t3,
            (SELECT count(id) as user_count FROM user) t4,
            (SELECT count(DISTINCT user_id) as online_user_count FROM session WHERE expire_time>"%s") t5
        ''' % now_str_time
        self.mysqldb_cursor.execute(select_sql)
        results = self.mysqldb_cursor.fetchall()
        return {'code': 200, 'msg': 'Query Successful', 'data': results}

class Handler(BaseRequestHandler, Dashboard):
    @permission()
    def get(self):
        response_data = self._summary()
        self._write(response_data)