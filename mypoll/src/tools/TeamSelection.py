#!/usr/bin/env python3

import contextlib
import db
import os.path as osp
import numpy as np
import pandas
import sys
from config import ZWSP
from collections import namedtuple


db.init() # Ensure tables set up

# select * from post where id=13;
# select * from answer where postid=13
# select distinct on (P.onyen)  P.id, P.onyen from post P, answer A where P.key='worksheet00-teams' and P.id = A.postid and A.field = '_submit' and A.value like '%%Submit%%' order by P.onyen, P.id;

KEY='worksheet00-teams'

connection = db.open_db()
with contextlib.closing(connection):
   cursor = connection.cursor()
   cursor.execute('''select distinct on (P.onyen) P.id, P.onyen
                     from post P, answer A 
                     where P.key= %(key)s 
                       and P.id = A.postid 
                       and A.field = '_submit' 
                       and A.value like '%%Submit%%'
                     order by P.onyen, P.id''',
                     {'key': KEY},
                  )
   rows = [{'postid': row.id, 'onyen': row.onyen}
           for row in cursor.fetchall() ]

team_choices = []
for row in rows:
   connection = db.open_db()
   with contextlib.closing(connection):
      cursor = connection.cursor()
      cursor.execute('''select value 
                        from answer 
                        where postid = %(postid)s
                          and field in ('Student.1', 'Student.2', 'Student.3') ''',
                     {'postid': row['postid']},
                     )
      choices = [ x.value for x in cursor.fetchall() ]
      choices.append(row['onyen'])
      while 'NONE' in choices:
         index = choices.index('NONE')
         choices.pop(index)
      while '' in choices:
         index = choices.index('')
         choices.pop(index)

      choices = sorted(choices, reverse=True)
      team_choices.append(choices)
team_choices.sort(key=lambda x: str(x))

 
final_teams = {} 
team_sections = {}
for team in team_choices:
   team = tuple(team)
   if 'jmajikes' in team:
       continue
   if team not in final_teams.keys():
       connection = db.open_db()
       with contextlib.closing(connection):
           cursor = connection.cursor()
           cursor.execute('''select distinct(section)
                             from roll
                             where onyen in %s
                          ''',
                          [ team ],
                          )
           sections = cursor.fetchall()
           assert len(sections) == 1, f"For team {team} members are in sections {sections}"
       final_teams[team] = 0
       team_sections[team] = sections[0].section
   final_teams[team] += 1

final_teams2 = {1: [], 2: [], 3:[], 4: []} 
for team in final_teams:
   if len(team) == final_teams[team]:
      final_teams2[len(team)].append(team)
   else:
      print(f"Mismatch {len(team)} {team}")

for section in ['002', '001']:
   print("Section ", section)
   for index in range(4,0, -1):
     for team in final_teams2[index]:
        if section ==team_sections[team]:
             print(team)
  
import pdb; pdb.set_trace()
