# Created by zhouwang on 2018/5/5.

import os

PROJECT_DIRS = os.path.dirname(os.path.abspath(__file__))

STATIC_PATH = os.path.join(PROJECT_DIRS, 'static')

TEMPLATE_PATH = os.path.join(PROJECT_DIRS, 'templates')

LOGIN_URL = '/login/html/'


MYSQL_DB = {
    'host': '<host>',      # 请不要使用localhost,127.0.0.1等本地地址，这些地址会导致生成的监控脚本在远程日志主机上无法连接数据库
    'port': <port>,
    'user': '<user>',
    'password': '<password>',
    'db': 'loggrove',
    'charset': 'utf8',
    'autocommit': True,
}

SSH = {
    'username': 'root',                      # 请使用 root，避免权限不够
    'password': '<password>',                # 使用公私钥认证时，密码可为空
    'port': 22,
#    'key_filename': '~/.ssh/id_rsa',        # 指定用户私钥文件路径，启用后优先使用公私钥验证且不能为空
    'timeout': 5
}

LOGGING = {
    'options': {
        'logging': 'info',                              # 日志级别 (debug|info|warning|error|none)
        'log_file_prefix': '/tmp/loggrove.log',         # 日志文件前缀
        'log_rotate_mode': 'time',                      # 日志切换模式 (time|size)
        'log_file_max_size': 1024 * 1024 * 1024,        # 日志最大大小
        'log_file_num_backups': 10,                     # 日志最大备份数
        'log_rotate_when': 'D',                         # 指定按时间切换的类型 ('S', 'M', 'H', 'D', 'W0'-'W6')
        'log_rotate_interval': 1,                       # 按时间切换间隔
    },
    'formatter': {
        'fmt': '{"datetime":"%(asctime)s", "module":"%(module)s", "lineno":"%(lineno)d", '
               '"level":"%(levelname)s", "message":"%(message)s"}',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    }
}


WEBSOCKET_PING_INTERVAL = 30
WEBSOCKET_PING_TIMEOUT = 5

