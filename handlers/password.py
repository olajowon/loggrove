# Created by zhouwang on 2018/6/6.

from .base import BaseRequestHandler, permission, validate_password, make_password
import logging

logger = logging.getLogger()

def reset_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id, username FROM user WHERE id="%d"' % int(pk)
        count = self.mysqldb_cursor.execute(select_sql)

        if not count:
            return {'code': 404, 'msg': 'Reset user not found'}
        else:
            username = self.mysqldb_cursor.fetchone().get('username')
            if username != 'admin' and self.application.settings.get('ldap').get('auth') == True:
                return {'code': 403, 'msg': 'Authentication based no LDAP, Prohibit reset password'}

        error = {}
        password = self.get_argument('password', '')
        if not password:
            error['password'] = 'Required'
        elif len(password) < 6:
            error['password'] = 'Must be more than 6 characters'

        if error:
            return {'code': 400, 'msg': 'Bad PUT param', 'error': error}

        self.reqdata = {
            'password': password
        }
        return func(self, pk)

    return _wrapper


def change_valid(func):
    def _wrapper(self):
        if self.application.settings.get('ldap').get('auth') == True and self.requser.get('username') != 'admin':
            return {'code': 403, 'msg': 'Authentication based no LDAP, Prohibit change password'}

        error = {}
        old_password = self.get_argument('old_password', '')
        new_password = self.get_argument('new_password', '')
        if not old_password:
            error['old_password'] = 'Required'
        elif not validate_password(old_password, self.requser.get('password')):
            error['old_password'] = 'Invalid password'
        if not new_password:
            error['new_password'] = 'Required'
        elif len(new_password) < 6:
            error['new_password'] = 'Must be more than 6 characters'
        elif validate_password(new_password, self.requser.get('password')):
            error['new_password'] = 'New password cannot be the same as the old'

        if error:
            return {'code': 400, 'msg': 'Bad PUT param', 'error': error}

        self.reqdata = {
            'password': new_password
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
        ''' % (make_password(self.reqdata['password']), pk)
        try:
            self.mysqldb_cursor.execute(update_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            logger.error('Reset password failed: %s' % str(e))
            return {'code': 500, 'msg': 'Reset failed'}
        else:
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
        ''' % (make_password(self.reqdata['password']), self.requser.get('id'))
        try:
            self.mysqldb_cursor.execute(update_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            logger.error('Change password failed: %s' % str(e))
            return {'code': 500, 'msg': 'Change failed'}
        else:
            self.requser['password'] = make_password(self.reqdata['password'])
            return {'code': 200, 'msg': 'Change successful', 'data': {'id': self.requser.get('id')}}
