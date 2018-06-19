# Created by zhouwang on 2018/5/17.

import tornado.websocket
import datetime
import json
import re
import os
#import time


def register_valid(func):
    def _wrapper(self):
        error = {}
        path = self.callback.get_argument('path', '')
        search_pattern = self.callback.get_argument('search_pattern', '')

        if not path:
            error['path'] = '文件路径是必选项'
        elif not os.path.isfile(path):
            error['path'] = '文件路径不存在'
        elif not os.access(path, os.R_OK):
            error['path'] = '文件不可读'

        if search_pattern:
            try:
                re.search(r'%s' % search_pattern, '')
            except:
                error['search_pattern'] = '不正确的正则表达式'

        if error:
            message = {'code': 400, 'msg': 'Bad Param', 'error': error, 'type':'on_open'}
            self.trigger(self.callback, message)
            self.callback.close()
            return False
        return func(self)
    return _wrapper


class LocalLogKeepRead():
    keep_callbacks = {}
    def __init__(self, callback):
        self.callback = callback

    @register_valid
    def register(self):
        now_time = datetime.datetime.now()
        path = self.callback.get_argument('path')
        logfile = open(path, 'r')
        logfile.seek(0, 2)
        position = logfile.tell()
        search_pattern = self.callback.get_argument('search_pattern', '')
        self.keep_callbacks[self.callback] = {
            'register_time': now_time,
            'begin_position': position,
            'position': position,
            'search_pattern': search_pattern,
            'path': self.callback.get_argument('path'),
            'logfile': logfile
        }
        data = {'lines':['连接成功 [Connection successful] ...'], 'read_line_count':0, 'logfile_size':position}
        message = {'code': 0, 'msg':'Open link successful', 'data':data, 'type':'on_open'}
        self.trigger(self.callback, message)

    def unregister(self):
        if self.callback in self.keep_callbacks:
            self.keep_callbacks[self.callback]['logfile'].close()
            del self.keep_callbacks[self.callback]


    def read_loglines(self):
        #begin_time = time.time()

        logfile = self.keep_callbacks[self.callback]['logfile']

        try:
            lines = logfile.readlines()
        except Exception as e:
            message = {'code': 500, 'msg': 'Read lines failed, %s' % str(e), 'type': 'on_message'}
            self.trigger(self.callback, message)
            self.callback.close()
            return

        read_line_count = len(lines)
        search_pattern = self.keep_callbacks[self.callback]['search_pattern']
        if search_pattern:
            lines = [line for line in lines if re.search(search_pattern, line)]

        if read_line_count:
            self.keep_callbacks[self.callback]['position'] = logfile.tell()

        data = {'lines':lines, 'read_line_count':read_line_count,
                'logfile_size':self.keep_callbacks[self.callback]['position']}
        message = {'code': 0, 'msg': 'read lines successful', 'data': data, 'type':'on_message'}
        #print('use time', time.time() - begin_time)
        self.trigger(self.callback, message)


    def trigger(self, callback, message):
        callback.write_message(json.dumps(message))


class Handler(tornado.websocket.WebSocketHandler):
    '''
        Keep read local log @ websocket
    '''
    def open(self):
        LocalLogKeepRead(self).register()

    def on_close(self):
        LocalLogKeepRead(self).unregister()

    def on_message(self, message):
        LocalLogKeepRead(self).read_loglines()