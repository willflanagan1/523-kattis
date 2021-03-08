#!/usr/bin/env python3

import contextlib
import db
import pandas
from config import admins
admins += ['www-data']

tables = ['post', 'post_id_seq', 'pages', 'answer', 'answer_id_seq',
          'fetched', 'fetched_id_seq', 'notfound', 'notfound_id_seq',
          'state', 'browser', 'browser_id_seq', 'codes', 'feedback', 'feedback_postid_seq',
          'zoom', 'roll', 'grades', 'worksheet_bonus', 'worksheet_bonus_id_seq',
          'seats', 'rubrics', 'messages', 'teams', 'lectures' ]

db.init() # Ensure tables set up

for admin in admins:
   for table in tables:
      grant = f"""grant all privileges on table {table} to "{admin}" """
      
      connection = db.open_db()
      with contextlib.closing(connection):
         cursor = connection.cursor()
         cursor.execute(grant)
         connection.commit()
