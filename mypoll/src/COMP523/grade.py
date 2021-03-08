"""
Imported from ../grades.py, takes a grade and possibly adjusts it

It should not be called directly

"""
import math
import re

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
   if key == 'worksheet-demo':
      q = 'Multiple.Choice'
      if not correct[q]:
        feedback = re.sub(q, '', feedback) 
        score += rubrics[q]['points']

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

   # For COMP550, any worksheet handed in on time that gets 75-99%, give 'em a 100%
   if (key == 'worksheet-00-teams') and (mins_late == 0):
      score = points_total
   if (key.startswith("worksheet") and (mins_late == 0) and
       (.75 * points_total <= score < points_total)):
      msg += "75% or better worksheet gets 100% "
      score = points_total

   if mins_late > 0:
      hours = math.ceil(mins_late / 60)
      penalty = min(max_penalty, rate * hours)
      penalty *= score
      msg = f"Late: {mins_late:.1f} minutes. "

      if penalty:
         msg = msg + f"Penalty: {penalty:.1f} points. "
         score -= penalty

   # For COMP550, any worksheet handed in has a minimum of 50%
   if key.startswith("worksheet"):
      if score < 0.5 * points_total:
         score = 0.5 * points_total
         msg += "Worksheet min score 50% "

   return score, msg
