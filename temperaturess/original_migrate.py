import sqlite3
dbname = 'temperaturess/db.sqlite3'
conn = sqlite3.connect(dbname)
cur = conn.cursor()

cur.execute('ALTER TABLE app_timedata RENAME TO viewer_timedata')
cur.execute('ALTER TABLE app_daydata RENAME TO viewer_daydata')
cur.execute('ALTER TABLE app_normaldata RENAME TO viewer_normaldata')
cur.execute("UPDATE django_content_type SET app_label='viewer' WHERE app_label='app'")
cur.execute("UPDATE django_migrations SET app='viewer' WHERE app='app'")
conn.commit()
cur.close()
conn.close()
