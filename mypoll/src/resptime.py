#!/usr/bin/env python3

import db
import json
import time

db.init()
connection = db.open_db()
cursor = connection.cursor()

cursor.execute("""
  SELECT P.onyen, P.id, A.field, A.value
  FROM (SELECT onyen, max(P.id) id 
        FROM post P 
        WHERE key='fe-bit' 
        GROUP BY onyen) P, answer A 
  WHERE A.postid = P.id and 
        A.field != '__pledge_journal' and
        onyen = 'aanpatel' and
        A.field like '_%_journal'
  ORDER BY P.onyen, P.id, A.field
  """)

last_onyen = ''
last_id = ''
last_value = ''
# import pdb; pdb.set_trace()
for row in cursor.fetchall():
 # print(f"Row onyen {row.onyen} id {row.id} field {row.field} value {row.value}")
  values = json.loads(row.value)
  # print(f'values {values}')
  for value in values:
     if 'correct' not in value:
        continue
     the_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime( value['now']/1000))
     print(f' name: {value["element_name"]} time {the_time} correct {"True " if value["correct"] == "1" else "False"} value {value["value"]}')
