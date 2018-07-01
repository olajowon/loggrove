# Created by zhouwang on 2018/5/16.

from .base import BaseRequestHandler
import hashlib

class Handler(BaseRequestHandler):
    ''' login '''
    def post(self):
        self.logout()   #退出登录

        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        error = {}
        if not username:
            error['username'] = '用户名是必填项'
        if not password:
            error['password'] = '密码是必填项'

        if username and password:
            select_sql = 'SELECT id,username,password,status FROM user WHERE username="%s" and password="%s"' % \
                         (username, hashlib.md5(password.encode('UTF-8')).hexdigest())
            count = self.mysqldb_cursor.execute(select_sql)
            user = self.mysqldb_cursor.fetchone()

            if not user:
                error['username'] = '用户名或密码错误'
                error['password'] = '用户名或密码错误'
            elif user.get('status') != 1:
                error['username'] = '用户已禁用'

        if error:
            response_data = {'code':400, 'msg':'Bad POST data', 'error':error}
        else:
            self.reqdata = {    # 用于存储操作记录
                'username': username,
                'password': '*' * 6     # 隐藏密码
            }
            response_data = self.login(user)    # 登录用户
        self._write(response_data)

