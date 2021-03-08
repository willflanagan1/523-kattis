#!/usr/bin/env python3
""" Arbitrary assign each student to a team
    For now, this is required for some things
    In the future, we really should not require teams
 """

import contextlib
import db
from ZWSP import ZWSP

zwsp_object = ZWSP()

db.init() # Ensure tables set up


connection = db.open_db()
with contextlib.closing(connection):
   cursor = connection.cursor()
   cursor.execute('''
                 SELECT onyen
                     FROM roll
                     where section = '003' ''')
   admins = [row.onyen for row in cursor.fetchall()]
print(f"admins={admins}")

member_number = 0
team_number = 0
for admin in admins:
   connection = db.open_db()
   with contextlib.closing(connection):
      cursor = connection.cursor()
      onyen = admin
      cursor.execute('''
           INSERT INTO teams
              (onyen, member_number, team_number)
           VALUES( %(onyen)s, %(member_number)s, %(team_number)s)
           ON CONFLICT (onyen) DO UPDATE SET
              (member_number, team_number) = (%(member_number)s, %(team_number)s)''',
                     {'onyen': onyen, 'member_number': member_number, 'team_number': team_number},
                     )
      member_number += 1
      connection.commit()

team_number = 0
for section in ['002', '001']:
   connection = db.open_db()
   with contextlib.closing(connection):
      cursor = connection.cursor()
      cursor.execute('''
                    SELECT onyen
                        FROM roll
                        where section = %(section)s 
                      ''',
                     {'section': section},
                     )
      onyens = [row.onyen for row in cursor.fetchall()]
   print(f"onyens={onyens}")

   num_teams = len(onyens) // 5 + 2
   member_number = 0

   for onyen in onyens:
      connection = db.open_db()
      with contextlib.closing(connection):
         cursor = connection.cursor()
         cursor.execute('''SELECT onyen, member_number, team_number
                            FROM teams
                            WHERE onyen=%s''',
                        [onyen])

         try:
            db_onyen, db_member_number, db_team_number = cursor.fetchone()
         except:  # pylint: disable=bare-except
            db_onyen = ''

         if member_number%4 == 0:
            team_number += 1
            member_number = 1
         else:
            member_number += 1

         if not db_onyen or (db_member_number != member_number) or (db_team_number != team_number):
            cursor.execute('''
                 INSERT INTO teams
                    (onyen, member_number, team_number)
                 VALUES( %(onyen)s, %(member_number)s, %(team_number)s)
                 ON CONFLICT (onyen) DO UPDATE SET
                    (member_number, team_number) = (%(member_number)s, %(team_number)s)''',
                           {'onyen': onyen, 'member_number': member_number,
                            'team_number': team_number},
                           )
            connection.commit()
