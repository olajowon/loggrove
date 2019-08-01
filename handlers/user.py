# Created by zhouwang on 2018/5/17.

from .base import BaseRequestHandler, permission
from utils import utils
import datetime
import logging
logger = logging.getLogger()


def argements_valid(handler, pk=None):
    error = {}
    username = handler.get_argument('username', '')
    password = handler.get_argument('password', '')
    email = handler.get_argument('email', '')
    status = handler.get_argument('status', '')
    role = handler.get_argument('role', '')
    fullname = handler.get_argument('fullname', '')

    if not username:
        error['username'] = 'Required'
    else:
        select_sql = 'SELECT id FROM user WHERE username="%s" %s' % (username, 'and id!="%d"' % pk if pk else '')
        count = handler.cursor.execute(select_sql)
        if count:
            error['username'] = 'Already existed'

    if handler.request.method == 'POST':
        if not password:
            error['password'] = 'Required'

    if not email:
        error['email'] = 'Required'
    if status not in ['1', '2']:
        error['status'] = 'Invalid'
    if role not in ['1', '2', '3']:
        error['role'] = 'Invalid'

    request_data = {
        'username': username,
        'password': password,
        'email': email,
        'status': status,
        'role': role,
        'fullname': fullname
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
            query_keys = ['id', 'username', 'email', 'fullname', 'order', 'search', 'offset', 'limit', 'sort']
            error = {key: 'Bad key' for key in argument_keys if key not in query_keys}
        if error:
            return {'code': 400, 'msg': 'Bad GET param', 'error': error}
        return func(self, pk)
    return _wrapper


def update_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM user WHERE id="%d"' % pk
        count = self.cursor.execute(select_sql)
        if not count:
            return {'code': 404, 'msg': 'Update row not found'}
        error, self.reqdata = argements_valid(self, pk)
        if error:
            return {'code': 400, 'msg': 'Bad PUT param', 'error': error}
        return func(self, pk)
    return _wrapper


def del_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM user WHERE id="%d"' % pk
        count = self.cursor.execute(select_sql)
        if not count:
            return {'code': 404, 'msg': 'Delete row not found'}
        return func(self, pk)
    return _wrapper


class Handler(BaseRequestHandler):
    @permission(role=1)
    def get(self, pk=0):
        response_data = self._query(int(pk))
        return self._write(response_data)

    @permission(role=1)
    def post(self):
        response_data = self._add()
        self._write(response_data)

    @permission(role=1)
    def put(self, pk=0):
        response_data = self._update(int(pk))
        self._write(response_data)

    @permission(role=1)
    def delete(self, pk=0):
        response_data = self._del(int(pk))
        self._write(response_data)

    @query_valid
    def _query(self, pk):
        fields = search_fields = ['id', 'username', 'email', 'fullname']
        where, order, limit = self.select_sql_params(int(pk), fields, search_fields)
        select_sql = '''
        SELECT
            id,
            username,
            fullname,
            email,
            status,
            role,  
            date_format(join_time, "%%Y-%%m-%%d %%H:%%i:%%s") as join_time
        FROM user
        %s %s %s
        ''' % (where, order, limit)
        self.cursor.execute(select_sql)
        results = self.cursor.dictfetchall()
        if limit:
            total_sql = 'SELECT count(*) as total FROM user %s' % where
            self.cursor.execute(total_sql)
            total = self.cursor.dictfetchone().get('total')
            return {'code': 200, 'msg': 'Query Successful', 'data': results, 'total': total}
        return {'code': 200, 'msg': 'Query successful', 'data': results}

    @add_valid
    def _add(self):
        insert_sql = '''
            INSERT INTO 
              user (
                username, 
                password, 
                fullname, 
                email,
                join_time, 
                status, 
                role) 
            VALUES ("%s", "%s", "%s", "%s", "%s", "%s", "%s")
        ''' % (self.reqdata['username'],
               utils.make_password(self.reqdata['password']),
               self.reqdata['fullname'],
               self.reqdata['email'],
               datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
               self.reqdata['status'],
               self.reqdata['role'])
        try:
            self.cursor.execute(insert_sql)
        except Exception as e:
            self.db.rollback()
            logger.error('Add user failed: %s' % str(e))
            return {'code': 500, 'msg': 'Add failed'}
        else:
            self.cursor.execute('SELECT LAST_INSERT_ID() as id')
            return {'code': 200, 'msg': 'Add successful', 'data': self.cursor.dictfetchall()}

    @update_valid
    def _update(self, pk):
        update_sql = '''
            UPDATE 
              user 
            SET 
              username="%s", 
              fullname="%s",
              email="%s",
              status="%s",
              role="%s"
            WHERE 
              id="%d"
        ''' % (self.reqdata['username'],
               self.reqdata['fullname'],
               self.reqdata['email'],
               self.reqdata['status'],
               self.reqdata['role'],
               pk)
        try:
            self.cursor.execute(update_sql)
        except Exception as e:
            self.db.rollback()
            logger.error('Update user failed: %s' % str(e))
            return {'code': 500, 'msg': 'Update failed'}
        else:
            return {'code': 200, 'msg': 'Update successful', 'data': {'id': pk}}

    @del_valid
    def _del(self, pk):
        delete_sql = 'DELETE FROM user WHERE id="%d"' % pk
        try:
            self.cursor.execute(delete_sql)
        except Exception as e:
            self.db.rollback()
            logger.error('Delete user failed: %s' % str(e))
            return {'code': 500, 'msg': 'Delete failed'}
        else:
            return {'code': 200, 'msg': 'Delete successful'}
