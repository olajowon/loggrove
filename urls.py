# Created by zhouwang on 2018/5/5.

from handlers import (
    html,
    local_log_file,
    local_log_keepread,
    local_log_dir,
    local_log_read,
    local_log_monitor_item,
    login,
    logout,
    user,
    password,
    auditlog,
    dashboard,
    profile,
    history
)



urlpatterns = [
    (r'/', html.Handler),
    (r'^/dashboard/$', dashboard.Handler),
    (r'^/login/html/$', html.LoginHander),
    (r'^/([local_log/dir|file|read|keepread user audit]+)/html/$', html.Handler),
    (r'^/local_log/dir/$', local_log_dir.Handler),
    (r'^/local_log/dir/(\d+)/$', local_log_dir.Handler),
    (r'^/local_log/file/$', local_log_file.Handler),
    (r'^/local_log/file/(\d+)/$', local_log_file.Handler),
    (r'^/local_log/monitor/item/$', local_log_monitor_item.Handler),
    (r'^/local_log/monitor/item/(\d+)/$', local_log_monitor_item.Handler),
    (r'^/local_log/read/$', local_log_read.Handler),
    (r'^/local_log/keepread/$', local_log_keepread.Handler),
    (r'^/login/$', login.Handler),
    (r'^/logout/$', logout.Handler),
    (r'^/profile/$', profile.Handler),
    (r'^/history/$', history.Handler),
    (r'^/user/$', user.Handler),
    (r'^/user/(\d+)/$', user.Handler),
    (r'^/user/(\d+)/password/reset/$', password.ResetHandler),
    (r'^/password/$', password.Handler),
    (r'^/auditlog/$', auditlog.Handler),
]