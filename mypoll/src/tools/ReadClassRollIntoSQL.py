#!/usr/bin/env python3
"""
Read a CSV file of student information into mypoll roll
"""

import Args
import contextlib
import pandas

import db
from ZWSP import ZWSP

# csv is required ./ReadClassRollIntoSQL.py csv=COMP550SP21.002.2020.12.09.csv
args = Args.Parse(csv=str)

# Get class information from CSV file
roll = pandas.read_csv(args.csv)
roll = roll[['Student ID', 'PID', 'Name', 'Section', 'imageURL']]
roll.columns = ['onyen', 'pid', 'name', 'section', 'imageURL']
roll = roll.fillna('')
print(len(roll.loc[roll.section == 1]), 'in section 1')
print(len(roll.loc[roll.section == 2]), 'in section 2')
print(len(roll.loc[roll.section == 3]), 'in section 3')

zwsp_object = ZWSP()

db.init() # Ensure tables set up

for index, row in roll.iterrows():
   onyen = row['onyen'].strip()
   pid = str(row['pid'])
   name = row['name'].strip()
   section = row['section']
   imageURL = row['imageURL'].strip()

   # Ensure section number is three digits
   section = '000' + str(section)
   section = section[-3:]

   connection = db.open_db()
   with contextlib.closing(connection):
      cursor = connection.cursor()
      cursor.execute('''
                 SELECT onyen, pid, name, section, imageURL, rid, zwsp
                     FROM roll
                     WHERE onyen='{}' '''.format(onyen))
      try:
         (db_onyen, db_pid, db_name, db_section, db_imageURL, rid, zwsp) = cursor.fetchone()
      except TypeError:
         db_onyen = db_name = db_pid = db_section = db_imageURL = zwsp = None
         rid = 0

   if ((db_onyen is None or (str(onyen) != str(db_onyen))) or
       (db_pid is None or (str(pid) != str(db_pid))) or
       (db_name is None or (str(name) != str(db_name))) or
       (zwsp is None) or
       (rid is None or (zwsp_object.getSequence(rid) != zwsp)) or
       (db_section is None or (str(section) != str(db_section))) or
       (db_imageURL is None or (str(imageURL) != str(db_imageURL)))):

      print('Inserting/ update user', onyen)
      print(db_onyen, db_pid, db_name, db_section, db_imageURL)
      print(*row, sep='\t')
      zwsp = zwsp_object.getSequence(rid)

      section = f"00{int(float(section))}"[-3:]
      connection = db.open_db()
      with contextlib.closing(connection):
         cursor = connection.cursor()
         cursor.execute('''
            INSERT INTO roll
               (onyen, pid, name, section, imageURL, zwsp)
            VALUES (%(onyen)s, %(pid)s, %(name)s, %(section)s, %(imageURL)s, %(zwsp)s)
            ON CONFLICT (onyen) DO UPDATE SET
                (onyen, pid, name, section, imageURL, zwsp) =
                      (%(onyen)s, %(pid)s, %(name)s, %(section)s, %(imageURL)s, %(zwsp)s)''',
                        {'onyen': onyen, 'pid': pid, 'name': name,
                         'section': section, 'imageURL': imageURL,
                         'zwsp': zwsp})
         connection.commit()

connection = db.open_db()
with contextlib.closing(connection):
   cursor = connection.cursor()
   cursor.execute('''SELECT onyen FROM roll WHERE zwsp is null''')
   for row in cursor.fetchall():
      print("Onyen {} has a NULL zero width space".format(row[0]))
