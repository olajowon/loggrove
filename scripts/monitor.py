# -*- coding: utf-8 -*-
# Created by zhouwang on 2019/7/26.
from apscheduler.schedulers.background import BackgroundScheduler
from queue import Queue
import requests
import threading
import time
import os
import glob
import re
import json
import sys
import getopt
import logging

logging.basicConfig(
    filename='/tmp/loggrove_monitor.log',
    filemode='w',
    format='{"datetime":"%(asctime)s", "lineno":"%(lineno)d", "name":"%(name)s", '
           '"level":"%(levelname)s", "message":"%(message)s"}',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

HOST = None
SERVER = None
LOGFILES = []
POSITION_MAP = {}
REPORT_QUEUE = Queue()
ALERTING_QUEUE = Queue()


def usage():
    print('''
    Usage:
        -s --server Loggrove服务器HTTP地址， 如：http://loggrove
        -h --host   主机地址，与Loggrove录入的主机地址一致，如：localhost
        --help      帮助
    ''')


def make_logfiles():
    ''' 从loggrove 更新日志 '''
    global LOGFILES
    params = {'host': HOST}
    url = '%shost_logfiles/' % SERVER if SERVER.endswith('/') else '%s/host_logfiles/' % SERVER
    while True:
        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            resp_json = resp.json()
            logfiles = resp_json.get('data')
            for logfile in logfiles:
                paths = glob.glob(logfile['path'])
                paths = [path for path in paths if os.path.isfile(path)]
                monitor_choice = logfile['monitor_choice']
                logfile['path'] = sorted(paths)[monitor_choice] if paths else ''
            LOGFILES = logfiles
        except Exception as e:
            logging.error('make_logfiles error, %s' % str(e))
        else:
            logging.info('make_logfiles successful')
        time.sleep(60)


def send_alert():
    ''' 发送报警 '''
    while True:
        if ALERTING_QUEUE.empty() is False:
            webhook, content = ALERTING_QUEUE.get()
            try:
                payload = {
                    'msgtype': 'text',
                    'text': {
                        'content': content
                    },
                    'at': {
                        'isAtAll': True
                    }
                }
                requests.post(
                    webhook,
                    data=json.dumps(payload),
                    headers={'content-type': 'application/json'}
                )
            except Exception as e:
                logging.error('send_alert error, %s' % (str(e)))
            else:
                logging.info('send_alert successful')
        else:
            time.sleep(5)


def monitor_report():
    ''' 上报至loggrove '''
    url = '%smonitor_report/' % SERVER if SERVER.endswith('/') else '%s/monitor_report/' % SERVER
    while True:
        try:
            counts = []
            while not REPORT_QUEUE.empty():
                fileid, count_map, strtime = REPORT_QUEUE.get()
                for itemid, count in count_map.items():
                    counts.append([fileid, HOST, itemid, count, strtime])
            data = dict(host=HOST, counts=json.dumps(counts))
            resp = requests.post(url, data=data)
            resp.raise_for_status()
        except Exception as e:
            logging.error('monitor_report error, %s' % str(e))
        else:
            logging.info('monitor_report successful')
        time.sleep(30)


class Monitor(threading.Thread):
    def __init__(self, logfile, begin_time):
        threading.Thread.__init__(self)
        self.fileid = logfile['id']
        self.filename = logfile['name']
        self.filepath = logfile['path']
        self.monitor_items = logfile['monitor_items']
        self.curr_time = (begin_time // 60) * 60
        self.curr_strtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(self.curr_time))
        self.host = HOST

    def run(self):
        try:
            open_position = os.path.getsize(self.filepath)  # 打开时的位置
            time.sleep(time.time() - self.curr_time)  # 等待日志经过一分钟
            end_position = os.path.getsize(self.filepath)  # 一分钟后的日志位置
            begin_position = self.get_begin_position(open_position, end_position)  # 开始读取的位置

            logging.info('Monitor run, %s, %s, %s, [%s-%s]' %
                         (self.curr_strtime, self.filename, self.filepath, begin_position, end_position))

            # 统计匹配
            count_map = self.make_count_map()
            with open(self.filepath) as file:
                file.seek(begin_position)
                while file.tell() < end_position:
                    line = file.readline()
                    if line:
                        for item in self.monitor_items:
                            if re.search(item['match_regex'], line):
                                count_map[item['id']] += 1

            # put 到上报队列
            REPORT_QUEUE.put((self.fileid, count_map, self.curr_strtime))

            # 更新&存储 监控项的最近1500分钟数据
            monitor_item_counts = {}
            for itemid, count in count_map.items():
                counts = self.load_counts(self.fileid, itemid)
                counts.append([self.curr_time, count])
                counts = counts[-1500:]
                monitor_item_counts[itemid] = counts
                self.save_counts(self.fileid, itemid, counts)

            # 检查报警项 & put到报警队列
            alert_items = self.make_alert_items()
            for item in alert_items:
                min_time = self.curr_time - item['intervals'] * 60 + 60
                interval_counts = monitor_item_counts[item['id']][-(item['intervals']+5):]
                counts = [count[1] for count in interval_counts if count[0] >= min_time and count[0] <= self.curr_time]
                alerting, content = self.check_alerting(item, counts, min_time)
                if alerting:
                    ALERTING_QUEUE.put((item['webhook'], content))
        except Exception as e:
            logging.error('Monitor error, %s, %s, %s, %s' % (self.curr_strtime, self.filename, self.filepath, str(e)))
        else:
            logging.info('Monitor end, %s, %s, %s, [%s-%s]' %
                         (self.curr_strtime, self.filename, self.filepath, begin_position, end_position))

    def check_alerting(self, item, counts, min_time):
        ''' 检查报警项 '''
        alerting = False
        content = None
        min_strtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(min_time))
        if counts is []:
            alerting = True
            content = '- Loggrove 告警 -\n日志: %s\n监控: %s\n主机: %s\n路径: %s\n匹配: %s\n' \
                            '时间: %s:00 至 %s:59\n统计: %d 次\n\n 注意: 统计异常 ！！！\n\n' % \
                            (self.filename, item['name'], self.host, self.filepath, item['match_regex'], min_strtime,
                             self.curr_strtime, 'None')
        elif eval(item['expression'].format(sum(counts))):
            alerting = True
            content = '- Loggrove 告警 -\n日志: %s\n监控: %s\n主机: %s\n路径: %s\n匹配: %s\n' \
                            '时间: %s:00 至 %s:59\n统计: %d 次\n公式: %s\n\n' % \
                            (self.filename, item['name'], self.host, self.filepath, item['match_regex'], min_strtime,
                             self.curr_strtime, sum(counts), item['expression'])
        return alerting, content

    def make_count_map(self):
        ''' 生成统计字典 '''
        count_map = {}
        for item in self.monitor_items:
            count_map[item['id']] = 0
        return count_map

    def make_alert_items(self):
        ''' 获取当前时间应该判断是否报警的监控项 '''
        alert_items = []
        for item in self.monitor_items:
            if item['alert'] == 1 and (self.curr_time + 60) % (item['intervals'] * 60) == 0:
                alert_items.append(item)
        return alert_items

    def load_counts(self, fileid, itemid):
        ''' 从本地缓存文件获取历史统计 '''
        with open('/tmp/%s_%s_count' % (fileid, itemid), 'a+') as f:
            f.seek(0)
            content = f.read()
            try:
                counts = json.loads(content) if content else []
            except Exception as e:
                logging.warning('load_counts error, %s' % str(e))
                counts = []
        return counts

    def save_counts(self, fileid, itemid, counts):
        ''' 保存最近统计值 '''
        with open('/tmp/%s_%s_count' % (fileid, itemid), 'w+') as f:
            f.write(json.dumps(counts))

    def get_begin_position(self, open_position, end_position):
        ''' 综合判断文件开始读取位置 '''
        previous_end_position = POSITION_MAP.get(self.fileid)
        POSITION_MAP[self.fileid] = end_position

        if end_position < open_position:
            begin_position = 0
        elif previous_end_position is None:
            begin_position = open_position
        elif previous_end_position > end_position:
            begin_position = open_position
        else:
            begin_position = previous_end_position
        return begin_position


def monitor_basic():
    begin_time = time.time()
    threads = []
    for logfile in LOGFILES:
        threads.append(Monitor(logfile, begin_time))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


def main():
    logging.info('Loggrove-Monitor running...')
    print('Loggrove-Monitor running...')
    make_logfile_thread = threading.Thread(target=make_logfiles, daemon=True)  # 每60s 获取主机日志及监控项
    make_logfile_thread.start()
    send_alert_thread = threading.Thread(target=send_alert, daemon=True)       # 消费报警队列，进行告警
    send_alert_thread.start()
    monitor_report_thread = threading.Thread(target=monitor_report, daemon=True)    # 消费日志统计队列，上报给loggrove
    monitor_report_thread.start()

    scheduler = BackgroundScheduler()
    scheduler.add_job(monitor_basic, 'cron', minute='*/1', max_instances=8)  # 监控、统计、检查
    scheduler.start()

    while send_alert_thread.is_alive() and make_logfile_thread.is_alive() and monitor_report_thread.is_alive():
        time.sleep(5)
    logging.info('Loggrove-Monitor exit...')
    print('Loggrove-Monitor exit...')


def opt():
    global HOST, SERVER
    opts, args = getopt.getopt(sys.argv[1:], 'h:s:', ['host=', 'server=', 'help'])
    for op, value in opts:
        if op in ('-h', '--host'):
            HOST = value
        elif op in ('-s', '--server'):
            SERVER = value
        elif op == "--help":
            usage()
            sys.exit()

    if not HOST or not SERVER:
        usage()
        sys.exit()

if __name__ == '__main__':
    opt()
    main()