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

def render_monitor_py():
    print('Step5: Render Monitor Script')
    import jinja2
    j2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'monitor.py.jinja2')
    py = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'monitor.py')
    print('-->', py)
    with open(py, 'w') as f:
        f.write(jinja2.Template(open(j2).read()).render(mysqldb=MYSQL_DB,
                                                        render_date=time.strftime('%Y/%m/%d', time.localtime())))
    print('Step5: End.\n')

def local_monitor_cron():
    print('Step6: Create Localhost Monitoring Task On Crontab')
    monitor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'monitor.py')
    command = 'cat /var/spool/cron/`whoami` | grep %s' % 'loggrove_monitor'
    print('-->', command)
    status = os.system(command)
    if status == 0:
        print('Existence of Monitoring Task On Crontab, Skip.\n')
    else:
        command = 'echo -e "\\n* * * * * `which python3` %s localhost >> ' \
                  '/tmp/loggrove_monitor.log # loggrove_monitor\\n" >> /var/spool/cron/`whoami`' % (monitor_path)
        print('-->', command)
        status = os.system(command)
        if status != 0:
            exit()

    print('Step6: End.\n')

def loggrove_admin():
    global NEW_SUPERADMIN

    print('Step7: Create Loggrove Superadmin')
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
    print('Step7: End.\n')


def main():
    print('### Loggrove Build ###')
    print('''   
要求：
    1: 已安装 Python36、PIP3、MySQL57、Crond，并保证 python3、pip3、mysql、crontab、yum 命令可用；
    2: 已完成 settings.py > MYSQL_DB host、port、user、password, SSH username、password、port 等配置；

步骤：
    1: 安装依赖工具（yum）
    2: 安装Python包 （pip3）
    3: 创建MySQL db，若存在则不进行创建动作
    4: 创建or更新 MySQL tables 结构
    5: 渲染生成监控脚本，若存在则进行覆盖
    6: 创建本地监控任务，若存在则不进行创建动作（注：远程主机需要手动添加监控任务，详情查看README）  
    7: 创建超级管理员，若存在则不进行创建动作       
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
    render_monitor_py()
    local_monitor_cron()
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