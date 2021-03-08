#!/usr/bin/env python3
"""Incrementally grade assignments for mypoll"""

import pandas as pd
import Args
from datetime import datetime
import math
import db
import importlib
import os.path as osp
import re
from wagnerfischerpp import WagnerFischer
from itertools import groupby
from evalInContext import evalMultiple

from config import course_name
exists = course_name != '' and osp.exists(f'./{course_name}/grade.py')
assert exists, f'You must define course_name={course_name} and./{course_name}/grade.py '\
               f'as an exit for grading'

grade_mod = importlib.import_module(f'{course_name}.grade')
get_feedback = grade_mod.get_feedback
handle_late_penalty = grade_mod.handle_late_penalty

# Note:  changed field='_submit" and value='Submit' to
# field='_submit' and value like '%%Submit%%' due to copying
# codes, ZWSPs get appended to the submit field

class Grader:
   """Handle grading a submission"""

   def __init__(self, key, cursor):
      """Grade posts for key"""
      self.key = key
      self.cursor = cursor
      self.cursor.execute("""select questions, info from rubrics where key = %s""", [key])
      row = self.cursor.fetchone()
      if row:
         self.rubrics = row.questions
         self.info = row.info
         self.exam = self.info.get("exam", 0)
         self.ps = "due" in self.info
      else:
         raise "missing rubrics for " + key

   def grade(self, user):
      """Compute grades"""
      if True: # self.exam:  pylint: disable=using-constant-test
         self.gradeExam(user)
      else: # elif self.ps:
         self.gradeProblemSet(user)

   def fetchExamSubmission(self, user):
      """Fetch the first submission where they
         pressed the submit button and
         included a valid code"""
      return pd.read_sql("""
            with
            -- get first fetch for computing duration
            firstfetch as (
              select distinct on (F.onyen) F.onyen, F.time
                from fetched F, roll R
                where F.key = %(key)s and
                      F.onyen = %(onyen)s and
                      F.onyen = R.onyen
                order by F.onyen, F.time)

            -- get the post id, onyen, time, and duration in minutes
            select distinct on (P.onyen) -- only the first
            P.id, P.onyen, R.section, P.time,
            -- compute the time they had it open
            extract(epoch from (P.time - F.time)) / 60 as duration
            from post P,
                 -- answer A1,
                 answer A2,
                 -- codes C,
                 firstfetch F,
                 roll R
            where P.key = %(key)s 
                and P.onyen = %(onyen)s 
                -- and P.id = A1.postid 
                and P.id = A2.postid 
                and F.onyen = P.onyen and F.onyen = R.onyen 
                -- and A1.field = '_submitCode' 
                -- and A1.value = C.code 
                and A2.field = '_submit' 
                and A2.value like '%%Submit%%' 
                -- codes are valid for 2 minutes
                -- and P.time < C.time
            order by P.onyen, P.id""",
                         db,
                         params={"key": self.key, "onyen": user},
                         )

   def fetchPartialSubmissions(self, user):
      """Return submissions for partial credit"""
      return pd.read_sql("""
            select P.id, P.onyen, P.time
            from post P,
                 -- answer A1,
                 answer A2
            where P.key = %(key)s
                  and P.onyen = %(onyen)s
                  -- and P.id = A1.postid
                  and P.id = A2.postid
                  -- and A1.field = '_submitCode'
                  -- and A1.value = 'partial'
                  and A2.field = '_submit'
                  and A2.value like '%%Submit%%' """,
                         db,
                         params={"key": self.key, "onyen": user},
                         )

   def gradeExam(self, user):
      """Grade a student exam with partial credit"""
      if args.verbose:
         print("gradeExam", user)
      # get the first valid post
      valid = self.fetchExamSubmission(user)
      if valid.empty:
         if args.verbose:
            print("no valid submission")
         return
      # I'm trying avoid the double application on the first row
      # that apply does
      # results = valid.apply(self.gradeOne, axis=1)
      results = pd.DataFrame(self.gradeOne(row) for row in valid.itertuples())
      results = results.apply(self.latePenalty, axis=1)
      if args.verbose >= 0:
         row = results.iloc[0]
         print(f"gradeExam: key {self.key} onyen {row.onyen} post id: "
               f" {row.id} percent: {math.ceil( 100*row.score/row.points_total)} {row.feedback}")
      # grade the partial credit submissions if enabled
      dopartial = self.info.get("partial", False)
      if dopartial:
         partial = self.fetchPartialSubmissions(user)
         partial = partial[~partial.id.isin(valid.id)]
         # avoid apply duplicate eval
         # partials = partial.apply(self.gradeOne, axis=1)
         partials = pd.DataFrame(self.gradeOne(row) for row in partial.itertuples())
         first = results.set_index("onyen")
         partials = partials.join(first, on="onyen", rsuffix="_f")
         partials = partials.apply(self.partialOne, axis=1)

      if args.validate:
         self.compareFeedback(results)
         if dopartial:
            self.compareFeedback(partials)

      elif not args.testing:
         self.updateFeedback(results, True)
         if dopartial:
            self.updateFeedback(partials)

      else:
         for row in results.itertuples():
            print('%s,%f,"%s"' % (row.onyen, row.score, row.feedback))
         if dopartial:
            for row in partials.itertuples():
               print(row.onyen, row.score, row.feedback)

   def gradeProblemSet(self, user):
      """Grade all PS submissions for a single user"""
      valid = pd.read_sql("""
            -- get the post id, onyen, and time
            select P.id, P.onyen, P.time
            from post P
            where P.key = %(key)s and
                  P.onyen = %(onyen)s
            order by time""",
                          db,
                          params={"key": self.key, "onyen": user},
                          )

      results = valid.apply(self.gradeOne, axis=1)
      results = results.apply(self.latePenalty, axis=1)

      if args.validate:
         self.compareFeedback(results)

      elif not args.testing:
         self.updateFeedback(results, False)

      else:
         for row in results.itertuples():
            print(row.onyen, row.feedback)

   # process each post producing feedback
   def gradeOne(self, row):
      """Grade a single assignment producing score and feedback"""
      # I'm doing this dance to avoid the apply double evaluation bug
      row = row._asdict()
      if args.verbose >= 0:
         print(f"gradeOne: grading key {self.key} onyen {row['onyen']} post id {row[r'id']}")
      postid = row["id"]
      # grab the values they submitted, store in a dictionary
      theirAnswers = self.getAnswers(postid)
      #    Add debug to the program
      # if self.key == 'worksheetxc':
      #    if 'Lost' in theirAnswers:
      #       theirAnswers['Lost'] += f';print("{row["onyen"]}", "1,1,2", lost_array(1,1,2))'
      #       theirAnswers['Lost'] += f';print("{row["onyen"]}", "2,1,2", lost_array(2,1,2))'
      #       theirAnswers['Lost'] += f';print("{row["onyen"]}", "3,1,2", lost_array(3,1,2))'
      #       theirAnswers['Lost'] += f';print("{row["onyen"]}", "2,2,4", lost_array(2,2,4))'
      result = evalMultiple(theirAnswers, self.rubrics)

      # Call the "plugin" to determine the message
      correct, row["score"], row["feedback"], row["points_total"] = (
         get_feedback(self.key, row['onyen'], row['section'], theirAnswers, self.rubrics, result,
                      self.info))

      if args.verbose >= 0:
         print(f"gradeOne: key {self.key} onyen {row['onyen']} feedback: {row['feedback']}")
         for q, c in correct.items():
            row[q] = c

      # compare what they saw to my results
      check = theirAnswers.get("_check")
      if check:
         for i, k in enumerate(tagSort(correct.keys())):
            if check[i] != "-" and check[i] == "1" and not correct[k]:
               print(f"{row['onyen']}: bad check {k} {postid}")

      return row

   def getInfo(self, onyen, key, section, default=None):
      """Get info allowing for exceptions"""
      exceptions = self.info.get("exceptions", {})
      info = {**self.info,
              **exceptions.get(f"_{section}", {}),
              **exceptions.get(onyen, {})}
      return info.get(key, default)

   def getAnswers(self, postid):
      """Retrieve the answers for a post"""
      self.cursor.execute("""
            select A.field, A.value
            from Answer A
            where A.postid = %s and A.field NOT LIKE '\_%%'
            order by A.id asc
        """,
                          [postid],
                          )
      answers = {K: V for K, V in cursor}
      return answers

   def latePenalty(self, row):
      """Apply late penalties when required"""
      # apply late penalty
      row["late"] = 0
      if self.exam:
         allowed = self.getInfo(row.onyen, "duration", row.section) * (
            1 + roll.loc[row.onyen, "extended"]
            )
         row.late = max(0, row.duration - allowed)
         rate = self.getInfo(row.onyen, "penalty", row.section, 50)
      elif self.ps:
         due = datetime.strptime(self.getInfo(row.onyen, "due", row.section), "%Y-%m-%d %H:%M:%S")
         row.late = max(0, (row.time - due).total_seconds() / 60)
         rate = self.getInfo(row.onyen, "penalty", row.section, 0.02)
      row.score, msg = handle_late_penalty(self.key, row.onyen, row.section, row.score, 
                                           row.points_total, row.late,
                                           self.getInfo(row.onyen, "maxpenalty", row.section,
                                                        args.maxpenalty), rate, self.info)
      row.feedback = msg + row.feedback

      return row

   def partialOne(self, row):
      """Compute partial credit"""
      row = row.copy()
      if row.score != 100:
         row.score = 0
         return row
      pa = self.getAnswers(row.id)
      fa = self.getAnswers(row.id_f)
      feedback = []
      total_credit = 0
      for k in self.rubrics:
         # the first submission is wrong
         if not row[k]:
            row.score = 0
            return row
         if not row[k + "_f"]:
            answer = self.rubrics[k]
            # no partial credit for simple questions
            if answer["kind"] in ["select", "checkbox"]:
               credit = answer.get("points", 0.0) * 0.25
               feedback.append(f"{k} c={credit:.1f}")
            else:
               distance, credit = getCredit(fa[k], pa[k], answer)
               feedback.append(f"{k} d={distance} c={credit:.1f}")
               if args.verbose > 3:
                  print(k, distance, credit, fa[k], pa[k])
            total_credit += credit
      row.feedback = f"Partial({total_credit:.1f}) " + ", ".join(feedback)
      row.score = row.score_f + total_credit
      if math.isnan(row.score):
         row.score = 0.0
      return row

   def updateFeedback(self, results, clear=False):
      """Update the db feedback table"""
      # clear old feedback for exams where there should be only one
      # record the feedback in the db
      for row in results.itertuples():
         if clear:
            cursor.execute("""
                    delete from feedback F
                    using post P
                    where F.postid = P.id and
                          P.key = %(key)s and
                          P.onyen = %(onyen)s
                """,
                           {"key": self.key, "onyen": row.onyen},
                           )
         cursor.execute("""
                insert into feedback (postid, score, points_total, msg)
                values (%(postid)s, %(score)s, %(points_total)s, %(msg)s)
                on conflict (postid)
                do update set score=%(score)s, points_total=%(points_total)s, msg=%(msg)s""",
                        {"postid": row.id, "score": row.score,
                         "points_total": row.points_total, "msg": row.feedback})
      db.commit()

   def compareFeedback(self, results):
      """For testing feedback to make sure it did not change"""
      for row in results.itertuples():
         cursor.execute("""
                select P.onyen, F.postid, F.score, F.msg
                from feedback F, post P
                where F.postid = %(postid)s and
                      P.id = F.postid""",
                        {"postid": row.id},
                        )
         r = cursor.fetchone()
         if not r:
            print("not present", row.id)

         elif abs(r.score - row.score) > 0.01 or r.msg != row.feedback:
            print(f"{r.onyen} {row.id} {r.score:.2f}={row.score:.2f} "
                  f"{r.msg}={row.feedback}")


def tagSort(tags):
   """Sort questions in reasonable order"""
   return sorted(
      tags,
      key=lambda tag: [
         s.isdigit() and int(s) or s for s in re.findall(r"\d+|\D+", tag)])


symbols = re.compile(r"[$a-zA-Z][a-zA-Z0-9]*|" r"0x[0-9a-fA-F]+|[\d.]+|<<|>>|\*\*|\S")


def getSymbols(text):
   """Convert string to list of symbols"""
   text = re.sub(r"#.*", "", text)
   return symbols.findall(text)


def getDistance(original, partial):
   """Compute the edit distance"""
   return WagnerFischer(
      original, partial, insertion=lambda s: 1 if s not in "()" else 0).cost


def getCredit(original, corrected, answer):
   """Compute the partial credit for a problem"""
   # convert code and expressions to list of symbols
   if answer["kind"] in ["expression"]:
      original = getSymbols(original)
      corrected = getSymbols(corrected)
      expected = getSymbols(answer["solution"])
   else:
      expected = answer["solution"]
   distance = getDistance(original, corrected)
   elen = len(expected)
   # we could parameterize these per question if desired.
   dmin = max(1, 0.1 * elen)
   dmax = max(2, 0.5 * elen)
   p = (distance - dmin) / (dmax - dmin)
   p = max(0, min(1, p))
   factor = 0.75 * (1 - p) + 0.25 * p
   return distance, factor * answer["points"]


if __name__ == "__main__":
   args = Args.Parse(
      testing=0,
      verbose=0,
      validate=0,
      list=0, # set to non-zero to get a list of items to grade
      force="",  # set to force grading an item
      user="",  # set to select only one user
      maxpenalty=0.50,  # set to reduce max penalty
      )

   # ## Connect to the class db
   db.init()
   db = db.open_db()
   cursor = db.cursor()

   # ## Get the classroll
   roll = pd.read_sql("""select * from roll""", db, index_col="onyen")

   # find those who need grading
   if args.force:
      cursor.execute("""
            select distinct key, onyen
            from post P, answer A
            where P.key = %(key)s and
                  P.id = A.postid and
                  A.field = '_submit' and
                  A.value like '%%Submit%%'
            order by key, onyen""",
                     {"key": args.force},
                     )
   else:
      cursor.execute("""
            select distinct key, onyen
            from post P, answer A
            where P.id > (select coalesce(max(postid), 0) from feedback) and
                  P.id = A.postid and
                  A.field = '_submit' and
                  A.value like '%%Submit%%'
            order by key, onyen"""
                     )
   toGrade = cursor.fetchall()
   if args.user:
      toGrade = [(k, o) for k, o in toGrade if o == args.user]
   print(f"{len(toGrade)} to grade")

   for key, group in groupby(toGrade, lambda x: x[0]):
      if args.list:
         print(f"Submissions of {key} needed to grade:")
      else:
         grader = Grader(key, cursor)
         if args.verbose:
            print(f"grading {key}")
      for _, onyen in group:
         if args.verbose or args.list:
            print(onyen)
         if not args.list:
            grader.grade(onyen)
