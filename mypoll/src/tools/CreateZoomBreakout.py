#!/usr/bin/env python3

import contextlib
import db
import os.path as osp
import numpy as np
import pandas
import sys
from config import ZWSP
import csv

db.init() # Ensure tables set up 

for section in ['001', '002']:
   connection = db.open_db()
   with contextlib.closing(connection):
       cursor = connection.cursor()
       cursor.execute('''
           SELECT R.onyen, T.team_number, T.member_number
             FROM roll R
             LEFT join teams T
                ON  R.onyen=T.onyen
                WHERE  R.section = %(section)s 
           ORDER BY T.team_number, T.member_number
           ''',
           {'section': section},
           )
       rows = [ {'room': f'0{row.team_number}', 'email': f'{row.onyen}@email.unc.edu'}
                for row in cursor.fetchall() ]
       for row in rows:
          row['room'] = 'Breakout room ' + row['room'][-2:]

   with open(f'ZoomBreakout.{section}.csv', 'w', newline='') as output_file:
      dict_writer = csv.DictWriter(output_file, rows[0].keys())
      dict_writer.writeheader()
      dict_writer.writerows(rows)

