"""
 Describe and list the assessments for COMP 550
"""
import sys
from collections import namedtuple

Assessment = namedtuple('Assessment',
                        'name name_list num_toward_score percentage')

ws_assessments = Assessment(name='worksheet',
                            name_list=['worksheet-demo',
                                       'worksheet-00-pseudo',
                                       'worksheet-00-teams',
                                       'worksheet-chapter-1',
                                       'worksheet-chapter-2',
                                       'worksheet-chapter-3-1',
                                       'worksheet-Appendix-A',
                                       ],
                            num_toward_score=6,
                            percentage=7)
q_assessments = Assessment(name='quiz',
                           name_list=[],
                           num_toward_score=0,
                           percentage=0)
hwk_assessments = Assessment(name='homework',
                             name_list=[],
                             num_toward_score=0,
                             percentage=20)
m1_assessments = Assessment(name='Midterm1',
                            name_list=[],
                            num_toward_score=0,
                            percentage=20)
m2_assessments = Assessment(name='Midterm2',
                            name_list=[],
                            num_toward_score=0,
                            percentage=25)
fe_assessments = Assessment(name='FE',
                            name_list=[],
                            num_toward_score=0,
                            percentage=30)
extracredit_assessments = Assessment(name='extracredit',
                                     name_list=[],
                                     num_toward_score=1,
                                     percentage=25)
last_quiz_before_midterm1 = 'quiz04-mastermethod'
last_quiz_before_midterm2 = 'quiz-graph'
last_quiz_before_fe = None

def log(*args):
   """Print for debugging"""
   print(*args, file=sys.stderr)

def getAssessmentPts(db, assessment, onyen):
   ''' Get the number of points a student has toward a grade '''

   if len(assessment.name_list) == 0:
      return 0.0
   assert assessment.num_toward_score != 0, (
      f"For assessment {assessment} there are {len(assessment.name_list)}"
      " but none count toward score")

   db.execute("""
       select F.score, F.points_total
       from post P, feedback F
       where onyen = %(onyen)s and F.postid = P.id and P.key in %(keys)s
       """,
              {'onyen': onyen, 'keys': tuple(assessment.name_list)},
              )
   rows = db.fetchall()
   score = [row.score / row.points_total for row in rows]
   score = sorted(score, reverse=True)[:assessment.num_toward_score]
   average = sum(score) / assessment.num_toward_score
   return average * 100

def getExtraCreditPts(db, assessment, onyen):
   ''' Get the number of points a student has toward a grade '''

   if len(assessment.name_list) == 0:
      return 0.0
   assert assessment.num_toward_score != 0, (
      f"For assessment {assessment} there are {len(assessment.name_list)}"
      " but none count toward score")

   db.execute("""
        select P.key, F.score, F.points_total
        from post P, feedback F
        where onyen = %(onyen)s and F.postid = P.id and P.key in %(keys)s
        """,
              {'onyen': onyen, 'keys': tuple(assessment.name_list)},
              )
   rows = {row.key: row.score * 100 / row.points_total for row in db.fetchall()}
   return rows

def getQuizPts(db, assessment, onyen, m1_score, m2_score, fe_score):
   ''' Get the number of quiz points a student has toward a grade '''

   if len(assessment.name_list) == 0:
      return 0.0
   assert assessment.num_toward_score != 0, (
      f"For assessment {assessment} there are {len(assessment.name_list)}"
      " but none count toward score")

   index_last_m1 = assessment.name_list.index(last_quiz_before_midterm1)
   quizzes_b4_m1 = assessment.name_list[:index_last_m1+1]
   db.execute("""
        select F.score, F.points_total
        from post P, feedback F
        where onyen = %(onyen)s and F.postid = P.id and P.key in %(keys)s
        """,
              {'onyen': onyen, 'keys': tuple(quizzes_b4_m1)},
              )
   rows = db.fetchall()
   scores_b4_m1 = [max(100* row.score/row.points_total, m1_score) for row in rows]
   if len(scores_b4_m1) < len(quizzes_b4_m1):
      scores_b4_m1 = scores_b4_m1 + [m1_score] * (len(quizzes_b4_m1) - len(scores_b4_m1))

   index_last_m2 = assessment.name_list.index(last_quiz_before_midterm2)
   quizzes_b4_m2 = assessment.name_list[index_last_m1+1:index_last_m2+1]
   db.execute("""
        select F.score, F.points_total
        from post P, feedback F
        where onyen = %(onyen)s and F.postid = P.id and P.key in %(keys)s
        """,
              {'onyen': onyen, 'keys': tuple(quizzes_b4_m2)},
              )
   rows = db.fetchall()
   scores_b4_m2 = [max(100* row.score/row.points_total, m2_score) for row in rows]
   if len(scores_b4_m2) < len(quizzes_b4_m2):
      scores_b4_m2 = scores_b4_m2 + [m2_score] * (len(quizzes_b4_m2) - len(scores_b4_m2))

   scores_last_m2 = []
   if index_last_m2 > len(assessment.name_list) +1:
      quizzes_last_m2 = assessment.name_list[scores_last_m2+1:]
      db.execute("""
           select F.score, F.points_total
           from post P, feedback F
           where onyen = %(onyen)s and F.postid = P.id and P.key in %(keys)s
           """,
                 {'onyen': onyen, 'keys': tuple(quizzes_last_m2)}
                 )
      rows = db.fetchall()
      scores_last_m2 = [max(100* row.score/row.points_total, fe_score) for row in rows]
      if len(scores_last_m2) < len(quizzes_last_m2):
         scores_last_m2 = scores_last_m2 + [fe_score] * (len(quizzes_last_m2) -
                                                         len(scores_last_m2))

   scores = scores_b4_m1 + scores_b4_m2 + scores_last_m2
   scores = sorted(scores, reverse=True)[:assessment.num_toward_score]
   average = sum(scores) / assessment.num_toward_score
   return average

def updateGrades(db, onyen):
   ''' Update the grades table for a student '''

   db.execute("""
       select sum(points)
           from worksheet_bonus
           where onyen = %s
       """,
              [onyen],
              )
   worksheet_bonus = db.fetchone()[0]
   if worksheet_bonus is None:
      worksheet_bonus = 0

   extracredit = getExtraCreditPts(db, extracredit_assessments, onyen)
   fe = getAssessmentPts(db, fe_assessments, onyen)
   m2 = getAssessmentPts(db, m2_assessments, onyen)
   m1 = getAssessmentPts(db, m1_assessments, onyen)
   q = getQuizPts(db, q_assessments, onyen, m1, m2, fe)
   if (len(extracredit_assessments.name_list) > 0) and ('extra00' in extracredit):
      m1_extra = (100-m1) * extracredit['extra00'] / 100.0
   else:
      m1_extra = 0
   if (len(extracredit_assessments.name_list) > 0) and ('extra01' in extracredit):
      m2_extra = (100-m1) * extracredit['extra01']
   else:
      m2_extra = 0
   hwk = getAssessmentPts(db, hwk_assessments, onyen)
   if ws_assessments.num_toward_score:
      ws = round((getAssessmentPts(db, ws_assessments, onyen) +
                  worksheet_bonus / ws_assessments.num_toward_score), 2)
   else:
      ws = round(getAssessmentPts(db, ws_assessments, onyen), 2)

   midterm1boost = round(0.25 * (m2 - m1), 2) if m2 > m1 else 0
   midterm2boost = round(0.20 * (fe - m2 - midterm1boost), 2) if fe > m2 else 0

   total = (round(fe * fe_assessments.percentage / 100, 2) +
            round(m2_extra * m1_assessments.percentage / 100, 2) +
            round(m2 * m2_assessments.percentage / 100, 2) +
            round(m1_extra * m1_assessments.percentage / 100, 2) +
            round(m1 * m1_assessments.percentage / 100, 2) +
            round(hwk * hwk_assessments.percentage / 100, 2) +
            round(q * q_assessments.percentage / 100, 2) +
            round(ws * ws_assessments.percentage / 100, 2) +
            round(midterm1boost * m1_assessments.percentage/ 100, 2) +
            round(midterm2boost * m2_assessments.percentage/ 100, 2))
   if total >= 95:
      letter_grade = 'A'
   elif total >= 90:
      letter_grade = 'A-'
   elif total >= 86 + 2/3:
      letter_grade = 'B+'
   elif total >= 83 + 1/3:
      letter_grade = 'B'
   elif total >= 80:
      letter_grade = 'B-'
   elif total >= 76 + 2/3:
      letter_grade = 'C+'
   elif total >= 73 + 1/3:
      letter_grade = 'C'
   elif total >= 70:
      letter_grade = 'C-'
   elif total >= 65:
      letter_grade = 'D+'
   elif total >= 60:
      letter_grade = 'D'
   else:
      letter_grade = 'F'

   db.execute("""delete from grades where onyen = %(onyen)s""",
              {"onyen": onyen})
   db.execute("""
       insert into grades
          (onyen, letterGrade, total, fe, 
           midterm2Boost, midterm2, midterm1Boost, midterm1,
           homeworks, quizzes, worksheets, worksheet_bonus,
           midterm1extra, midterm2extra)
       values (%(onyen)s, %(letterGrade)s, %(total)s, %(fe)s, 
               %(midterm2Boost)s, %(midterm2)s, %(midterm1Boost)s, %(midterm1)s,
               %(homeworks)s, %(quizzes)s, %(worksheets)s, %(worksheet_bonus)s,
               %(midterm1extra)s, %(midterm2extra)s
              )
         """,
              {"onyen": onyen, "letterGrade": letter_grade, "total": total, "fe": fe,
               "midterm2Boost": midterm2boost, "midterm2": m2,
               "midterm1extra": m1_extra, "midterm2extra": m2_extra,
               "midterm1Boost": midterm1boost, "midterm1": m1,
               "homeworks": hwk, "quizzes": q, "worksheets": ws,
               "worksheet_bonus": worksheet_bonus},
              )
