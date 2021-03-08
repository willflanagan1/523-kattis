#!/usr/bin/python3

import db
import assessments
db.init()
conn = db.open_db()
cursor = conn.cursor()

cursor.execute("SELECT onyen from roll where section in ('001', '002', '000') order by onyen")
rows = cursor.fetchall()
for row in rows:
   print(f"Updating grades for {row.onyen}")
   conn = db.open_db()
   cursor = conn.cursor()
   assessments.updateGrades(cursor, row.onyen)
   conn.commit()
