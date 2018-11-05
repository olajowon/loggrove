# Created by zhouwang on 2018/5/31.

from .base import BaseRequestHandler, permission
import datetime
import re
import logging

logger = logging.getLogger()


def argements_valid(handler, pk=None):
    error = {}
    logfile_id = handler.get_argument('logfile_id', '')
    search_pattern = handler.get_argument('search_pattern', '')
    comment = handler.get_argument('comment', '')
    alert = handler.get_argument('alert', '2')
    check_interval = handler.get_argument('check_interval', '0')
    trigger_format = handler.get_argument('trigger_format', '')
    dingding_webhook = handler.get_argument('dingding_webhook', '')
    if not logfile_id:
        error['logfile_id'] = 'Required'

    if not search_pattern:
        error['search_pattern'] = 'Required'
    else:
        try:
            re.search(r'%s' % search_pattern, '')
        except:
            error['search_pattern'] = 'Incorrect regular expression'
        else:
            select_sql = 'SELECT id FROM monitor_item WHERE search_pattern="%s" and logfile_id="%s" %s' % \
                         (search_pattern, logfile_id, 'and id!="%d"' % pk if pk else '')
            count = handler.mysqldb_cursor.execute(select_sql)
            if count:
                error['search_pattern'] = 'Already existed'

    if not comment:
        error['comment'] = 'Required'

    if alert != '1' and alert != '2':
        error['alert'] = 'Invalid'
    elif alert == '1':
        if not check_interval:
            error['check_interval'] = 'Required'
        elif not check_interval.isnumeric():
            error['check_interval'] = 'Must be integer'
        elif int(check_interval) < 1:
            error['check_interval'] = 'Must be greater than 0'

        if not trigger_format:
            error['trigger_format'] = 'Required'
        elif not (
            re.match(r'^([0-9]+[<=])?{}([<=][1-9][0-9]*)?$', trigger_format) and (trigger_format.strip() != '{}')):
            error['trigger_format'] = 'Incorrect format'

        if not dingding_webhook:
            error['dingding_webhook'] = 'Required'

    data = {
        'logfile_id': logfile_id,
        'search_pattern': search_pattern,
        'comment': comment,
        'alert': alert or '2',
        'check_interval': check_interval or '0',
        'trigger_format': trigger_format,
        'dingding_webhook': dingding_webhook
    }
    return error, data


def add_valid(func):
    def _wrapper(self):
        error, self.reqdata = argements_valid(self)
        if error:
            return {'code': 400, 'msg': 'Bad POST data', 'error': error}
        return func(self)

    return _wrapper


def query_valid(func):
    def _wrapper(self, pk):
        error = {}
        if not pk and self.request.arguments:
            argument_keys = self.request.arguments.keys()
            query_keys = ['id', 'logfile_id', 'search_pattern', 'alert', 'crontab_cycle', 'check_interval',
                          'trigger_format', 'dingding_webhook', 'comment', 'create_time', 'order', 'search',
                          'offset', 'limit', 'sort']
            error = {key: 'Bad key' for key in argument_keys if key not in query_keys}
        if error:
            return {'code': 400, 'msg': 'Bad GET param', 'error': error}
        return func(self, pk)

    return _wrapper


def update_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM monitor_item WHERE id="%d"' % pk
        count = self.mysqldb_cursor.execute(select_sql)
        if not count:
            return {'code': 404, 'msg': 'Update row not found'}
        error, self.reqdata = argements_valid(self, pk)
        if error:
            return {'code': 400, 'msg': 'Bad PUT param', 'error': error}
        return func(self, pk)

    return _wrapper


def del_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM monitor_item WHERE id="%d"' % pk
        count = self.mysqldb_cursor.execute(select_sql)
        if not count:
            return {'code': 404, 'msg': 'Delete row not found'}
        return func(self, pk)

    return _wrapper


class Handler(BaseRequestHandler):
    @permission(role=2)
    def post(self):
        response_data = self._add()
        self._write(response_data)

    @permission()
    def get(self, pk=0):
        response_data = self._query(int(pk))
        self._write(response_data)

    @permission(role=2)
    def put(self, pk=0):
        response_data = self._update(int(pk))
        self._write(response_data)

    @permission(role=2)
    def delete(self, pk=0):
        response_data = self._del(int(pk))
        self._write(response_data)

    @add_valid
    def _add(self):
        insert_sql = '''
            INSERT INTO 
              monitor_item (
                logfile_id, 
                search_pattern, 
                alert, 
                check_interval, 
                trigger_format, 
                dingding_webhook, 
                create_time, 
                comment) 
            VALUES ("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")
        ''' % (self.reqdata['logfile_id'], self.reqdata['search_pattern'], self.reqdata['alert'],
               self.reqdata['check_interval'], self.reqdata['trigger_format'], self.reqdata['dingding_webhook'],
               datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), self.reqdata['comment'])
        try:
            self.mysqldb_cursor.execute(insert_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            logger.error('Add monitor_item failed: %s' % str(e))
            return {'code': 500, 'msg': 'Add failed'}
        else:
            self.mysqldb_cursor.execute('SELECT LAST_INSERT_ID() as id')
            return {'code': 200, 'msg': 'Add successful', 'data': self.mysqldb_cursor.fetchall()}

    @update_valid
    def _update(self, pk):
        update_sql = '''
            UPDATE 
              monitor_item 
            SET 
              logfile_id="%s", 
              search_pattern="%s", 
              alert="%s", 
              check_interval="%s", 
              trigger_format="%s",
              dingding_webhook="%s", 
              comment="%s"
            WHERE id="%d"
        ''' % (self.reqdata['logfile_id'], self.reqdata['search_pattern'], self.reqdata['alert'],
               self.reqdata['check_interval'], self.reqdata['trigger_format'], self.reqdata['dingding_webhook'],
               self.get_argument('comment'), pk)
        try:
            self.mysqldb_cursor.execute(update_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            logger.error('Update monitor_item failed: %s' % str(e))
            return {'code': 500, 'msg': 'Update failed'}
        else:
            return {'code': 200, 'msg': 'Update successful', 'data': {'id': pk}}

    @query_valid
    def _query(self, pk):
        fields = search_fields = ['id', 'logfile_id', 'search_pattern', 'alert', 'crontab_cycle', 'check_interval',
                                  'trigger_format', 'dingding_webhook', 'comment', 'create_time']
        where, order, limit = self.select_sql_params(int(pk), fields, search_fields)
        select_sql = '''
            SELECT
              id, logfile_id, 
              search_pattern, 
              alert, 
              check_interval, 
              trigger_format, 
              dingding_webhook, 
              date_format(create_time, "%%Y-%%m-%%d %%H:%%i:%%s") as create_time, 
              comment 
            FROM 
              monitor_item
            %s %s %s
        ''' % (where, order, limit)
        self.mysqldb_cursor.execute(select_sql)
        results = self.mysqldb_cursor.fetchall()
        if limit:
            total_sql = 'SELECT count(*) as total FROM monitor %s' % where
            self.mysqldb_cursor.execute(total_sql)
            total = self.mysqldb_cursor.fetchone().get('total')
            return {'code': 200, 'msg': 'Query Successful', 'data': results, 'total': total}
        return {'code': 200, 'msg': 'Query successful', 'data': results}

    @del_valid
    def _del(self, pk):
        delete_sql = 'DELETE FROM monitor_item WHERE id="%d"' % pk
        try:
            self.mysqldb_cursor.execute(delete_sql)
        except Exception as e:
            self.mysqldb_conn.rollback()
            logger.error('Delete monitor_item failed: %s' % str(e))
            return {'code': 500, 'msg': 'Delete failed'}
        else:
            return {'code': 200, 'msg': 'Delete successful'}
