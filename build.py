# Created by zhouwang on 2018/6/9.

import os
from settings import MYSQL_DB
import subprocess
import random
import string
import hashlib
import time

NEW_SUPERADMIN = False

def tools():
    print('Step1: Install Tools')
    command = 'yum install -y openldap openldap-devel'
    print('-->', command)
    status = os.system(command)
    if status != 0:
        exit()
    print('Step1: End.\n')

def python_packages():
    print('Step2: Install Python Packages')
    command = 'pip3 install -r requirements.txt'
    print('-->', command)
    status = os.system(command)
    if status != 0:
        exit()
    print('Step2: End.\n')

def mysql_db():
    print('Step3: Build Mysql Database')
    command = 'mysql -h%s -P%d -u%s -p%s -e \'CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARSET utf8 COLLATE utf8_general_ci;\'' \
              % (MYSQL_DB['host'], MYSQL_DB['port'], MYSQL_DB['user'], MYSQL_DB['password'], MYSQL_DB['db'])
    print('-->', command)
    status = os.system(command)
    if status != 0:
        exit()
    print('Step3: End.\n')

def mysql_tables():
    print('Step4: Build MySQL Tables:')
    command = 'mysql -h%s -P%d -u%s -p%s loggrove < tables.sql' % \
              (MYSQL_DB['host'], MYSQL_DB['port'], MYSQL_DB['user'], MYSQL_DB['password'])
    print('-->', command)
    status = os.system(command)
    if status != 0:
        exit()
    print('Step4: End.\n')

def loggrove_admin():
    global NEW_SUPERADMIN

    print('Step5: Create Loggrove Superadmin')
    status, output = subprocess.getstatusoutput(
        'mysql -h%s -P%d -u%s -p%s loggrove -e \'select "Existence of superadmin" from user where username="admin"\'' %
        (MYSQL_DB['host'], MYSQL_DB['port'], MYSQL_DB['user'], MYSQL_DB['password']))
    if status != 0:
        print(output)
        exit()

    if output.find('Existence of superadmin') < 0:
        salt = ''.join(random.sample(string.ascii_letters, 8))
        password = '%s%s' % (salt, hashlib.md5((salt + 'loggrove').encode('UTF-8')).hexdigest())
        sqltext = '''
        INSERT INTO user (username, password, fullname, email, join_time, status, role) 
        VALUES ("admin", "%s", "Admin", "admin@loggrove.com", now(), "1", "1");
        ''' % password
        command = 'mysql -h%s -P%d -u%s -p%s loggrove -e \'%s\'' % \
                  (MYSQL_DB['host'], MYSQL_DB['port'], MYSQL_DB['user'], MYSQL_DB['password'], sqltext)
        print('-->', command)
        status = os.system(command)
        if status != 0:
            exit()
        NEW_SUPERADMIN = True
    else:
        print('Existence of Superadmin, Skip.\n')
    print('Step5: End.\n')


def main():
    print('### Loggrove Build ###')
    print('''   
要求：
    1: 已安装 Python36、PIP3、MySQL57，并保证 python3、pip3、mysql、yum 命令可用；
    2: 已完成 settings.py > MYSQL_DB host、port、user、password, SSH username、password、port 等配置；

步骤：
    1: 安装依赖工具（yum）
    2: 安装Python包 （pip3）
    3: 创建MySQL db，若存在则不进行创建动作
    4: 创建or更新 MySQL tables 结构
    5: 创建超级管理员，若存在则不进行创建动作       
    ''')

    while True:
        put = input('开始(y/n):')
        if put == 'y':
            break
        if put == 'n':
            exit()

    print('\n')
    print('>>> Begin:\n')
    tools()
    python_packages()
    mysql_db()
    mysql_tables()
    loggrove_admin()
    print('End and successful. <<< \n')
    if NEW_SUPERADMIN:
        print(
            '''
# # # # Super Admin # # # #
#                         #
#   username: admin       #
#   password: loggrove    # 
#                         #
# # # # # # # # # # # # # #
            '''
        )


if __name__ == '__main__':
    main()