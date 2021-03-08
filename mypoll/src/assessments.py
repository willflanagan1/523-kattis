"""
 Describe and list the assessments
"""
from collections import namedtuple
import importlib
import os.path as osp
from config import course_name

exists = course_name != '' and osp.exists(f'./{course_name}/assessments.py')
if exists:
    assessment_mod = importlib.import_module(f'{course_name}.assessments')

if exists:
    Assessment = assessment_mod.Assessment
    ws_assessments = assessment_mod.ws_assessments
    q_assessments = assessment_mod.q_assessments
    hwk_assessments = assessment_mod.hwk_assessments
    m1_assessments = assessment_mod.m1_assessments
    m2_assessments = assessment_mod.m2_assessments
    fe_assessments = assessment_mod.fe_assessments
    updateGrades = assessment_mod.updateGrades
else:
    Assessment = namedtuple('Assessment',
                            'name name_list num_toward_score percentage')
    ws_assessments = Assessment(name='worksheet',
                                name_list=['worksheet00-example'],
                                num_toward_score=43,
                                percentage=5)
    q_assessments = Assessment(name='quiz',
                               name_list=['quiz00-example'],
                               num_toward_score=6,
                               percentage=5)
    hwk_assessments = Assessment(name='homework',
                                 name_list=['homework00-example'],
                                 num_toward_score=4,
                                 percentage=25)
    m1_assessments = Assessment(name='Midterm1',
                                name_list=['m1-inception'],
                                num_toward_score=1,
                                percentage=20)
    m2_assessments = Assessment(name='Midterm2',
                                name_list=['m2-halloween'],
                                num_toward_score=1,
                                percentage=25)
    fe_assessments = Assessment(name='FE',
                                name_list=[],
                                num_toward_score=1,
                                percentage=25)

    def getAssessmentPts(db, assessment, onyen):
        ''' Get the number of points a student has toward a grade '''

        if len(assessment.name_list) == 0:
            return 0.0
        assert assessment.num_toward_score != 0, (
            f"For assessment {assessment} there are {len(assessment.name_list)} "
            "but none count toward score")

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

        fe = getAssessmentPts(db, fe_assessments, onyen)
        m2 = getAssessmentPts(db, m2_assessments, onyen)
        m1 = getAssessmentPts(db, m1_assessments, onyen)
        hwk = getAssessmentPts(db, hwk_assessments, onyen)
        q = getAssessmentPts(db, q_assessments, onyen)
        ws = getAssessmentPts(db, ws_assessments, onyen)
        total = (round(fe * fe_assessments.percentage / 100, 2) +
                 round(m2 * m2_assessments.percentage / 100, 2) +
                 round(m1 * m1_assessments.percentage / 100, 2) +
                 round(hwk * hwk_assessments.percentage / 100, 2) +
                 round(q * q_assessments.percentage / 100, 2) +
                 round(ws * ws_assessments.percentage / 100, 2))
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
               midterm2, midterm1,
               homeworks, quizzes, worksheets)
           values (%(onyen)s, %(letterGrade)s, %(total)s, %(fe)s,
                   %(midterm2)s, %(midterm1)s,
                   %(homeworks)s, %(quizzes)s, %(worksheets)s)
             """,
                   {"onyen": onyen, "letterGrade": letter_grade, "total": total, "fe": fe,
                    "midterm2": m2,
                    "midterm1": m1,
                    "homeworks": hwk, "quizzes": q, "worksheets": ws},
                   )
