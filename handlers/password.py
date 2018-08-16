# Created by zhouwang on 2018/6/6.

from .base import BaseRequestHandler, permission
import hashlib

def reset_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM user WHERE id="%d"' % int(pk)
        count = self.mysqldb_cursor.execute(select_sql)
        if not count:
            return  {'code': 404, 'msg': 'Reset user not found'}

        error = {}
        password = self.get_argument('password', '')
        if not password:
            error['password'] = '密码是必填项'
        elif len(password) < 6:
            error['password'] = '密码不可少于6个字符'

        if error:
            return {'code': 400, 'msg': 'Bad PUT param', 'error': error}

        self.reqdata = {
            'password': hashlib.md5(password.encode('UTF-8')).hexdigest()
        }
        return func(self, pk)
    return _wrapper


def change_valid(func):
    def _wrapper(self):
        error = {}
        old_password = self.get_argument('old_password', '')
        new_password = self.get_argument('new_password', '')
        if not old_password:
            error['old_password'] = '旧密码是必填项'
        elif hashlib.md5(old_password.encode('UTF-8')).hexdigest() != self.requser.get('password'):
            error['old_password'] = '旧密码不正确'

        if not new_password:
            error['new_password'] = '新密码是必填项'
        elif len(new_password) < 6:
            error['new_password'] = '新密码不可少于6个字符'
        elif hashlib.md5(new_password.encode('UTF-8')).hexdigest() == self.requser.get('password'):
            error['new_password'] = '新密码不可与旧密码相同'

        if error:
            return {'code': 400, 'msg': 'Bad PUT param', 'error': error}

        self.reqdata = {
            'password': hashlib.md5(new_password.encode('UTF-8')).hexdigest()
        }
        return func(self)
    return _wrapper


class ResetHandler(BaseRequestHandler):
    @permission(role=1)
    def put(self, pk=0):
        response_data = self._reset(int(pk))
        self._write(response_data)

    @reset_valid
    def _reset(self, pk):
        update_sql = '''
            UPDATE 
              user 
            SET 
              password="%s"
            WHERE 
              id="%d"
        ''' % (self.reqdata['password'], pk)
        try:
            self.mysqldb_cursor.execute(update_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            return {'code': 500, 'msg': 'Reset failed, %s' % str(e)}
        else:
            self.reqdata['password'] = '*' * 6  # 隐藏密码
            return {'code': 200, 'msg': 'Reset successful', 'data': {'id': pk}}


class Handler(BaseRequestHandler):
    @permission()
    def put(self):
        response_data = self._change()
        self._write(response_data)

    @change_valid
    def _change(self):
        update_sql = '''
            UPDATE 
              user 
            SET 
              password="%s"
            WHERE 
              id="%d"
        ''' % (self.reqdata['password'], self.requser.get('id'))
        try:
            self.mysqldb_cursor.execute(update_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            return {'code': 500, 'msg': 'Change failed, %s' % str(e)}
        else:
            self.requser['password'] = self.reqdata['password']
            self.reqdata['password'] = '*' * 6  # 隐藏密码
            return {'code': 200, 'msg': 'Change successful', 'data': {'id': self.requser.get('id')}}