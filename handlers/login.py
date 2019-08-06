# Created by zhouwang on 2018/5/16.

from .base import BaseRequestHandler
from utils import utils
import time
import ldap
import datetime
import json
import pymysql
import uuid
import logging

logger = logging.getLogger()


def login_valid(func):
    def _wrapper(self):
        self.username = self.get_argument('username', '')
        self.password = self.get_argument('password', '')
        error = {}
        if not self.username:
            error['username'] = 'Required'
        if not self.password:
            error['password'] = 'Required'
        if error:
            self._write(dict(code=400, msg='Bad POST data', error=error))
        else:
            self.reqdata = dict(
                username=self.username,
                password=self.password
            )
            return func(self)

    return _wrapper


class Handler(BaseRequestHandler):
    ''' login '''

    @login_valid
    def post(self):
        self.logout()  # logout
        if self.application.settings.get('ldap').get('auth') != True or self.username == 'admin':
            response_data = self.base_auth_login()
        else:
            response_data = self.ldap_auth_login()
        self._write(response_data)

    def ldap_auth_login(self):
        _ldap = self.application.settings.get('ldap')
        try:
            conn = ldap.initialize(_ldap.get('server_uri'))
            conn.protocal_version = ldap.VERSION3
            conn.simple_bind_s(_ldap.get('bind_dn'), _ldap.get('bind_password'))
        except Exception as e:
            logging.error('Initialize Bind ldap failed: %s' % str(e))
            response_data = dict(code=500, msg='Login failed')
        else:
            scope_subtree = ldap.SCOPE_SUBTREE
            filterstr = '(uid=%s)' % self.username
            result_id = conn.search(_ldap.get('base_dn'), scope_subtree, filterstr, None)
            result_type, result_data = conn.result(result_id, 0)
            if not result_data:
                response_data = dict(code=401, msg='Username or password incorrect')
            else:
                try:
                    conn.simple_bind_s(result_data[0][0], self.password)
                except Exception as e:
                    logging.error('Bind ldap user failed: %s' % str(e))
                    response_data = dict(code=401, msg='Username or password incorrect')
                else:
                    self.ldap_user = result_data[0][1]
                    user = self.base_user()  # loggrove base user
                    if not user:
                        response_data = dict(code=500, msg='Login failed')
                    elif user.get('status') != 1:
                        response_data = dict(code=403, msg='User disabled')
                    else:
                        response_data = self.login(user)
            conn.unbind_s()
        return response_data

    def base_auth_login(self):
        self.cursor.execute(self.select_user_sql, self.username)
        user = self.cursor.dictfetchone()

        if not user:
            response_data = dict(code=401, msg='User does not exist')
        elif user.get('status') != 1:
            response_data = dict(code=403, msg='User disabled')
        elif not utils.validate_password(self.password, user.get('password')):
            response_data = dict(code=403, msg='Invalid password')
        else:
            response_data = self.login(user)  # login & session
        return response_data

    def base_user(self):
        self.cursor.execute(self.select_user_sql, self.username)
        user = self.cursor.dictfetchone()

        if not user:
            try:
                insert_user_arg = (
                    self.username,
                    utils.make_password(self.password),
                    self.username.capitalize(),
                    self.ldap_user.get('mail')[0].decode('UTF-8')
                    if self.ldap_user.get('mail') else '%s@loggrove.com' % self.username,
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                )
                with self.transaction():
                    self.cursor.execute(self.insert_user_sql, insert_user_arg)
            except Exception as e:
                logger.error('Add base user failed: %s' % str(e))
                return False
        else:
            try:
                update_user_arg = (
                    self.username,
                    utils.make_password(self.password),
                    self.ldap_user.get('mail')[0].decode('UTF-8') if self.ldap_user.get('mail') else user['email'],
                    user['id']
                )
                with self.transaction():
                    self.cursor.execute(self.update_user_sql, update_user_arg)
            except Exception as e:
                logger.error('Update base user failed: %s' % str(e))
                return False

        self.cursor.execute(self.select_user_sql, self.username)
        return self.cursor.dictfetchone()


    def login(self, user, active=60 * 60 * 24):
        try:
            session_id = str(uuid.uuid4()).replace('-', '')
            user_id = user.get('id')
            create_time = time.time()
            expire_time = time.time() + active
            session_data = {'username': user.get('username')}
            insert_session_arg = (
                session_id,
                user_id,
                pymysql.escape_string(json.dumps(session_data)),
                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(create_time)),
                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expire_time))
            )
            with self.transaction():
                self.cursor.execute(self.insert_session_sql, insert_session_arg)
                self.set_secure_cookie('session_id', session_id, expires=expire_time)
                self.requser = user
        except Exception as e:
            logger.error('Login failed: %s' % str(e))
            response_data = dict(code=500, msg='Login failed')
        else:
            response_data = dict(code=200, msg='Login successful', cookies=dict(session_id=session_id))
        return response_data

    def logout(self):
        if self.session:
            try:
                with self.transaction():
                    self.cursor.execute(self.delete_session_sql, self.session.get('session_id'))
            except Exception as e:
                logger.error('Logout failed: %s' % str(e))
        if self.session_id:
            self.clear_cookie('session_id')

    select_user_sql = 'SELECT id,username,password,status FROM user WHERE username=%s'

    insert_user_sql = '''INSERT INTO user (username, password, fullname, email, join_time, status, role) 
        VALUES (%s, %s, %s, %s, %s, "1", "3")
    '''

    update_user_sql = 'UPDATE user SET username=%s, password=%s, email=%s WHERE id=%d'

    insert_session_sql = '''INSERT INTO session (session_id, user_id, session_data, create_time, expire_time) 
        VALUES (%s, %s, %s, %s, %s)
    '''

    delete_session_sql = 'DELETE FROM session WHERE session_id=%s'