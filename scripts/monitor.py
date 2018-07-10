# Created by zhouwang on 2018/6/13.

import pymysql
import threading
import time
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
import requests
import json
import traceback
from settings import MYSQL_DB

def query_files(cursor):
    select_sql = 'SELECT id,path FROM local_log_file'
    cursor.execute(select_sql)
    results = cursor.fetchall()
    return results

thread_lock = threading.Lock()
class MonitorCount(threading.Thread):
    def __init__(self, fileid, filepath, conn, cursor, str_time, mk_time, begin_time):
        threading.Thread.__init__(self)
        self.fileid = fileid
        self.filepath = filepath
        self.conn = conn
        self.cursor = cursor
        self.str_time = str_time
        self.mk_time = mk_time
        self.begin_time = begin_time
        self.count = {}
        self.search = []

    def run(self):
        open_position = os.path.getsize(self.filepath)
        time.sleep(60 - (time.time() - self.begin_time))
        end_position = os.path.getsize(self.filepath)

        with open('/tmp/%d_position' % self.fileid, 'a+') as pfile:
            pfile.seek(0)
            content = pfile.read()
            previous_end_position = None
            if content:
                previous_end_position = int(content)
                pfile.seek(0)
                pfile.truncate()
            pfile.write(str(end_position))


        if end_position < open_position:
            begin_position = 0
        elif previous_end_position == None:
            begin_position = open_position
        elif previous_end_position > end_position:
            begin_position = open_position
        else:
            begin_position = previous_end_position

        monitor_items = self.select_monitor_items()
        self.counts, self.alerts = {}, []

        for item in monitor_items:
            self.counts[item['id']] = 0

            if item['alert'] == 1 and self.mk_time%(item['check_interval']*60) == 0:
                self.alerts.append(item)

        self.counts[0] = 0

        with open(self.filepath) as file:
            file.seek(begin_position)
            while True:
                line = file.readline()
                if line:
                    self.counts[0] += 1
                    for item in monitor_items:
                        if re.search(item['search_pattern'], line):
                            self.counts[item['id']] += 1

                if file.tell() >= end_position:
                    break

        inserts = [(self.fileid, itemid, count, self.str_time) for itemid, count in self.counts.items()]

        thread_lock.acquire()
        try:
            self.cursor.executemany('INSERT INTO local_log_monitor_count (local_log_file_id, monitor_item_id, count, count_time) VALUES(%s, %s, %s, %s)', inserts)
        except Exception as e:
            self.conn.rollback()
            print('Insert %s monitor count faild, %s' % (self.filepath, str(e)))
            print(traceback.format_exc())
        thread_lock.release()


        for alert in self.alerts:
            min_str_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(self.mk_time))
            select_sql = '''
                SELECT
                  SUM(count) as count_sum
                FROM
                  local_log_monitor_count
                WHERE
                  local_log_file_id="%d"
                AND 
                  monitor_item_id="%d"
                AND 
                  count_time >="%s" 
            ''' % (self.fileid, alert['id'], min_str_time)
            thread_lock.acquire()
            self.cursor.execute(select_sql)
            results = self.cursor.fetchall()
            thread_lock.release()

            if results:
                alert_content = None
                if results[0]['count_sum'] is None:
                    alert_content = '# Loggrove 告警\n文件: %s\n匹配: %s\n时间: %s 至 %s\n统计: %d 次\n\n 注意: 统计异常 ！！！\n\n' % \
                              (self.filepath, alert['search_pattern'], min_str_time,
                               self.str_time, 'None')

                elif eval(alert['trigger_format'].format(results[0].get('count_sum'))):
                    alert_content = '# Loggrove 告警\n文件: %s\n匹配: %s\n时间: %s 至 %s\n统计: %d 次\n公式: %s\n\n' % \
                              (self.filepath, alert['search_pattern'], min_str_time,
                               self.str_time, results[0]['count_sum'], alert['trigger_format'])

                if alert_content:
                    try:
                        payload = {
                            'msgtype': 'text',
                            'text': {
                                'content': alert_content
                            },
                            'at': {
                                'isAtAll': True
                            }
                        }
                        requests.post(
                            alert['dingding_webhook'],
                            data=json.dumps(payload),
                            headers={'content-type': 'application/json'}
                        )
                    except Exception as e:
                        print('Post %s alert faild, %s' % (self.filepath, str(e)))
                        print(traceback.format_exc())



    def select_monitor_items(self):
        select_sql = '''
          SELECT 
            id,
            search_pattern,
            alert,
            check_interval,
            trigger_format,
            dingding_webhook
          FROM local_log_monitor_item 
          WHERE local_log_file_id="%d"
        ''' % self.fileid
        thread_lock.acquire()
        self.cursor.execute(select_sql)
        results = self.cursor.fetchall()
        thread_lock.release()
        return results


def main():
    begin_time = time.time()
    conn = pymysql.connect(**MYSQL_DB)
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    try:
        files = query_files(cursor)
        str_time = time.strftime('%Y-%m-%d %H:%M', time.localtime())
        mk_time = time.mktime(time.strptime(str_time, '%Y-%m-%d %H:%M'))

        theads = []
        for file in files:
            theads.append(MonitorCount(file['id'], file['path'], conn, cursor, str_time, mk_time, begin_time))

        for thead in theads:
            thead.start()

        for thead in theads:
            thead.join()
    except Exception as e:
        print('Main error, %s' % str(e))
        print(traceback.format_exc())
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()