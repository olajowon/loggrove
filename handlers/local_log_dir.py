# Created by zhouwang on 2018/5/17.

from .base import BaseRequestHandler, permission
import datetime
import os

def check_argements(handler, pk=None):
    error = {}
    path = os.path.join(handler.get_argument('path', ''), '')
    comment = handler.get_argument('comment', '')
    if not path:
        error['path'] = '目录路径是必填项'
    elif not os.path.exists(path):
        error['path'] = '目录路径[本地]不存在'
    elif not os.path.isdir(path):
        error['path'] = '路径不是一个目录'
    else:
        select_sql = 'SELECT id FROM local_log_dir WHERE path="%s" %s' % (path, 'and id!="%d"' % pk if pk else '')
        count = handler.mysqldb_cursor.execute(select_sql)
        if count:
            error['path'] = '目录路径已存在'
    if not comment:
        error['comment'] = '备注是必填项'
    request_data = {
        'path':path,
        'comment':comment
    }
    return error, request_data


def add_valid(func):
    def _wrapper(self):
        error, self.reqdata = check_argements(self)
        if error:
            return {'code': 400, 'msg': 'Bad POST data', 'error': error}
        return func(self)
    return _wrapper


def query_valid(func):
    def _wrapper(self, pk):
        error = {}
        if not pk and self.request.arguments:
            argument_keys = self.request.arguments.keys()
            query_keys = ['id', 'path', 'comment', 'create_time']
            error = {key:'参数不可用' for key in argument_keys if key not in query_keys}
        if error:
            return {'code': 400, 'msg': 'Bad GET param', 'error': error}
        return func(self, pk)
    return _wrapper


def update_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM local_log_dir WHERE id="%d"' % pk
        count = self.mysqldb_cursor.execute(select_sql)
        if not count:
            return {'code': 404, 'msg': 'Update row not found'}
        error, self.reqdata = check_argements(self, pk)
        if error:
            return {'code': 400, 'msg': 'Bad PUT param', 'error': error}
        return func(self, pk)
    return _wrapper


def del_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM local_log_dir WHERE id="%d"' % pk
        count = self.mysqldb_cursor.execute(select_sql)
        if not count:
            return {'code': 404, 'msg': 'Delete row not found'}
        return func(self, pk)
    return _wrapper


class LocalLogDir():
    def __init__(self):
        self.reqdata = {}

    @add_valid
    def _add(self):
        insert_sql = 'INSERT INTO local_log_dir (path, create_time, comment) VALUES ("%s", "%s", "%s")' % \
                     (self.reqdata['path'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                      self.reqdata['comment'],)
        try:
            self.mysqldb_cursor.execute(insert_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            return {'code': 500, 'msg': 'Add failed, %s' % str(e)}
        else:
            self.mysqldb_cursor.execute('SELECT LAST_INSERT_ID() as id')
            return {'code': 200, 'msg': 'Add successful', 'data': self.mysqldb_cursor.fetchall()}


    @query_valid
    def _query(self, pk):
        select_sql = '''
                        SELECT
                            id,
                            path,  
                            date_format(create_time, "%%Y-%%m-%%d %%H:%%i:%%s") as create_time,
                            comment 
                        FROM local_log_dir
                        %s
                        ''' % self.format_where_param(pk, self.request.arguments)
        self.mysqldb_cursor.execute(select_sql)
        results = self.mysqldb_cursor.fetchall()
        data = [dict(result, **{'nodes':self._nodes(result['path']) if os.path.isdir(result['path']) else [] }) for result in results]
        return {'code': 200, 'msg': 'Query successful', 'data': data}


    @update_valid
    def _update(self, pk):
        update_sql = 'UPDATE local_log_dir SET path="%s", comment="%s" WHERE id="%d"' % \
                     (self.reqdata['path'], self.reqdata['comment'], pk)
        try:
            self.mysqldb_cursor.execute(update_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            return {'code': 500, 'msg': 'Update failed, %s' % str(e)}
        else:
            return {'code': 200, 'msg': 'Update successful', 'data': {'id': pk}}


    @del_valid
    def _del(self, pk):
        delete_sql = 'DELETE FROM local_log_dir WHERE id="%d"' % pk
        try:
            self.mysqldb_cursor.execute(delete_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            return {'code': 500, 'msg': 'Delete failed, %s' % str(e)}
        else:
            return {'code': 200, 'msg': 'Delete successful'}


    def _nodes(self, path):
        results = []
        list_names = os.listdir(path)
        for name in list_names:
            next_path = os.path.join(path, name)
            if os.path.isdir(next_path):
                results.append({'text': name, 'nodes': self._nodes(next_path)})
            else:
                results.append({'text': name})
        return results



class Handler(BaseRequestHandler, LocalLogDir):
    '''
        本地日志目录 Handler
    '''
    @permission(role=2)
    def post(self):
        response_data = self._add()
        self._write(response_data)

    @permission(role=2)
    def put(self, pk=0):
        response_data = self._update(int(pk))
        self._write(response_data)

    @permission(role=2)
    def delete(self, pk=0):
        response_data = self._del(int(pk))
        self._write(response_data)

    @permission()
    def get(self, pk=0):
        response_data = self._query(int(pk))
        self._write(response_data)