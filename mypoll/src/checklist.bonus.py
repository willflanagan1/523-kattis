#! /usr/bin/python3
""" Given a set of worksheets and checklist date, give out worksheet bonuses """

from datetime import datetime
import dotenv
from COMP550.app import set_worksheet_bonus

import Args
import db

db.init()
dotenv.load_dotenv()
dotenv_values = dotenv.dotenv_values()

def get_argument():
   """ Read the args and return a date object from the date=
       the worksheets= and the optional bonus """
   args = Args.Parse(date=str, worksheets=str, bonus=False)
   try:
      date = args.date
      date = [int(x) for x in date.split('-')]
      date = datetime(date[0], date[1], date[2]).date()
   except:
      print(f"Date {args.date} should be in format yyyy-mm-dd")
      raise

   try:
      worksheets = args.worksheets.split(',')
   except:
      print(f"Worksheets {args.worksheets} should be in the form of "
            "\"worksheet-demo,worksheet00-pseudo\"")
      print("No blanks or quoates allowed by the parser Comma separated!")
      raise

   bonus = bool(args.bonus)  # Force to True/Fals
   return date, worksheets, bonus

@db.with_db
def get_onyens_completed_checklist(date, db):
   """ Return the onyens that have the checklist date with the
       same count as jmajikes
   """
   db.execute('''
      select CL.onyen, count(CL.item)
         from checklist as CL,
              roll as R
         where CL.onyen=R.onyen  
           and R.section != '000'
           and agenda_type = 'student'
           and CL.lecture_date = %(date)s
           and R.onyen not like 'student%%'
           and NOT EXISTS(select * from checklist as CL2
                          where CL.onyen = CL2.onyen
                            and checklist = 'student'
                            and CL.item = CL2.item
                            and CL.time < CL2.time)
         group by CL.onyen''',
              dict(date=date))
   cl_dict = {rec.onyen: rec.count for rec in db.fetchall()}
   onyens = [k for k in cl_dict if cl_dict[k] == cl_dict['jmajikes']]
   return onyens

@db.with_db
def get_worksheets_submitted(worksheets, onyens, db):
   """ Return the subset of onyens that submitted all the workshsets """

   db.execute('''
      with _worksheets as (
          select onyen, key, row_number() over
                    (partition by key order by key) as row_number 
                               from post P, answer A
                               where A.postid = P.id
                                 and onyen in %(onyens)s
                                 and key in %(worksheets)s
                                 and A.field = '_submit'
                                 and A.value = 'Submit'
                                 and key in ('worksheet-demo', 'worksheet00-pseudo')
                    )

      select onyen, count(key) from _worksheets where row_number=1 group by onyen 
     ''', dict(onyens=tuple(onyens), worksheets=tuple(worksheets)))
   onyens = {rec.onyen: rec.count for rec in db.fetchall()}
   onyens = [k for k in onyens if onyens[k] == len(worksheets)]
   return onyens

@db.with_db
def give_bonus(date, onyens, db):
   """ Give students bonus's for checklist """
   reason = f"Checklist worksheet_bonus for {date}"
   db.execute('''
      select onyen
      from roll
      where onyen in %(onyens)s
        and onyen not in (select onyen from worksheet_bonus 
                          where reason = %(reason)s)''',
              dict(reason=reason, onyens=tuple(onyens)))
   onyens = [rec.onyen for rec in db.fetchall()]
   if len(onyens) == 0:
      print(f"No one should get a bonus for {reason}")

   for onyen in onyens:
      set_bonus(onyen, reason)  # pylint:disable=no-value-for-parameter
      print(f"Set bonus for {onyen}: {reason}")
   return onyens

@db.with_db
def set_bonus(onyen, reason, db):
   """ Single commit worksheet bonus insertion """
   set_worksheet_bonus(db, onyen, 'jmajikes', reason)

if __name__ == '__main__':
   # No db, supplied for functions. Decorator used
   # pylint: disable=no-value-for-parameter
   date, worksheets, bonus = get_argument()
   onyens = get_onyens_completed_checklist(date)
   onyens = get_worksheets_submitted(worksheets, onyens)
   if bonus:
      onyens = give_bonus(date, onyens)
   else:
      print(f"Bonuses shouild be given to {onyens}")
