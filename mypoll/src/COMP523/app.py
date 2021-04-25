"""
 COMP 523 Specific routes
"""
import site
site.addsitedir('..')


# pylint: disable=wrong-import-position, no-member, unsupported-membership-test
# pylint: disable=import-error, import-self
from appbase import app, auth, user_is_known, get_user, user_is_admin, allow_json, get_url
from app import renderTemplate, renderMarkdown
from app import not_found, not_allowed, user_in_roll
from bottle import view, request, redirect, HTTPError, static_file
from db import with_db
import dotenv
from editRubrics import editRubrics
from assessments import updateGrades, ws_assessments, q_assessments, hwk_assessments
from assessments import m1_assessments, m2_assessments, fe_assessments
from email.mime.text import MIMEText
from datetime import datetime
import smtplib
import os
import os.path as osp
import sys
import numpy as np
import pandas as pd
from config import course_name, assessment_folders
from inputs import inputs
from .dockerClient import run_submission
from subprocess import check_output
from datetime import datetime



assessment_list = [ws_assessments, q_assessments, hwk_assessments,
                   m1_assessments, m2_assessments, fe_assessments]

def log(*args):
   """Print for debugging"""
   print(*args, file=sys.stderr)

dotenv.load_dotenv()
dotenv_values = dotenv.dotenv_values()

@app.route("/syllabi/<page_name>", name="syllabi")
@with_db
@auth(user_is_known)
@view("syllabi")
def syllabi(page_name, db):
   """Render a page such as the syllabus, help, etc."""
   user = get_user()
   if user_is_admin(user) and request.query.user:
      original_user = user
      user = request.query.user
   else:
      original_user = ''
   if not user_in_roll(user, db):
      log(f"syllabi: {user} not enrolled in COMP523.")

   path = f"views/COMP523/{page_name}.html"
   if not osp.exists(path):
      not_found(db)

   title = ""
   with open(path, "rt") as fp:
      top = fp.readline()
      if top.startswith("# "):
         title = title + top[2:].strip()

   content = renderTemplate(path, user=user, title=title)
   content = renderMarkdown(content)
   if original_user == '':
      db.execute("""
         insert into fetched (time, onyen, key, ip, pages, url) values (%s, %s, %s, %s, %s, %s)""",
                 [datetime.now(), user, page_name, request.remote_addr, [], request.url],
                 )
   return {"base": content, "title": title, "user": user, "admin": user_is_admin(user),
           "agenda_type": 'student'}


@app.route("/", name="root")
@auth(user_is_known)
def home():
   """ Display home page """
   return syllabi("home")  # pylint: disable=no-value-for-parameter

@app.get("/create", name="create")
@auth(user_is_admin)
@view("create")
def create():
   """Generate a problem creation screen"""
   return

@app.post("/create-problem")
@auth(user_is_admin)
@view("create")
@with_db
def create_problem(db):
   """Creates a new problem based off admin input"""
   name = request.forms.get("name")
   description = request.forms.get("description")
   inputDesc = request.forms.get("inputDesc")
   outputDesc = request.forms.get("outputDesc")
   sampleIn = request.forms.get("sampleIn")
   sampleOut = request.forms.get("sampleOut")

   #inserts data into problems db
   fb = [name, description, inputDesc, outputDesc, sampleIn, sampleOut]
   db.execute("""insert into problems (name, description, inputDesc, outputDesc, sampleIn, sampleOut)
                 values (%s, %s, %s, %s, %s, %s)""", fb,)


@app.get("/problems", name="problems")
@auth(user_is_known)
@view("problems")
@with_db
def all_problems(db):
   """Generates screen with list of all problems"""
   db.execute("""select id, name from problems""")
   result = db.fetchall()
   problems = []
   for id, name in result: 
      problems.append({"id": id, "name": name})
   return dict(data=problems)

@app.get("/problem/<pid>", name="problem")
@auth(user_is_known)
@view("problem")
@with_db
def problems(db, pid):
   """Generates screen with specific problem details"""
   fb = [pid]
   db.execute("""select id, name, description, inputDesc, outputDesc, sampleIn, sampleOut from problems where id = %s""", fb)
   result = db.fetchall()
   problems = []
   for id, name, description, inputDesc, outputDesc, sampleIn, sampleOut in result: 
      problems.append({"id": id, "name": name, "description": description, "inputDesc": inputDesc, "outputDesc": outputDesc, "sampleIn": sampleIn, "sampleOut": sampleOut})
   return dict(data=problems)

@app.post("/submit/<pid>")
@auth(user_is_known)
@with_db
def submit(db, pid):
   """Submits student uploaded solution"""

   ct = datetime.now()
   user = get_user()

   #gets solution from form and checks language
   solution = request.files.get("solution")
   name, ext = os.path.splitext(solution.filename)
   if ext not in ('.py'):
        return "File extension not allowed."

   #gets input and output for the specific problem
   fb = [pid]
   db.execute("""select name, sampleIn, sampleOut from problems where id = %s""", fb)
   result = db.fetchall()
   for name, sampleIn, sampleOut in result:
      name = name
      sampleIn = sampleIn
      sampleOut = sampleOut

   #saves file into a tmp folder
   solution_save_path = f"COMP523/container/submissions"
   solution_file_path = "{path}/{file}".format(path=solution_save_path, file=solution.filename)
   solution.save(solution_file_path)

   with open("COMP523/container/submissions/sampleInput.txt", "w") as input_file:
      print(f"{sampleIn}", file=input_file)

   #TO DO: add different functions depending on language submitted. just need to create a check_ouput for each language
   #runs uploaded script with sampleIn and tests that the script output matches sampleOut
   try:
      script_output = run_submission(solution.filename)
      script_output = " ".join(script_output.split())
      sampleOut = " ".join(sampleOut.split())
      check_submission = (script_output == sampleOut)
   except:
      #if error, submission check is false
      check_submission = False

   #insert this submission instance into db
   fb = [ct, name, user, True, check_submission]
   db.execute("""insert into user_submissions (date, name, onyen, submitted, correct)
      values(%s, %s, %s, %s, %s)""", fb,)

   #deletes the file from the tmp folder
   if os.path.exists(solution_file_path):
      os.remove(solution_file_path)

@app.get("/submissions", name="submissions")
@auth(user_is_known)
@view("submissions")
@with_db
def submissions(db):
   """Gets submissions from db given user"""
   user = get_user()
   fb = [user]
   db.execute("""select id, date, onyen, name, submitted, correct from user_submissions where onyen = %s order by date desc""", fb)
   result = db.fetchall()
   submissions = []
   for id, date, onyen, name, submitted, correct in result: 
      submissions.append({"id": id, "date": date, "onyen": onyen, "name": name, "submitted": submitted, "correct": correct})
   return dict(data=submissions)


