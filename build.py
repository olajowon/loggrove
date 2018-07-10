# Created by zhouwang on 2018/6/9.

import os
from settings import MYSQL_DB
import subprocess

NEW_SUPERADMIN = False


def python_packages():
    print('Step1: Install Python Packages')
    command = 'pip3 install -r requirements.txt'
    print('-->', command)
    status = os.system(command)
    if status != 0:
        exit()
    print('Step1: End.\n')

def mysql_db():
    print('Step2: Build Mysql Database')

    command = 'mysql -h%s -P%d -u%s -p%s -e \'CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARSET utf8 COLLATE utf8_general_ci;\'' \
              % (MYSQL_DB['host'], MYSQL_DB['port'], MYSQL_DB['user'], MYSQL_DB['passwd'], MYSQL_DB['db'])
    print('-->', command)
    status = os.system(command)
    if status != 0:
        exit()
    print('Step2: End.\n')

def mysql_tables():
    print('Step3: Build MySQL Tables:')
    command = 'mysql -h%s -P%d -u%s -p%s loggrove < tables.sql' % (MYSQL_DB['host'], MYSQL_DB['port'], MYSQL_DB['user'], MYSQL_DB['passwd'])
    print('-->', command)
    status = os.system(command)
    if status != 0:
        exit()
    print('Step3: End.\n')


def loggrove_admin():
    global NEW_SUPERADMIN

    print('Step5: Create Loggrove Superadmin')
    status, output = subprocess.getstatusoutput('mysql -h%s -P%d -u%s -p%s loggrove -e \'select "Existence of superadmin" from user where username="admin"\'' % (MYSQL_DB['host'], MYSQL_DB['port'], MYSQL_DB['user'], MYSQL_DB['passwd']))
    if status != 0:
        print(output)
        exit()

    if output.find('Existence of superadmin') < 0:
        sqltext = '''
        INSERT INTO user (username, password, fullname, email, join_time, status, role) VALUES ("admin", md5("loggrove"), "Admin", "admin@loggrove.com", now(), "1", "1");
        '''
        command = 'mysql -h%s -P%d -u%s -p%s loggrove -e \'%s\'' % (MYSQL_DB['host'], MYSQL_DB['port'], MYSQL_DB['user'], MYSQL_DB['passwd'], sqltext)
        print('-->', command)
        status = os.system(command)
        if status != 0:
            exit()
        NEW_SUPERADMIN = True
    else:
        print('Existence of Superadmin, Skip.\n')
    print('Step5: End.\n')


def monitor_cron():
    print('Step4: Create Monitoring Task On Crontab')
    monitor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'monitor.py')
    command = 'cat /var/spool/cron/`whoami` | grep %s' % monitor_path
    print('-->', command)
    status = os.system(command)
    if status == 0:
        print('Existence of Monitoring Task On Crontab, Skip.\n')
    else:
        command = 'echo -e "\\n* * * * * `which python3` %s >> /tmp/loggrove_monitor.log # loggrove_monitor\\n" >> /var/spool/cron/`whoami`' % (monitor_path)
        print('-->', command)
        status = os.system(command)
        if status != 0:
            exit()

    print('Step4: End.\n')


def main():
    print('### Loggrove Build ###')
    print('''   
要求：
    1: 已安装 Python36、PIP3、MySQL57、Crond，并保证 python3、pip3、mysql、crontab 命令可用；
    2: 已完成 settings.py > MYSQL_DB host、port、user、passwd 等配置；

步骤：
    1: 安装Python Packages
    2: 创建MySQL db，若存在则不进行创建动作
    3: 创建or更新 MySQL tables 结构
    4: 创建定时监控任务，若存在则不进行创建动作  
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
    python_packages()
    mysql_db()
    mysql_tables()
    monitor_cron()
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