# Created by zhouwang on 2019/7/4.

from .base import BaseRequestHandler, permission
import subprocess
import os
import paramiko
import logging

logger = logging.getLogger()

def get_valid(func):
    def _wrapper(self):
        error = {}
        logfile = self.get_argument('logfile', '')
        host = self.get_argument('host', '')

        if not logfile:
            error['logfile'] = 'Required'
        else:
            select_sql = 'SELECT * FROM logfile WHERE name="%s"' % logfile
            self.cursor.execute(select_sql)
            logfile = self.cursor.dictfetchone()
            if not logfile:
                error['logfile'] = 'Not exist'

        if not host:
            error['host'] = 'Required'

        if host not in logfile.get('host').split(','):
            error['host'] = 'Not exist'

        if error:
            self._write(dict(code=400, msg='Bad GET param', error=error))
            return

        self.reqdata = dict(
            logfile=logfile,
            path=logfile.get('path'),
            host=host
        )

        return func(self)
    return _wrapper


def ssh_conn(func):
    def _wrapper(self):
        host = self.reqdata.get('host')
        if host not in ('localhost', '127.0.0.1'):
            try:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(host, **self.application.settings.get('ssh'))
            except Exception as e:
                logger.error('Query path failed: SSH connect, %s' % str(e))
                return self._write(dict(code=500, msg='Query failed', detail=str(e)))
        response = func(self)
        if self.ssh_client:
            self.ssh_client.close()
        return response

    return _wrapper


class Handler(BaseRequestHandler):
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.ssh_client = None

    @permission()
    @get_valid
    @ssh_conn
    def get(self):
        self.host = self.reqdata.get('host')
        self.path = self.reqdata.get('path')

        cmd = 'ls %s | sort' % self.path

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

        if status == 0:
            paths = output.split('\n')
            paths = sorted(list(set([path for path in paths if path])))
            self._write(dict(code=200, msg='Query successful', data=paths))
        else:
            self._write(dict(code=500, msg='Query failed', detail='Cmd: %s, Output: %s' % (cmd, output)))


