# Created by zhouwang on 2018/5/5.

from .base import BaseRequestHandler, permission
import datetime
import pymysql
import logging

logger = logging.getLogger()


def argements_valid(handler, pk=None):
    error = dict()
    name = handler.get_argument('name', '')
    path = handler.get_argument('path', '')
    comment = handler.get_argument('comment', '')
    host = handler.get_argument('host', '')
    monitor_choice = handler.get_argument('monitor_choice', '0')

    if not path:
        error['path'] = 'Required'
    else:
        select_sql = 'SELECT id FROM logfile WHERE name="%s" %s'
        select_arg = (pymysql.escape_string(name), 'and id!="%d"' % pk if pk else '')
        count = handler.cursor.execute(select_sql % select_arg)
        if count:
            error['path'] = 'Already existed'

    for i, j in ((name, 'name'), (host, 'host'), (comment, 'comment')):
        if not i:
            error[j] = 'Required'

    if monitor_choice not in ('0', '-1'):
        error['monitor_choice'] = 'Invalid'

    data = dict(name=name,
                path=path,
                comment=comment,
                host=host,
                hosts=host.split(','),
                monitor_choice=int(monitor_choice))
    return error, data


def add_valid(func):
    def _wrapper(self):
        error, self.reqdata = argements_valid(self)
        if error:
            return dict(code=400, msg='Bad POST data', error=error)
        return func(self)

    return _wrapper


def query_valid(func):
    def _wrapper(self, pk):
        error = dict()
        if not pk and self.request.arguments:
            argument_keys = self.request.arguments.keys()
            query_keys = ['id', 'name', 'host', 'path', 'comment', 'create_time',
                          'order', 'search', 'offset', 'limit', 'sort']
            error = {key: 'Bad key' for key in argument_keys if key not in query_keys}
        if error:
            return dict(code=400, msg='Bad GET param', error=error)
        return func(self, pk)

    return _wrapper


def update_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM logfile WHERE id="%d"' % pk
        count = self.cursor.execute(select_sql)
        if not count:
            return {'code': 404, 'msg': 'Update row not found'}
        error, self.reqdata = argements_valid(self, pk)
        if error:
            return dict(code=400, msg='Bad PUT param', error=error)
        return func(self, pk)

    return _wrapper


def del_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM logfile WHERE id="%d"' % pk
        count = self.cursor.execute(select_sql)
        if not count:
            return dict(code=404, msg='Delete row not found')
        return func(self, pk)

    return _wrapper


class Handler(BaseRequestHandler):
    @permission()
    def get(self, pk=0):
        ''' Query logfile '''
        response_data = self._query(int(pk))
        self._write(response_data)

    @permission(role=2)
    def post(self):
        ''' Add logfile '''
        response_data = self._add()
        self._write(response_data)

    @permission(role=2)
    def put(self, pk=0):
        ''' Update logfile '''
        response_data = self._update(int(pk))
        self._write(response_data)

    @permission(role=2)
    def delete(self, pk=0):
        ''' Delete logfile '''
        response_data = self._del(int(pk))
        self._write(response_data)

    @query_valid
    def _query(self, pk):
        fields = search_fields = ['id', 'name', 'host', 'path', 'comment', 'create_time']
        where, order, limit = self.select_sql_params(int(pk), fields, search_fields)
        self.cursor.execute(self.select_sql % (where, order, limit))
        results = self.cursor.dictfetchall()
        if limit:
            self.cursor.execute(self.total_sql % where)
            total = self.cursor.dictfetchone().get('total')
            return dict(code=200, msg='Query Successful', data=results, total=total)
        return dict(code=200, msg='Query Successful', data=results)

    @add_valid
    def _add(self):
        try:
            with self.transaction(atomic=True):
                insert_arg = (self.reqdata['name'], self.reqdata['host'], self.reqdata['path'],
                              datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), self.reqdata['comment'],
                              self.reqdata['monitor_choice'])
                self.cursor.execute(self.insert_sql, insert_arg)
                self.cursor.execute(self.last_insert_id_sql)
                insert = self.cursor.dictfetchone()
                insert_host_mp_args = [(insert['id'], host) for host in self.reqdata['hosts']]
                self.cursor.executemany(self.insert_host_mp_sql, insert_host_mp_args)
        except Exception as e:
            logger.error('Add logfile failed: %s' % str(e))
            return dict(code=500, msg='Add failed')
        else:
            return dict(code=200, msg='Add successful', data=insert)

    @update_valid
    def _update(self, pk):
        try:
            with self.transaction(atomic=True):
                update_arg = (self.reqdata['name'], self.reqdata['host'], self.reqdata['path'],
                              self.reqdata['comment'], self.reqdata['monitor_choice'], pk)
                self.cursor.execute(self.update_sql, update_arg)
                delete_host_mp_arg = (pk,)
                self.cursor.execute(self.delete_host_mp_sql, delete_host_mp_arg)
                insert_host_mp_args = [(pk, host) for host in self.reqdata['hosts']]
                self.cursor.executemany(self.insert_host_mp_sql, insert_host_mp_args)
        except Exception as e:
            logger.error('Update logfile failed: %s' % str(e))
            return dict(code=500, msg='Update failed')
        else:
            return dict(code=200, msg='Update successful', data=dict(id=pk))

    @del_valid
    def _del(self, pk):
        try:
            with self.transaction(atomic=True):
                delete_arg = (pk,)
                self.cursor.execute(self.delete_sql, delete_arg)
                self.cursor.execute(self.delete_host_mp_sql, delete_arg)
                self.cursor.execute(self.delete_monitor_sql, delete_arg)
                self.cursor.execute(self.delete_monitor_count_sql, delete_arg)
        except Exception as e:
            logger.error('Delete logfile failed: %s' % str(e))
            return dict(code=500, msg='Delete failed')
        else:
            return dict(code=200, msg='Delete successful')

    insert_sql = \
        'INSERT INTO logfile (name, host, path, create_time, comment, monitor_choice) VALUES (%s, %s, %s, %s, %s, %s)'

    insert_host_mp_sql = 'INSERT INTO logfile_host (logfile_id, host) VALUES (%s, %s)'

    update_sql = 'UPDATE logfile SET name=%s, host=%s, path=%s, comment=%s, monitor_choice=%s WHERE id=%s'

    delete_sql = 'DELETE FROM logfile WHERE id=%s'

    delete_host_mp_sql = 'DELETE FROM logfile_host WHERE logfile_id=%s'

    delete_monitor_sql = 'DELETE FROM monitor_item WHERE logfile_id=%s'

    delete_monitor_count_sql = 'DELETE FROM monitor_count WHERE logfile_id=%s'

    last_insert_id_sql = 'SELECT LAST_INSERT_ID() as id'

    select_sql = '''
        SELECT
          id, name, host, path, 
          date_format(create_time, "%%Y-%%m-%%d %%H:%%i:%%s") as create_time, 
          comment, monitor_choice
        FROM
          logfile
        %s %s %s
    '''

    total_sql = 'SELECT count(*) as total FROM logfile %s'