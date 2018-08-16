# Created by zhouwang on 2018/5/5.

from handlers import (
    html,
    login,
    logout,
    user,
    password,
    auditlog,
    dashboard,
    profile,
    history,
    logfile,
    monitor_item,
    read,
    keepread,
    chart
)



urlpatterns = [
    (r'/', html.Handler),
    (r'^/dashboard/$', dashboard.Handler),
    (r'^/login/html/$', html.LoginHander),
    (r'^/(logfiles|read|keepread|charts|users|auditlogs)/html/$', html.Handler),
    (r'^/login/$', login.Handler),
    (r'^/logout/$', logout.Handler),
    (r'^/profile/$', profile.Handler),
    (r'^/history/$', history.Handler),
    (r'^/users/$', user.Handler),
    (r'^/users/(\d+)/$', user.Handler),
    (r'^/users/(\d+)/password/$', password.ResetHandler),
    (r'^/password/$', password.Handler),
    (r'^/auditlogs/$', auditlog.Handler),
    (r'^/logfiles/$', logfile.Handler),
    (r'^/logfiles/(\d+)/$', logfile.Handler),
    (r'^/monitor/items/$', monitor_item.Handler),
    (r'^/monitor/items/(\d+)/$', monitor_item.Handler),
    (r'^/read/$', read.Handler),
    (r'^/keepread/$', keepread.Handler),
    (r'^/charts/$', chart.Handler),
]