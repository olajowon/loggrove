# Created by zhouwang on 2018/5/23.
from .base import BaseRequestHandler, permission
import os
import time
import re

def get_valid(func):
    def _wrapper(self):
        error = {}
        path = self.get_argument('path', '')
        search_pattern = self.get_argument('search_pattern', '')

        if not path:
            error['path'] = '文件路径是必填项'
        elif not os.path.isfile(path):
            error['path'] = '文件路径[本地]不存在'
        elif not os.access(path, os.R_OK):
            error['path'] = '文件不可读'

        if search_pattern:
            try:
                re.search(r'%s' % search_pattern, '')
            except:
                error['search_pattern'] = '不正确的正则表达式'

        if error:
            self._write({'code': 400, 'msg': 'Bad GET param', 'error': error})
            return
        return func(self)
    return _wrapper


class Handler(BaseRequestHandler):
    @permission()
    @get_valid
    def get(self):
        page = self.get_argument('page', '0') or '0'
        path = self.get_argument('path', '')
        search_pattern = self.get_argument('search_pattern', '')
        logfile_size = os.path.getsize(path)
        page_count = (logfile_size // 1048576) + (1 if logfile_size % 1048576 else 0) if logfile_size else 1

        if not page.isnumeric():
            page = page_count
        elif int(page) == 0 or int(page) > page_count:
            page = page_count
        else:
            page = int(page)

        begin_position = (page - 1) * 1048576
        with open(path, 'r') as logfile:
            logfile.seek(begin_position)
            try:
                page_content = logfile.read(1048576)
                page_content += logfile.readline()
            except Exception as e:
                self._write({'code': 500, 'msg': 'Read lines failed, %s' % str(e)})
                return
            else:
                page_size = logfile.tell() - begin_position
                lines = page_content.split('\n')
                page_line_count= len(lines)
                if search_pattern:
                    lines = [line for line in lines if re.search(search_pattern, line)]

                self._write({'code': 200, 'msg': 'Read successful', 'data': {'lines': lines, 'page': page,
                                                                        'page_count': page_count,
                                                                        'logfile_size': logfile_size,
                                                                        'page_size': page_size,
                                                                        'page_line_count': page_line_count
                                                                        }})
                return

