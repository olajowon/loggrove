# Created by zhouwang on 2018/6/8.

from .base import BaseRequestHandler, permission


class Handler(BaseRequestHandler):
    @permission()
    def get(self):
        response_data = self._query()
        self._write(response_data)

    def _query(self):
        select_arg = (self.requser['id'], self.session['session_id'])
        self.cursor.execute(self.select_sql, select_arg)
        results = self.cursor.dictfetchall()
        return dict(code=200, msg='Query Successful', data=results)

    select_sql = '''
      SELECT
        *
      FROM
        (
          SELECT
            id,
            username,
            fullname,
            email,
            role,
            status,
            date_format(join_time, "%%Y-%%m-%%d %%H:%%i:%%s") as join_time
          FROM
            user
          WHERE 
            id=%s
        ) t1,
        (            
          SELECT
            date_format(create_time, "%%Y-%%m-%%d %%H:%%i:%%s") as login_time,
            date_format(expire_time, "%%Y-%%m-%%d %%H:%%i:%%s") as expire_time
          FROM 
            session 
          WHERE 
            session_id=%s
        ) t2                   
    '''