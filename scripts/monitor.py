# Created by zhouwang on 2018/6/13.

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.dirname(__file__))
import pymysql
import threading
import time
import os
import re
import traceback
from settings import MYSQL_DB


def query_files(cursor):
    select_sql = 'SELECT id,path FROM local_log_file'
    cursor.execute(select_sql)
    results = cursor.fetchall()
    print(results)
    return results

thread_lock = threading.Lock()
class MonitorCount(threading.Thread):
    def __init__(self, fileid, filepath, conn, cursor, mtime):
        threading.Thread.__init__(self)
        self.fileid = fileid
        self.filepath = filepath
        self.conn = conn
        self.cursor = cursor
        self.mtime = mtime
        self.count = {}
        self.search = []

    def run(self):
        open_position = os.path.getsize(self.filepath)
        time.sleep(60)
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

        print(begin_position, end_position)
        monitor_items = self.select_monitor_items()
        self.counts = {itemid:0 for itemid,_ in monitor_items}
        self.counts[0] = 0

        with open(self.filepath) as file:
            file.seek(begin_position)
            while True:
                #print(self.filepath, 'while')
                line = file.readline()
                if line:
                    self.counts[0] += 1
                    for itemid, search_pattern in monitor_items:
                        if re.search(search_pattern, line):
                            self.counts[itemid] += 1

                if file.tell() >= end_position:
                    break
        print(self.counts)
        inserts = [(self.fileid, itemid, count, self.mtime) for itemid, count in self.counts.items()]
        print(inserts)

        thread_lock.acquire()
        try:
            self.cursor.executemany('INSERT INTO local_log_monitor_count (local_log_file_id, monitor_item_id, count, count_time) VALUES(%s, %s, %s, %s)', inserts)
        except Exception as e:
            self.conn.rollback()
            print('Insert %s monitor count faild, %s' % (self.filepath, str(e)))
        thread_lock.release()


    def select_monitor_items(self):
        select_sql = 'SELECT id,search_pattern FROM local_log_monitor_item WHERE local_log_file_id="%d"' % self.fileid
        print(select_sql)
        thread_lock.acquire()
        self.cursor.execute(select_sql)
        results = self.cursor.fetchall()
        thread_lock.release()
        return results


def main():
    conn = pymysql.connect(**MYSQL_DB)
    cursor = conn.cursor()
    try:
        files = query_files(cursor)
        nowtime = time.strftime('%Y-%m-%d %H:%M', time.localtime())
        theads = []
        for fileid, filepath in files:
            theads.append(MonitorCount(fileid, filepath, conn, cursor, nowtime))
        print(theads)
        for thead in theads:
            thead.start()

        for thead in theads:
            thead.join()

        print('end')
    except Exception as e:
        print('Main error, %s' % str(e))
        print(traceback.format_exc())
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()