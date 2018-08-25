# Created by zhouwang on 2018/5/17.

import re
import os
import asyncio
import threading
import time
import json
import paramiko
import pymysql
import subprocess
from .base import BaseWebsocketHandler, permission
import logging
logger = logging.getLogger()


def open_valid(func):
    def _wrapper(self):
        error = {}
        logfile_id = self.get_argument('logfile_id', '')
        search_pattern = self.get_argument('search_pattern', '')

        if not logfile_id:
            error['logfile_id'] = '日志文件是必选项'
        else:
            with self.mysqldb_conn.cursor(cursor=pymysql.cursors.DictCursor) as mysqldb_cursor:
                select_sql = 'SELECT * FROM logfile WHERE id="%s"' % (int(logfile_id))
                mysqldb_cursor.execute(select_sql)
                self.logfile = mysqldb_cursor.fetchone()
                if not self.logfile:
                    error['logfile_id'] = '日志文件不存在'
                elif self.logfile.get('location')=='1' and not os.path.isfile(self.logfile.get('path')):
                    error['logfile_id'] = '日志文件[本地]不存在'

        if search_pattern:
            try:
                re.search(r'%s' % search_pattern, '')
            except:
                error['search_pattern'] = '不正确的正则表达式'
        if error:
            message = {'code': 400, 'msg': 'Bad Param', 'error': error}
            self.write_message(message)
            self.close()
        else:
            for callback in self.registers:
                if callback.requser.get('username') == self.requser.get('username'):
                    message = {'code': 403,
                               'msg': 'New connection has been opened, and this connection needs to be closed'}
                    callback.write_message(message)
                    callback.close()
            self.registers.append(self)
            self.search_pattern = search_pattern
            return func(self)
    return _wrapper


class Handler(BaseWebsocketHandler):
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.logfile = None
        self.search_pattern = None
        self.read_contents = []
        self.ssh_client = None
        self.session = None
        self.transport = None
        self.lock = None


    registers = []

    @permission(role=3)
    @open_valid
    def open(self):
        self.loop = asyncio.get_event_loop()
        if self.logfile.get('location') == 1:
            thread = threading.Thread(target=self.kpread_local_logfile, daemon=True)
            thread.start()
        else:
            try:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(self.logfile.get('host'), **self.application.settings.get('ssh'))
                self.transport = self.ssh_client.get_transport()
                self.session = self.transport.open_session()
                self.session.get_pty('xterm')
            except Exception as e:
                logging.error('Keepread logfile failed: %s' % str(e))
                message = {'code': 500, 'msg': 'Keepread logfile failed', 'detail': str(e)}
                self.write_message(json.dumps(message))
                self.close()
            else:
                self.lock = threading.Lock()
                rthread = threading.Thread(target=self.kpread_remote_logfile, daemon=True)
                sthread = threading.Thread(target=self.kpsend_remote_logfile, daemon=True)
                rthread.start()
                sthread.start()


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
        with open(self.logfile.get('path')) as logfile:
            try:
                status, output = self.command('wc -l %s' % self.logfile.get('path'))
                if status != 0:
                    raise Exception('get total lines error, %d, %s' % (status, output))
                total_lines = int(output.split()[0].strip())

                logfile.seek(0, 2)
                total_size = logfile.tell()
                while self.ws_connection:
                    contents = logfile.readlines()
                    if contents:
                        total_size = logfile.tell()
                        total_lines += len(contents)

                        if self.search_pattern:
                            contents = [line for line in contents if re.search(self.search_pattern, line)]
                    data = {'contents': contents, 'total_size': total_size, 'total_lines':total_lines,
                            'lines': len(contents), 'size': len(''.join(contents))}
                    message = {'code': 0, 'msg': 'Read lines successful', 'data': data}
                    if self.ws_connection:
                        self.write_message(json.dumps(message))
                    time.sleep(3)
            except Exception as e:
                logging.error('Keepread logfile failed: %s' % str(e))
                if self.ws_connection:
                    message = {'code': 500, 'msg': 'Keepread logfile failed', 'detail': str(e)}
                    self.write_message(json.dumps(message))
            finally:
                if self.ws_connection:
                    self.close()
        logger.info('Keepread logfile end')


    def kpread_remote_logfile(self):
        asyncio.set_event_loop(self.loop)
        path = self.logfile.get('path')
        try:
            grep = '| grep -E "%s"' % self.search_pattern if self.search_pattern else ''
            cmd = 'tail -f %s %s' % (path, grep)
            self.session.exec_command(cmd)

            leftover = ''
            while self.ws_connection and self.transport.is_active():
                output = self.session.recv(1024).decode()
                if len(output) == 0:
                    break
                else:
                    output = leftover + output
                    endindex = output.rfind('\n') + 1
                    read_content, leftover = output[:endindex], output[endindex:]
                    self.lock.acquire()
                    self.read_contents += read_content.splitlines()
                    self.lock.release()
                time.sleep(0.5)
        except Exception as e:
            logging.error('Keepread logfile failed: %s' % str(e))
            if self.ws_connection:
                message = {'code': 500, 'msg': 'Keepread logfile failed', 'detail': str(e)}
                self.write_message(json.dumps(message))
        finally:
            if self.ws_connection:
                self.close()
        logger.info('Keepread logfile end')


    def kpsend_remote_logfile(self):
        asyncio.set_event_loop(self.loop)
        path = self.logfile.get('path')
        try:
            while self.ws_connection:
                status, output = self.command('wc -c %s' % path)
                if status != 0:
                    raise Exception('get size error, %d, %s' % (status, output))
                total_size = int(output.split()[0].strip())

                status, output = self.command('wc -l %s' % path)
                if status != 0:
                    raise Exception('get lines error, %d, %s' % (status, output))
                total_lines = int(output.split()[0].strip())

                if self.read_contents:
                    self.lock.acquire()
                    contents, self.read_contents = self.read_contents, []
                    self.lock.release()
                    data = {'contents': contents, 'total_size': total_size, 'total_lines': total_lines,
                            'lines': len(contents), 'size': len(''.join(contents))}
                else:
                    data = {'contents': [], 'total_size': total_size, 'total_lines': total_lines,
                            'lines': 0, 'size': 0}

                message = {'code': 0, 'msg': 'Keepread logfile successful', 'data': data}
                if self.ws_connection:
                    self.write_message(message)
                time.sleep(3)
        except Exception as e:
            logging.error('Keepsend logfile failed: %s' % str(e))
            if self.ws_connection:
                message = {'code': 500, 'msg': 'Keepread logfile failed', 'detail': str(e)}
                self.write_message(json.dumps(message))
        finally:
            if self.ws_connection:
                self.close()
        logger.info('Keepsend logfile end')


    def command(self, cmd):
        if self.logfile.get('location') == 1:
            status, output = subprocess.getstatusoutput(cmd)
        else:
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            status = stdout.channel.recv_exit_status()
            output = str(stdout.read(), encoding='utf-8') if status == 0 else str(stderr.read(), encoding='utf-8')
        return status, output