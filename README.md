# Loggrove
***

[![Python](https://img.shields.io/badge/python-3.6-brightgreen.svg?style=flat)](https://www.python.org/)
[![Tornado](https://img.shields.io/badge/tornado-5.0.2-brightgreen.svg)](http://www.tornadoweb.org/)

## Introduction
Loggrove 是对本地、远程**日志文件**进行 分页阅读、实时阅读（websocket）、关键词匹配、统计、监控、钉钉告警、Highcharts趋势图展示 的 Web 平台服务，并包含 用户认证、LDAP认证、操作审计 等基础服务。

### DEMO
地址：<http://39.105.81.124:6218>

用户：guest 

密码：guest123

### Web UI 界面
简洁大方的 Web UI 界面，进行 日志文件、日志图表、日志阅读、日志轮询、日志关键词匹配、用户、审计 等统一管理，提供一系列简单、准确、美观的日志管理、查看、过滤 等服务。

![image](https://github.com/olajowon/exhibitions/blob/master/loggrove/dashboard2019.png?raw=true)

[更多图片](#Exhibition)

### 超轻组件
Python 3.6 

Tornado 5.0.2

MySQL 5.7

JQuery 3.1.0

Bootstrap 3.3

Sb-admin 2.0

### Logmonit
Logmonit 是一个纯监控报警的daemon程序，作为Loggrove监控报警功能的独立项目，不依赖Loggrove运行，它根据定义的TOML配置文件完成对日志的监控。

项目地址：<https://github.com/olajowon/logmonit>

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
**MYSQL_DB：** MySQL数据库连接配置。	

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
	
#### 进行监控
在日志真实存储的机器上运行该脚本，使用参考 --help

	python3 monitor.py -s http://<loggrove> -h <host>

注：推荐supervisor进行管理，也可以使用nohup简单运行
	

<a name="Exhibition"></a>
## Exhibition

### dashboard
![image](https://github.com/olajowon/exhibitions/blob/master/loggrove/dashboard2019.png?raw=true)	

### 日志文件 file
![image](https://github.com/olajowon/exhibitions/blob/master/loggrove/logfile2019.png?raw=true)	

### 监控项 monitor item
![image](https://github.com/olajowon/exhibitions/blob/master/loggrove/monitor_item2019.png?raw=true)
	
### 日志阅读 read
![image](https://github.com/olajowon/exhibitions/blob/master/loggrove/read2019.png?raw=true)

### 日志轮询 keepread
![image](https://github.com/olajowon/exhibitions/blob/master/loggrove/keepread2019.png?raw=true)

### 日志图表 charts
![image](https://github.com/olajowon/exhibitions/blob/master/loggrove/chart2019.png?raw=true)
![image](https://github.com/olajowon/exhibitions/blob/master/loggrove/chart_content2019.png?raw=true)

### 登录 login
![image](https://github.com/olajowon/exhibitions/blob/master/loggrove/login.png?raw=true)












