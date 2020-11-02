# Created by zhouwang on 2018/5/23.
from .base import BaseRequestHandler, permission
import subprocess
import tornado
import re
import paramiko
import logging
import copy
import gevent
from gevent import monkey
monkey.patch_all()

logger = logging.getLogger()


def get_valid(func):
    def _wrapper(self):
        error = {}
        logfile = self.get_argument('logfile', '')
        path = self.get_argument('path', '')
        host = self.get_argument('host', '')
        match = self.get_argument('match', '')
        clean = self.get_argument('clean', 'false')
        page = self.get_argument('page', 1)
        posit = self.get_argument('posit', 'head')

        logfile_row = None
        if not logfile:
            error['logfile'] = 'Required'
        else:
            if logfile.isnumeric():
                select_sql = 'SELECT * FROM logfile WHERE id="%s"' % (int(logfile))
            else:
                select_sql = 'SELECT * FROM logfile WHERE name="%s"' % logfile

            self.cursor.execute(select_sql)
            logfile_row = self.cursor.dictfetchone()
            if not logfile_row:
                error['logfile'] = 'Not exist'

        if not path:
            error['path'] = 'Required'

        if not host:
            error['host'] = 'Required'
        elif logfile_row and host not in logfile_row['host'].split(','):
            error['host'] = 'Invalid host'

        if match:
            try:
                re.search(r'%s' % match, '')
            except:
                error['match'] = 'Incorrect regular expression'

        if not isinstance(page, int) and not page.isnumeric():
            error['page'] = 'Invalid page'

        if posit not in ('head', 'tail'):
            error['posit'] = 'Invalid posit'

        if error:
            self._write(dict(code=400, msg='Bad GET param', error=error))
            return

        self.match = match
        self.page = int(page)
        self.path = path
        self.host = host
        self.logfile = logfile
        self.clean = clean
        self.posit = posit
        return func(self)

    return _wrapper


def ssh_conn(func):
    def _wrapper(self):
        if self.host not in ('localhost', '127.0.0.1'):
            try:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(self.host, **self.application.settings.get('ssh'))
            except Exception as e:
                logger.error('Read logfile failed: %s' % str(e))
                return dict(code=500, msg='Read logfile failed', detail=str(e))
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
        self.match = None
        self.path = None
        self.host = None
        self.ssh_client = None
        self.clean = None
        self.posit = None
        self.total_lines = None
        self.match_lines = None
        self.contents = []
        self.total_pages = None
        self.tasks = []
        self.task_errors = []

    @permission()
    @get_valid
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        response = yield tornado.gen.Task(self.read_logfile)
        self._write(response)

    def command(self, cmd):
        if self.host in ('localhost', '127.0.0.1'):
            status, output = subprocess.getstatusoutput(cmd)
        else:
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            status = stdout.channel.recv_exit_status()
            out, err = str(stdout.read(), encoding='utf-8'), str(stderr.read(), encoding='utf-8')
            if status == 0:
                if err and not out:
                    status, output = 1, err
                else:
                    output = out
            else:
                output = err

        return status, output

    @tornado.gen.coroutine
    @ssh_conn
    def read_logfile(self):
        try:
            self.tasks = [
                gevent.spawn(self.make_total_lines),
                gevent.spawn(self.make_match_lines),
                gevent.spawn(self.make_contents),
            ]
            gevent.joinall(self.tasks)
            if self.task_errors:
                raise Exception('; '.join(self.task_errors))
            self.make_total_pages()
        except Exception as e:
            logger.error('Read logfile failed: %s' % str(e))
            return dict(code=500, msg='Read failed', detail=str(e))

        data = dict(
            contents=self.contents,
            page=self.page if self.total_pages != 0 else 0,
            total_pages=self.total_pages,
            total_lines=self.total_lines,
            match_lines=self.match_lines,
            lines=len(self.contents)
        )
        return dict(code=200, msg='Read successfule', data=data)

    def make_contents(self):
        if self.match and self.clean == 'true':
            read_cmd = 'grep -a "%s" %s | head -n %d | tail -n +%d' % \
                       (self.match, self.path, self.page * 1000, (self.page-1) * 1000 + 1)
        else:
            if self.posit == 'head':
                read_cmd = 'head -n %d %s | tail -n +%d' % (self.page * 1000, self.path, (self.page-1) * 1000 + 1)
            else:
                read_cmd = 'tail -n +%d %s | head -n 1000' % (((self.page - 1) * 1000) + 1, self.path)
        status, output = self.command(read_cmd)
        if status != 0:
            self.task_errors.append('get contents error, %d, %s' % (status, output))
        else:
            self.contents = output.splitlines()

    def make_total_lines(self):
        if self.page == 1:
            status, output = self.command('wc -l %s' % self.path)
            if status != 0:
                self.task_errors.append('get lines error, %d, %s' % (status, output))
            else:
                self.total_lines = int(output.split()[0].strip())

    def make_match_lines(self):
        if self.page == 1 and not self.match:
            while self.tasks[0].started:
                gevent.sleep(0.1)
            self.match_lines = copy.copy(self.total_lines)
        elif self.page == 1:
            status, output = self.command('grep -c "%s" %s' % (self.match, self.path))
            if status != 0 and status != 1:
                self.task_errors.append('get grep lines error, %d, %s' % (status, output))
            else:
                self.match_lines = int(output.split()[0].strip()) if status == 0 else 0

    def make_total_pages(self):
        if self.page == 1 and self.clean == 'true':
            self.total_pages = (self.match_lines // 1000) + (1 if self.match_lines % 1000 else 0) \
                if self.match_lines else 0
        elif self.page == 1:
            self.total_pages = (self.total_lines // 1000) + (1 if self.total_lines % 1000 else 0) \
                if self.total_lines else 0
