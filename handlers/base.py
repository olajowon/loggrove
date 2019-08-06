# Created by zhouwang on 2018/5/5.

import tornado.web
import tornado.websocket
import pymysql
import pymysql.cursors
import json
import time
import urllib
import uuid
import datetime
import settings
import logging

logger = logging.getLogger()


def permission(role=3):
    def _decorator(func):
        def _wrapper(self, *args):
            if self.is_authenticated:
                if role != 3:
                    if self.requser and self.requser.get('role') <= role:
                        return func(self, *args)
                    elif self.request.headers.get('Upgrade') == 'websocket':
                        self.write_message(dict(code=403, msg='Forbidden'))
                        self.close()
                    elif self.request.headers.get('Accept', '*/*').find('html') >= 0:
                        self.set_status(403)
                        self.write('HTTP 403: Forbidden')
                    else:
                        self._write(dict(code=403, msg='Forbidden'))
                else:
                    return func(self, *args)
            elif self.request.headers.get('Upgrade') == 'websocket':
                self.write_message(dict(code=401, msg='Unauthorized'))
                self.close()
            elif self.request.headers.get('Accept', '*/*').find('html') >= 0:
                self.redirect('/login/html/?next=%s' % urllib.parse.quote(self.request.uri))
            else:
                self._write(dict(code=401, msg='Unauthorized'))

        return _wrapper

    return _decorator


def db_valid(func):
    ''' ping mysql connect '''

    def _wrapper(self):
        self.db = self.application.settings.get('db')
        try:
            self.db.ping(True)
        except Exception as e:
            logger.error('Ping MySQL failed: %s' % str(e))
            try:
                mysqldb = settings.MYSQL_DB
                self.db = pymysql.connect(**mysqldb)
            except Exception as e:
                logger.error('Connect MySQL failed: %s' % str(e))
                if self.request.headers.get('Accept', '*/*').find('html') >= 0:
                    self.set_status(500)
                    self.write('HTTP 500: Internal Server Error')
                else:
                    self._write(dict(code=500, msg='Internal Server Error'))
                return
            else:
                self.application.settings['db'] = self.db
        return func(self)

    return _wrapper


class InitHandler():
    def __init__(self):
        self.db = None
        self.cursor = None
        self.session_id = None
        self.session = {}
        self.requser = {}

    def init_db(self):
        self.db = self.application.settings.get('db')
        try:
            self.db.ping(True)
        except Exception as e:
            logger.error('Ping MySQL failed: %s' % str(e))
            try:
                mysqldb = settings.MYSQL_DB
                db = pymysql.connect(**mysqldb)
            except Exception as e:
                logger.error('Connect MySQL failed: %s' % str(e))
                self._write(dict(code=500, msg='Internal Server Error'))
                self.finish()
            else:
                self.application.settings['db'] = db

    def init_session(self):
        self.session_id = self.get_secure_cookie('session_id')
        self.session = None
        if self.session_id:
            session_id = self.session_id.decode('utf-8')
            select_sql = '''
                        SELECT * FROM session WHERE session_id="%s" and expire_time>="%s"
                    ''' % (pymysql.escape_string(session_id), time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
            self.cursor.execute(select_sql)
            self.session = self.cursor.dictfetchone()

    def init_requser(self):
        self.requser = None
        if self.session:
            select_sql = '''
                        SELECT * FROM user WHERE id="%d"
                    ''' % (self.session.get('user_id'))

            self.cursor.execute(select_sql)
            self.requser = self.cursor.dictfetchone()
        self.is_authenticated = bool(self.requser)

    def init_cursor(self):
        self.cursor = self.db.cursor()
        setattr(self.cursor, 'dictfetchall', self.dictfetchall)
        setattr(self.cursor, 'dictfetchone', self.dictfetchone)

    def dictfetchall(self):
        desc = self.cursor.description
        return [
            dict(zip([col[0] for col in desc], row))
            for row in self.cursor.fetchall()
        ]

    def dictfetchone(self):
        desc = self.cursor.description
        row = self.cursor.fetchone()
        return dict(zip([col[0] for col in desc], row)) if row else row

    def transaction(self, atomic=False):
        return Transaction(self.db, self.cursor, atomic)


class Transaction():
    def __init__(self, db, cursor, atomic=False):
        self.db = db
        self.cursor = cursor
        self.atomic = atomic

    def __enter__(self):
        if self.atomic:
            self.cursor.execute('start transaction')

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        elif self.atomic:
            self.db.commit()


class BaseRequestHandler(tornado.web.RequestHandler, InitHandler):
    def initialize(self):
        try:
            self.init_db()
            self.init_cursor()
            self.init_session()
            self.init_requser()
        except Exception as e:
            logger.error('Initialize failed: %s' % str(e))
            self._write(dict(code=500, msg='Internal Server Error'))
            self.on_finish()
        self.reqdata = {}

    def get_current_user(self):
        user_id = None
        return user_id

    def on_finish(self):
        self.cursor.close()

    def write_error(self, status_code, **kwargs):
        exc_info = kwargs['exc_info']
        if status_code == 500:
            self.write(json.dumps(dict(code=status_code,
                                   msg='HTTP 500: Internal Server Error')))
        else:
            self.write(json.dumps(dict(code=status_code,
                                   msg=exc_info[1].__str__())))

    def _write(self, response_data):
        self.set_status(response_data.get('code'))
        self.write(json.dumps(response_data))

        if self.requser and self.get_status() == 200 and (self.request.method != 'GET'):
            self.auditlog()

    def auditlog(self):
        if self.reqdata.get('password'):
            self.reqdata['password'] = '*' * 6

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
            with self.transaction():
                self.cursor.execute(insert_sql)
        except Exception as e:
            logger.error('Add auditlog failed: %s' % str(e))

    def select_sql_params(self, pk=0, fields=[], search_fields=[]):
        where, limit, order = '', '', ''
        if pk:
            where = 'WHERE id="%d"' % pk
        elif self.request.arguments:
            if not self.get_argument('search', None):
                where_fields = [field for field in fields if self.get_argument(field, None) != None]
                if where_fields:
                    where = ' WHERE %s' % ' and '.join(
                        ['%s in (%s)' % (field, ','.join(
                            ['"%s"' % pymysql.escape_string(v) for v in self.get_arguments(field)]))
                         for field in where_fields])
            else:
                where = 'WHERE concat(%s) like "%%%s%%"' % (','.join(search_fields),
                                                            pymysql.escape_string(self.get_argument('search')))

            if self.get_argument('offset', None) and self.get_argument('limit', None):
                limit = 'LIMIT %s, %s' % (pymysql.escape_string(self.get_argument('offset')),
                                          pymysql.escape_string(self.get_argument('limit')))

            if self.get_argument('order', None) and self.get_argument('sort', None):
                order = 'ORDER BY %s %s' % (pymysql.escape_string(self.get_argument('sort')),
                                            pymysql.escape_string(self.get_argument('order')))
        return where, order, limit


class BaseWebsocketHandler(tornado.websocket.WebSocketHandler, InitHandler):
    def __init__(self, *args, **kwargs):
        super(BaseWebsocketHandler, self).__init__(*args, **kwargs)
        try:
            self.init_db()
            self.init_cursor()
            self.init_session()
            self.init_requser()
        except Exception as e:
            logger.error('Initialize failed: %s' % str(e))
            self.write_message(json.dumps(dict(code=500, msg='Internal Server Error')))
            self.on_finish()
