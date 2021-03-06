from requests.utils import quote
import mariadb
import api_logger as logger
from flask import abort, make_response, jsonify
import config
cfg = config.config

def insert_into(table, data):
    columns = ', '.join("`" + str(x) + "`" for x in data.keys())
    values = ', '.join("'" + str(x) + "'" for x in data.values())
    sql = "INSERT INTO %s ( %s ) SELECT %s" % (table, columns, values)
    return sql

def insert_into_where_not_exists(table, data, unique):
    columns = ', '.join("`" + str(x) + "`" for x in data.keys())
    values = ', '.join("'" + str(x) + "'" for x in data.values())
    sql = "INSERT INTO %s ( %s ) SELECT %s" % (table, columns, values)
    sql += " FROM DUAL WHERE NOT EXISTS (SELECT * FROM "+table+" WHERE " + unique + " = '"+str(data[unique])+"');"
    return sql

def insert_into_where_not_exists_2(table, data, unique1, unique2):
    columns = ', '.join("`" + str(x) + "`" for x in data.keys())
    values = ', '.join("'" + str(x) + "'" for x in data.values())
    sql = "INSERT INTO %s ( %s ) SELECT %s" % (table, columns, values)
    sql += " FROM DUAL WHERE NOT EXISTS (SELECT * FROM "+table+" WHERE " + unique1 + " = '"+str(data[unique1])+"' AND " + unique2 + " = '"+str(data[unique2])+"');"
    return sql

def replace_into(table, data):
    columns = ', '.join("`" + str(x) + "`" for x in data.keys())
    values = ', '.join("'" + str(x) + "'" for x in data.values())
    sql = "REPLACE INTO %s ( %s ) VALUES ( %s )" % (table, columns, values)
    return sql

def esc_db(item):
    return item.replace("'", "\\'")

def sanitize_db_field(db_field):
    special_chars_replace_with_blank = ['"', "\\'"]
    special_chars_replace_with_space = ['•']
    sanitized = "REPLACE({}, '{}', '')".format(db_field, special_chars_replace_with_blank.pop(0))
    for s in special_chars_replace_with_blank:
       sanitized = "REPLACE({}, '{}', '')".format(sanitized, s)
    for s in special_chars_replace_with_space:
       sanitized = "REPLACE({}, '{}', ' ')".format(sanitized, s)
    return sanitized

def sanitize_query(query):
    special_chars_replace_with_blank = ['"', "'"]
    special_chars_replace_with_space = ['•']
    for s in special_chars_replace_with_blank:
        query = query.replace(s, '')
    for s in special_chars_replace_with_space:
        query = query.replace(s, ' ')
    return query

def execute_db(sql, commit=False, tz=False, log=False, pass_on_error=False):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    if tz:
        cursor.execute("SET time_zone='+00:00';")

    try:
        if log or cfg['sql_logging']:
            logger.debug("Executing SQL: {}".format(sql))
        cursor.execute(sql)
        records = [] if commit else list(cursor)
        if commit:
                mdb.commit()
    except mariadb.Error as e:
            mdb.close()
            logger.log("[PASS] A database error occured: {}".format(e))
            logger.log("\tSQL: {}".format(sql))
            if not pass_on_error:
                abort(make_response(jsonify(error="A database error occured: {}".format(e)), 500))

    mdb.close()
    return records