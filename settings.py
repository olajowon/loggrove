# Created by zhouwang on 2018/5/5.

import os

PROJECT_DIRS = os.path.dirname(os.path.abspath(__file__))

STATIC_PATH = os.path.join(PROJECT_DIRS, 'static')

TEMPLATE_PATH = os.path.join(PROJECT_DIRS, 'templates')

LOGIN_URL = '/login/html/'


MYSQL_DB = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'passwd': '123456',
    'db': 'loggrove',
    'charset': 'utf8',
    'autocommit': True,
}


LOGGING = {
    'options': {
        'logging': 'info', # 日志级别 (debug|info|warning|error|none)
        'log_file_prefix': '/tmp/loggrove.log', # 日志文件前缀
        'log_rotate_mode': 'time', # 日志切换模式 (time|size)
        'log_file_max_size': 1024 * 1024 * 1024, # 日志最大大小
        'log_file_num_backups': 10, # 日志最大备份数
        'log_rotate_when': 'D', # 指定按时间切换的类型 ('S', 'M', 'H', 'D', 'W0'-'W6')
        'log_rotate_interval': 1, # 按时间切换间隔
    },
    'formatter': {
        'fmt': '{"datetime":"%(asctime)s", "module":"%(module)s", "lineno":"%(lineno)d", "level":"%(levelname)s", "message":"%(message)s"}',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    }
}