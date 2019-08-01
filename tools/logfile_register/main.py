#!/usr/bin/env python3
# Created by zhouwang on 2019/1/9.

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import toml
import threading
import pymysql
import socket
import subprocess

TOMLNAMES = sys.argv[1].split(',')
PATH = os.path.dirname(os.path.abspath(__file__))
TOMLPATH = os.path.join(PATH, 'example.toml')
TOMLFILES = []


def get_host_tmpls():
    tmpls = {}
    for tomlname in TOMLNAMES:
        tomlpath = os.path.join(PATH, tomlname)
        if os.path.isfile(tomlpath):
            res = toml.loads(open(tomlpath).read())
            hosts = res.pop('host')
            for host in set(hosts):
                if host not in tmpls:
                    tmpls[host] = []
                tmpls[host].append(res)
    print(tmpls)
    return tmpls


def is_localhost(host):
    if host in ['localhost', '127.0.0.1']:
        return True
    hostname = socket.gethostname()
    if host == hostname:
        return True
    ip = socket.gethostbyname(hostname)
    if host == ip:
        return True
    return False


def handler(host, tmpls):
    if is_localhost(host):
        pass
    for tmpl in tmpls:
        cmd = tmpl.get('find')
        print(subprocess.getstatusoutput(cmd))


def main():
    host_tmpls = get_host_tmpls()
    threads = []
    for host, tmpls in host_tmpls.items():
        thread = threading.Thread(target=handler, args=(host, tmpls))
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()