"""
Imported from ../grades.py, takes a grade and possibly adjusts it

It should not be called directly

"""
import math

# pylint: disable=unused-argument

def get_feedback(key, user, section, theirAnswers, rubrics, result, info):
   """Given a graded assessment, take their answers and the rubric and return the result"""

   # Calculate the items that are correct
   correct = {tag: result[tag].get("correct", False) for tag in result}

   # Compute their score and their points total
   points_total = info.get("points_total", 100)
   points_limit = info.get("points_limit", points_total)
   score = min(points_limit,
               points_total - sum(
                  rubrics[K]["points"] for K in rubrics.keys()
                  if (K not in correct or not correct[K])))
   points_total = min(points_total, points_limit)
   feedback = ", ".join(K for K in rubrics.keys()
                        if (K in correct and not correct[K]))

   # Do any modifications that you may want to make on a per assessment basis
   if key == 'worksheetm2-select':
      # Remove question 'Select.k' from worksheetm2-select
      # points_total was updated in the content/worksheets/worksheetm2-select.tmd
      feedback = ", ".join(K for K in rubrics.keys()
                           if (K in correct and not correct[K] and (K != 'Select.k')))

   if feedback:
      feedback = "Incorrect: " + feedback
   else:
      feedback = "All correct"

   return correct, score, feedback, points_total

def handle_late_penalty(key, onyen, section, score, points_total, mins_late, max_penalty, rate, info):
   """ Given a assignment(key) and user/section, their score, the number
       of hours they're late, the maximum penalty, and the penalty rate...
       return the score and the late-penalty message
   """
   msg = ''

   if mins_late > 0:
      hours = math.ceil(mins_late / 60)
      penalty = min(max_penalty, rate * hours)
      penalty *= score
      msg = f"Late: {mins_late:.1f} minutes. "

      if penalty:
         msg = msg + f"Penalty: {penalty:.1f} points. "
         score -= penalty

   return score, msg
