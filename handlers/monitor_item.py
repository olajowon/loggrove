# Created by zhouwang on 2018/5/31.

from .base import BaseRequestHandler, permission
import datetime
import re
import logging

logger = logging.getLogger()


def argements_valid(handler, pk=None):
    error = {}
    logfile_id = handler.get_argument('logfile_id', '')
    name = handler.get_argument('name', '')
    match_regex = handler.get_argument('match_regex', '')
    comment = handler.get_argument('comment', '')
    alert = handler.get_argument('alert', '2')
    intervals = handler.get_argument('intervals', '0')
    expression = handler.get_argument('expression', '')
    webhook = handler.get_argument('webhook', '')

    if not logfile_id:
        error['logfile_id'] = 'Required'

    if not name:
        error['name'] = 'Required'
    else:
        select_sql = 'SELECT id FROM monitor_item WHERE name="%s" and logfile_id="%s" %s' % \
                     (name, logfile_id, 'and id!="%d"' % pk if pk else '')
        count = handler.cursor.execute(select_sql)
        if count:
            error['name'] = 'Already existed'

    if not match_regex:
        error['match_regex'] = 'Required'
    else:
        try:
            re.search(r'%s' % match_regex, '')
        except:
            error['match_regex'] = 'Incorrect regular expression'

    if alert != '1' and alert != '2':
        error['alert'] = 'Invalid'
    elif alert == '1':
        if not intervals:
            error['intervals'] = 'Required'
        elif not intervals.isnumeric():
            error['intervals'] = 'Must be integer'
        elif int(intervals) < 1:
            error['intervals'] = 'Must be greater than 0'

        if not expression:
            error['expression'] = 'Required'
        elif not (re.match(r'^([0-9]+[<=])?{}([<=][1-9][0-9]*)?$', expression) and (expression.strip() != '{}')):
            error['expression'] = 'Incorrect format'

        if not webhook:
            error['webhook'] = 'Required'

    data = {
        'logfile_id': logfile_id,
        'name': name,
        'match_regex': match_regex,
        'comment': comment,
        'alert': alert or '2',
        'intervals': intervals or '0',
        'expression': expression,
        'webhook': webhook
    }
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
        error = {}
        if not pk and self.request.arguments:
            argument_keys = self.request.arguments.keys()
            query_keys = ['id', 'logfile_id', 'name', 'match_regex', 'alert', 'intervals',
                          'expression', 'webhook', 'comment', 'create_time', 'order', 'search',
                          'offset', 'limit', 'sort']
            error = {key: 'Bad key' for key in argument_keys if key not in query_keys}
        if error:
            return dict(code=400, msg='Bad GET param', error=error)
        return func(self, pk)

    return _wrapper


def update_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM monitor_item WHERE id="%d"' % pk
        count = self.cursor.execute(select_sql)
        if not count:
            return dict(code=404, msg='Update row not found')
        error, self.reqdata = argements_valid(self, pk)
        if error:
            return dict(code=400, msg='Bad PUT param', error=error)
        return func(self, pk)

    return _wrapper


def del_valid(func):
    def _wrapper(self, pk):
        select_sql = 'SELECT id FROM monitor_item WHERE id="%d"' % pk
        count = self.cursor.execute(select_sql)
        if not count:
            return dict(code=404, msg='Delete row not found')
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
        try:
            insert_arg = (
                self.reqdata['logfile_id'], self.reqdata['name'], self.reqdata['match_regex'], self.reqdata['alert'],
                self.reqdata['intervals'], self.reqdata['expression'], self.reqdata['webhook'],
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), self.reqdata['comment']
            )
            with self.transaction():
                self.cursor.execute(self.insert_sql, insert_arg)
        except Exception as e:
            logger.error('Add monitor_item failed: %s' % str(e))
            return dict(code=500, msg='Add failed')
        else:
            self.cursor.execute('SELECT LAST_INSERT_ID() as id')
            return dict(code=200, msg='Add successful', data=self.cursor.dictfetchall())

    @update_valid
    def _update(self, pk):
        try:
            update_arg = (
                self.reqdata['logfile_id'], self.reqdata['name'], self.reqdata['match_regex'], self.reqdata['alert'],
                self.reqdata['intervals'], self.reqdata['expression'], self.reqdata['webhook'],
                self.get_argument('comment'), pk
            )
            with self.transaction():
                self.cursor.execute(self.update_sql, update_arg)
        except Exception as e:
            logger.error('Update monitor_item failed: %s' % str(e))
            return {'code': 500, 'msg': 'Update failed'}
        else:
            return dict(code=200, msg='Update successful', data={'id': pk})

    @query_valid
    def _query(self, pk):
        fields = search_fields = ['id', 'logfile_id', 'name', 'match_regex', 'alert', 'intervals',
                                  'expression', 'webhook', 'comment', 'create_time']
        where, order, limit = self.select_sql_params(int(pk), fields, search_fields)
        self.cursor.execute(self.select_sql % (where, order, limit))
        results = self.cursor.dictfetchall()
        if limit:
            self.cursor.execute(self.select_total_sql % where)
            total = self.cursor.dictfetchone().get('total')
            return dict(code=200, msg='Query Successful', data=results, total=total)
        return dict(code=200, msg='Query successful', data=results)

    @del_valid
    def _del(self, pk):
        try:
            with self.transaction():
                self.cursor.execute(self.delete_sql, pk)
        except Exception as e:
            logger.error('Delete monitor_item failed: %s' % str(e))
            return dict(code=500, msg='Delete failed')
        else:
            return dict(code=200, msg='Delete successful')

    insert_sql = '''
        INSERT INTO 
          monitor_item (
            logfile_id,
            name, 
            match_regex, 
            alert, 
            intervals, 
            expression, 
            webhook, 
            create_time, 
            comment) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''

    update_sql = '''
        UPDATE 
          monitor_item 
        SET 
          logfile_id=%s,
          name=%s, 
          match_regex=%s, 
          alert=%s, 
          intervals=%s, 
          expression=%s,
          webhook=%s, 
          comment=%s
        WHERE id=%s
    '''

    select_sql = '''
        SELECT
          id, logfile_id,
          name, 
          match_regex, 
          alert, 
          intervals, 
          expression, 
          webhook, 
          date_format(create_time, "%%Y-%%m-%%d %%H:%%i:%%s") as create_time, 
          comment 
        FROM 
          monitor_item
        %s %s %s
    '''

    select_total_sql = 'SELECT count(*) as total FROM monitor_item %s'

    delete_sql = 'DELETE FROM monitor_item WHERE id=%s'