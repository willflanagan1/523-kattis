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
import os.path as osp
import sys
import numpy as np
import pandas as pd
from config import course_name, assessment_folders
from inputs import inputs

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
   """Generate a notes data entry screen"""
   return

@app.post("/submit")
def submit():
   """ Submit Problem """
   # store file in kattis submissions folder or db
   return syllabi("home")

@app.post("/create-problem")
@auth(user_is_admin)
@view("create")
@with_db
def create_problem(db):
   description = request.forms.get("description")
   solution = request.forms.get("solution")
   log(f"description: {description}, solution: {solution}")
   fb = [description, solution]

   db.execute("""insert into problems (description, solution)
                  values (%s, %s)""", fb,)