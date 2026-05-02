import pymysql

try:
    conn = pymysql.connect(host='localhost', user='root', password='root', database='network_slicing')
    cur = conn.cursor()
    cur.execute('SHOW TABLES')
    print('OK', cur.fetchall())
    conn.close()
except Exception as e:
    print(type(e).__name__, e)
    raise
