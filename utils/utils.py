# Created by zhouwang on 2019/6/25.

import random
import string
import hashlib
import pymysql

def make_password(password):
    salt = ''.join(random.sample(string.ascii_letters, 8))
    return '%s%s' % (salt, hashlib.md5((salt + password).encode('UTF-8')).hexdigest())

def validate_password(password, encrypted_password):
    salt, salt_password = encrypted_password[:8], encrypted_password[8:]
    return hashlib.md5((salt + password).encode('UTF-8')).hexdigest() == salt_password

def select_sql_params(self, pk=0, fields=[], search_fields=[]):
    where, limit, order = '', '', ''
    if pk:
        where = 'WHERE id="%d"' % pk
    elif self.request.arguments:
        if not self.get_argument('search', None):
            where_fields = [field for field in fields if self.get_argument(field, None) != None]
            if where_fields:
                where = ' WHERE %s' % ' and '.join(
                    ['%s in (%s)' % (field, ','.join(
                        ['"%s"' % pymysql.escape_string(v) for v in self.get_arguments(field)]))
                     for field in where_fields])
        else:
            where = 'WHERE concat(%s) like "%%%s%%"' % (','.join(search_fields),
                                                        pymysql.escape_string(self.get_argument('search')))

        if self.get_argument('offset', None) and self.get_argument('limit', None):
            limit = 'LIMIT %s, %s' % (pymysql.escape_string(self.get_argument('offset')),
                                      pymysql.escape_string(self.get_argument('limit')))

        if self.get_argument('order', None) and self.get_argument('sort', None):
            order = 'ORDER BY %s %s' % (pymysql.escape_string(self.get_argument('sort')),
                                        pymysql.escape_string(self.get_argument('order')))
    return where, order, limit