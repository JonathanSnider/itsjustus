import sqlite3
conn = sqlite3.connect('dbs/posted_schedules.db')
c = conn.cursor()
c.execute('CREATE TABLE posted_schedules (message_id TEXT, schedule_id TEXT)')
conn.commit() 
c.close()
conn.close()