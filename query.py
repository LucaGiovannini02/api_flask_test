import sqlite3 as sq

conn = sq.connect('../CodiceFiscale.sqlite3')
cur = conn.cursor()

cur.execute("INSERT INTO TUser (email, password) VALUES (?, ?)", ["luca@gmail.com", "123"])
cur.execute("INSERT INTO TUser (email, password) VALUES (?, ?)", ["marco@gmail.com", "1234"])

conn.commit()
conn.close()