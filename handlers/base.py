# Created by zhouwang on 2018/5/5.

import tornado.web
import pymysql
import pymysql.cursors
import json
import time
import urllib
import uuid
import datetime

def permission(role=3):
    def __decorator(func):
        def __wrapper(self, *args):
            if self.is_authenticated:
                if role != 3:
                    if self.requser and self.requser.get('role') <= role:
                        return func(self, *args)
                    elif self.request.headers.get('Accept', '*/*').find('html') >= 0:
                        #self.redirect('/user/login/html/?next=%s' % urllib.parse.quote(self.request.uri))
                        self.write('HTTP 403: Forbidden')
                    else:
                        self._write({'code': 403, 'msg': 'Forbidden'})
                else:
                    return func(self, *args)
            elif self.request.headers.get('Accept', '*/*').find('html') >= 0:
                self.redirect('/login/html/?next=%s' % urllib.parse.quote(self.request.uri))
            else:
                self._write({'code': 401, 'msg': 'Unauthorized'})

        return __wrapper
    return __decorator


class BaseRequestHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.mysqldb_conn = self.application.settings.get('mysqldb_conn')
        self.mysqldb_cursor = self.mysqldb_conn.cursor(cursor=pymysql.cursors.DictCursor)
        self.reqdata = {}
        self.session = None
        self.session_id = self.get_secure_cookie('session_id')
        if self.session_id:
            self.session_id = self.session_id.decode('utf-8')
            select_sql = '''
                SELECT
                  * 
                FROM 
                  session 
                WHERE 
                  session_id="%s" and expire_time>="%s"
            ''' % (self.session_id, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
            self.mysqldb_cursor.execute(select_sql)
            self.session = self.mysqldb_cursor.fetchone()
            #print(self.session)

        self.requser = None
        if self.session:
            select_sql = '''
                SELECT
                  * 
                FROM 
                  user 
                WHERE 
                  id="%d"
            ''' % (self.session.get('user_id'))
            self.mysqldb_cursor.execute(select_sql)
            self.requser = self.mysqldb_cursor.fetchone()

        self.is_authenticated = False
        if self.requser:
            self.is_authenticated = True

    def logout(self):
        if self.session:
            delete_sql = 'DELETE FROM session WHERE session_id="%s"' % self.session.get('session_id')
            try:
                self.mysqldb_cursor.execute(delete_sql)
            except Exception as e:
                self.mysqldb_conn.rollback()
                return {'code': 500, 'msg': 'Logout failed, %s' % str(e)}
        if self.session_id:
            self.clear_cookie('session_id')
        return {'code': 200, 'msg': 'Logout successful'}


    def login(self, user, active=60*60*24):
        session_id = str(uuid.uuid4()).replace('-', '')
        user_id = user.get('id')
        create_time = time.time()
        expire_time = time.time() + active
        session_data = {'username': user.get('username')}
        insert_sql = '''
            INSERT INTO 
              session (
                session_id, 
                user_id, 
                session_data, 
                create_time,
                expire_time) 
            VALUES ("%s", "%s", "%s", "%s", "%s")
        ''' % (session_id,
               user_id,
               pymysql.escape_string(json.dumps(session_data)),
               time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(create_time)),
               time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expire_time)))
        try:
            self.mysqldb_cursor.execute(insert_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            response_data = {'code': 500, 'msg': 'Login failed, %s' % str(e)}
        else:
            self.set_secure_cookie('session_id', session_id, expires=expire_time)
            self.requser = user
            response_data = {'code': 200, 'msg': 'Login successful', 'cookies': {'session_id': session_id}}
        return response_data


    def get_current_user(self):
        user_id = None
        return user_id


    def on_finish(self):
        self.mysqldb_cursor.close()


    def write_error(self, status_code, **kwargs):
        exc_info = kwargs['exc_info']
        if status_code == 500:
            self.write(json.dumps({'code': status_code,
                                   'msg': 'HTTP 500: Internal Server Error, %s' % exc_info[1].__str__()}))
        else:
            self.write(json.dumps({'code': status_code,
                                   'msg': exc_info[1].__str__()}))


    def _write(self, response_data, audit=False):
        self.set_status(response_data.get('code'))
        self.write(json.dumps(response_data))

        if self.get_status()==200 and (self.request.method != 'GET'):
            self.add_auditlog()


    def add_auditlog(self):
        insert_sql = '''
            INSERT INTO 
              auditlog (
                user_id, 
                uri, 
                method, 
                reqdata,
                record_time) 
            VALUES ("%s", "%s", "%s", "%s", "%s")
        ''' % (self.requser['id'],
               self.request.uri,
               self.request.method,
               pymysql.escape_string(json.dumps(self.reqdata)),
               datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            self.mysqldb_cursor.execute(insert_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()


    def _update_row(self, update_sql, pk=0):
        try:
            self.mysqldb_cursor.execute(update_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            return {'code': 500, 'msg': 'Failed, %s' % str(e)}
        else:
            return {'code': 200, 'msg': 'Successful', 'data': {'id': int(pk)}}


    def _select_row(self, select_sql):
        self.mysqldb_cursor.execute(select_sql)
        results = self.mysqldb_cursor.fetchall()
        return {'code': 200, 'msg': 'Successful', 'data': results}


    def _insert_row(self, insert_sql):
        try:
            self.mysqldb_cursor.execute(insert_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            return {'code': 500, 'msg': 'Failed, %s' % str(e)}
        else:
            self.mysqldb_cursor.execute('SELECT LAST_INSERT_ID() as id')
            return {'code': 200, 'msg': 'Successful', 'data': self.mysqldb_cursor.fetchall()}


    def _delete_row(self, delete_sql):
        try:
            self.mysqldb_cursor.execute(delete_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            return {'code': 500, 'msg': 'Failed, %s' % str(e)}
        else:
            return {'code': 200, 'msg': 'Successful'}


    def format_where_param(self, pk, arguments):
        where = ''
        if pk:
            where = 'WHERE id="%d"' % pk
        elif arguments:
            where = 'WHERE %s' % \
                    ' and '.join(['%s in (%s)' % (key, ",".join(['"%s"' % val.decode() for val in vals if vals]))
                                  for key, vals in arguments.items()])
        return where
