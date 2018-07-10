# Loggrove
***

[![Python](https://img.shields.io/badge/python-3.6-brightgreen.svg?style=flat)](https://www.python.org/)
[![Tornado](https://img.shields.io/badge/tornado-5.0.2-brightgreen.svg)](http://www.tornadoweb.org/)

## Introduction
Loggrove 是对**日志文件**进行 阅读、轮询、关键词匹配、监控告警、图表展示 的 Web 服务。

### 超轻组件
Python 3.6 

Tornado 5.0.2

MySQL 5.7

JQuery 3.1.0

Bootstrap 3.3

Sb-admin 2.0

### Web UI 界面
简洁大方的 Web UI 界面，进行 日志目录、日志文件、日志图表、日志阅读、日志轮询、日志关键词匹配、用户、审计 等统一管理，提供一系列简单、准确、美观的日志管理、查看、过滤 等服务。

### DEMO
地址：<http://39.105.81.124:6218>

用户：guest 

密码：guest123


## Requirements

**位置：** 必须部署在日志服务器上，Loggrove 暂不支持对远程日志的管理和查看；

**组件：** 安装 Python3.6、Pip3、MySQL5.7、Nginx、Crond 等服务；

**命令：** python3、pip3、mysql、crontab 命令可用，否则会导致初始化 Loggrove 失败。


## Installation & Configuration
### 下载
	git clone http://git@github.com:olajowon/loggrove.git

### 修改配置 settings.py
	MYSQL_DB = {
	    'host': '<host>',
	    'port': <port>,
	    'user': '<user>',
	    'passwd': '<passwd>',
	    ...
	}

### 构建 build.py
	python3 build.py

## Start-up
### 启动多实例 (建议使用Supervisor管理)
	python3 start.py --port=8800
	python3 start.py --port=8801
	python3 start.py --port=8802
	python3 start.py --port=8803
Supervisor 文档: <http://demo.pythoner.com/itt2zh/ch8.html#ch8-3>

### Nginx 代理
	upstream loggrove {
	    server 127.0.0.1:8800;
	    server 127.0.0.1:8801;
	    server 127.0.0.1:8802;
	    server 127.0.0.1:8803;
	}

	server {
	    listen 80;
	    server_name localhost;

	    location / {
	        proxy_pass_header Server;
	        proxy_set_header Host $http_host;
	        proxy_redirect off;

	        proxy_http_version 1.1;
	        proxy_set_header Upgrade $http_upgrade;
	        proxy_set_header Connection "upgrade";

	        proxy_set_header X-Real-IP $remote_addr;
	        proxy_set_header X-Scheme $scheme;
	        proxy_pass http://loggrove;
	    }
	}
	
### 默认日志
	tail -f /tmp/loggrove.log	














