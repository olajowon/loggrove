# Created by zhouwang on 2018/5/5.

from .base import BaseRequestHandler, permission
import datetime
import os
import re
import logging
logger = logging.getLogger()


def argements_valid(handler, pk=None):
    error = {}
    path = handler.get_argument('path', '')
    comment = handler.get_argument('comment', '')
    location = handler.get_argument('location', '1')
    host = handler.get_argument('host', 'localhost')
    if not path:
        error['path'] = '文件路径是必填项'
    elif location == '1' and not os.path.isfile(path):
        error['path'] = '本地文件不存在'
    else:
        select_sql = 'SELECT id FROM logfile WHERE host="%s" and path="%s" %s' % \
                     (host, path, 'and id!="%d"' % pk if pk else '')
        count = handler.mysqldb_cursor.execute(select_sql)
        if count:
            error['path'] = '日志文件已存在'

    if location not in ['1', '2']:
        error['location'] = '位置不正确'

    if location == '1' and host != 'localhost':
        host = 'localhost'
    elif location == '2' and not \
        re.match(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', host):
        error['host'] = 'IP地址格式不正确'

    if not comment:
        error['comment'] = '备注是必填项'
    request_data = {
        'path': path,
        'comment': comment,
        'location': int(location),
        'host': host
    }
    return error, request_data


def add_valid(func):
    def _wrapper(self):
        error, self.reqdata = argements_valid(self)
        if error:
            return {'code': 400, 'msg': 'Bad POST data', 'error': error}
        return func(self)

    return _wrapper


def query_valid(func):
    def _wrapper(self, pk):
        error = {}
        if not pk and self.request.arguments:
            argument_keys = self.request.arguments.keys()
            query_keys = ['id', 'location', 'host', 'path', 'comment', 'create_time',
                          'order', 'search', 'offset', 'limit', 'sort']
            error = {key: '参数不可用' for key in argument_keys if key not in query_keys}
        if error:
            return {'code': 400, 'msg': 'Bad GET param', 'error': error}
        return func(self, pk)
    return _wrapper


def update_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM logfile WHERE id="%d"' % pk
        count = self.mysqldb_cursor.execute(select_sql)
        if not count:
            return {'code': 404, 'msg': 'Update row not found'}
        error, self.reqdata = argements_valid(self, pk)
        if error:
            return {'code': 400, 'msg': 'Bad PUT param', 'error': error}
        return func(self, pk)

    return _wrapper


def del_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM logfile WHERE id="%d"' % pk
        count = self.mysqldb_cursor.execute(select_sql)
        if not count:
            return {'code': 404, 'msg': 'Delete row not found'}
        return func(self, pk)

    return _wrapper



class Handler(BaseRequestHandler):
    @permission()
    def get(self, pk=0):
        ''' Query logfile '''
        response_data = self._query(int(pk))
        self._write(response_data)


    @permission(role=2)
    def post(self):
        ''' Add logfile '''
        response_data = self._add()
        self._write(response_data)


    @permission(role=2)
    def put(self, pk=0):
        ''' Update logfile '''
        response_data = self._update(int(pk))
        self._write(response_data)


    @permission(role=2)
    def delete(self, pk=0):
        ''' Delete logfile '''
        response_data = self._del(int(pk))
        self._write(response_data)


    @query_valid
    def _query(self, pk):
        fields = search_fields = ['id', 'location', 'host', 'path', 'comment', 'create_time']
        where, order, limit = self.select_sql_params(int(pk), fields, search_fields)
        select_sql = '''
            SELECT
              id, location, host, path, date_format(create_time, "%%Y-%%m-%%d %%H:%%i:%%s") as create_time, comment
            FROM
              logfile
            %s %s %s
        ''' % (where, order, limit)
        self.mysqldb_cursor.execute(select_sql)
        results = self.mysqldb_cursor.fetchall()
        if limit:
            total_sql = 'SELECT count(*) as total FROM logfile %s' % where
            self.mysqldb_cursor.execute(total_sql)
            total = self.mysqldb_cursor.fetchone().get('total')
            return {'code': 200, 'msg': 'Query Successful', 'data': results, 'total': total}
        return {'code': 200, 'msg': 'Query Successful', 'data': results}



    @add_valid
    def _add(self):
        insert_sql = '''
            INSERT INTO 
              logfile (location, host, path, create_time, comment) 
            VALUES 
              ("%s", "%s", "%s", "%s", "%s")
        ''' % (self.reqdata['location'], self.reqdata['host'], self.reqdata['path'],
               datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), self.reqdata['comment'],)
        try:
            self.mysqldb_cursor.execute(insert_sql)
        except Exception as e:
            logger.error('Add logfile failed: %s' % str(e))
            self.mysqldb_conn.rollback()
            return {'code': 500, 'msg': 'Add failed'}
        else:
            self.mysqldb_cursor.execute('SELECT LAST_INSERT_ID() as id')
            return {'code': 200, 'msg': 'Add successful', 'data': self.mysqldb_cursor.fetchall()}


    @update_valid
    def _update(self, pk):
        update_sql = 'UPDATE logfile SET location="%d", host="%s", path="%s", comment="%s" WHERE id="%d"' % \
                 (self.reqdata['location'], self.reqdata['host'], self.reqdata['path'], self.reqdata['comment'], pk)
        try:
            self.mysqldb_cursor.execute(update_sql)
        except Exception as e:
            logger.error('Update logfile failed: %s' % str(e))
            self.mysqldb_conn.rollback()
            return {'code': 500, 'msg': 'Update failed'}
        else:
            return {'code': 200, 'msg': 'Update successful', 'data': {'id': pk}}


    @del_valid
    def _del(self, pk):
        delete_sql = 'DELETE FROM logfile WHERE id="%d"' % pk
        try:
            self.mysqldb_cursor.execute(delete_sql)
        except Exception as e:
            logger.error('Delete logfile failed: %s' % str(e))
            self.mysqldb_conn.rollback()
            return {'code': 500, 'msg': 'Delete failed'}
        else:
            return {'code': 200, 'msg': 'Delete successful'}