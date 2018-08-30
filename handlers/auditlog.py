# Created by zhouwang on 2018/6/8.

from .base import BaseRequestHandler, permission
import tornado

def query_valid(func):
    def _wrapper(self, pk):
        error = {}
        if not pk and self.request.arguments:
            argument_keys = self.request.arguments.keys()
            query_keys = ['id', 'uri', 'method', 'record_time', 'username',
                          'order', 'search', 'offset', 'limit', 'sort']
            error = {key:'参数不可用' for key in argument_keys if key not in query_keys}
        if error:
            return {'code': 400, 'msg': 'Bad GET param', 'error': error}
        return func(self, pk)
    return _wrapper


class Handler(BaseRequestHandler):
    @permission(role=1)
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, pk=0):
        ''' Query audit log '''
        response = yield tornado.gen.Task(self._query, int(pk))
        self._write(response)

    @tornado.gen.coroutine
    @query_valid
    def _query(self, pk=0):
        fields = ['id', 'uri', 'method', 'record_time', 'username']
        search_fields = ['uri', 'method', 'record_time', 'username']
        where, order, limit = self.select_sql_params(int(pk), fields, search_fields)
        where, order = self._replace(where), self._replace(order)

        select_sql = '''
            SELECT
              t1.id,
              t2.username,
              t1.uri,
              t1.method,  
              date_format(t1.record_time, "%%Y-%%m-%%d %%H:%%i:%%s") as record_time,
              t1.reqdata 
            FROM 
              auditlog t1
            INNER JOIN
              user t2
            ON 
              t1.user_id = t2.id
            %s %s %s  
        ''' % (where, order, limit)

        self.mysqldb_cursor.execute(select_sql)
        results = self.mysqldb_cursor.fetchall()
        if limit:
            total_sql = 'SELECT count(*) as total FROM auditlog t1 INNER JOIN user t2 ON t1.user_id = t2.id %s' % where
            self.mysqldb_cursor.execute(total_sql)
            total = self.mysqldb_cursor.fetchone().get('total')
            return {'code': 200, 'msg': 'Query Successful', 'data': results, 'total': total}
        return {'code': 200, 'msg': 'Query Successful', 'data': results}

    def _replace(self, param):
        return param.replace('id', 't1.id').replace('uri', 't1.uri').replace('method', 't1.method').\
            replace('record_time', 't1.record_time').replace('username', 't2.username')