# Created by zhouwang on 2018/6/6.

from .base import BaseRequestHandler, permission
from utils import utils
import logging

logger = logging.getLogger()

def reset_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id, username FROM user WHERE id="%d"' % int(pk)
        count = self.cursor.execute(select_sql)

        if not count:
            return dict(code=404, msg='Reset user not found')
        else:
            username = self.cursor.dictfetchone().get('username')
            if username != 'admin' and self.application.settings.get('ldap').get('auth') == True:
                return dict(code=403, msg='Authentication based no LDAP, Prohibit reset password')

        error = {}
        password = self.get_argument('password', '')
        if not password:
            error['password'] = 'Required'
        elif len(password) < 6:
            error['password'] = 'Must be more than 6 characters'

        if error:
            return dict(code=400, msg='Bad PUT param', error=error)

        self.reqdata = dict(password=password)
        return func(self, pk)

    return _wrapper


def change_valid(func):
    def _wrapper(self):
        if self.application.settings.get('ldap').get('auth') == True and self.requser.get('username') != 'admin':
            return dict(code=403, msg='Authentication based no LDAP, Prohibit change password')

        error = {}
        old_password = self.get_argument('old_password', '')
        new_password = self.get_argument('new_password', '')
        if not old_password:
            error['old_password'] = 'Required'
        elif not utils.validate_password(old_password, self.requser.get('password')):
            error['old_password'] = 'Invalid password'
        if not new_password:
            error['new_password'] = 'Required'
        elif len(new_password) < 6:
            error['new_password'] = 'Must be more than 6 characters'
        elif utils.validate_password(new_password, self.requser.get('password')):
            error['new_password'] = 'New password cannot be the same as the old'

        if error:
            return dict(code=400, msg='Bad PUT param', error=error)

        self.reqdata = dict(password=new_password)

        return func(self)

    return _wrapper


class ResetHandler(BaseRequestHandler):
    @permission(role=1)
    def put(self, pk=0):
        response_data = self._reset(int(pk))
        self._write(response_data)

    @reset_valid
    def _reset(self, pk):
        try:
            update_arg = (utils.make_password(self.reqdata['password']), pk)
            with self.transaction():
                self.cursor.execute(self.update_sql, update_arg)
        except Exception as e:
            logger.error('Reset password failed: %s' % str(e))
            return dict(code=500, msg='Reset failed')
        else:
            return dict(code=200, msg='Reset successful', data={'id': pk})

    update_sql = 'UPDATE user SET password=%s WHERE id=%s'


class Handler(BaseRequestHandler):
    @permission()
    def put(self):
        response_data = self._change()
        self._write(response_data)

    @change_valid
    def _change(self):
        try:
            update_arg = (utils.make_password(self.reqdata['password']), self.requser.get('id'))
            with self.transaction():
                self.cursor.execute(self.update_sql, update_arg)
        except Exception as e:
            logger.error('Change password failed: %s' % str(e))
            return dict(code=500, msg='Change failed')
        else:
            self.requser['password'] = utils.make_password(self.reqdata['password'])
            return dict(code=200, msg='Change successful', data={'id': self.requser.get('id')})

    update_sql = 'UPDATE user SET password=%s WHERE id=%s'
