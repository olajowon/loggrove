# Created by zhouwang on 2018/5/5.

import tornado.options
import tornado.web
import tornado.log
import tornado.httpserver
import urls
import settings
import os
import sys
import logging
import pymysql
import pymysql.cursors

sys.path.append(os.path.join(settings.PROJECT_DIRS, '..'))
sys.path.append(os.path.dirname(__file__))

tornado.options.define('port', default=8800, help='Run on the given port', type=int)

for key, value in settings.LOGGING['options'].items():
    tornado.options.options.__setattr__(key, value)

tornado.options.parse_command_line()

formatter = tornado.log.LogFormatter(**settings.LOGGING['formatter'])
logger = logging.getLogger()
for loghandler in logger.handlers:
    loghandler.setFormatter(formatter)

mysqldb = settings.MYSQL_DB
mysqldb_conn = pymysql.connect(**mysqldb)

application = tornado.web.Application(
    mysqldb_conn = mysqldb_conn,
    handlers = urls.handlers,
    template_path = settings.TEMPLATE_PATH,
    static_path = settings.STATIC_PATH,
    cookie_secret = 'qsefthukoplijygrdwa',
    login_url = settings.LOGIN_URL,
    debug = True,
    xsrf_cookies = True
)

http_server = tornado.httpserver.HTTPServer(application)
http_server.listen(tornado.options.options.port)
print('Loggrove running...')
try:
    tornado.ioloop.IOLoop.instance().start()
except Exception as e:
    print(e)
finally:
    mysqldb_conn.close()