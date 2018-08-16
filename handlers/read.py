# Created by zhouwang on 2018/5/23.
from .base import BaseRequestHandler, permission
import subprocess
import tornado
import re
import paramiko
import tornado.log
import logging
logger = logging.getLogger()

def get_valid(func):
    def _wrapper(self):
        error = {}
        logfile_id = self.get_argument('logfile_id', '')
        search_pattern = self.get_argument('search_pattern', '')
        page = self.get_argument('page', '0') or '0'

        if not logfile_id:
            error['logfile_id'] = '日志文件是必选项'
        else:
            select_sql = 'SELECT * FROM logfile WHERE id="%s"' % (int(logfile_id))
            self.mysqldb_cursor.execute(select_sql)
            self.logfile = self.mysqldb_cursor.fetchone()
            if not self.logfile:
                error['logfile_id'] = '日志文件不存在'

        if search_pattern:
            try:
                re.search(r'%s' % search_pattern, '')
            except:
                error['search_pattern'] = '不正确的正则表达式'

        if not page.isnumeric():
            page = 0

        if error:
            self._write({'code': 400, 'msg': 'Bad GET param', 'error': error})
            return
        self.search_pattern = search_pattern
        self.page = int(page)
        return func(self)
    return _wrapper


def ssh_conn(func):
    def _wrapper(self):
        if self.logfile.get('location') == 2:
            try:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(self.logfile.get('host'), **self.application.settings.get('ssh'))
            except Exception as e:
                logger.error('Read logfile failed: %s' % str(e))
                return {'code': 500, 'msg': 'Read logfile failed', 'detail':str(e)}
        response = func(self)
        if self.ssh_client:
            self.ssh_client.close()
        return response
    return _wrapper


class Handler(BaseRequestHandler):
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.logfile = None
        self.page = None
        self.search_pattern = None
        self.ssh_client = None


    @permission()
    @get_valid
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        response = yield tornado.gen.Task(self.read_local_logfile)
        self._write(response)


    def command(self, cmd):
        if self.logfile.get('location') == 1:
            status, output = subprocess.getstatusoutput(cmd)
        else:
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            status = stdout.channel.recv_exit_status()
            output = str(stdout.read(), encoding='utf-8') if status == 0 else str(stderr.read(), encoding='utf-8')
        return status, output


    @tornado.gen.coroutine
    @ssh_conn
    def read_local_logfile(self):
        path = self.logfile.get('path')
        try:
            status, output = self.command('wc -c %s' % path)
            if status != 0:
                raise Exception('get size error, %d, %s' % (status, output))
            total_size = int(output.split()[0].strip())

            status, output = self.command('wc -l %s' % path)
            if status != 0:
                raise Exception('get lines error, %d, %s' % (status, output))
            total_lines = int(output.split()[0].strip())

            total_pages = (total_lines // 1000) + (1 if total_lines % 1000 else 0) if total_lines else 1

            page = total_pages if self.page == 0 or self.page > total_pages else self.page
            grep = '| grep -E "%s"' % self.search_pattern if self.search_pattern else ''
            read_cmd = 'head -n %d %s | tail -n 1000 %s' % (page * 1000, path, grep) if page < (total_pages/2) \
                else 'tail -n +%d %s | head -n 1000 %s' % (((page-1) * 1000) + 1, path, grep)

            status, output = self.command(read_cmd)
            if status > 0 and output:
                raise Exception('get contents error, %d, %s' % (status, output))
        except Exception as e:
            logger.error('Read logfile failed: %s' % str(e))
            return {'code': 500, 'msg': 'Read logfile failed', 'detail': str(e)}

        size = len(output)
        contents = output.splitlines()
        return {'code': 200, 'msg': 'Read logfile successful', 'data': {'contents': contents, 'page': page,
            'total_pages': total_pages, 'total_size': total_size, 'total_lines': total_lines, 'size': size,
            'lines': len(contents)}}
