# Created by zhouwang on 2018/5/16.

from .base import BaseRequestHandler, validate_password, make_password
import hashlib
import ldap
import datetime
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
            self._write({'code': 400, 'msg': 'Bad POST data', 'error': error})
        else:
            self.reqdata = {
                'username': self.username,
                'password': self.password
            }
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
            response_data = {'code': 500, 'msg': 'Login failed'}
        else:
            scope_subtree = ldap.SCOPE_SUBTREE
            filterstr = '(uid=%s)' % self.username
            result_id = conn.search(_ldap.get('base_dn'), scope_subtree, filterstr, None)
            result_type, result_data = conn.result(result_id, 0)
            if not result_data:
                response_data = {'code': 401, 'msg': 'Username or password incorrect'}
            else:
                try:
                    conn.simple_bind_s(result_data[0][0], self.password)
                except Exception as e:
                    logging.error('Bind ldap user failed: %s' % str(e))
                    response_data = {'code': 401, 'msg': 'Username or password incorrect'}
                else:
                    self.ldap_user = result_data[0][1]
                    user = self.base_user()  # loggrove base user
                    if not user:
                        response_data = {'code': 500, 'msg': 'Login failed'}
                    elif user.get('status') != 1:
                        response_data = {'code': 403, 'msg': 'User disabled'}
                    else:
                        response_data = self.login(user)
            conn.unbind_s()
        return response_data

    def base_auth_login(self):
        select_sql = 'SELECT id,username,password,status FROM user WHERE username="%s"' % \
                     (self.username)
        self.mysqldb_cursor.execute(select_sql)
        user = self.mysqldb_cursor.fetchone()

        if not user:
            response_data = {'code': 401, 'msg': 'User does not exist'}
        elif user.get('status') != 1:
            response_data = {'code': 403, 'msg': 'User disabled'}
        elif not validate_password(self.password, user.get('password')):
            response_data = {'code': 403, 'msg': 'Invalid password'}
        else:
            response_data = self.login(user)  # login & session
        return response_data

    def base_user(self):
        select_sql = 'SELECT * FROM user WHERE username="%s"' % self.username
        self.mysqldb_cursor.execute(select_sql)
        user = self.mysqldb_cursor.fetchone()

        if not user:
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
                VALUES ("%s", "%s", "%s", "%s", "%s", "1", "3")
            ''' % (self.username,
                   hashlib.md5(self.password.encode('UTF-8')).hexdigest(),
                   self.username.capitalize(),
                   self.ldap_user.get('mail')[0].decode('UTF-8')
                                            if self.ldap_user.get('mail') else '%s@loggrove.com' % self.username,
                   datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),)

            try:
                self.mysqldb_cursor.execute(insert_sql)
            except Exception as e:
                self.mysqldb_conn.rollback()
                logger.error('Add base user failed: %s' % str(e))
                return False
        else:
            update_sql = '''
                UPDATE 
                  user 
                SET 
                  username="%s", 
                  password="%s",
                  email="%s"
                WHERE 
                  id="%d"
            ''' % (self.username,
                   make_password(self.password),
                   self.ldap_user.get('mail')[0].decode('UTF-8') if self.ldap_user.get('mail') else user['email'],
                   user['id'])

            try:
                self.mysqldb_cursor.execute(update_sql)
            except Exception as e:
                self.mysqldb_conn.rollback()
                logger.error('Update base user failed: %s' % str(e))
                return False

        select_sql = 'SELECT * FROM user WHERE username="%s"' % self.username
        self.mysqldb_cursor.execute(select_sql)
        return self.mysqldb_cursor.fetchone()
