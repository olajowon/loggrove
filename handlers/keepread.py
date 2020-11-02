# Created by zhouwang on 2018/5/17.

import re
import os
import asyncio
import threading
import time
import json
import paramiko
import pymysql
from .base import BaseWebsocketHandler, permission
import logging

logger = logging.getLogger()


def open_valid(func):
    def _wrapper(self):
        error = {}
        logfile = self.get_argument('logfile', '')
        match = self.get_argument('match', '')
        path = self.get_argument('path', '')
        host = self.get_argument('host', '')

        if not logfile:
            error['logfile'] = 'Required'
        else:
            if logfile.isnumeric():
                select_sql = 'SELECT * FROM logfile WHERE id="%s"' % (int(logfile))
            else:
                select_sql = 'SELECT * FROM logfile WHERE name="%s"' % pymysql.escape_string(logfile)

            self.cursor.execute(select_sql)
            logfile_row = self.cursor.dictfetchone()
            if not logfile_row:
                error['logfile'] = 'Not exist'

        if match:
            try:
                re.search(r'%s' % match, '')
            except:
                error['match'] = 'Incorrect format'

        if not path:
            error['path'] = 'Required'

        if not host:
            error['host'] = 'Required'
        elif logfile_row and host not in logfile_row['host'].split(','):
            error['host'] = 'Invalid host'

        if error:
            message = dict(code=400, msg='Bad Param', error=error)
            self.write_message(message)
            self.close()
        else:
            for callback in self.registers:
                if callback.requser.get('username') == self.requser.get('username'):
                    message = dict(code=403,
                                   msg='New connection has been opened, and this connection needs to be closed')
                    callback.write_message(message)
                    callback.close()
            self.registers.append(self)
            self.match = match
            self.path = path
            self.host = host
            self.logfile = logfile
            return func(self)

    return _wrapper


class Handler(BaseWebsocketHandler):
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.logfile = None
        self.path = None
        self.match = None
        self.host = None
        self.ssh_client = None
        self.session = None
        self.transport = None
        self.loop = None

    registers = []

    @permission(role=3)
    @open_valid
    def open(self):
        self.loop = asyncio.get_event_loop()
        if self.host in ('localhost', '127.0.0.1'):
            thread = threading.Thread(target=self.kpread_local_logfile, daemon=True)
            thread.start()
        else:
            try:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(self.host, **self.application.settings.get('ssh'))
                self.transport = self.ssh_client.get_transport()
                self.session = self.transport.open_session()
                self.session.get_pty('xterm')
            except Exception as e:
                logging.error('Keepread logfile failed: %s' % str(e))
                message = dict(code=500, msg='Keepread logfile failed', detail=str(e))
                self.write_message(json.dumps(message))
                self.close()
            else:
                thread = threading.Thread(target=self.kpread_remote_logfile, daemon=True)
                thread.start()

    def on_close(self):
        if self.ssh_client:
            if self.session:
                if not self.session.closed:
                    self.session.send('\x03')
                    self.session.close()
            self.ssh_client.close()
        self.registers.remove(self)
        logger.info('Keepread logfile connection closed, %s' % self)

    def kpread_local_logfile(self):
        asyncio.set_event_loop(self.loop)
        try:
            with open(self.path) as logfile:
                logfile.seek(0, 2)
                keep_lines = 0
                while self.ws_connection:
                    contents = logfile.readlines()
                    if contents and self.match:
                        contents = [line for line in contents if re.search(self.match, line)]
                    lines = len(contents)
                    keep_lines += lines
                    data = dict(contents=contents, lines=lines, keep_lines=keep_lines)
                    message = dict(code=0, msg='Keepread logfile successful', data=data)
                    if self.ws_connection:
                        self.write_message(json.dumps(message))
                    time.sleep(3)
        except Exception as e:
            logging.error('Keepread logfile failed: %s' % str(e))
            if self.ws_connection:
                message = dict(code=500, msg='Keepread logfile failed', detail=str(e))
                self.write_message(json.dumps(message))
        finally:
            if self.ws_connection:
                self.close()
        logger.info('Keepread logfile end')

    def kpread_remote_logfile(self):
        asyncio.set_event_loop(self.loop)
        try:
            grep = '| grep "%s"' % self.match if self.match else ''
            cmd = 'tail -f %s %s' % (self.path, grep)
            self.session.exec_command(cmd)
            leftover = ''
            keep_lines = 0
            while self.ws_connection and self.transport.is_active():
                output = self.session.recv(65535).decode()
                if len(output) == 0:
                    break
                else:
                    output = leftover + output
                    endindex = output.rfind('\n') + 1
                    read_content, leftover = output[:endindex], output[endindex:]
                    contents = read_content.splitlines()
                    lines = len(contents)
                    keep_lines += lines
                    data = dict(contents=contents, lines=lines, keep_lines=keep_lines)
                    message = dict(code=0, msg='Keepread logfile successful', data=data)
                    if self.ws_connection:
                        self.write_message(message)
                time.sleep(0.5)
        except Exception as e:
            logging.error('Keepread logfile failed: %s' % str(e))
            if self.ws_connection:
                message = dict(code=500, msg='Keepread logfile failed', detail=str(e))
                self.write_message(json.dumps(message))
        finally:
            if self.ws_connection:
                self.close()
        logger.info('Keepread logfile end')