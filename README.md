# Loggrove
***

[![Python](https://img.shields.io/badge/python-3.6-brightgreen.svg?style=flat)](https://www.python.org/)
[![Tornado](https://img.shields.io/badge/tornado-5.0.2-brightgreen.svg)](http://www.tornadoweb.org/)

## Introduction
Loggrove 是对本地、远程**日志文件**进行 阅读、轮询、关键词匹配、统计、监控、钉钉告警、Highcharts图表展示 的 Web 平台服务，并包含 用户认证、LDAP认证、操作审计 等基础服务。

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
**组件：** 安装 Python3.6、Pip3、MySQL5.7、Nginx、Crond 等服务；

**命令：** python3、pip3、mysql、crontab、yum 命令可用，否则会导致初始化 Loggrove 失败；

## Installation & Configuration
### 下载
	git clone http://git@github.com:olajowon/loggrove.git

### 修改配置 settings.py
	MYSQL_DB = {
	    'host': 'host',
	    'port': 3306,
	    'user': 'user',
	    'password': 'password',
	    ...
	}
	
	SSH = {
       'username': 'root',                  
       'password': 'password', 
       'port': 22,                         
       ...
	}
	
	LDAP = {
       'auth': False,           # True 开启ldap认证
       'base_dn': 'cn=cn,dc=dc,dc=dc',     
       'server_uri': 'ldap://...',
       'bind_dn': 'uid=uid,cn=cn,cn=cn,dc=dc,dc=dc',    
       'bind_password': 'password',
	}
**MYSQL_DB：** MySQL数据库连接配置，请配置一个所有远程日志主机可以正确的连接的地址，避免localhost、127.0.0.1 类似的地址。	

**SSH：** SSH连接配置，用于SSH连接远程日志主机，建议使用root，避免权限不够。

**LDAP：** LDAP认证配置，这里选择性开启，Loggrove 本身内置了用户认证 ，没有LDAP需求的场景可以忽略此配置。

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
	
### 项目日志
	tail -f /tmp/loggrove.log	

### 监控任务（统计、监控、告警）
#### 监控脚本
	loggrove/scripts/monitor.py
	
#### 本地日志监控（crontab）
	crontab -e
	
	* * * * * /usr/local/bin/python3 <loggrove path>/scripts/monitor.py localhost >> /tmp/loggrove_monitor.log # loggrove_monitor
**注：** 构建 build.py 初始化时，程序会向本地crontab添加该任务	 
	
#### 远程日志监控（crontab）				
	crontab -e
	
	* * * * * /usr/bin/python <any path>/monitor.py HOST >> /tmp/loggrove_monitor.log # loggrove_monitor
**注：** 添加远程日志后，需要在远程主机上，部署monitor.py脚本，并添加crontab任务
	
	
	













