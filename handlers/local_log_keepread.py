# Created by zhouwang on 2018/5/17.

import tornado.websocket
import re
import os
import asyncio
import threading
import time
import json


def open_valid(func):
    def _wrapper(self):
        error = {}
        path = self.get_argument('path', '')
        search_pattern = self.get_argument('search_pattern', '')
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
            self.write_message(message)
            self.close()
            return
        return func(self)
    return _wrapper


class Handler(tornado.websocket.WebSocketHandler):
    @open_valid
    def open(self):
        self.path = self.get_argument('path')
        self.search_pattern = self.get_argument('search_pattern', '')
        self.keep = True
        data = {'lines': [], 'lines_quantity': 0, 'lines_size': 0, 'total_size': os.path.getsize(self.path)}
        message = {'code': 0, 'msg': 'Open ws successful', 'data': data, 'type': 'on_open'}
        self.write_message(json.dumps(message))
        self.loop = asyncio.get_event_loop()
        thread = threading.Thread(target=self.keep_read, daemon=True)
        thread.start()

    def on_close(self):
        self.keep = False

    def on_message(self, message):
        pass

    def keep_read(self):
        asyncio.set_event_loop(self.loop)
        with open(self.path) as logfile:
            logfile.seek(0, 2)
            try:
                while self.keep:
                    lines = logfile.readlines()
                    if lines:
                        total_size = logfile.tell()
                        if self.search_pattern:
                            lines = [line for line in lines if re.search(self.search_pattern, line)]
                        data = {'lines': lines, 'lines_quantity': len(lines),
                                'total_size': total_size, 'lines_size': len(''.join(lines))}
                        message = {'code': 0, 'msg': 'Read lines successful', 'data': data, 'type': 'on_message'}
                        if self.keep:
                            self.write_message(json.dumps(message))
                    time.sleep(3)
            except Exception as e:
                if self.keep:
                    message = {'code': 500, 'msg': 'Read lines failed, %s' % str(e), 'type': 'on_message'}
                    self.write_message(json.dumps(message))
            finally:
                if self.keep:
                    self.close()


    # def keep_read(self):
    #     # command = 'tail -f %s %s' % (self.path, '|grep "%s"' % self.search_pattern if self.search_pattern else '')
    #     # print(command)
    #     # self.subpopen = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    #     # while self.keep:
    #     #     print('read')
    #     #     line = self.subpopen.stdout.readline().decode()
    #     #     if len(line) == 0:
    #     #         break
    #     #     print(line)
    #     #     self.read_lines.append(line)
    #     # self.subpopen.kill()
    #     with open(self.path) as logfile:
    #         logfile.seek(0, 2)
    #         while self.keep:
    #             line = logfile.readline()
    #             print(line)
    #             if (line and not self.search_pattern) or \
    #                 (line and self.search_pattern and re.search(self.search_pattern, line)):
    #                 self.read_lines.append(line)
    #             elif not line:
    #                 time.sleep(1)
    #
    #     print('keep read end')
    #
    #
    # def keep_send(self):
    #     asyncio.set_event_loop(self.loop)
    #     while self.keep:
    #         total_size = os.path.getsize(self.path)
    #         if self.read_lines:
    #             lines, self.read_lines = self.read_lines, []
    #             print(len(''.join(lines)))
    #             data = {'lines': lines, 'lines_quantity': len(lines),
    #                     'total_size': total_size, 'lines_size': len(''.join(lines))}
    #             message = {'code': 0, 'msg': 'read lines successful', 'data': data, 'type': 'on_message'}
    #             if self.keep:
    #                 self.write_message(message)
    #         time.sleep(3)
    #     print('keep send end')