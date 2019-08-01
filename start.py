# Created by zhouwang on 2018/5/5.

import tornado.options
import tornado.web
import tornado.log
import tornado.httpserver
import urls
import settings
import logging
import pymysql
import pymysql.cursors


tornado.options.define('port', default=8800, help='Run on the given port', type=int)

#logging options
for key, value in settings.LOGGING['options'].items():
    tornado.options.options.__setattr__(key, value)

tornado.options.parse_command_line()

# log formatter
formatter = tornado.log.LogFormatter(**settings.LOGGING['formatter'])
logger = logging.getLogger()
for loghandler in logger.handlers:
    loghandler.setFormatter(formatter)

# mysqldb connect
db = pymysql.connect(**settings.MYSQL_DB)

application = tornado.web.Application(
    ssh = settings.SSH,
    ldap = settings.LDAP,
    db = db,
    handlers = urls.urlpatterns,
    template_path = settings.TEMPLATE_PATH,
    static_path = settings.STATIC_PATH,
    cookie_secret = 'qsefthukoplijygrdwa',
    login_url = settings.LOGIN_URL,
    debug = True,
    #xsrf_cookies = True,
    #websocket_ping_interval = settings.WEBSOCKET_PING_INTERVAL,
    #websocket_ping_timeout = settings.WEBSOCKET_PING_TIMEOUT,
)

http_server = tornado.httpserver.HTTPServer(application)
http_server.listen(tornado.options.options.port)
print('Loggrove running...')
try:
    tornado.ioloop.IOLoop.instance().start()
except Exception as e:
    print(e)
finally:
    db.close()